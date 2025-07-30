好的，这是一个使用 Python 和 Pygame 库实现的物理模拟。

这个程序的核心是物理引擎，它处理重力、碰撞和运动。对于旋转的六边形盒子，我们将通过更新它们的顶点位置来模拟旋转，并实时计算这些顶点以进行精确的碰撞检测。

### 设计思路

1. **Pygame Setup**: 使用 Pygame 创建一个窗口，设置帧率，并处理用户输入（如鼠标点击）。
2. **物理对象**:
   - **Balls (球)**: 简单的圆形物体，具有位置、速度、半径和颜色。它们会受到重力影响，并能与其他球或盒子发生碰撞。
   - **Hollow Hexagons (空心六边形盒子)**: 由6个顶点定义的多边形。我们将只绘制5条边，模拟一个开口。它们围绕屏幕中心旋转。
3. **物理引擎**:
   - **运动 (Movement)**: 在每一帧，球的速度会因重力而增加，然后位置会根据新速度更新。
   - **碰撞检测 (Collision Detection)**:
     - **球与球 (Ball-Ball)**: 通过检查两个球心之间的距离是否小于它们半径之和来判断。
     - **球与盒子 (Ball-Hexagon)**: 这是最复杂的部分。我们将六边形的每条边视为一个线段，并检查球是否与任何线段发生碰撞。这涉及到计算球心到线段的最短距离。
   - **碰撞响应 (Collision Response)**:
     - **球与球**: 使用一维弹性碰撞公式来计算碰撞后的新速度。
     - **球与盒子**: 将盒子视为静止的（因为其质量远大于球），碰撞时球的速度会沿着碰撞点的法线方向反射。
4. **旋转**: 六边形的顶点位置会根据一个随时间变化的角度进行更新，以实现旋转效果。
5. **用户交互**: 点击鼠标会在屏幕中心生成一个具有随机颜色的新球。

### 代码实现

首先，请确保你已经安装了 Pygame。如果还没有安装，可以在终端中运行：

```bash
pip install pygame
```

然后，将以下代码保存为一个 Python 文件（例如 `physics_simulation.py`）并运行它。

