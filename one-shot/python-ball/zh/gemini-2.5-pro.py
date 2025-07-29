import pygame
import pymunk
import pymunk.pygame_util
import random
import math

# --- 常量定义 ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
FPS = 60

# --- Pymunk 物理引擎设置 ---
# 重力向量 (x, y)，y为正表示向下
GRAVITY = (0.0, 900.0)
# 小球属性
BALL_RADIUS = 10
BALL_MASS = 1
# 弹性设为1.0表示完全弹性碰撞
BALL_ELASTICITY = 1.0
# 摩擦力设为0
BALL_FRICTION = 0.0

# --- 六边形盒子设置 ---
# 4个六边形的半径（从内到外）
HEXAGON_RADII = [100, 180, 260, 340]
# 六边形边框的厚度
HEXAGON_THICKNESS = 10
# 旋转速度（正数=顺时针, 负数=逆时针），单位：弧度/秒
ROTATION_SPEEDS = [0.5, -0.4, 0.3, -0.2]

# --- 颜色 ---
COLOR_BACKGROUND = (10, 20, 30)  # 深蓝色背景
COLOR_HEXAGON = (141, 153, 174) # 灰色

class PhysicsSimulation:
    def __init__(self):
        """ 初始化 Pygame 和 Pymunk """
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("六边形物理模拟")
        self.clock = pygame.time.Clock()

        # 初始化 Pymunk 空间
        self.space = pymunk.Space()
        self.space.gravity = GRAVITY

        # Pymunk 的绘图工具 (可选，但对于调试很有用)
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        
        # 存储物理对象
        self.balls = []
        self.hexagons = []
        
        self.create_hexagons()

    def create_hexagons(self):
        """ 创建4个旋转的六边形盒子 """
        center_pos = (SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2)

        for i in range(4):
            radius = HEXAGON_RADII[i]
            speed = ROTATION_SPEEDS[i]

            # 创建一个 KINEMATIC 类型的 body
            # KINEMATIC body 不受重力或碰撞影响，但可以移动和旋转，非常适合做移动平台
            hexagon_body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            hexagon_body.position = center_pos
            hexagon_body.angular_velocity = speed # Pymunk可以直接设置角速度
            
            # 计算六边形的6个顶点
            vertices = []
            for j in range(6):
                angle = j * math.pi / 3  # 60度一个顶点
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                vertices.append((x, y))

            # 创建5个边（Segment），留一个缺口
            # 我们不连接最后一个顶点和第一个顶点，以形成缺口
            segments = []
            for j in range(5):
                p1 = vertices[j]
                p2 = vertices[j+1]
                segment = pymunk.Segment(hexagon_body, p1, p2, HEXAGON_THICKNESS / 2)
                segment.elasticity = 1.0  # 完全弹性
                segment.friction = 0.0
                segment.color = pygame.Color(COLOR_HEXAGON)
                segments.append(segment)
            
            # 将 body 和 segments 添加到物理空间
            self.space.add(hexagon_body, *segments)
            # 存储起来用于绘图
            self.hexagons.append({'body': hexagon_body, 'segments': segments})
            
    def create_ball(self, position):
        """ 在指定位置创建一个随机颜色的小球 """
        mass = BALL_MASS
        radius = BALL_RADIUS
        
        # 创建一个 DYNAMIC 类型的 body
        # DYNAMIC body 是标准的物理对象，受力、会碰撞
        ball_body = pymunk.Body(mass, pymunk.moment_for_circle(mass, 0, radius))
        ball_body.position = position
        
        # 创建圆形 Shape
        ball_shape = pymunk.Circle(ball_body, radius)
        ball_shape.elasticity = BALL_ELASTICITY
        ball_shape.friction = BALL_FRICTION
        
        # 为小球分配一个随机颜色
        ball_shape.color = pygame.Color(random.randint(50, 255), 
                                        random.randint(50, 255), 
                                        random.randint(50, 255), 255)
        
        # 添加到物理空间
        self.space.add(ball_body, ball_shape)
        # 添加到列表用于绘图
        self.balls.append(ball_shape)

    def run(self):
        """ 主循环 """
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # 点击鼠标时在屏幕中心创建小球
                    self.create_ball(pygame.mouse.get_pos())
                    # 或者，严格按照要求从屏幕中心释放
                    # self.create_ball((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

            # --- 绘图 ---
            self.screen.fill(COLOR_BACKGROUND)
            
            # 使用 Pymunk 的调试绘图功能
            # 这个函数会画出所有在 space 中的 shape，包括我们手动创建的
            # 它会自动处理旋转和位置，非常方便
            self.space.debug_draw(self.draw_options)
            
            pygame.display.flip()

            # --- 更新 ---
            # 以固定的时间步长更新物理引擎，保证模拟稳定
            dt = 1.0 / FPS
            self.space.step(dt)
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == '__main__':
    sim = PhysicsSimulation()
    sim.run()