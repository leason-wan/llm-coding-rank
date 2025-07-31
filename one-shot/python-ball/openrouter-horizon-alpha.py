import math
import random
import pygame
import pymunk
import pymunk.pygame_util

# ---------------- Config ----------------
W, H = 900, 900
CENTER = (W // 2, H // 2)
GRAVITY = (0, 900)  # downward
FPS = 120

BALL_RADIUS = 8
BALL_MASS = 1.0
BALL_ELASTICITY = 1.0
BALL_FRICTION = 0.0

WALL_ELASTICITY = 1.0
WALL_FRICTION = 0.0

# Radii of the 4 hexagons (from small to large)
HEX_RADII = [90, 160, 230, 300]

# Angular velocities (rad/s); alternating CW(-)/CCW(+)
# small->large: CW, CCW, CW, CCW
OMEGAS = [-math.radians(30), math.radians(20), -math.radians(15), math.radians(10)]

# Which edge is missing? index 0..5 corresponds to the edge between vertex i and (i+1)%6
MISSING_EDGE_INDEX = 0

# ---------------- Utility ----------------
def hex_vertices(center, radius, rot_angle):
    cx, cy = center
    verts = []
    for k in range(6):
        ang = rot_angle + math.radians(60 * k)
        x = cx + radius * math.cos(ang)
        y = cy + radius * math.sin(ang)
        verts.append((x, y))
    return verts

def make_color():
    return (random.randint(60, 255), random.randint(60, 255), random.randint(60, 255))

# ---------------- Simulation Class ----------------
class RotatingHexWalls:
    def __init__(self, space, center, radii, omegas, missing_edge_index=0):
        self.space = space
        self.center = center
        self.radii = radii
        self.omegas = omegas
        self.missing_edge_index = missing_edge_index
        self.rot_angles = [0.0 for _ in radii]
        # we will rebuild segments each frame; store current segments to remove
        self.current_segments = []

    def update(self, dt):
        # advance rotation angles
        for i in range(len(self.rot_angles)):
            self.rot_angles[i] += self.omegas[i] * dt
        # rebuild walls
        self.rebuild_segments()

    def rebuild_segments(self):
        # remove old segments from space
        for seg in self.current_segments:
            self.space.remove(seg, seg.body)
        self.current_segments = []

        # create new segments for each hexagon, omitting one edge
        for i, R in enumerate(self.radii):
            rot = self.rot_angles[i]
            verts = hex_vertices(self.center, R, rot)

            # body for kinematic segments
            body = pymunk.Body(body_type=pymunk.Body.KINEMATIC)
            body.position = (0, 0)  # we'll use world coords directly
            # create 5 segments
            for e in range(6):
                if e == self.missing_edge_index:
                    continue
                a = verts[e]
                b = verts[(e + 1) % 6]
                seg = pymunk.Segment(body, a, b, 0.0)
                seg.elasticity = WALL_ELASTICITY
                seg.friction = WALL_FRICTION
                # group or layers can be left default so balls collide with them
                self.space.add(body, seg)
                self.current_segments.append(seg)

# ---------------- Main ----------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Rotating 5-edge Hex Boxes with Elastic Balls")
    clock = pygame.time.Clock()

    # Pymunk space
    space = pymunk.Space()
    space.gravity = GRAVITY

    draw_options = pymunk.pygame_util.DrawOptions(screen)

    # Rotating hex walls
    walls = RotatingHexWalls(space, CENTER, HEX_RADII, OMEGAS, MISSING_EDGE_INDEX)
    walls.rebuild_segments()

    balls = []  # list of (body, shape, color)

    running = True
    accumulator = 0.0
    dt_fixed = 1.0 / FPS

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # spawn a ball at center
                body = pymunk.Body()
                body.position = CENTER
                shape = pymunk.Circle(body, BALL_RADIUS)
                shape.mass = BALL_MASS
                shape.elasticity = BALL_ELASTICITY
                shape.friction = BALL_FRICTION
                # moment of inertia for a solid circle: I = m r^2 / 2
                body.moment = pymunk.moment_for_circle(BALL_MASS, 0, BALL_RADIUS)
                space.add(body, shape)
                color = make_color()
                balls.append((body, shape, color))

        # Step simulation with fixed timestep for stability
        frame_dt = clock.tick(FPS) / 1000.0
        accumulator += frame_dt
        while accumulator >= dt_fixed:
            walls.update(dt_fixed)
            space.step(dt_fixed)
            accumulator -= dt_fixed

        # Render
        screen.fill((12, 12, 16))
        # Draw walls via pygame (we already have segments in space; debug draw is fine)
        space.debug_draw(draw_options)

        # Overdraw balls with their colors (to distinguish)
        for body, shape, color in balls:
            x, y = body.position
            pygame.draw.circle(screen, color, (int(x), int(y)), int(shape.radius))

        # Center point for reference
        pygame.draw.circle(screen, (200, 200, 200), (int(CENTER[0]), int(CENTER[1])), 3)

        # Text hint
        font = pygame.font.SysFont(None, 22)
        txt = font.render("Click to spawn a ball at center. Gravity on. Perfectly elastic collisions.", True, (230, 230, 230))
        screen.blit(txt, (16, 16))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()