```python
import pygame
import sys
import math
import random

# --- 常量定义 ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 800
FPS = 60
 CENTER = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# 物理常量
GRAVITY = 0.5
ELASTICITY = 1.0 # 完全弹性碰撞

# --- 辅助函数 ---

def distance(p1, p2):
    """计算两点之间的欧几里得距离"""
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def rotate_point(point, angle, center):
    """将一个点绕指定中心旋转给定角度"""
    x, y = point
    cx, cy = center
    s = math.sin(angle)
    c = math.cos(angle)
    
    # 平移到原点
    x -= cx
    y -= cy
    
    # 旋转
    new_x = x * c - y * s
    new_y = x * s + y * c
    
    # 平移回去
    new_x += cx
    new_y += cy
    
    return new_x, new_y

# --- 类定义 ---

class Ball:
    def __init__(self, x, y, radius, color):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.vx = random.uniform(-2, 2) # 初始随机速度，避免完全静止
        self.vy = 0

    def move(self):
        """根据速度更新位置，并应用重力"""
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

    def draw(self, screen):
        """在屏幕上绘制球"""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class HollowHexagon:
    def __init__(self, center, size, rotation_speed):
        self.center = center
        self.size = size
        self.rotation_speed = rotation_speed
        self.angle = 0
        self.vertices = self._calculate_vertices()
        self.open_side_index = 0 # 假设第一条边是开口

    def _calculate_vertices(self):
        """根据当前角度计算六边形的顶点"""
        vertices = []
        for i in range(6):
            angle_deg = 60 * i + self.angle
            angle_rad = math.radians(angle_deg)
            x = self.center[0] + self.size * math.cos(angle_rad)
            y = self.center[1] + self.size * math.sin(angle_rad)
            vertices.append((x, y))
        return vertices

    def update(self):
        """更新六边形的旋转角度和顶点"""
        self.angle += self.rotation_speed
        self.vertices = self._calculate_vertices()

    def draw(self, screen):
        """绘制六边形的五条边"""
        for i in range(6):
            if i != self.open_side_index:
                start_pos = self.vertices[i]
                end_pos = self.vertices[(i + 1) % 6]
                pygame.draw.line(screen, WHITE, start_pos, end_pos, 3)

    def get_walls(self):
        """获取构成盒子的线段列表（不包括开口边）"""
        walls = []
        for i in range(6):
            if i != self.open_side_index:
                start_pos = self.vertices[i]
                end_pos = self.vertices[(i + 1) % 6]
                walls.append((start_pos, end_pos))
        return walls

# --- 碰撞检测与响应 ---

def collide_balls(ball1, ball2):
    """处理两个球之间的弹性碰撞"""
    dx = ball2.x - ball1.x
    dy = ball2.y - ball1.y
    dist = math.hypot(dx, dy)
    
    # 检查是否发生碰撞
    if dist < ball1.radius + ball2.radius:
        # 1. 防止球体粘连，将它们分开
        overlap = 0.5 * (dist - ball1.radius - ball2.radius)
        ball1.x -= overlap * (dx / dist)
        ball1.y -= overlap * (dy / dist)
        ball2.x += overlap * (dx / dist)
        ball2.y += overlap * (dy / dist)
        
        # 2. 一维弹性碰撞公式 (质量相等时简化)
        # 在球心连线方向上的速度分量
        dot_product = (ball2.vx - ball1.vx) * dx + (ball2.vy - ball1.vy) * dy
        
        if dot_product > 0: # 只有当球相互靠近时才交换速度
            collision_scalar = dot_product / (dist**2)
            ball1.vx += collision_scalar * dx * ELASTICITY
            ball1.vy += collision_scalar * dy * ELASTICITY
            ball2.vx -= collision_scalar * dx * ELASTICITY
            ball2.vy -= collision_scalar * dy * ELASTICITY

def distance_point_to_segment(p, a, b):
    """计算点 P 到线段 AB 的最短距离，并返回最近点"""
    # 向量 AB 和 AP
    ab_x, ab_y = b[0] - a[0], b[1] - a[1]
    ap_x, ap_y = p[0] - a[0], p[1] - a[1]

    # 线段 AB 长度的平方
    ab_mag_sq = ab_x**2 + ab_y**2

    if ab_mag_sq == 0.0:
        # A 和 B 是同一个点
        return distance(p, a), a

    # 投影参数 t，用于计算线段上的最近点
    t = (ap_x * ab_x + ap_y * ab_y) / ab_mag_sq

    if t < 0.0:
        # 最近点是 A
        return distance(p, a), a
    elif t > 1.0:
        # 最近点是 B
        return distance(p, b), b
    else:
        # 最近点在线段上
        closest_x = a[0] + t * ab_x
        closest_y = a[1] + t * ab_y
        return distance(p, (closest_x, closest_y)), (closest_x, closest_y)

def collide_ball_with_walls(ball, walls):
    """处理球与所有墙壁的碰撞"""
    for wall in walls:
        p1, p2 = wall
        dist, closest_point = distance_point_to_segment((ball.x, ball.y), p1, p2)
        
        if dist < ball.radius:
            # 1. 防止球穿透墙壁
            penetration_depth = ball.radius - dist
            # 从碰撞点到球心的向量
            nx = ball.x - closest_point[0]
            ny = ball.y - closest_point[1]
            norm_length = math.hypot(nx, ny)
            
            if norm_length > 0:
                nx /= norm_length
                ny /= norm_length
            
                ball.x += nx * penetration_depth
                ball.y += ny * penetration_depth

                # 2. 反射速度向量 (假设墙壁质量无穷大)
                # v' = v - 2 * dot(v, n) * n
                dot_product = ball.vx * nx + ball.vy * ny
                ball.vx = ball.vx - 2 * dot_product * nx * ELASTICITY
                ball.vy = ball.vy - 2 * dot_product * ny * ELASTICITY
                # 碰撞一次就够了，跳出循环
                break 

# --- 主程序 ---

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("物理模拟：旋转六边形与弹性球")
    clock = pygame.time.Clock()

    # 创建四个旋转方向交替的六边形盒子
    hexagons = []
    base_size = 80
    speeds = [1, -1.5, 2, -2.5] # 旋转速度和方向
    for i in range(4):
        size = base_size + i * 50
        hexagon = HollowHexagon(CENTER, size, speeds[i])
        hexagons.append(hexagon)

    balls = []
    colors = [
        (255, 0, 0), (0, 255, 0), (0, 0, 255),
        (255, 255, 0), (255, 0, 255), (0, 255, 255),
        (255, 165, 0), (128, 0, 128)
    ]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # 点击鼠标，在中心生成一个新球
                new_color = random.choice(colors)
                new_ball = Ball(CENTER[0], CENTER[1], 15, new_color)
                balls.append(new_ball)

        # --- 更新状态 ---
        # 更新六边形
        for hexagon in hexagons:
            hexagon.update()
        
        # 移动球
        for ball in balls:
            ball.move()

        # 获取所有墙壁
        all_walls = []
        for hexagon in hexagons:
            all_walls.extend(hexagon.get_walls())

        # 球与墙壁碰撞
        for ball in balls:
            collide_ball_with_walls(ball, all_walls)

        # 球与球碰撞
        for i in range(len(balls)):
            for j in range(i + 1, len(balls)):
                collide_balls(balls[i], balls[j])

        # --- 绘制 ---
        screen.fill(BLACK)

        # 绘制所有六边形
        for hexagon in hexagons:
            hexagon.draw(screen)

        # 绘制所有球
        for ball in balls:
            ball.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
```

