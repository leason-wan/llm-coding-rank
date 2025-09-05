import math
import random
import sys
import pygame

Vec2 = pygame.math.Vector2

# ------------ 参数 ------------
W, H = 900, 900
CENTER = Vec2(W / 2, H / 2)

GRAVITY = 800.0  # 像素/秒^2
BALL_RADIUS = 10
BALL_RESTITUTION = 1.0  # 完全弹性

LINE_COLOR = (230, 230, 230)
BG_COLOR = (15, 15, 20)

FPS = 120
SUBSTEPS = 3  # 每帧物理子步，增大可减小穿透

# 六边形从小到大的外接圆半径（顶点到中心的距离）
HEX_RADII = [90, 170, 250, 330]

# 角速度（弧度/秒），按“顺时针/逆时针/顺时针/逆时针”
# 数学上 CCW 为正，CW 为负；因此用 [-, +, -, +]
OMEGAS = [-0.8, +0.6, -0.5, +0.4]

# 每个六边形缺失的边索引（0~5），固定不变但随整体一起旋转
MISSING_SIDE_INDEX = 0

LINE_WIDTH = 3


def rand_color():
    # 随机亮色方便区分
    return (random.randint(40, 255), random.randint(40, 255), random.randint(40, 255))


def closest_point_on_segment(a: Vec2, b: Vec2, p: Vec2):
    ab = b - a
    ab_len2 = ab.length_squared()
    if ab_len2 == 0:
        return Vec2(a)
    t = (p - a).dot(ab) / ab_len2
    t = max(0.0, min(1.0, t))
    return a + t * ab


class Ball:
    __slots__ = ("pos", "vel", "r", "color")

    def __init__(self, pos, vel, r, color):
        self.pos = Vec2(pos)
        self.vel = Vec2(vel)
        self.r = float(r)
        self.color = color


class RotatingHex:
    __slots__ = ("R", "omega", "angle", "missing")

    def __init__(self, radius, omega, missing_index=0, init_angle=0.0):
        self.R = float(radius)
        self.omega = float(omega)
        self.angle = float(init_angle)
        self.missing = int(missing_index)

    def update(self, dt):
        self.angle += self.omega * dt

    def vertices(self):
        # 返回当前世界坐标下 6 个顶点
        verts = []
        for i in range(6):
            theta = self.angle + i * math.tau / 6.0
            verts.append(CENTER + Vec2(math.cos(theta), math.sin(theta)) * self.R)
        return verts

    def sides(self):
        # 返回 5 条存在的边段（(p1, p2) 列表），跳过缺失边
        v = self.vertices()
        segs = []
        for i in range(6):
            if i == self.missing:
                continue
            p1 = v[i]
            p2 = v[(i + 1) % 6]
            segs.append((p1, p2))
        return segs

    def point_velocity(self, point: Vec2):
        # 刚体绕 CENTER 转动时，点的速度 u = ω × r （2D: (-ω*y, ω*x)）
        r = point - CENTER
        return Vec2(-self.omega * r.y, self.omega * r.x)


def resolve_ball_ball(b1: Ball, b2: Ball):
    # 完全弹性、等质量碰撞
    delta = b2.pos - b1.pos
    dist2 = delta.length_squared()
    r_sum = b1.r + b2.r
    if dist2 == 0:
        # 完全重合，随机微扰
        n = Vec2(1, 0)
        dist = 0.0
    else:
        dist = math.sqrt(dist2)
        if dist >= r_sum:
            return
        n = delta / dist

    # 相对速度沿法线的分量
    rel = b1.vel - b2.vel
    rel_n = rel.dot(n)
    if rel_n > 0:
        # 分离中，无需处理
        pass
    else:
        # 冲量（等质量 + e=1）
        j = -rel_n
        b1.vel += -j * n
        b2.vel += +j * n

    # 位置纠正（半半分离），避免重叠粘连
    overlap = r_sum - dist if dist != 0 else r_sum
    correction = 0.5 * overlap + 0.1  # slop
    b1.pos -= correction * n
    b2.pos += correction * n


