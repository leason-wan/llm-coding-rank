import pygame
import sys
import math
import random
import numpy as np

# --- 常量定义 ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
FPS = 60
BACKGROUND_COLOR = (10, 20, 30)  # 深蓝色背景

# 物理常量
GRAVITY = 300  # 像素/s^2
ELASTICITY = 1.0  # 完全弹性碰撞

# 颜色
WHITE = (255, 255, 255)
RED = (220, 60, 60)
GREEN = (60, 220, 60)
BLUE = (60, 60, 220)
YELLOW = (220, 220, 60)
PURPLE = (180, 60, 220)
CYAN = (60, 220, 220)
COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, CYAN]

# --- 辅助函数 ---

def distance(p1, p2):
    """计算两点之间的欧几里得距离"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def rotate_point(point, angle, origin):
    """绕原点旋转一个点"""
    ox, oy = origin
    px, py = point
    qx = ox + math.cos(angle) * (px - ox) - math.sin(angle) * (py - oy)
    qy = oy + math.sin(angle) * (px - ox) + math.cos(angle) * (py - oy)
    return qx, qy

# --- 类定义 ---

class Ball:
    """代表一个物理小球"""
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vx = random.uniform(-50, 50)  # 初始随机速度
        self.vy = random.uniform(-50, 50)
        self.mass = radius * radius  # 质量与面积成正比

    def update(self, dt):
        """根据物理定律更新位置和速度"""
        # 应用重力
        self.vy += GRAVITY * dt

        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, screen):
        """在屏幕上绘制小球"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

    def get_aabb(self):
        """获取用于粗略碰撞检测的轴对齐包围盒 (AABB)"""
        return (self.x - self.radius, self.y - self.radius,
                self.x + self.radius, self.y + self.radius)


class Hexagon:
    """代表一个旋转的六边形容器"""
    def __init__(self, center, radius, rotation_speed, is_open_side):
        """
        :param center: 六边形中心点
        :param radius: 外接圆半径
        :param rotation_speed: 旋转速度 (弧度/秒)
        :param is_open_side: 开口边的索引 (0-5)
        """
        self.center = center
        self.radius = radius
        self.rotation_speed = rotation_speed
        self.is_open_side = is_open_side
        self.angle = 0  # 初始角度

        # 预计算静态顶点 (未旋转)
        self.static_vertices = []
        for i in range(6):
            angle_rad = math.radians(60 * i)
            x = center[0] + radius * math.cos(angle_rad)
            y = center[1] + radius * math.sin(angle_rad)
            self.static_vertices.append((x, y))

    def update(self, dt):
        """更新六边形的旋转角度"""
        self.angle += self.rotation_speed * dt

    def get_vertices(self):
        """获取当前旋转后的顶点"""
        rotated_vertices = []
        for v in self.static_vertices:
            rotated_v = rotate_point(v, self.angle, self.center)
            rotated_vertices.append(rotated_v)
        return rotated_vertices

    def get_edges(self):
        """获取当前旋转后的边"""
        vertices = self.get_vertices()
        edges = []
        for i in range(6):
            if i == self.is_open_side:
                continue  # 跳过开口边
            start = vertices[i]
            end = vertices[(i + 1) % 6]
            edges.append((start, end))
        return edges

    def draw(self, screen):
        """在屏幕上绘制六边形"""
        edges = self.get_edges()
        for edge in edges:
            pygame.draw.line(screen, WHITE, edge[0], edge[1], 3)


