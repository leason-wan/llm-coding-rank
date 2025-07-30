import pygame
import math
import random
import numpy as np

# 初始化Pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("六边形盒子物理模拟")
clock = pygame.time.Clock()

# 物理常数
GRAVITY = 500  # 像素/秒²
RESTITUTION = 1.0  # 完全弹性碰撞系数
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
HEX_COLOR = (100, 100, 100)
BACKGROUND = (30, 30, 40)

# 球的颜色列表
BALL_COLORS = [
    (255, 100, 100),  # 红
    (100, 255, 100),  # 绿
    (100, 100, 255),  # 蓝
    (255, 255, 100),  # 黄
    (255, 100, 255),  # 紫
    (100, 255, 255),  # 青
]

class Ball:
    """球体类"""
    def __init__(self, x, y, radius=8):
        self.x = x
        self.y = y
        self.vx = 0
        self.vy = 0
        self.radius = radius
        self.color = random.choice(BALL_COLORS)
        
    def update(self, dt):
        """更新球的位置（应用重力）"""
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        
    def draw(self, screen):
        """绘制球"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.radius, 1)

class Hexagon:
    """六边形盒子类"""
    def __init__(self, center_x, center_y, radius, rotation_speed, open_side=0):
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.rotation = 0
        self.rotation_speed = rotation_speed  # 弧度/秒
        self.open_side = open_side  # 开放的边索引（0-5）
        
    def get_vertices(self):
        """获取六个顶点的坐标"""
        vertices = []
        for i in range(6):
            angle = self.rotation + i * math.pi / 3
            x = self.center_x + self.radius * math.cos(angle)
            y = self.center_y + self.radius * math.sin(angle)
            vertices.append((x, y))
        return vertices
    
    def get_edges(self):
        """获取五条边的起点和终点坐标（排除开放边）"""
        vertices = self.get_vertices()
        edges = []
        for i in range(6):
            if i != self.open_side:  # 跳过开放边
                start = vertices[i]
                end = vertices[(i + 1) % 6]
                edges.append((start, end))
        return edges
    
    def update(self, dt):
        """更新旋转角度"""
        self.rotation += self.rotation_speed * dt
        self.rotation %= 2 * math.pi
    
    def draw(self, screen):
        """绘制六边形"""
        vertices = self.get_vertices()
        edges = self.get_edges()
        
        # 绘制边
        for edge in edges:
            pygame.draw.line(screen, HEX_COLOR, edge[0], edge[1], 3)
        
        # 绘制顶点
        for vertex in vertices:
            pygame.draw.circle(screen, HEX_COLOR, (int(vertex[0]), int(vertex[1])), 5)
        
        # 高亮显示开放边的顶点
        open_index = (self.open_side + 5) % 6  # 开放边的前一个顶点
        open_next_index = (self.open_side + 1) % 6  # 开放边的后一个顶点
        pygame.draw.circle(screen, (255, 0, 0), 
                         (int(vertices[open_index][0]), int(vertices[open_index][1])), 
                         8, 2)
        pygame.draw.circle(screen, (255, 0, 0), 
                         (int(vertices[open_next_index][0]), int(vertices[open_next_index][1])), 
                         8, 2)

def point_to_line_segment_distance(point, line_start, line_end):
    """计算点到线段的距离"""
    px, py = point
    x1, y1 = line_start
    x2, y2 = line_end
    
    # 线段长度的平方
    line_length_sq = (x2-x1)**2 + (y2-y1)**2
    
    if line_length_sq == 0:
        return math.sqrt((px-x1)**2 + (py-y1)**2)
    
    # 计算投影比例
    t = max(0, min(1, ((px-x1)*(x2-x1) + (py-y1)*(y2-y1)) / line_length_sq))
    
    # 投影点
    projection_x = x1 + t * (x2 - x1)
    projection_y = y1 + t * (y2 - y1)
    
    # 距离
    distance = math.sqrt((px - projection_x)**2 + (py - projection_y)**2)
    
    return distance, (projection_x, projection_y), t

def check_ball_hexagon_collision(ball, hexagon):
    """检查球与六边形的碰撞"""
    edges = hexagon.get_edges()
    
    for edge in edges:
        distance, closest_point, t = point_to_line_segment_distance(
            (ball.x, ball.y), edge[0], edge[1]
        )
        
        if distance < ball.radius:
            # 计算法向量
            edge_vector = (edge[1][0] - edge[0][0], edge[1][1] - edge[0][1])
            edge_length = math.sqrt(edge_vector[0]**2 + edge_vector[1]**2)
            
            if edge_length > 0:
                # 归一化边向量
                edge_unit = (edge_vector[0]/edge_length, edge_vector[1]/edge_length)
                
                # 法向量（垂直于边，指向外部）
                normal = (-edge_unit[1], edge_unit[0])
                
                # 确保法向量指向球的方向
                to_ball = (ball.x - closest_point[0], ball.y - closest_point[1])
                if normal[0]*to_ball[0] + normal[1]*to_ball[1] < 0:
                    normal = (-normal[0], -normal[1])
                
                # 计算相对速度
                velocity_along_normal = ball.vx * normal[0] + ball.vy * normal[1]
                
                if velocity_along_normal < 0:  # 正在接近
                    # 弹性碰撞
                    ball.vx -= 2 * velocity_along_normal * normal[0] * RESTITUTION
                    ball.vy -= 2 * velocity_along_normal * normal[1] * RESTITUTION
                    
                    # 将球推出碰撞区域
                    overlap = ball.radius - distance
                    ball.x += normal[0] * overlap
                    ball.y += normal[1] * overlap
                    
                    return True
    return False

def check_ball_ball_collision(ball1, ball2):
    """检查两球之间的碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    distance = math.sqrt(dx**2 + dy**2)
    
    if distance < ball1.radius + ball2.radius and distance > 0:
        # 归一化碰撞向量
        nx = dx / distance
        ny = dy / distance
        
        # 相对速度
        dvx = ball2.vx - ball1.vx
        dvy = ball2.vy - ball1.vy
        
        # 相对速度在碰撞方向上的分量
        dvn = dvx * nx + dvy * ny
        
        if dvn < 0:  # 球正在接近
            # 弹性碰撞（假设质量相等）
            ball1.vx += dvn * nx
            ball1.vy += dvn * ny
            ball2.vx -= dvn * nx
            ball2.vy -= dvn * ny
            
            # 分离重叠的球
            overlap = ball1.radius + ball2.radius - distance
            separate_x = nx * overlap / 2
            separate_y = ny * overlap / 2
            ball1.x -= separate_x
            ball1.y -= separate_y
            ball2.x += separate_x
            ball2.y += separate_y
            
            return True
    return False

