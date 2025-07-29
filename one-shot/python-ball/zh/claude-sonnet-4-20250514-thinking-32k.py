import pygame
import math
import random
import sys

# 初始化pygame
pygame.init()

# 设置屏幕尺寸
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("物理模拟 - 旋转五边形与弹性小球")

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (255, 0, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)

# 物理常量
GRAVITY = 0.3
BALL_RADIUS = 8
DAMPING = 0.99  # 轻微的能量损失

# 屏幕中心
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2

class Ball:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-3, 3)
        self.vy = random.uniform(-3, 3)
        self.color = color
        self.radius = BALL_RADIUS
        
    def update(self):
        # 应用重力
        self.vy += GRAVITY
        
        # 更新位置
        self.x += self.vx
        self.y += self.vy
        
        # 轻微的阻尼
        self.vx *= DAMPING
        self.vy *= DAMPING
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 2)

class Pentagon:
    def __init__(self, center_x, center_y, radius, rotation_speed, missing_side=0):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.rotation_speed = rotation_speed  # 弧度每帧
        self.angle = 0
        self.missing_side = missing_side  # 哪一边缺失 (0-5)
        
    def get_vertices(self):
        """获取五边形的顶点坐标"""
        vertices = []
        for i in range(6):  # 计算6个顶点
            angle = self.angle + i * math.pi / 3
            x = self.center_x + self.radius * math.cos(angle)
            y = self.center_y + self.radius * math.sin(angle)
            vertices.append((x, y))
        return vertices
    
    def get_edges(self):
        """获取存在的边（线段）"""
        vertices = self.get_vertices()
        edges = []
        for i in range(6):
            if i != self.missing_side:  # 跳过缺失的边
                start = vertices[i]
                end = vertices[(i + 1) % 6]
                edges.append((start, end))
        return edges
    
    def update(self):
        self.angle += self.rotation_speed
        
    def draw(self, screen):
        edges = self.get_edges()
        for edge in edges:
            pygame.draw.line(screen, WHITE, edge[0], edge[1], 3)

def distance_point_to_line(px, py, x1, y1, x2, y2):
    """计算点到线段的最短距离"""
    # 线段向量
    A = x2 - x1
    B = y2 - y1
    
    # 点到线段起点的向量
    C = px - x1
    D = py - y1
    
    # 计算投影参数
    dot = C * A + D * B
    len_sq = A * A + B * B
    
    if len_sq == 0:
        return math.sqrt(C * C + D * D)
    
    param = dot / len_sq
    
    if param < 0:
        # 最近点是线段起点
        xx, yy = x1, y1
    elif param > 1:
        # 最近点是线段终点
        xx, yy = x2, y2
    else:
        # 最近点在线段上
        xx = x1 + param * A
        yy = y1 + param * B
    
    dx = px - xx
    dy = py - yy
    return math.sqrt(dx * dx + dy * dy), (xx, yy)

def reflect_velocity(vx, vy, nx, ny):
    """计算反射后的速度"""
    # 标准化法向量
    length = math.sqrt(nx * nx + ny * ny)
    if length == 0:
        return vx, vy
    nx /= length
    ny /= length
    
    # 计算反射
    dot = vx * nx + vy * ny
    vx_new = vx - 2 * dot * nx
    vy_new = vy - 2 * dot * ny
    
    return vx_new, vy_new

def check_ball_wall_collision(ball, pentagons):
    """检查小球与五边形边界的碰撞"""
    for pentagon in pentagons:
        edges = pentagon.get_edges()
        for edge in edges:
            x1, y1 = edge[0]
            x2, y2 = edge[1]
            
            dist, closest_point = distance_point_to_line(ball.x, ball.y, x1, y1, x2, y2)
            
            if dist < ball.radius:
                # 发生碰撞，计算法向量
                cx, cy = closest_point
                nx = ball.x - cx
                ny = ball.y - cy
                
                # 标准化法向量
                length = math.sqrt(nx * nx + ny * ny)
                if length > 0:
                    nx /= length
                    ny /= length
                    
                    # 将球移动到不碰撞的位置
                    ball.x = cx + nx * ball.radius
                    ball.y = cy + ny * ball.radius
                    
                    # 反射速度
                    ball.vx, ball.vy = reflect_velocity(ball.vx, ball.vy, nx, ny)

def check_ball_ball_collision(ball1, ball2):
    """检查两个小球之间的碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.sqrt(dx * dx + dy * dy)
    
    if distance < ball1.radius + ball2.radius and distance > 0:
        # 标准化碰撞向量
        nx = dx / distance
        ny = dy / distance
        
        # 分离小球
        overlap = ball1.radius + ball2.radius - distance
        ball1.x -= nx * overlap * 0.5
        ball1.y -= ny * overlap * 0.5
        ball2.x += nx * overlap * 0.5
        ball2.y += ny * overlap * 0.5
        
        # 计算相对速度
        dvx = ball2.vx - ball1.vx
        dvy = ball2.vy - ball1.vy
        
        # 相对速度在碰撞方向上的分量
        dvn = dvx * nx + dvy * ny
        
        # 如果小球正在分离，不处理碰撞
        if dvn > 0:
            return
            
        # 弹性碰撞（假设质量相等）
        ball1.vx += dvn * nx
        ball1.vy += dvn * ny
        ball2.vx -= dvn * nx
        ball2.vy -= dvn * ny

def get_random_color():
    """获取随机颜色"""
    colors = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN, ORANGE]
    return random.choice(colors)

def main():
    clock = pygame.time.Clock()
    balls = []
    
    # 创建4个五边形，从小到大，交替旋转方向
    pentagons = [
        Pentagon(CENTER_X, CENTER_Y, 100, 0.02, missing_side=0),   # 最小，顺时针
        Pentagon(CENTER_X, CENTER_Y, 160, -0.015, missing_side=1), # 逆时针
        Pentagon(CENTER_X, CENTER_Y, 220, 0.01, missing_side=2),   # 顺时针
        Pentagon(CENTER_X, CENTER_Y, 280, -0.008, missing_side=3)  # 最大，逆时针
    ]
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 在屏幕中心释放新球
                color = get_random_color()
                ball = Ball(CENTER_X, CENTER_Y, color)
                balls.append(ball)
        
        # 更新物理
        for pentagon in pentagons:
            pentagon.update()
            
        for ball in balls:
            ball.update()
            
        # 检查碰撞
        for ball in balls:
            check_ball_wall_collision(ball, pentagons)
            
        # 检查小球之间的碰撞
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                check_ball_ball_collision(balls[i], balls[j])
        
        # 移除超出屏幕边界太远的球
        balls = [ball for ball in balls if 
                -100 < ball.x < WIDTH + 100 and 
                -100 < ball.y < HEIGHT + 100]
        
        # 渲染
        screen.fill(BLACK)
        
        # 绘制五边形
        for pentagon in pentagons:
            pentagon.draw(screen)
            
        # 绘制小球
        for ball in balls:
            ball.draw(screen)
            
        # 显示信息
        font = pygame.font.Font(None, 36)
        text = font.render(f"小球数量: {len(balls)}", True, WHITE)
        screen.blit(text, (10, 10))
        
        text2 = font.render("点击鼠标释放小球", True, WHITE)
        screen.blit(text2, (10, 50))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()