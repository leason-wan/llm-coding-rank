import pygame
import math
import random
import numpy as np

# 初始化Pygame
pygame.init()

# 屏幕设置
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("旋转六边形物理模拟")

# 物理常量
GRAVITY = 500  # 重力加速度 (像素/秒²)
RESTITUTION = 1.0  # 弹性系数（1.0表示完全弹性）
FPS = 60
dt = 1.0 / FPS

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

class Hexagon:
    def __init__(self, center, radius, rotation_speed, missing_edge_index):
        self.center = center
        self.radius = radius
        self.rotation_speed = rotation_speed  # 弧度/秒
        self.angle = 0
        self.missing_edge_index = missing_edge_index
        self.vertices = []
        self.edges = []
        self.update_geometry()
    
    def update_geometry(self):
        """更新六边形的顶点和边"""
        self.vertices = []
        # 计算六个顶点
        for i in range(6):
            angle = self.angle + i * math.pi / 3
            x = self.center[0] + self.radius * math.cos(angle)
            y = self.center[1] + self.radius * math.sin(angle)
            self.vertices.append((x, y))
        
        # 计算五条边（排除缺失的边）
        self.edges = []
        for i in range(6):
            if i != self.missing_edge_index:
                start = self.vertices[i]
                end = self.vertices[(i + 1) % 6]
                self.edges.append((start, end))
    
    def update(self, dt):
        """更新六边形的旋转"""
        self.angle += self.rotation_speed * dt
        self.update_geometry()
    
    def draw(self, screen):
        """绘制六边形"""
        # 绘制存在的边
        for edge in self.edges:
            pygame.draw.line(screen, WHITE, edge[0], edge[1], 3)
        
        # 绘制顶点
        for vertex in self.vertices:
            pygame.draw.circle(screen, GRAY, (int(vertex[0]), int(vertex[1])), 4)
    
    def point_inside(self, point):
        """检查点是否在六边形内部"""
        x, y = point
        cx, cy = self.center
        
        # 使用叉积法判断点是否在多边形内部
        inside = True
        for i in range(6):
            if i == self.missing_edge_index:
                continue
            
            v1 = self.vertices[i]
            v2 = self.vertices[(i + 1) % 6]
            
            # 计算叉积
            cross = (v2[0] - v1[0]) * (y - v1[1]) - (v2[1] - v1[1]) * (x - v1[0])
            if cross < 0:
                inside = False
                break
        
        return inside

class Ball:
    def __init__(self, x, y, radius=10):
        self.x = x
        self.y = y
        self.vx = random.uniform(-100, 100)  # 初始速度
        self.vy = random.uniform(-100, 100)
        self.radius = radius
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self = radius * radius  # 质量与半径平方成正比
    
    def update(self, dt):
        """更新小球位置"""
        # 应用重力
        self.vy += GRAVITY * dt
        
        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt
    
    def draw(self, screen):
        """绘制小球"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 1)

def line_circle_collision(line_start, line_end, circle_center, circle_radius):
    """检测线段与圆的碰撞"""
    x1, y1 = line_start
    x2, y2 = line_end
    cx, cy = circle_center
    
    # 线段向量
    dx = x2 - x1
    dy = y2 - y1
    
    # 线段长度的平方
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return False, None, None
    
    # 计算投影参数
    t = max(0, min(1, ((cx - x1) * dx + (cy - y1) * dy) / len_sq))
    
    # 最近点
    closest_x = x1 + t * dx
    closest_y = y1 + t * dy
    
    # 距离
    dist_x = cx - closest_x
    dist_y = cy - closest_y
    dist_sq = dist_x * dist_x + dist_y * dist_y
    
    if dist_sq <= circle_radius * circle_radius:
        # 计算法向量
        dist = math.sqrt(dist_sq)
        if dist > 0:
            nx = dist_x / dist
            ny = dist_y / dist
        else:
            nx, ny = -dy / math.sqrt(len_sq), dx / math.sqrt(len_sq)
        
        return True, (nx, ny), (closest_x, closest_y)
    
    return False, None, None

def resolve_ball_ball_collision(ball1, ball2):
    """处理两个球之间的碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    dist = math.sqrt(dx * dx + dy * dy)
    
    if dist < ball1.radius + ball2.radius and dist > 0:
        # 碰撞法向量
        nx = dx / dist
        ny = dy / dist
        
        # 相对速度
        dvx = ball2.vx - ball1.vx
        dvy = ball2.vy - ball1.vy
        
        # 相对速度在法向量上的投影
        dvn = dvx * nx + dvy * ny
        
        # 如果球正在分离，不处理
        if dvn > 0:
            return
        
        # 计算冲量
        impulse = 2 * dvn / (1/ball1.mass + 1/ball2.mass)
        
        # 应用冲量
        ball1.vx += impulse * nx / ball1.mass * RESTITUTION
        ball1.vy += impulse * ny / ball1.mass * RESTITUTION
        ball2.vx -= impulse * nx / ball2.mass * RESTITUTION
        ball2.vy -= impulse * ny / ball2.mass * RESTITUTION
        
        # 分离重叠的球
        overlap = ball1.radius + ball2.radius - dist
        separate_x = nx * overlap / 2
        separate_y = ny * overlap / 2
        ball1.x -= separate_x
        ball1.y -= separate_y
        ball2.x += separate_x
        ball2.y += separate_y

