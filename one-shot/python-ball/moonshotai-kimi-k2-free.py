<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>物理六边形盒子模拟器</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            background: #1e1e1e;
            font-family: Arial, sans-serif;
        }
        
        #gameContainer {
            position: relative;
        }
        
        canvas {
            border: 1px solid #333;
            background: #0a0a0a;
            cursor: pointer;
        }
        
        #info {
            position: absolute;
            top: 10px;
            left: 10px;
            color: white;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div id="gameContainer">
        <canvas id="gameCanvas" width="800" height="800"></canvas>
        <div id="info">点击屏幕释放小球</div>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        
        // 物理常数
        const GRAVITY = 0.5;
        const BALL_RADIUS = 8;
        const BOX_SIDES = 5; // 五边形
        
        // 六边形盒子配置（实际上是五边形）
        const boxes = [
            { innerRadius: 50, rotationSpeed: 0.02, direction: 1, color: 'rgba(255, 255, 255, 0.3)' },
            { innerRadius: 100, rotationSpeed: 0.015, direction: -1, color: 'rgba(255, 255, 255, 0.25)' },
            { innerRadius: 150, rotationSpeed: 0.01, direction: 1, color: 'rgba(255, 255, 255, 0.2)' },
            { innerRadius: 200, rotationSpeed: 0.005, direction: -1, color: 'rgba(255, 255, 255, 0.15)' }
        ];
        
        let balls = [];
        let nextColorIndex = 0;
        const colors = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8',
            '#F7DC6F', '#BB8FCE', '#85C1E2', '#F8C471', '#82E0AA'
        ];
        
        class Ball {
            constructor(x, y, color) {
                this.x = x;
                this.y = y;
                this.vx = 0;
                this.vy = 0;
                this.radius = BALL_RADIUS;
                this.color = color;
            }
            
            update() {
                // 应用重力
                this.vy += GRAVITY;
                
                // 更新位置
                this.x += this.vx;
                this.y += this.vy;
                
                // 摩擦（虽然是完全弹性碰撞，但这里保持简单）
            }
            
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();
                ctx.strokeStyle = 'white';
                ctx.stroke();
            }
        }
        
        function getBoxVertices(boxIndex, time) {
            const box = boxes[boxIndex];
            const vertices = [];
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            
            for (let i = 0; i < BOX_SIDES; i++) {
                const angle = (2 * Math.PI / BOX_SIDES) * i + 
                             time * box.rotationSpeed * box.direction;
                vertices.push({
                    x: centerX + box.innerRadius * Math.cos(angle),
                    y: centerY + box.innerRadius * Math.sin(angle)
                });
            }
            
            // 添加缺失边的连接点
            const missingSideAngle1 = (2 * Math.PI / BOX_SIDES) * BOX_SIDES + 
                                     time * box.rotationSpeed * box.direction;
            const missingSideAngle2 = (2 * Math.PI / BOX_SIDES) * 0 + 
                                     time * box.rotationSpeed * box.direction;
            
            return vertices;
        }
        
        function checkBallBoxCollision(ball) {
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            
            for (let boxIndex = boxes.length - 1; boxIndex >= 0; boxIndex--) {
                const box = boxes[boxIndex];
                const vertices = getBoxVertices(boxIndex, Date.now() * 0.001);
                
                // 检查球是否在盒子外
                const dx = ball.x - centerX;
                const dy = ball.y - centerY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > box.innerRadius + ball.radius) {
                    // 检查是否与边碰撞
                    for (let i = 0; i < vertices.length; i++) {
                        const j = (i + 1) % vertices.length;
                        
                        const edge = {
                            x1: vertices[i].x,
                            y1: vertices[i].y,
                            x2: vertices[j].x,
                            y2: vertices[j].y
                        };
                        
                        // 计算球到边的最近点
                        const edgeDx = edge.x2 - edge.x1;
                        const edgeDy = edge.y2 - edge.y1;
                        const edgeLength = Math.sqrt(edgeDx * edgeDx + edgeDy * edgeDy);
                        const edgeUnitDx = edgeDx / edgeLength;
                        const edgeUnitDy = edgeDy / edgeLength;
                        
                        const t = Math.max(0, Math.min(1, 
                            ((ball.x - edge.x1) * edgeUnitDx + (ball.y - edge.y1) * edgeUnitDy) / edgeLength
                        ));
                        
                        const closestX = edge.x1 + t * edgeDx;
                        const closestY = edge.y1 + t * edgeDy;
                        
                        const dx2 = ball.x - closestX;
                        const dy2 = ball.y - closestY;
                        const distance2 = Math.sqrt(dx2 * dx2 + dy2 * dy2);
                        
                        if (distance2 < ball.radius) {
                            // 碰撞响应
                            const normalX = dx2 / distance2;
                            const normalY = dy2 / distance2;
                            
                            // 将球移出
                            ball.x = closestX + normalX * ball.radius;
                            ball.y = closestY + normalY * ball.radius;
                            
                            // 反射速度
                            const dotProduct = ball.vx * normalX + ball.vy * normalY;
                            ball.vx -= 2 * dotProduct * normalX;
                            ball.vy -= 2 * dotProduct * normalY;
                        }
                    }
                } else if (boxIndex === 0) {
                    // 检查四个盒子之间是否可以移动
                    let canPass = false;
                    
                    // 计算球的角度位置
                    const ballAngle = Math.atan2(ball.y - centerY, ball.x - centerX);
                    const currentAngle = ballAngle + time * box.rotationSpeed * box.direction;
                    
                    // 检查是否在缺口的允许范围内（大约60度）
                    for (let i = 0; i < BOX_SIDES - 1; i++) {
                        const sectorStart = (2 * Math.PI / BOX_SIDES) * i;
                        const sectorEnd = (2 * Math.PI / BOX_SIDES) * (i + 1);
                        
                        if (currentAngle >= sectorStart - 0.1 && currentAngle <= sectorEnd + 0.1) {
                            canPass = true;
                            break;
                        }
                    }
                }
            }
        }
        
        function drawBoxes() {
            const centerX = canvas.width / 2;
            const centerY = canvas.height / 2;
            const time = Date.now() * 0.001;
            
            for (const [index, box] of boxes.entries()) {
                const vertices = getBoxVertices(index, time);
                
                ctx.beginPath();
                ctx.moveTo(vertices[0].x, vertices[0].y);
                
                for (let i = 1; i < vertices.length; i++) {
                    ctx.lineTo(vertices[i].x, vertices[i].y);
                }
                
                // 不闭合路径形成开口
                ctx.strokeStyle = box.color;
                ctx.lineWidth = 3;
                ctx.stroke();
                
                // 绘制缺口提示
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.arc(centerX, centerY, box.innerRadius, 0, Math.PI * 2);
                ctx.strokeStyle = box.color;
                ctx.stroke();
                ctx.setLineDash([]);
            }
        }
        
        function checkBallCollisions() {
            for (let i = 0; i < balls.length; i++) {
                for (let j = i + 1; j < balls.length; j++) {
                    const ball1 = balls[i];
                    const ball2 = balls[j];
                    
                    const dx = ball2.x - ball1.x;
                    const dy = ball2.y - ball1.y;
                    const distance = Math.sqrt(dx * dx + dy * dy);
                    
                    if (distance < ball1.radius + ball2.radius) {
                        // 碰撞检测
                        const nx = dx / distance;
                        const ny = dy / distance;
                        
                        // 分离小球
                        const overlap = (ball1.radius + ball2.radius) - distance;
                        ball1.x -= nx * overlap / 2;
                        ball1.y -= ny * overlap / 2;
                        ball2.x += nx * overlap / 2;
                        ball2.y += ny * overlap / 2;
                        
                        // 计算相对速度
                        const relativeVx = ball2.vx - ball1.vx;
                        const relativeVy = ball2.vy - ball1.vy;
                        
                        // 计算碰撞法向速度
                        const speed = relativeVx * nx + relativeVy * ny;
                        
                        if (speed > 0) return; // 小球正在分离
                        
                        // 计算冲量
                        const impulse = 2 * speed / 2;
                        
                        // 应用冲量
                        ball1.vx += impulse * nx;
                        ball1.vy += impulse * ny;
                        ball2.vx -= impulse * nx;
                        ball2.vy -= impulse * ny;
                    }
                }
            }
        }
        
        function gameLoop() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            // 绘制盒子
            drawBoxes();
            
            // 更新和绘制球
            for (let i = balls.length - 1; i >= 0; i--) {
                const ball = balls[i];
                ball.update();
                
                // 检查与盒子的碰撞
                checkBallBoxCollision(ball);
                
                // 检查球与球的碰撞
                checkBallCollisions();
                
                // 检查是否出界
                if (ball.y > canvas.height + 50) {
                    balls.splice(i, 1);
                    continue;
                }
                
                ball.draw();
            }
            
            requestAnimationFrame(gameLoop);
        }
        
        // 点击事件
        canvas.addEventListener('click', () => {
            const color = colors[nextColorIndex % colors.length];
            nextColorIndex++;
            const newBall = new Ball(canvas.width / 2, canvas.height / 2, color);
            // 初始速度
            newBall.vx = (Math.random() - 0.5) * 4;
            newBall.vy = (Math.random() - 0.5) * 4;
            balls.push(newBall);
        });
        
        // 开始游戏循环
        gameLoop();
    </script>
</body>
</html>
