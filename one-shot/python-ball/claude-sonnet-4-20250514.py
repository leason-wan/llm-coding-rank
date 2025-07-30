import pygame
import math
import random
import numpy as np

# 初始化pygame
pygame.init()

# 常量设置
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
FPS = 60
GRAVITY = 500  # 重力加速度
BALL_RADIUS = 8
BALL_MASS = 1.0
RESTITUTION = 1.0  # 完全弹性碰撞

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)

class Ball:
    def __init__(self, x, y, vx=0, vy=0):
        self.x = x
        self.y = y
        self.vx = vx + random.uniform(-100, 100)  # 添加随机初始速度
        self.vy = vy + random.uniform(-100, 100)
        self.radius = BALL_RADIUS
        self.mass = BALL_MASS
        self.color = random.choice([RED, GREEN, BLUE, YELLOW, PURPLE, CYAN])
    
    def update(self, dt):
        # 应用重力
        self.vy += GRAVITY * dt
        
        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # 边界碰撞检测
        if self.x - self.radius < 0:
            self.x = self.radius
            self.vx = -self.vx * RESTITUTION
        elif self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.vx = -self.vx * RESTITUTION
            
        if self.y - self.radius < 0:
            self.y = self.radius
            self.vy = -self.vy * RESTITUTION
        elif self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.vy = -self.vy * RESTITUTION
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class Pentagon:
    def __init__(self, center_x, center_y, radius, rotation_speed):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.rotation_speed = rotation_speed  # 弧度/秒
        self.angle = 0
        self.vertices = []
        self.edges = []
        
    def update(self, dt):
        self.angle += self.rotation_speed * dt
        self.calculate_vertices()
        self.calculate_edges()
    
    def calculate_vertices(self):
        self.vertices = []
        # 生成5个顶点（缺少一边，所以只有5个顶点形成开口）
        for i in range(5):
            angle = self.angle + i * 2 * math.pi / 6  # 6边形的角度，但只取5个点
            x = self.center_x + self.radius * math.cos(angle)
            y = self.center_y + self.radius * math.sin(angle)
            self.vertices.append((x, y))
    
    def calculate_edges(self):
        self.edges = []
        # 连接相邻顶点形成边（最后一个顶点不连接到第一个，形成开口）
        for i in range(4):  # 只有4条边
            self.edges.append((self.vertices[i], self.vertices[i + 1]))
    
    def draw(self, screen):
        if len(self.vertices) > 1:
            for edge in self.edges:
                pygame.draw.line(screen, WHITE, edge[0], edge[1], 3)

def point_to_line_distance(px, py, x1, y1, x2, y2):
    """计算点到线段的最短距离"""
    A = px - x1
    B = py - y1
    C = x2 - x1
    D = y2 - y1
    
    dot = A * C + B * D
    len_sq = C * C + D * D
    
    if len_sq == 0:
        return math.sqrt(A * A + B * B)
    
    param = dot / len_sq
    
    if param < 0:
        xx, yy = x1, y1
    elif param > 1:
        xx, yy = x2, y2
    else:
        xx = x1 + param * C
        yy = y1 + param * D
    
    dx = px - xx
    dy = py - yy
    return math.sqrt(dx * dx + dy * dy), xx, yy

def check_ball_pentagon_collision(ball, pentagon):
    """检查球与五边形的碰撞"""
    for edge in pentagon.edges:
        x1, y1 = edge[0]
        x2, y2 = edge[1]
        
        distance, closest_x, closest_y = point_to_line_distance(ball.x, ball.y, x1, y1, x2, y2)
        
        if distance < ball.radius:
            # 计算法向量
            normal_x = ball.x - closest_x
            normal_y = ball.y - closest_y
            normal_length = math.sqrt(normal_x**2 + normal_y**2)
            
            if normal_length > 0:
                normal_x /= normal_length
                normal_y /= normal_length
                
                # 将球移出碰撞区域
                overlap = ball.radius - distance
                ball.x += normal_x * overlap
                ball.y += normal_y * overlap
                
                # 计算反射速度
                dot_product = ball.vx * normal_x + ball.vy * normal_y
                ball.vx -= 2 * dot_product * normal_x * RESTITUTION
                ball.vy -= 2 * dot_product * normal_y * RESTITUTION

def check_ball_ball_collision(ball1, ball2):
    """检查两球之间的碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < ball1.radius + ball2.radius and distance > 0:
        # 标准化碰撞向量
        nx = dx / distance
        ny = dy / distance
        
        # 分离球体
        overlap = ball1.radius + ball2.radius - distance
        ball1.x -= nx * overlap * 0.5
        ball1.y -= ny * overlap * 0.5
        ball2.x += nx * overlap * 0.5
        ball2.y += ny * overlap * 0.5
        
        # 计算相对速度
        dvx = ball2.vx - ball1.vx
        dvy = ball2.vy - ball1.vy
        
        # 计算相对速度在碰撞法线方向的分量
        dvn = dvx * nx + dvy * ny
        
        # 如果球体正在分离，不处理碰撞
        if dvn > 0:
            return
        
        # 计算碰撞冲量
        impulse = 2 * dvn / (ball1.mass + ball2.mass)
        
        # 更新速度
        ball1.vx += impulse * ball2.mass * nx * RESTITUTION
        ball1.vy += impulse * ball2.mass * ny * RESTITUTION
        ball2.vx -= impulse * ball1.mass * nx * RESTITUTION
        ball2.vy -= impulse * ball1.mass * ny * RESTITUTION

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("物理模拟 - 旋转五边形和弹性碰撞")
    clock = pygame.time.Clock()
    
    # 创建四个不同大小的五边形盒子
    center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
    pentagons = [
        Pentagon(center_x, center_y, 80, math.pi/3),    # 顺时针
        Pentagon(center_x, center_y, 140, -math.pi/4),  # 逆时针
        Pentagon(center_x, center_y, 200, math.pi/5),   # 顺时针
        Pentagon(center_x, center_y, 260, -math.pi/6),  # 逆时针
    ]
    
    balls = []
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # 转换为秒
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 在屏幕中心释放一个新球
                ball = Ball(center_x, center_y)
                balls.append(ball)
        
        # 更新五边形
        for pentagon in pentagons:
            pentagon.update(dt)
        
        # 更新球
        for ball in balls:
            ball.update(dt)
        
        # 检查球与五边形的碰撞
        for ball in balls:
            for pentagon in pentagons:
                check_ball_pentagon_collision(ball, pentagon)
        
        # 检查球与球之间的碰撞
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                check_ball_ball_collision(balls[i], balls[j])
        
        # 绘制
        screen.fill(BLACK)
        
        # 绘制五边形
        for pentagon in pentagons:
            pentagon.draw(screen)
        
        # 绘制球
        for ball in balls:
            ball.draw(screen)
        
        # 绘制中心点
        pygame.draw.circle(screen, WHITE, (center_x, center_y), 3)
        
        # 显示信息
        font = pygame.font.Font(None, 36)
        text = font.render(f"球数量: {len(balls)}", True, WHITE)
        screen.blit(text, (10, 10))
        text2 = font.render("点击鼠标释放小球", True, WHITE)
        screen.blit(text2, (10, 50))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()