def resolve_ball_line_collision(ball, line_start, line_end):
    """处理球与线段的碰撞"""
    collision, normal, contact_point = line_circle_collision(line_start, line_end, (ball.x, ball.y), ball.radius)
    
    if collision:
        nx, ny = normal
        
        # 速度在法向量上的投影
        vn = ball.vx * nx + ball.vy * ny
        
        # 如果球正在远离线段，不处理
        if vn > 0:
            return
        
        # 反射速度
        ball.vx -= 2 * vn * nx * RESTITUTION
        ball.vy -= 2 * vn * ny * RESTITUTION
        
        # 将球推出线段
        push_distance = ball.radius - math.sqrt((ball.x - contact_point[0])**2 + (ball.y - contact_point[1])**2) + 1
        ball.x += nx * push_distance
        ball.y += ny * push_distance

# 创建六边形
center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
hexagons = []
radii = [100, 150, 200, 250]
rotation_speeds = [0.5, -0.7, 0.9, -1.1]  # 交替的顺时针和逆时针
missing_edges = [0, 1, 2, 3]  # 每个六边形缺失不同的边

for i in range(4):
    hexagon = Hexagon(center, radii[i], rotation_speeds[i], missing_edges[i])
    hexagons.append(hexagon)

# 小球列表
balls = []

# 主游戏循环
clock = pygame.time.Clock()
running = True

while running:
    dt = clock.tick(FPS) / 1000.0  # 转换为秒
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 在鼠标点击位置创建小球
            mouse_x, mouse_y = pygame.mouse.get_pos()
            ball = Ball(center[0], center[1])
            balls.append(ball)
    
    # 更新六边形
    for hexagon in hexagons:
        hexagon.update(dt)
    
    # 更新小球
    for ball in balls:
        ball.update(dt)
        
        # 检查是否超出屏幕边界
        if ball.y > SCREEN_HEIGHT + 100:
            balls.remove(ball)
            continue
    
    # 碰撞检测
    # 球与球之间的碰撞
    for i in range(len(balls)):
        for j in range(i + 1, len(balls)):
            resolve_ball_ball_collision(balls[i], balls[j])
    
    # 球与六边形边的碰撞
    for ball in balls:
        for hexagon in hexagons:
            # 检查球是否在六边形内部
            if hexagon.point_inside((ball.x, ball.y)):
                # 如果在内部，只检查五条存在的边
                for edge in hexagon.edges:
                    resolve_ball_line_collision(ball, edge[0], edge[1])
            else:
                # 如果在外部，检查所有六条边（包括缺失的边）
                for i in range(6):
                    start = hexagon.vertices[i]
                    end = hexagon.vertices[(i + 1) % 6]
                    # 只检查非缺失的边
                    if i != hexagon.missing_edge_index:
                        resolve_ball_line_collision(ball, start, end)
    
    # 绘制
    screen.fill(BLACK)
    
    # 绘制六边形
    for hexagon in hexagons:
        hexagon.draw(screen)
    
    # 绘制小球
    for ball in balls:
        ball.draw(screen)
    
    # 显示信息
    font = pygame.font.Font(None, 36)
    text = font.render(f"小球数量: {len(balls)}", True, WHITE)
    screen.blit(text, (10, 10))
    
    pygame.display.flip()

pygame.quit()