def main():
    """主函数"""
    running = True
    
    # 创建四个六边形盒子
    center_x, center_y = WIDTH // 2, HEIGHT // 2
    hexagons = [
        Hexagon(center_x, center_y, 150, 0.5, 0),   # 顺时针
        Hexagon(center_x, center_y, 200, -0.3, 3),  # 逆时针
        Hexagon(center_x, center_y, 250, 0.2, 1),   # 顺时针
        Hexagon(center_x, center_y, 300, -0.4, 4),  # 逆时针
    ]
    
    # 球列表
    balls = []
    
    while running:
        dt = clock.tick(FPS) / 1000.0  # 转换为秒
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键点击
                    x, y = WIDTH // 2, HEIGHT // 2
                    balls.append(Ball(x, y))
        
        # 更新六边形旋转
        for hexagon in hexagons:
            hexagon.update(dt)
        
        # 更新球的位置
        for ball in balls:
            ball.update(dt)
        
        # 检查球与六边形的碰撞
        for ball in balls:
            for hexagon in hexagons:
                check_ball_hexagon_collision(ball, hexagon)
        
        # 检查球与球之间的碰撞
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                check_ball_ball_collision(balls[i], balls[j])
        
        # 屏幕边界碰撞
        for ball in balls:
            # 左右边界
            if ball.x - ball.radius < 0:
                ball.x = ball.radius
                ball.vx = abs(ball.vx) * RESTITUTION
            elif ball.x + ball.radius > WIDTH:
                ball.x = WIDTH - ball.radius
                ball.vx = -abs(ball.vx) * RESTITUTION
            
            # 上下边界
            if ball.y - ball.radius < 0:
                ball.y = ball.radius
                ball.vy = abs(ball.vy) * RESTITUTION
            elif ball.y + ball.radius > HEIGHT:
                ball.y = HEIGHT - ball.radius
                ball.vy = -abs(ball.vy) * RESTITUTION
        
        # 绘制
        screen.fill(BACKGROUND)
        
        # 绘制中心点
        pygame.draw.circle(screen, WHITE, (center_x, center_y), 5)
        
        # 绘制六边形
        for hexagon in hexagons:
            hexagon.draw(screen)
        
        # 绘制球
        for ball in balls:
            ball.draw(screen)
        
        # 显示说明文字
        font = pygame.font.Font(None, 36)
        text = font.render("Click to drop balls", True, WHITE)
        screen.blit(text, (10, 10))
        
        # 显示球的数量
        text2 = font.render(f"Balls: {len(balls)}", True, WHITE)
        screen.blit(text2, (10, 50))
        
        pygame.display.flip()
    
    pygame.quit()

if __name__ == "__main__":
    main()