### 代码解释

1. **常量和辅助函数**:
   - 定义了屏幕尺寸、颜色、物理常数（重力、弹性）。
   - `distance`, `rotate_point`: 用于计算距离和旋转向量的实用函数。
2. **`Ball` 类**:
   - 属性包括位置 (`x`, `y`)、速度 (`vx`, `vy`)、半径和颜色。
   - `move()`: 应用重力并更新位置。
   - `draw()`: 使用 `pygame.draw.circle` 绘制球。
3. **`HollowHexagon` 类**:
   - 属性包括中心点、大小、旋转速度、当前角度和顶点列表。
   - `_calculate_vertices()`: 核心方法，根据当前角度计算六个顶点的屏幕坐标。
   - `update()`: 每帧调用，增加角度并重新计算顶点，实现旋转。
   - `draw()`: 只绘制 `open_side_index` 以外的五条边。
   - `get_walls()`: 返回一个由线段（元组对）组成的列表，代表盒子的实体边界。
4. **碰撞处理函数**:
   - `collide_balls(b1, b2)`: 实现了两个相同质量球体的弹性碰撞。它首先通过轻微移动球体来防止它们重叠，然后使用向量数学来交换法线方向上的速度分量。
   - `distance_point_to_segment(p, a, b)`: 这是一个关键的几何函数，用于计算一个点到一条线段的最短距离。这对于球与墙壁的碰撞检测至关重要。
   - `collide_ball_with_walls(ball, walls)`: 遍历所有墙壁，使用上述函数检测碰撞。如果发生碰撞，它会先将球推出墙壁以解决穿透问题，然后通过反射其速度向量来响应碰撞。
5. **`main` 函数**:
   - 初始化 Pygame，创建窗口和时钟。
   - 创建了四个 `HollowHexagon` 对象，大小递增，旋转方向交替（通过正负速度实现）。
   - `balls` 列表用于存储所有活动的球。
   - **主循环**:
     - **事件处理**: 检查退出事件和鼠标点击。点击时会创建一个新球并添加到 `balls` 列表中。
     - **更新**:
       - 调用每个六边形的 `update()` 方法。
       - 调用每个球的 `move()` 方法。
       - 收集所有盒子的墙壁。
       - 遍历所有球，先检测与墙壁的碰撞，再检测球与球之间的碰撞。
     - **绘制**:
       - 清空屏幕为黑色。
       - 绘制所有六边形和球。
       - `pygame.display.flip()` 更新屏幕显示。
     - `clock.tick(FPS)` 确保程序以稳定的帧率运行。