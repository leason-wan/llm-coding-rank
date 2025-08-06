import random
import math
import sys

import pygame
import pymunk
from pymunk import Vec2d
from pygame.color import THECOLORS

# ------------------------------------------------------------
# 参数 & 常量
# ------------------------------------------------------------
WIDTH, HEIGHT = 800, 600          # 窗口尺寸
FPS = 60                         # 帧率
BALL_RADIUS = 12                  # 小球半径（统一大小，便于观察）
GRAVITY = (0, 900)                # 重力加速度 (pixel/s^2)
HEXAGON_SCALE = 200               # 六边形（实际是五边）的半径
HEXAGON_ANG_VEL = math.radians(30)  # 每秒 30° 旋转 => rad/s
# ------------------------------------------------------------


class Hexagon:
    """
    5 条线段+1 个刚体，构成一个缺一面的正六边形（实际上是 5 条边围成的多边形）。
    所有线段是 `STATIC` 的，但它们附着在同一个旋转的刚体上，从而实现“一体”旋转。
    ``elasticity`` 为 1（完全弹性），``friction`` 为 0（无摩擦）。
    """
    def __init__(self, space, center, angle_offset, angular_velocity, clockwise=True):
        """
        :param space: pymunk.Space
        :param center: (x, y) – 画面中心坐标
        :param angle_offset: 初始角度（弧度），用于让四个六边形错开
        :param angular_velocity: 旋转角速度（rad/s），正负决定方向
        :param clockwise: True → 顺时针, False → 逆时针（这里仅用来确定颜色展示顺序）
        """
        self.space = space
        self.center = Vec2d(center)
        self.body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)  # 只携带角速度，不受力
        self.body.position = self.center
        self.body.angle = angle_offset
        self.body.angular_velocity = angular_velocity if clockwise else -angular_velocity

        # 生成六边形的六个顶点（正六边形），随后去掉一条边
        verts = []
        for i in range(6):
            theta = angle_offset + i * math.pi / 3  # 60°
            v = Vec2d(math.cos(theta) * HEXAGON_SCALE,
                      math.sin(theta) * HEXAGON_SCALE)
            verts.append(v)

        # 这里决定“缺哪一面”。我们把第 0 条边（0→1）去掉
        # 其余 5 条边依次相连 (1→2, 2→3, ..., 5→0) 形成封闭的 5 条边形。
        # 只要把第 0 条 segment 删掉即可。
        self.shapes = []  # 保存所有 segment，以便后续绘制

        for i in range(1, 6):
            seg = pymunk.Segment(self.body,
                                 verts[i],
                                 verts[(i + 1) % 6],
                                 radius=2)             # 边的厚度仅用于绘制，物理上是无厚度
            seg.elasticity = 1.0
            seg.friction = 0.0
            seg.collision_type = 1
            space.add(seg)
            self.shapes.append(seg)

        # 把刚体加入 space（KINEMATIC body 只需要 position/angle/vel 手动更新）
        space.add(self.body)

    def update(self, dt):
        """只要让 body 按角速度旋转即可，pymunk 自动保持位置不变"""
        self.body.angle += self.body.angular_velocity * dt

    def draw(self, screen):
        """把 5 条线段绘制为多边形的轮廓"""
        for seg in self.shapes:
            a = seg.a.rotated(self.body.angle) + self.body.position
            b = seg.b.rotated(self.body.angle) + self.body.position
            pygame.draw.line(screen,
                             THECOLORS["darkgray"],
                             (int(a.x), int(a.y)),
                             (int(b.x), int(b.y)),
                             3)


def create_ball(space, pos):
    """用户点击时生成一个随机颜色的小球"""
    mass = 1
    radius = BALL_RADIUS
    moment = pymunk.moment_for_circle(mass, 0, radius)

    body = pymunk.Body(mass, moment, body_type=pymunk.Body.DYNAMIC)
    body.position = Vec2d(pos)

    shape = pymunk.Circle(body, radius)
    shape.elasticity = 1.0      # 完全弹性
    shape.friction = 0.0       # 无摩擦
    # 随机颜色保存在 shape 上，后面绘制时直接读取
    shape.color = (random.randint(50, 255),
                   random.randint(50, 255),
                   random.randint(50, 255))
    space.add(body, shape)
    return shape


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("四个缺一面的旋转六边形 + 完全弹性小球")
    clock = pygame.time.Clock()

    # --------------------------------------------------------
    # 1. 物理世界
    # --------------------------------------------------------
    space = pympm.Space()
    space.gravity = Vec2d(GRAVITY)

    # 为了保证完全弹性，关闭全局 damping（防止速度衰减）
    space.damping = 1.0

    # --------------------------------------------------------
    # 2. 创建四个旋转的“六边形”（其实是五条边围成的形）
    # --------------------------------------------------------
    # 设定它们的初始角度让它们相互错开 90°
    hexagons = []
    for i in range(4):
        centre = (WIDTH // 2, HEIGHT // 2)
        angle_offset = i * math.pi / 2          # 0, 90°, 180°, 270°
        # 交替顺时针/逆时针
        clockwise = (i % 2 == 0)
        hexagon = Hexagon(space,
                          centre,
                          angle_offset,
                          HEXAGON_ANG_VEL,
                          clockwise=clockwise)
        hexagons.append(hexagon)

    # --------------------------------------------------------
    # 3. 主循环
    # --------------------------------------------------------
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0   # 秒

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            # 鼠标左键点击 → 从画面中心释放一个小球
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                create_ball(space, (WIDTH // 2, HEIGHT // 2))

        # 1) 更新旋转六边形
        for h in hexagons:
            h.update(dt)

        # 2) 物理求解
        space.step(dt)

        # 3) 绘制
        screen.fill(THECOLORS["black"])

        # 绘制六边形（5 条边）
        for h in hexagons:
            h.draw(screen)

        # 绘制所有小球
        for shape in space.shapes:
            if isinstance(shape, pymunk.Circle):
                pos = shape.body.position
                pygame.draw.circle(screen,
                                   shape.color,
                                   (int(pos.x), int(pos.y)),
                                   int(shape.radius),
                                   0)

        # 显示帧率
        fps_text = f"FPS: {clock.get_fps():.0f}"
        font = pygame.font.SysFont("Arial", 16)
        txt = font.render(fps_text, True, THECOLORS["white"])
        screen.blit(txt, (10, 10))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
