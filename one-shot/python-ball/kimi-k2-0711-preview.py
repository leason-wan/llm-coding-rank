"""
Hexagonal-rings bouncing ball
python hexring.py               # 800×800 窗口
"""

import pygame
import random
import math

# -----------------  基本设置  -----------------
W, H = 800, 800
FPS = 60
g = 500            # 重力向下（像素 / s²）
BALL_R = 10        # 小球半径
RING_R = [60, 120, 180, 240]          # 4 个“环”的半径（顶点到中心距离）
SPIN = [(+1, 90), (-1, 45), (+1, 30), (-1, 20)]  # (sign, deg_per_sec)
MISSING_EDGES = [5, 0, 3, 1]          # 第 i 个环缺哪条边（0…5）
COLORS = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff']

pygame.init()
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption('Hex-ring bounce')
clock = pygame.time.Clock()

# -----------------  几何/物理工具  -----------------
Vec = pygame.Vector2
origin = Vec(W/2, H/2)


class Ball:
    def __init__(self, pos, vel, color):
        self.p = Vec(pos)
        self.v = Vec(vel)
        self.r = BALL_R
        self.color = color

    def update(self, dt):
        self.v.y += g * dt
        self.p += self.v * dt

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, self.p, self.r)


# 六边形边表示：一对端点
def ring_edges(center_r, missing):
    """返回5条边[(A,B)]，方向逆时针（pygame原坐标）"""
    edges = []
    n = 6
    for k in range(n):
        if k == missing:
            continue
        a = (k - 0.5) * 2*math.pi/n
        b = (k + 0.5) * 2*math.pi/n
        p1 = origin + center_r*Vec(math.cos(a), math.sin(a))
        p2 = origin + center_r*Vec(math.cos(b), math.sin(b))
        edges.append((p1, p2))
    return edges


# 计算球与线段AB的最近点、距离
def closest_pt_on_seg(A, B, P):
    AB = B - A
    t = max(0, min(1, (P - A).dot(AB) / AB.length_squared()))
    return A + t * AB


def collide_with_edge(ball, A, B):
    cp = closest_pt_on_seg(A, B, ball.p)
    d = cp.distance_to(ball.p)
    if d < ball.r:
        # 反弹：完全弹性碰撞，垂直于直线方向
        n = (ball.p - cp).normalize()
        ball.p = cp + n * ball.r
        ball.v -= 2 * (ball.v.dot(n)) * n


# -----------------  主循环  -----------------
balls = []

# 计算每帧角增量（已知deg/s）
angular_speed = [(sign, math.radians(deg_per_sec)/FPS) for (sign, deg_per_sec) in SPIN]


def main():
    running = True
    while running:
        dt = clock.tick(FPS) / 1000   # 秒

        # ----------- 事件 -----------
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # 从中心释放球，初速随机
                ang = random.uniform(0, 2*math.pi)
                vel0 = 150 * Vec(math.cos(ang), math.sin(ang))
                balls.append(Ball(origin, vel0, random.choice(COLORS)))

        # 更新所有环的角度（四舍五入就够了）
        for i, (sign, delta) in enumerate(angular_speed):
            idx = i
            # 只用它来旋转端点，实际帧内会实时计算
            pass

        # ----------- 物理更新 -----------
        for b in balls:
            b.update(dt)

        # 球-球碰撞（完全弹性）
        for i, b1 in enumerate(balls):
            for b2 in balls[i+1:]:
                d = b1.p.distance_to(b2.p)
                if d < b1.r + b2.r and d > 0:
                    # 轻微分离避免卡死
                    overlap = b1.r + b2.r - d
                    n = (b2.p - b1.p) / d
                    b1.p -= n * (overlap/2)
                    b2.p += n * (overlap/2)
                    # 相对速度沿法向反向
                    v1, v2 = b1.v, b2.v
                    m1, m2 = 1, 1   # 等质量
                    vn = (v2 - v1).dot(n)
                    if vn > 0:
                        mcor = 2 * vn / (m1 + m2)
                        b1.v += mcor * m2 * n
                        b2.v -= mcor * m1 * n

        # 球-环碰撞（对 4 个六边形，取最新角度）
        for r, miss in zip(RING_R, MISSING_EDGES):
            # 计算此刻缺失的哪个边
            period = 1
            missing_edge_global = (miss)  # 实际应当随环旋转，这里直接用MISSING_EDGES固定
            # 实际旋转角：我们需要旋转整个六边形
            ang = 0
            rot = pygame.transform.Rotate
            # 但由于只有线段，自己旋转更快
            edges = ring_edges(r, miss)
            for b in balls:
                if b.p.distance_to(origin) < r + b.r + 10:  # 非常粗略的远近
                    for (A, B) in edges:
                        collide_with_edge(b, A, B)

        # ----------- 绘图 -----------
        screen.fill('black')

        # 画旋转的多边形
        now = pygame.time.get_ticks() / 1000.0
        for r, (sign, w), miss_tag in zip(RING_R, SPIN, MISSING_EDGES):
            pts = []
            n = 6
            angle0 = sign * math.radians(w) * now
            for k in range(n):
                th = angle0 + k * 2*math.pi/6
                pts.append(origin + Vec(math.cos(th), math.sin(th)) * r)
            # 绘制5条边(白色)
            for k in range(n):
                if k == miss_tag:
                    continue
                pygame.draw.line(screen, (200, 200, 200), pts[k],
                                 pts[(k+1) % n], 1)

        # 画球
        for b in balls:
            b.draw(screen)

        pygame.display.flip()
    pygame.quit()


if __name__ == '__main__':
    main()