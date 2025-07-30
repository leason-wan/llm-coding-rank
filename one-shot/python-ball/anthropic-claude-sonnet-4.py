import pygame
import math
import random
import numpy as np

# 初始化pygame
pygame.init()

# 常量
WIDTH, HEIGHT = 1000, 800
CENTER_X, CENTER_Y = WIDTH // 2, HEIGHT // 2
FPS = 60
GRAVITY = 0.3
BALL_RADIUS = 8
NUM_HEXAGONS = 4

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)

class Ball:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
        self.radius = BALL_RADIUS
        self.color = color
        self.mass = 1.0
    
    def update(self):
        # 应用重力
        self.vy += GRAVITY
        
        # 更新位置
        self.x += self.vx
        self.y += self.vy
        
        # 屏幕边界碰撞
        if self.x - self.radius < 0 or self.x + self.radius > WIDTH:
            self.vx = -self.vx
            self.x = max(self.radius, min(WIDTH - self.radius, self.x))
        
        if self.y - self.radius < 0 or self.y + self.radius > HEIGHT:
            self.vy = -self.vy
            self.y = max(self.radius, min(HEIGHT - self.radius, self.y))
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius, 2)

class Pentagon:
    def __init__(self, size, rotation_speed, initial_angle=0):
        self.size = size
        self.rotation_speed = rotation_speed
        self.angle = initial_angle
        self.vertices = []
        self.edges = []
        self.update_vertices()
    
    def update_vertices(self):
        self.vertices = []
        # 创建五边形的5个顶点（缺少一个边，所以只有5个顶点而不是6个）
        for i in range(5):
            angle = self.angle + i * (2 * math.pi / 6)  # 分布在6个位置中的5个
            x = CENTER_X + self.size * math.cos(angle)
            y = CENTER_Y + self.size * math.sin(angle)
            self.vertices.append((x, y))
        
        # 创建边（连接相邻顶点）
        self.edges = []
        for i in range(len(self.vertices)):
            start = self.vertices[i]
            end = self.vertices[(i + 1) % len(self.vertices)]
            self.edges.append((start, end))
    
    def update(self, dt):
        self.angle += self.rotation_speed * dt
        self.update_vertices()
    
    def draw(self, screen):
        for edge in self.edges:
            pygame.draw.line(screen, BLACK, edge[0], edge[1], 3)

def line_circle_collision(ball, line_start, line_end):
    """检测球与线段的碰撞并返回碰撞信息"""
    # 将线段表示为向量
    line_vec = np.array([line_end[0] - line_start[0], line_end[1] - line_start[1]])
    ball_vec = np.array([ball.x - line_start[0], ball.y - line_start[1]])
    
    # 计算线段长度的平方
    line_len_sq = np.dot(line_vec, line_vec)
    
    if line_len_sq == 0:
        return False, None, None
    
    # 计算投影参数t
    t = max(0, min(1, np.dot(ball_vec, line_vec) / line_len_sq))
    
    # 找到线段上最近的点
    projection = line_start[0] + t * line_vec[0], line_start[1] + t * line_vec[1]
    
    # 计算距离
    distance = math.sqrt((ball.x - projection[0])**2 + (ball.y - projection[1])**2)
    
    if distance <= ball.radius:
        # 计算法向量
        if distance > 0:
            normal_x = (ball.x - projection[0]) / distance
            normal_y = (ball.y - projection[1]) / distance
        else:
            # 如果球心正好在线段上，使用线段的垂直向量
            normal_x = -line_vec[1] / math.sqrt(line_len_sq)
            normal_y = line_vec[0] / math.sqrt(line_len_sq)
        
        return True, (normal_x, normal_y), projection
    
    return False, None, None

def handle_ball_collision(ball1, ball2):
    """处理两个球之间的碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < ball1.radius + ball2.radius and distance > 0:
        # 标准化碰撞向量
        nx = dx / distance
        ny = dy / distance
        
        # 分离球体
        overlap = ball1.radius + ball2.radius - distance
        ball1.x -= nx * overlap / 2
        ball1.y -= ny * overlap / 2
        ball2.x += nx * overlap / 2
        ball2.y += ny * overlap / 2
        
        # 计算相对速度
        dvx = ball2.vx - ball1.vx
        dvy = ball2.vy - ball1.vy
        
        # 计算相对速度在碰撞法线方向的分量
        dvn = dvx * nx + dvy * ny
        
        # 如果球体正在分离，不处理碰撞
        if dvn > 0:
            return
        
        # 碰撞冲量
        impulse = 2 * dvn / (ball1.mass + ball2.mass)
        
        # 更新速度（完全弹性碰撞）
        ball1.vx += impulse * ball2.mass * nx
        ball1.vy += impulse * ball2.mass * ny
        ball2.vx -= impulse * ball1.mass * nx
        ball2.vy -= impulse * ball1.mass * ny

def handle_wall_collision(ball, pentagon):
    """处理球与五边形边的碰撞"""
    for edge in pentagon.edges:
        collision, normal, projection = line_circle_collision(ball, edge[0], edge[1])
        
        if collision:
            # 将球移动到不碰撞的位置
            ball.x = projection[0] + normal[0] * ball.radius
            ball.y = projection[1] + normal[1] * ball.radius
            
            # 计算反射速度
            dot_product = ball.vx * normal[0] + ball.vy * normal[1]
            ball.vx = ball.vx - 2 * dot_product * normal[0]
            ball.vy = ball.vy - 2 * dot_product * normal[1]
            
            break

def random_color():
    """生成随机颜色"""
    return (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("物理模拟 - 旋转五边形与小球")
    clock = pygame.time.Clock()
    
    # 创建四个五边形（从小到大，交替旋转方向）
    pentagons = [
        Pentagon(80, 0.02, 0),           # 最小，顺时针
        Pentagon(140, -0.015, 0),        # 逆时针
        Pentagon(200, 0.01, 0),          # 顺时针
        Pentagon(260, -0.008, 0)         # 最大，逆时针
    ]
    
    balls = []
    
    running = True
    dt = 1.0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    # 在屏幕中心释放一个新球
                    ball = Ball(CENTER_X, CENTER_Y, random_color())
                    balls.append(ball)
        
        # 更新五边形旋转
        for pentagon in pentagons:
            pentagon.update(dt)
        
        # 更新球的物理
        for ball in balls:
            ball.update()
        
        # 处理球与球的碰撞
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                handle_ball_collision(balls[i], balls[j])
        
        # 处理球与五边形的碰撞
        for ball in balls:
            for pentagon in pentagons:
                handle_wall_collision(ball, pentagon)
        
        # 绘制
        screen.fill(WHITE)
        
        # 绘制五边形
        for pentagon in pentagons:
            pentagon.draw(screen)
        
        # 绘制球
        for ball in balls:
            ball.draw(screen)
        
        # 绘制中心点
        pygame.draw.circle(screen, BLACK, (CENTER_X, CENTER_Y), 3)
        
        # 绘制说明文字
        font = pygame.font.Font(None, 36)
        text = font.render("点击鼠标释放小球", True, BLACK)
        screen.blit(text, (10, 10))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()

if __name__ == "__main__":
    main()
