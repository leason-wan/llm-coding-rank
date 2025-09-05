import pygame
import sys
import math
import random
from pygame.locals import *

# 初始化pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("六边形盒子物理模拟")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COLORS = [
    (255, 0, 0),    # 红
    (0, 255, 0),    # 绿
    (0, 0, 255),    # 蓝
    (255, 255, 0),  # 黄
    (255, 0, 255),  # 紫
    (0, 255, 255),  # 青
    (255, 165, 0),  # 橙
    (128, 0, 128)   # 紫罗兰
]

# 物理参数
GRAVITY = 0.2
FRICTION = 0.0  # 无摩擦
RESTITUTION = 1.0  # 完全弹性碰撞

# 中心点
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

class Ball:
    def __init__(self, x, y, radius=10):
        self.x = x
        self.y = y
        self.radius = radius
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.color = random.choice(COLORS)
        self.mass = math.pi * radius ** 2
    
    def update(self):
        # 应用重力
        self.vy += GRAVITY
        
        # 更新位置
        self.x += self.vx
        self.y += self.vy
    
    def draw(self):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 1)

class Hexagon:
    def __init__(self, center_x, center_y, radius, rotation=0, gap_side=None):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.rotation = rotation  # 旋转角度（弧度）
        self.gap_side = gap_side  # 缺失的边（0-5）
        self.sides = 6
        self.angles = [math.pi/2 + 2*math.pi*i/self.sides + self.rotation for i in range(self.sides)]
        
    def get_vertices(self):
        vertices = []
        for i in range(self.sides):
            if i == self.gap_side:
                continue  # 跳过缺失的边
            angle = self.angles[i]
            x = self.center_x + self.radius * math.cos(angle)
            y = self.center_y - self.radius * math.sin(angle)
            vertices.append((x, y))
        return vertices
    
    def get_edges(self):
        vertices = self.get_vertices()
        edges = []
        for i in range(len(vertices)):
            edges.append((vertices[i], vertices[(i+1) % len(vertices)]))
        return edges
    
    def draw(self):
        vertices = self.get_vertices()
        if len(vertices) > 2:
            pygame.draw.polygon(screen, BLACK, vertices, 2)

def distance_point_to_line(point, line):
    """计算点到线段的距离"""
    x0, y0 = point
    x1, y1 = line[0]
    x2, y2 = line[1]
    
    # 线段长度的平方
    l2 = (x2 - x1)**2 + (y2 - y1)**2
    
    # 如果线段长度为0，直接返回点到端点的距离
    if l2 == 0:
        return math.sqrt((x0 - x1)**2 + (y0 - y1)**2)
    
    # 计算投影比例 t
    t = max(0, min(1, ((x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)) / l2))
    
    # 计算投影点
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)
    
    # 返回点到投影点的距离
    return math.sqrt((x0 - projection_x)**2 + (y0 - projection_y)**2), (projection_x, projection_y)

def check_collision(ball, hexagons):
    """检查球与六边形边的碰撞"""
    for hexagon in hexagons:
        for edge in hexagon.get_edges():
            dist, projection = distance_point_to_line((ball.x, ball.y), edge)
            
            if dist <= ball.radius:
                # 计算法线向量（从投影点指向球心）
                nx = ball.x - projection[0]
                ny = ball.y - projection[1]
                
                # 归一化法线向量
                length = math.sqrt(nx**2 + ny**2)
                if length > 0:
                    nx /= length
                    ny /= length
                    
                    # 计算入射速度在法线方向上的分量
                    vn = ball.vx * nx + ball.vy * ny
                    
                    # 如果球正在远离边，不处理碰撞
                    if vn > 0:
                        continue
                    
                    # 计算反弹后的速度
                    ball.vx -= (1 + RESTITUTION) * vn * nx
                    ball.vy -= (1 + RESTITUTION) * vn * ny
                    
                    # 稍微将球推离边界以防止卡住
                    overlap = ball.radius - dist
                    ball.x += overlap * nx
                    ball.y += overlap * ny
                    
                    return True
    return False

def check_ball_collision(ball1, ball2):
    """检查两个球之间的碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < ball1.radius + ball2.radius:
        # 计算法线方向
        nx = dx / distance
        ny = dy / distance
        
        # 计算相对速度
        dvx = ball2.vx - ball1.vx
        dvy = ball2.vy - ball1.vy
        
        # 计算相对速度在法线方向上的分量
        vn = dvx * nx + dvy * ny
        
        # 如果球正在远离，不处理碰撞
        if vn > 0:
            return False
        
        # 计算冲量
        m1 = ball1.mass
        m2 = ball2.mass
        j = -(1 + RESTITUTION) * vn / (1/m1 + 1/m2)
        
        # 应用冲量
        ball1.vx -= j * nx / m1
        ball1.vy -= j * ny / m1
        ball2.vx += j * nx / m2
        ball2.vy += j * ny / m2
        
        # 分离球体以防止卡住
        overlap = (ball1.radius + ball2.radius - distance) / 2
        ball1.x -= overlap * nx
        ball1.y -= overlap * ny
        ball2.x += overlap * nx
        ball2.y += overlap * ny
        
        return True
    return False

# 创建六边形盒子
hexagons = [
    Hexagon(CENTER_X, CENTER_Y, 100, 0, 2),
    Hexagon(CENTER_X, CENTER_Y, 150, math.pi/6, 5),
    Hexagon(CENTER_X, CENTER_Y, 200, 0, 1),
    Hexagon(CENTER_X, CENTER_Y, 250, math.pi/6, 4)
]

# 球列表
balls = []

# 旋转速度（弧度/帧）
rotation_speeds = [0.01, -0.015, 0.02, -0.01]

# 主循环
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False
        elif event.type == MOUSEBUTTONDOWN:
            # 点击时在中心创建新球
            balls.append(Ball(CENTER_X, CENTER_Y))
    
    # 清屏
    screen.fill(WHITE)
    
    # 更新六边形旋转
    for i, hexagon in enumerate(hexagons):
        hexagon.rotation += rotation_speeds[i]
        hexagon.angles = [math.pi/2 + 2*math.pi*i/hexagon.sides + hexagon.rotation for i in range(hexagon.sides)]
    
    # 更新球的位置
    for ball in balls:
        ball.update()
        
        # 检查与六边形的碰撞
        check_collision(ball, hexagons)
    
    # 检查球之间的碰撞
    for i in range(len(balls)):
        for j in range(i+1, len(balls)):
            check_ball_collision(balls[i], balls[j])
    
    # 绘制六边形
    for hexagon in hexagons:
        hexagon.draw()
    
    # 绘制球
    for ball in balls:
        ball.draw()
    
    # 显示球的数量
    font = pygame.font.SysFont(None, 24)
    text = font.render(f"小球数量: {len(balls)}", True, BLACK)
    screen.blit(text, (10, 10))
    
    # 显示说明
    instructions = font.render("点击屏幕添加小球", True, BLACK)
    screen.blit(instructions, (10, 40))
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
