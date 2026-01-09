import pygame
import math
from config import COLORS, WINDOW_WIDTH, WINDOW_HEIGHT


class IsometricRenderer:
    """
    Renders a realistic isometric city intersection
    Similar to the reference image with buildings, trees, and proper perspective
    """
    
    def __init__(self):
        # Isometric projection settings
        self.tile_width = 100
        self.tile_height = 50
        self.offset_x = WINDOW_WIDTH // 2 - 200  # Center offset (account for panel)
        self.offset_y = 150
        
        # Road settings
        self.road_width = 200  # 4 lanes
        self.lane_width = 50
        self.num_lanes_per_direction = 2  # 2 lanes each direction = 4 total
        
        # Colors for isometric view
        self.colors = {
            'road': (70, 70, 75),
            'road_dark': (50, 50, 55),
            'sidewalk': (180, 180, 180),
            'sidewalk_edge': (150, 150, 150),
            'grass': (80, 160, 80),
            'grass_dark': (60, 130, 60),
            'building_wall': (200, 200, 210),
            'building_side': (160, 160, 170),
            'building_roof': (180, 100, 100),
            'building_window': (150, 200, 230),
            'tree_trunk': (100, 70, 40),
            'tree_leaves': (50, 140, 50),
            'tree_leaves_dark': (30, 100, 30),
            'marking_white': (255, 255, 255),
            'marking_yellow': (255, 220, 50),
            'zebra': (255, 255, 255),
        }
        
    def cart_to_iso(self, x, y):
        """Convert cartesian coordinates to isometric"""
        iso_x = (x - y) + self.offset_x
        iso_y = (x + y) / 2 + self.offset_y
        return int(iso_x), int(iso_y)
    
    def draw_ground(self, screen):
        """Draw the ground/grass areas"""
        # Fill with grass
        screen.fill(self.colors['grass'])
        
        # Add some texture variation
        for i in range(0, WINDOW_WIDTH, 40):
            for j in range(0, WINDOW_HEIGHT, 40):
                if (i + j) % 80 == 0:
                    pygame.draw.rect(screen, self.colors['grass_dark'], 
                                   (i, j, 20, 20))
    
    def draw_isometric_road(self, screen):
        """Draw the main intersection roads in isometric view"""
        center_x, center_y = 300, 300
        road_half = self.road_width // 2
        
        # Road polygon points for horizontal road (left-right)
        # Far left to intersection
        h_road_left = [
            self.cart_to_iso(0, center_y - road_half),
            self.cart_to_iso(0, center_y + road_half),
            self.cart_to_iso(center_x - road_half, center_y + road_half),
            self.cart_to_iso(center_x - road_half, center_y - road_half),
        ]
        pygame.draw.polygon(screen, self.colors['road'], h_road_left)
        
        # Far right from intersection
        h_road_right = [
            self.cart_to_iso(center_x + road_half, center_y - road_half),
            self.cart_to_iso(center_x + road_half, center_y + road_half),
            self.cart_to_iso(600, center_y + road_half),
            self.cart_to_iso(600, center_y - road_half),
        ]
        pygame.draw.polygon(screen, self.colors['road'], h_road_right)
        
        # Vertical road (top-bottom)
        # Top section
        v_road_top = [
            self.cart_to_iso(center_x - road_half, 0),
            self.cart_to_iso(center_x + road_half, 0),
            self.cart_to_iso(center_x + road_half, center_y - road_half),
            self.cart_to_iso(center_x - road_half, center_y - road_half),
        ]
        pygame.draw.polygon(screen, self.colors['road'], v_road_top)
        
        # Bottom section
        v_road_bottom = [
            self.cart_to_iso(center_x - road_half, center_y + road_half),
            self.cart_to_iso(center_x + road_half, center_y + road_half),
            self.cart_to_iso(center_x + road_half, 600),
            self.cart_to_iso(center_x - road_half, 600),
        ]
        pygame.draw.polygon(screen, self.colors['road'], v_road_bottom)
        
        # Center intersection
        intersection = [
            self.cart_to_iso(center_x - road_half, center_y - road_half),
            self.cart_to_iso(center_x + road_half, center_y - road_half),
            self.cart_to_iso(center_x + road_half, center_y + road_half),
            self.cart_to_iso(center_x - road_half, center_y + road_half),
        ]
        pygame.draw.polygon(screen, self.colors['road'], intersection)
        
        # Draw lane markings
        self._draw_lane_markings(screen, center_x, center_y, road_half)
        
        # Draw zebra crossings
        self._draw_zebra_crossings(screen, center_x, center_y, road_half)
        
    def _draw_lane_markings(self, screen, cx, cy, road_half):
        """Draw road lane markings"""
        # Center line (yellow) for horizontal road
        for i in range(0, 600, 30):
            if i < cx - road_half or i > cx + road_half:
                p1 = self.cart_to_iso(i, cy)
                p2 = self.cart_to_iso(i + 15, cy)
                pygame.draw.line(screen, self.colors['marking_yellow'], p1, p2, 3)
        
        # Center line for vertical road
        for i in range(0, 600, 30):
            if i < cy - road_half or i > cy + road_half:
                p1 = self.cart_to_iso(cx, i)
                p2 = self.cart_to_iso(cx, i + 15)
                pygame.draw.line(screen, self.colors['marking_yellow'], p1, p2, 3)
        
        # White lane dividers (dashed)
        lane_offsets = [-75, -25, 25, 75]
        for offset in [-50, 50]:
            # Horizontal road
            for i in range(0, 600, 40):
                if i < cx - road_half - 20 or i > cx + road_half + 20:
                    p1 = self.cart_to_iso(i, cy + offset)
                    p2 = self.cart_to_iso(i + 20, cy + offset)
                    pygame.draw.line(screen, self.colors['marking_white'], p1, p2, 2)
            
            # Vertical road
            for i in range(0, 600, 40):
                if i < cy - road_half - 20 or i > cy + road_half + 20:
                    p1 = self.cart_to_iso(cx + offset, i)
                    p2 = self.cart_to_iso(cx + offset, i + 20)
                    pygame.draw.line(screen, self.colors['marking_white'], p1, p2, 2)
    
    def _draw_zebra_crossings(self, screen, cx, cy, road_half):
        """Draw zebra/pedestrian crossings"""
        stripe_width = 15
        stripe_gap = 10
        
        # North crossing
        for i in range(-road_half + 10, road_half - 10, stripe_width + stripe_gap):
            points = [
                self.cart_to_iso(cx + i, cy - road_half - 30),
                self.cart_to_iso(cx + i + stripe_width, cy - road_half - 30),
                self.cart_to_iso(cx + i + stripe_width, cy - road_half - 5),
                self.cart_to_iso(cx + i, cy - road_half - 5),
            ]
            pygame.draw.polygon(screen, self.colors['zebra'], points)
        
        # South crossing
        for i in range(-road_half + 10, road_half - 10, stripe_width + stripe_gap):
            points = [
                self.cart_to_iso(cx + i, cy + road_half + 5),
                self.cart_to_iso(cx + i + stripe_width, cy + road_half + 5),
                self.cart_to_iso(cx + i + stripe_width, cy + road_half + 30),
                self.cart_to_iso(cx + i, cy + road_half + 30),
            ]
            pygame.draw.polygon(screen, self.colors['zebra'], points)
        
        # West crossing
        for i in range(-road_half + 10, road_half - 10, stripe_width + stripe_gap):
            points = [
                self.cart_to_iso(cx - road_half - 30, cy + i),
                self.cart_to_iso(cx - road_half - 5, cy + i),
                self.cart_to_iso(cx - road_half - 5, cy + i + stripe_width),
                self.cart_to_iso(cx - road_half - 30, cy + i + stripe_width),
            ]
            pygame.draw.polygon(screen, self.colors['zebra'], points)
        
        # East crossing
        for i in range(-road_half + 10, road_half - 10, stripe_width + stripe_gap):
            points = [
                self.cart_to_iso(cx + road_half + 5, cy + i),
                self.cart_to_iso(cx + road_half + 30, cy + i),
                self.cart_to_iso(cx + road_half + 30, cy + i + stripe_width),
                self.cart_to_iso(cx + road_half + 5, cy + i + stripe_width),
            ]
            pygame.draw.polygon(screen, self.colors['zebra'], points)
    
    def draw_building(self, screen, x, y, width, depth, height, color=None):
        """Draw an isometric building"""
        if color is None:
            color = self.colors['building_wall']
        
        # Calculate isometric points
        # Base points
        front_left = self.cart_to_iso(x, y + depth)
        front_right = self.cart_to_iso(x + width, y + depth)
        back_left = self.cart_to_iso(x, y)
        back_right = self.cart_to_iso(x + width, y)
        
        # Top points (raised by height)
        top_front_left = (front_left[0], front_left[1] - height)
        top_front_right = (front_right[0], front_right[1] - height)
        top_back_left = (back_left[0], back_left[1] - height)
        top_back_right = (back_right[0], back_right[1] - height)
        
        # Draw faces (back to front for proper overlap)
        # Right face (darker)
        right_face = [front_right, back_right, top_back_right, top_front_right]
        right_color = tuple(max(0, c - 40) for c in color)
        pygame.draw.polygon(screen, right_color, right_face)
        pygame.draw.polygon(screen, (50, 50, 50), right_face, 1)
        
        # Left face
        left_face = [front_left, back_left, top_back_left, top_front_left]
        pygame.draw.polygon(screen, color, left_face)
        pygame.draw.polygon(screen, (50, 50, 50), left_face, 1)
        
        # Top face (lighter)
        top_face = [top_front_left, top_front_right, top_back_right, top_back_left]
        top_color = tuple(min(255, c + 20) for c in color)
        pygame.draw.polygon(screen, top_color, top_face)
        pygame.draw.polygon(screen, (50, 50, 50), top_face, 1)
        
        # Draw windows
        self._draw_windows(screen, x, y, width, depth, height)
        
    def _draw_windows(self, screen, x, y, width, depth, height):
        """Draw windows on building"""
        window_size = 15
        window_gap = 25
        
        # Windows on left face
        for row in range(2, height - 20, window_gap):
            for col in range(10, depth - 10, window_gap):
                wx, wy = self.cart_to_iso(x, y + col)
                wy -= row
                pygame.draw.rect(screen, self.colors['building_window'],
                               (wx - window_size//2, wy - window_size//2, 
                                window_size, window_size))
        
        # Windows on right face
        for row in range(2, height - 20, window_gap):
            for col in range(10, width - 10, window_gap):
                wx, wy = self.cart_to_iso(x + col, y + depth)
                wy -= row
                pygame.draw.rect(screen, self.colors['building_window'],
                               (wx - window_size//2, wy - window_size//2, 
                                window_size, window_size))
    
    def draw_tree(self, screen, x, y, size=30):
        """Draw an isometric tree"""
        iso_x, iso_y = self.cart_to_iso(x, y)
        
        # Trunk
        trunk_width = size // 4
        trunk_height = size // 2
        pygame.draw.rect(screen, self.colors['tree_trunk'],
                        (iso_x - trunk_width//2, iso_y - trunk_height,
                         trunk_width, trunk_height))
        
        # Foliage (multiple circles for fullness)
        leaf_radius = size // 2
        pygame.draw.circle(screen, self.colors['tree_leaves_dark'],
                          (iso_x, iso_y - trunk_height - leaf_radius//2), leaf_radius)
        pygame.draw.circle(screen, self.colors['tree_leaves'],
                          (iso_x - 5, iso_y - trunk_height - leaf_radius), leaf_radius - 5)
        pygame.draw.circle(screen, self.colors['tree_leaves'],
                          (iso_x + 5, iso_y - trunk_height - leaf_radius - 5), leaf_radius - 8)
    
    def draw_sidewalk(self, screen, x, y, width, depth):
        """Draw a sidewalk section"""
        points = [
            self.cart_to_iso(x, y),
            self.cart_to_iso(x + width, y),
            self.cart_to_iso(x + width, y + depth),
            self.cart_to_iso(x, y + depth),
        ]
        pygame.draw.polygon(screen, self.colors['sidewalk'], points)
        pygame.draw.polygon(screen, self.colors['sidewalk_edge'], points, 2)
    
    def draw_scene(self, screen):
        """Draw the complete isometric city scene"""
        # Ground
        self.draw_ground(screen)
        
        # Roads
        self.draw_isometric_road(screen)
        
        # Sidewalks around intersection
        cx, cy = 300, 300
        road_half = 100
        sw_width = 30
        
        # Buildings in corners (sorted by depth for proper rendering)
        buildings = [
            # Top-left area
            (50, 50, 80, 60, 120, (180, 180, 190)),
            (50, 130, 60, 50, 80, (190, 180, 170)),
            
            # Top-right area
            (420, 50, 70, 70, 100, (200, 190, 180)),
            (500, 80, 60, 50, 90, (180, 190, 200)),
            
            # Bottom-left area
            (50, 420, 80, 70, 110, (190, 200, 190)),
            (30, 500, 70, 60, 85, (200, 190, 190)),
            
            # Bottom-right area
            (420, 420, 90, 80, 130, (185, 185, 195)),
            (520, 450, 60, 50, 75, (195, 185, 185)),
        ]
        
        # Sort buildings by y position for proper depth rendering
        buildings.sort(key=lambda b: b[1])
        
        for bx, by, bw, bd, bh, bc in buildings:
            self.draw_building(screen, bx, by, bw, bd, bh, bc)
        
        # Trees
        tree_positions = [
            (140, 100), (160, 180), (450, 120), (520, 160),
            (130, 450), (170, 520), (440, 480), (500, 530),
        ]
        
        for tx, ty in tree_positions:
            self.draw_tree(screen, tx, ty, 25)


class IsometricVehicle:
    """Draws realistic isometric vehicles"""
    
    @staticmethod
    def draw_car(screen, iso_x, iso_y, color, direction='right', scale=1.0):
        """Draw an isometric car"""
        w = int(35 * scale)
        h = int(20 * scale)
        height = int(15 * scale)
        
        # Car body color
        body_color = color
        dark_color = tuple(max(0, c - 50) for c in color)
        light_color = tuple(min(255, c + 30) for c in color)
        
        if direction in ['right', 'left']:
            # Side view car
            # Body
            body = [
                (iso_x - w//2, iso_y),
                (iso_x + w//2, iso_y),
                (iso_x + w//2, iso_y - height),
                (iso_x - w//2, iso_y - height),
            ]
            pygame.draw.polygon(screen, body_color, body)
            pygame.draw.polygon(screen, dark_color, body, 2)
            
            # Roof/cabin
            cabin_w = w * 0.5
            cabin = [
                (iso_x - cabin_w//2, iso_y - height),
                (iso_x + cabin_w//2, iso_y - height),
                (iso_x + cabin_w//2 - 5, iso_y - height - 10),
                (iso_x - cabin_w//2 + 5, iso_y - height - 10),
            ]
            pygame.draw.polygon(screen, light_color, cabin)
            pygame.draw.polygon(screen, dark_color, cabin, 1)
            
            # Windows
            pygame.draw.rect(screen, (150, 200, 230),
                           (iso_x - cabin_w//2 + 3, iso_y - height - 8, cabin_w - 6, 6))
            
            # Wheels
            wheel_color = (30, 30, 30)
            pygame.draw.circle(screen, wheel_color, (iso_x - w//3, iso_y), 6)
            pygame.draw.circle(screen, wheel_color, (iso_x + w//3, iso_y), 6)
            
        else:  # up or down
            # Front/back view car
            body = [
                (iso_x - h//2, iso_y),
                (iso_x + h//2, iso_y),
                (iso_x + h//2, iso_y - height),
                (iso_x - h//2, iso_y - height),
            ]
            pygame.draw.polygon(screen, body_color, body)
            pygame.draw.polygon(screen, dark_color, body, 2)
            
            # Roof
            cabin = [
                (iso_x - h//3, iso_y - height),
                (iso_x + h//3, iso_y - height),
                (iso_x + h//3 - 3, iso_y - height - 8),
                (iso_x - h//3 + 3, iso_y - height - 8),
            ]
            pygame.draw.polygon(screen, light_color, cabin)
            
            # Windshield
            if direction == 'down':
                pygame.draw.rect(screen, (150, 200, 230),
                               (iso_x - h//3 + 2, iso_y - height - 6, h//1.5 - 2, 5))
            
            # Wheels (visible sides)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x - h//2, iso_y - 3), 4)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + h//2, iso_y - 3), 4)
    
    @staticmethod
    def draw_truck(screen, iso_x, iso_y, color, direction='right', scale=1.0):
        """Draw an isometric truck"""
        w = int(55 * scale)
        h = int(25 * scale)
        height = int(20 * scale)
        
        body_color = color
        dark_color = tuple(max(0, c - 50) for c in color)
        cabin_color = (60, 60, 70)
        
        if direction in ['right', 'left']:
            # Cargo area
            cargo = [
                (iso_x - w//4, iso_y),
                (iso_x + w//2, iso_y),
                (iso_x + w//2, iso_y - height - 5),
                (iso_x - w//4, iso_y - height - 5),
            ]
            pygame.draw.polygon(screen, body_color, cargo)
            pygame.draw.polygon(screen, dark_color, cargo, 2)
            
            # Cabin
            cabin = [
                (iso_x - w//2, iso_y),
                (iso_x - w//4, iso_y),
                (iso_x - w//4, iso_y - height),
                (iso_x - w//2, iso_y - height),
            ]
            pygame.draw.polygon(screen, cabin_color, cabin)
            pygame.draw.polygon(screen, (40, 40, 50), cabin, 2)
            
            # Windshield
            pygame.draw.rect(screen, (150, 200, 230),
                           (iso_x - w//2 + 3, iso_y - height + 3, w//5, height//2))
            
            # Wheels
            wheel_y = iso_y
            pygame.draw.circle(screen, (30, 30, 30), (iso_x - w//3, wheel_y), 8)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + w//4, wheel_y), 8)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + w//3 + 5, wheel_y), 8)
            
        else:
            # Front view truck
            cargo = [
                (iso_x - h//2, iso_y + 10),
                (iso_x + h//2, iso_y + 10),
                (iso_x + h//2, iso_y - height),
                (iso_x - h//2, iso_y - height),
            ]
            pygame.draw.polygon(screen, body_color, cargo)
            pygame.draw.polygon(screen, dark_color, cargo, 2)
            
            # Cabin
            cabin = [
                (iso_x - h//2, iso_y),
                (iso_x + h//2, iso_y),
                (iso_x + h//2, iso_y + 10),
                (iso_x - h//2, iso_y + 10),
            ]
            pygame.draw.polygon(screen, cabin_color, cabin)
            
            # Wheels
            pygame.draw.circle(screen, (30, 30, 30), (iso_x - h//2, iso_y + 7), 6)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + h//2, iso_y + 7), 6)
    
    @staticmethod
    def draw_bike(screen, iso_x, iso_y, color, direction='right', scale=1.0):
        """Draw an isometric motorcycle"""
        w = int(25 * scale)
        h = int(12 * scale)
        
        body_color = color
        
        if direction in ['right', 'left']:
            # Body
            pygame.draw.ellipse(screen, body_color,
                              (iso_x - w//2, iso_y - 12, w, 10))
            # Wheels
            pygame.draw.circle(screen, (30, 30, 30), (iso_x - w//3, iso_y), 5)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + w//3, iso_y), 5)
            # Rider
            pygame.draw.circle(screen, (255, 200, 150), (iso_x, iso_y - 18), 5)
            pygame.draw.rect(screen, (50, 50, 150), (iso_x - 3, iso_y - 14, 6, 8))
        else:
            # Front view
            pygame.draw.ellipse(screen, body_color,
                              (iso_x - h//2, iso_y - 10, h, 8))
            pygame.draw.circle(screen, (30, 30, 30), (iso_x, iso_y), 4)
            # Rider
            pygame.draw.circle(screen, (255, 200, 150), (iso_x, iso_y - 16), 5)
    
    @staticmethod
    def draw_ambulance(screen, iso_x, iso_y, direction='right', blink=False, scale=1.0):
        """Draw an isometric ambulance"""
        w = int(50 * scale)
        h = int(22 * scale)
        height = int(22 * scale)
        
        body_color = (255, 255, 255)
        dark_color = (220, 220, 220)
        
        if direction in ['right', 'left']:
            # Body
            body = [
                (iso_x - w//2, iso_y),
                (iso_x + w//2, iso_y),
                (iso_x + w//2, iso_y - height),
                (iso_x - w//2, iso_y - height),
            ]
            pygame.draw.polygon(screen, body_color, body)
            pygame.draw.polygon(screen, dark_color, body, 2)
            
            # Red stripe
            pygame.draw.rect(screen, (220, 0, 0),
                           (iso_x - w//2, iso_y - height//2 - 3, w, 6))
            
            # Red cross
            cross_x = iso_x + w//4
            cross_y = iso_y - height//2
            pygame.draw.rect(screen, (220, 0, 0), (cross_x - 8, cross_y - 2, 16, 4))
            pygame.draw.rect(screen, (220, 0, 0), (cross_x - 2, cross_y - 8, 4, 16))
            
            # Lights
            light_color = (255, 0, 0) if blink else (0, 0, 255)
            pygame.draw.circle(screen, light_color, (iso_x - w//3, iso_y - height - 5), 5)
            pygame.draw.circle(screen, (255, 0, 0) if not blink else (0, 0, 255),
                             (iso_x - w//3 + 12, iso_y - height - 5), 5)
            
            # Wheels
            pygame.draw.circle(screen, (30, 30, 30), (iso_x - w//3, iso_y), 7)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + w//3, iso_y), 7)
            
        else:
            # Front/back view
            body = [
                (iso_x - h//2, iso_y),
                (iso_x + h//2, iso_y),
                (iso_x + h//2, iso_y - height),
                (iso_x - h//2, iso_y - height),
            ]
            pygame.draw.polygon(screen, body_color, body)
            pygame.draw.polygon(screen, dark_color, body, 2)
            
            # Red stripe
            pygame.draw.rect(screen, (220, 0, 0),
                           (iso_x - h//2, iso_y - height//2 - 2, h, 4))
            
            # Lights
            light_color = (255, 0, 0) if blink else (0, 0, 255)
            pygame.draw.circle(screen, light_color, (iso_x - 5, iso_y - height - 3), 4)
            pygame.draw.circle(screen, (255, 0, 0) if not blink else (0, 0, 255),
                             (iso_x + 5, iso_y - height - 3), 4)
            
            # Wheels
            pygame.draw.circle(screen, (30, 30, 30), (iso_x - h//2, iso_y - 3), 5)
            pygame.draw.circle(screen, (30, 30, 30), (iso_x + h//2, iso_y - 3), 5)
    
    @staticmethod
    def draw_pedestrian(screen, iso_x, iso_y, color=(255, 200, 150), scale=1.0):
        """Draw an isometric pedestrian"""
        # Head
        pygame.draw.circle(screen, color, (iso_x, iso_y - 20), 5)
        # Body
        shirt_color = (50 + (iso_x * 3) % 150, 50 + (iso_y * 2) % 150, 150)
        pygame.draw.rect(screen, shirt_color, (iso_x - 4, iso_y - 15, 8, 10))
        # Legs
        pygame.draw.rect(screen, (50, 50, 100), (iso_x - 4, iso_y - 5, 3, 8))
        pygame.draw.rect(screen, (50, 50, 100), (iso_x + 1, iso_y - 5, 3, 8))