def resolve_ball_segment(ball: Ball, p1: Vec2, p2: Vec2, wall_vel_at_cp: Vec2):
    # 找最近点
    cp = closest_point_on_segment(p1, p2, ball.pos)
    d = ball.pos - cp
    dist2 = d.length_squared()
    r = ball.r
    if dist2 > r * r:
        return

    # 法线（指向小球）
    if dist2 > 1e-12:
        n = d / math.sqrt(dist2)
    else:
        # 退化：用边的法线并指向小球
        seg = p2 - p1
        if seg.length_squared() == 0:
            n = Vec2(0, -1)
        else:
            n = Vec2(-seg.y, seg.x).normalize()
            if (ball.pos - cp).dot(n) < 0:
                n = -n

    # 相对法向速度：仅当逼近时才反射，避免反复加能
    v_rel = ball.vel - wall_vel_at_cp
    vn = v_rel.dot(n)
    if vn >= 0:
        # 在远离或掠过，不处理速度，但仍做位置分离
        pass
    else:
        # 速度反射：v' = v - 2 ((v - u)·n) n
        ball.vel = ball.vel - 2.0 * vn * n

    # 位置修正，推出边界
    penetration = r - math.sqrt(dist2) if dist2 > 1e-12 else r
    ball.pos += (penetration + 0.2) * n  # 少量 slop 防止持续重叠


def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("旋转六边形盒子 - 弹性碰撞物理模拟")
    clock = pygame.time.Clock()

    # 初始化四个六边形
    hexes = [
        RotatingHex(HEX_RADII[0], OMEGAS[0], MISSING_SIDE_INDEX, init_angle=0.0),
        RotatingHex(HEX_RADII[1], OMEGAS[1], MISSING_SIDE_INDEX, init_angle=math.pi / 12),
        RotatingHex(HEX_RADII[2], OMEGAS[2], MISSING_SIDE_INDEX, init_angle=math.pi / 6),
        RotatingHex(HEX_RADII[3], OMEGAS[3], MISSING_SIDE_INDEX, init_angle=math.pi / 4),
    ]

    balls = []

    running = True
    while running:
        dt_frame = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # 从中心释放小球，初速度为 0（重力生效）
                balls.append(Ball(CENTER, Vec2(0, 0), BALL_RADIUS, rand_color()))

        # 物理更新（子步）
        dt = dt_frame / SUBSTEPS
        for _ in range(SUBSTEPS):
            # 更新六边形角度
            for hx in hexes:
                hx.update(dt)

            # 重力 + 积分
            for b in balls:
                b.vel.y += GRAVITY * dt
                b.pos += b.vel * dt

            # 小球-小球碰撞
            n_b = len(balls)
            for i in range(n_b):
                for j in range(i + 1, n_b):
                    resolve_ball_ball(balls[i], balls[j])

            # 小球-六边形边碰撞（带动边速度）
            for b in balls:
                for hx in hexes:
                    for p1, p2 in hx.sides():
                        # 计算最近点并用其速度
                        cp = closest_point_on_segment(p1, p2, b.pos)
                        u = hx.point_velocity(cp)
                        resolve_ball_segment(b, p1, p2, u)

            # 边界限制（可选：屏幕边界，处理避免飞出视野）
            # 这里不作为刚性墙，仅作软限制
            margin = 20
            if balls:
                for b in balls:
                    if b.pos.x < margin:
                        b.pos.x = margin
                        b.vel.x = abs(b.vel.x)
                    elif b.pos.x > W - margin:
                        b.pos.x = W - margin
                        b.vel.x = -abs(b.vel.x)
                    if b.pos.y < margin:
                        b.pos.y = margin
                        b.vel.y = abs(b.vel.y)
                    elif b.pos.y > H - margin:
                        b.pos.y = H - margin
                        b.vel.y = -abs(b.vel.y)

        # 渲染
        screen.fill(BG_COLOR)

        # 画六边形的 5 条边（缺失一边作为开口）
        for idx, hx in enumerate(hexes):
            for k, (p1, p2) in enumerate(hx.sides()):
                pygame.draw.line(screen, LINE_COLOR, p1, p2, LINE_WIDTH)

        # 画小球
        for b in balls:
            pygame.draw.circle(screen, b.color, (int(b.pos.x), int(b.pos.y)), int(b.r))

        # 中心标记（发射点）
        pygame.draw.circle(screen, (180, 180, 180), (int(CENTER.x), int(CENTER.y)), 3)

        # 文本提示
        font = pygame.font.SysFont(None, 22)
        tip = font.render("左键点击 从中心释放小球 | 完全弹性 | 无摩擦/阻力", True, (200, 200, 200))
        screen.blit(tip, (15, 15))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