class PhysicsSimulator:
    """主模拟器类"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("旋转六边形中的弹性小球")
        self.clock = pygame.time.Clock()

        self.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        
        # 创建4个六边形
        self.hexagons = [
            Hexagon(self.center, 100, math.radians(30), 0),   # 顺时针
            Hexagon(self.center, 150, math.radians(-45), 1),  # 逆时针
            Hexagon(self.center, 200, math.radians(60), 2),   # 顺时针
            Hexagon(self.center, 250, math.radians(-90), 3),  # 逆时针
        ]

        self.balls = []
        self.ball_radius = 10

    def handle_events(self):
        """处理用户输入事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # 点击时在中心生成一个新球
                color = random.choice(COLORS)
                new_ball = Ball(self.center[0], self.center[1], self.ball_radius, color)
                self.balls.append(new_ball)

    def update(self, dt):
        """更新所有物体的状态"""
        # 更新六边形
        for hexagon in self.hexagons:
            hexagon.update(dt)

        # 更新小球
        for ball in self.balls:
            ball.update(dt)

        # 处理小球与六边形的碰撞
        self.handle_hexagon_collisions()

        # 处理小球之间的碰撞
        self.handle_ball_collisions()

    def handle_hexagon_collisions(self):
        """处理小球与所有六边形的碰撞"""
        for ball in self.balls:
            for hexagon in self.hexagons:
                edges = hexagon.get_edges()
                for edge in edges:
                    self.resolve_collision_with_edge(ball, edge)

    def resolve_collision_with_edge(self, ball, edge):
        """解决小球与单条线段的碰撞"""
        p1, p2 = np.array(edge[0]), np.array(edge[1])
        ball_pos = np.array([ball.x, ball.y])

        # 计算线段向量和球到线段起点的向量
        line_vec = p2 - p1
        ball_vec = ball_pos - p1

        # 计算投影长度
        line_len_sq = np.dot(line_vec, line_vec)
        if line_len_sq == 0: return # 线段长度为0

        t = max(0, min(1, np.dot(ball_vec, line_vec) / line_len_sq))

        # 找到线段上离球心最近的点
        closest_point = p1 + t * line_vec
        
        dist = np.linalg.norm(ball_pos - closest_point)

        # 如果发生碰撞
        if dist < ball.radius:
            # 计算法向量 (从碰撞点指向球心)
            normal = ball_pos - closest_point
            normal_len = np.linalg.norm(normal)
            if normal_len == 0: continue
            normal = normal / normal_len

            # 将球移出边界
            overlap = ball.radius - dist
            ball.x += normal[0] * overlap
            ball.y += normal[1] * overlap

            # 反射速度
            dot_product = np.dot([ball.vx, ball.vy], normal)
            ball.vx -= 2 * dot_product * normal[0] * ELASTICITY
            ball.vy -= 2 * dot_product * normal[1] * ELASTICITY

    def handle_ball_collisions(self):
        """处理小球之间的弹性碰撞 (简化版)"""
        for i in range(len(self.balls)):
            for j in range(i + 1, len(self.balls)):
                ball1 = self.balls[i]
                ball2 = self.balls[j]

                # 粗略AABB检测
                aabb1 = ball1.get_aabb()
                aabb2 = ball2.get_aabb()
                if not (aabb1[0] < aabb2[2] and aabb1[2] > aabb2[0] and
                        aabb1[1] < aabb2[3] and aabb1[3] > aabb2[1]):
                    continue

                # 精确距离检测
                dx = ball2.x - ball1.x
                dy = ball2.y - ball1.y
                dist = math.sqrt(dx*dx + dy*dy)

                if dist < ball1.radius + ball2.radius:
                    # 发生碰撞
                    # 1. 重新定位球体，防止重叠
                    overlap = 0.5 * (ball1.radius + ball2.radius - dist)
                    ball1.x -= overlap * (dx / dist)
                    ball1.y -= overlap * (dy / dist)
                    ball2.x += overlap * (dx / dist)
                    ball2.y += overlap * (dy / dist)

                    # 2. 计算碰撞后的速度 (一维弹性碰撞公式)
                    # 法线方向
                    nx = dx / dist
                    ny = dy / dist
                    
                    # 切线方向
                    tx = -ny
                    ty = nx

                    # 投影速度到法线和切线方向
                    v1n = ball1.vx * nx + ball1.vy * ny
                    v1t = ball1.vx * tx + ball1.vy * ty
                    v2n = ball2.vx * nx + ball2.vy * ny
                    v2t = ball2.vx * tx + ball2.vy * ty

                    # 使用一维弹性碰撞公式计算新法线速度
                    # (m1*v1 + m2*v2) / (m1+m2) + (v2-v1) * m2/(m1+m2) 等
                    # 为了简化，我们假设质量与半径平方成正比
                    m1, m2 = ball1.mass, ball2.mass
                    v1n_final = (v1n * (m1 - m2) + 2 * m2 * v2n) / (m1 + m2)
                    v2n_final = (v2n * (m2 - m1) + 2 * m1 * v1n) / (m1 + m2)

                    # 转换回x,y坐标系
                    ball1.vx = v1n_final * nx + v1t * tx
                    ball1.vy = v1n_final * ny + v1t * ty
                    ball2.vx = v2n_final * nx + v2t * tx
                    ball2.vy = v2n_final * ny + v2t * ty

                    # 应用弹性系数
                    ball1.vx *= ELASTICITY
                    ball1.vy *= ELASTICITY
                    ball2.vx *= ELASTICITY
                    ball2.vy *= ELASTICITY

    def draw(self):
        """绘制所有物体"""
        self.screen.fill(BACKGROUND_COLOR)
        
        # 绘制所有六边形
        for hexagon in self.hexagons:
            hexagon.draw(self.screen)

        # 绘制所有小球
        for ball in self.balls:
            ball.draw(self.screen)

        pygame.display.flip()

    def run(self):
        """主循环"""
        while True:
            dt = self.clock.tick(FPS) / 1000.0  # 将毫秒转换为秒

            self.handle_events()
            self.update(dt)
            self.draw()

if __name__ == '__main__':
    simulator = PhysicsSimulator()
    simulator.run()