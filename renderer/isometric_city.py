import pygame
import math
import time


class IsometricCity:
    """
    Renders an isometric city intersection view
    Matching the reference images with green dividers, buildings, trees
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Isometric projection angle
        self.iso_angle = 30  # degrees
        self.scale = 1.0
        
        # Center of the view
        self.center_x = width // 2
        self.center_y = height // 2 + 50
        
        # Road dimensions
        self.road_width = 180
        self.lane_width = 45
        self.divider_width = 12
        
        # Colors matching reference images
        self.colors = {
            'sky': (180, 210, 240),
            'grass': (90, 160, 90),
            'grass_dark': (70, 140, 70),
            'road': (85, 85, 90),
            'road_dark': (70, 70, 75),
            'sidewalk': (190, 185, 175),
            'sidewalk_edge': (160, 155, 145),
            'divider': (60, 140, 60),  # Green divider
            'divider_dark': (45, 110, 45),
            'marking_white': (255, 255, 255),
            'marking_yellow': (255, 220, 50),
            'zebra': (250, 250, 250),
            'building_wall': (220, 215, 210),
            'building_side': (180, 175, 170),
            'building_roof': (160, 155, 150),
            'building_window': (140, 180, 210),
            'building_window_dark': (100, 140, 170),
            'tree_trunk': (90, 65, 40),
            'tree_leaves': (50, 130, 50),
            'tree_leaves_light': (70, 160, 70),
            'signal_post': (60, 60, 60),
        }
        
        # Pre-render static background
        self.background = None
        self._render_background()
        
    def _iso_transform(self, x, y, z=0):
        """Transform 3D coordinates to isometric 2D screen coordinates"""
        # Isometric projection
        iso_x = (x - y) * math.cos(math.radians(30))
        iso_y = (x + y) * math.sin(math.radians(30)) - z
        
        # Center on screen
        screen_x = self.center_x + iso_x
        screen_y = self.center_y + iso_y
        
        return int(screen_x), int(screen_y)
    
    def _render_background(self):
        """Pre-render static elements"""
        self.background = pygame.Surface((self.width, self.height))
        self.background.fill(self.colors['grass'])
        
        # Draw in order: grass, roads, dividers, sidewalks, buildings, trees
        self._draw_grass_areas(self.background)
        self._draw_roads(self.background)
        self._draw_dividers(self.background)
        self._draw_zebra_crossings(self.background)
        self._draw_buildings(self.background)
        self._draw_trees(self.background)
        
    def _draw_grass_areas(self, surface):
        """Draw grass background with texture"""
        # Fill with grass
        surface.fill(self.colors['grass'])
        
        # Add grass texture variation
        for i in range(0, self.width, 30):
            for j in range(0, self.height, 30):
                if (i // 30 + j // 30) % 2 == 0:
                    pygame.draw.rect(surface, self.colors['grass_dark'], (i, j, 15, 15))
                    
    def _draw_roads(self, surface):
        """Draw the intersection roads"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        
        # Horizontal road (full width)
        pygame.draw.rect(surface, self.colors['road'], 
                        (0, cy - rw//2, self.width, rw))
        
        # Vertical road (full height)
        pygame.draw.rect(surface, self.colors['road'],
                        (cx - rw//2, 0, rw, self.height))
        
        # Intersection center (darker)
        pygame.draw.rect(surface, self.colors['road_dark'],
                        (cx - rw//2, cy - rw//2, rw, rw))
        
        # Lane markings
        self._draw_lane_markings(surface)
        
    def _draw_lane_markings(self, surface):
        """Draw road lane markings"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        
        # Yellow center lines (dashed)
        dash_len = 30
        gap_len = 20
        
        # Horizontal road - left section
        for x in range(0, cx - rw//2 - 20, dash_len + gap_len):
            pygame.draw.line(surface, self.colors['marking_yellow'],
                           (x, cy), (min(x + dash_len, cx - rw//2 - 20), cy), 4)
        
        # Horizontal road - right section
        for x in range(cx + rw//2 + 20, self.width, dash_len + gap_len):
            pygame.draw.line(surface, self.colors['marking_yellow'],
                           (x, cy), (min(x + dash_len, self.width), cy), 4)
        
        # Vertical road - top section
        for y in range(0, cy - rw//2 - 20, dash_len + gap_len):
            pygame.draw.line(surface, self.colors['marking_yellow'],
                           (cx, y), (cx, min(y + dash_len, cy - rw//2 - 20)), 4)
        
        # Vertical road - bottom section
        for y in range(cy + rw//2 + 20, self.height, dash_len + gap_len):
            pygame.draw.line(surface, self.colors['marking_yellow'],
                           (cx, y), (cx, min(y + dash_len, self.height)), 4)
        
        # White lane dividers
        lane_offset = self.lane_width
        
        for offset in [-lane_offset, lane_offset]:
            # Horizontal - left
            for x in range(0, cx - rw//2 - 30, 25):
                pygame.draw.line(surface, self.colors['marking_white'],
                               (x, cy + offset), (x + 15, cy + offset), 2)
            # Horizontal - right
            for x in range(cx + rw//2 + 30, self.width, 25):
                pygame.draw.line(surface, self.colors['marking_white'],
                               (x, cy + offset), (x + 15, cy + offset), 2)
            # Vertical - top
            for y in range(0, cy - rw//2 - 30, 25):
                pygame.draw.line(surface, self.colors['marking_white'],
                               (cx + offset, y), (cx + offset, y + 15), 2)
            # Vertical - bottom
            for y in range(cy + rw//2 + 30, self.height, 25):
                pygame.draw.line(surface, self.colors['marking_white'],
                               (cx + offset, y), (cx + offset, y + 15), 2)
                               
    def _draw_dividers(self, surface):
        """Draw green median dividers like in reference images"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        dw = self.divider_width
        
        # Left divider (horizontal road, left of intersection)
        div_left = pygame.Rect(20, cy - dw//2, cx - rw//2 - 40, dw)
        pygame.draw.rect(surface, self.colors['divider'], div_left, border_radius=4)
        pygame.draw.rect(surface, self.colors['divider_dark'], div_left, 2, border_radius=4)
        
        # Right divider
        div_right = pygame.Rect(cx + rw//2 + 20, cy - dw//2, self.width - cx - rw//2 - 40, dw)
        pygame.draw.rect(surface, self.colors['divider'], div_right, border_radius=4)
        pygame.draw.rect(surface, self.colors['divider_dark'], div_right, 2, border_radius=4)
        
        # Top divider (vertical road)
        div_top = pygame.Rect(cx - dw//2, 20, dw, cy - rw//2 - 40)
        pygame.draw.rect(surface, self.colors['divider'], div_top, border_radius=4)
        pygame.draw.rect(surface, self.colors['divider_dark'], div_top, 2, border_radius=4)
        
        # Bottom divider
        div_bottom = pygame.Rect(cx - dw//2, cy + rw//2 + 20, dw, self.height - cy - rw//2 - 40)
        pygame.draw.rect(surface, self.colors['divider'], div_bottom, border_radius=4)
        pygame.draw.rect(surface, self.colors['divider_dark'], div_bottom, 2, border_radius=4)
        
        # Small bushes on dividers
        for x in range(40, cx - rw//2 - 40, 50):
            self._draw_small_bush(surface, x, cy)
        for x in range(cx + rw//2 + 40, self.width - 40, 50):
            self._draw_small_bush(surface, x, cy)
        for y in range(40, cy - rw//2 - 40, 50):
            self._draw_small_bush(surface, cx, y)
        for y in range(cy + rw//2 + 40, self.height - 40, 50):
            self._draw_small_bush(surface, cx, y)
            
    def _draw_small_bush(self, surface, x, y):
        """Draw small bush/shrub on divider"""
        pygame.draw.circle(surface, self.colors['tree_leaves'], (x, y), 5)
        pygame.draw.circle(surface, self.colors['tree_leaves_light'], (x-2, y-2), 3)
        
    def _draw_zebra_crossings(self, surface):
        """Draw zebra crossings at intersection"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        
        stripe_w = 10
        stripe_gap = 8
        stripe_len = 45
        
        # Left crossing (west approach)
        x_start = cx - rw//2 - stripe_len - 5
        for i in range(10):
            y = cy - rw//2 + 15 + i * (stripe_w + stripe_gap)
            if y < cy + rw//2 - 15:
                pygame.draw.rect(surface, self.colors['zebra'],
                               (x_start, y, stripe_len, stripe_w))
        
        # Right crossing (east approach)
        x_start = cx + rw//2 + 5
        for i in range(10):
            y = cy - rw//2 + 15 + i * (stripe_w + stripe_gap)
            if y < cy + rw//2 - 15:
                pygame.draw.rect(surface, self.colors['zebra'],
                               (x_start, y, stripe_len, stripe_w))
        
        # Top crossing (north approach)
        y_start = cy - rw//2 - stripe_len - 5
        for i in range(10):
            x = cx - rw//2 + 15 + i * (stripe_w + stripe_gap)
            if x < cx + rw//2 - 15:
                pygame.draw.rect(surface, self.colors['zebra'],
                               (x, y_start, stripe_w, stripe_len))
        
        # Bottom crossing (south approach)
        y_start = cy + rw//2 + 5
        for i in range(10):
            x = cx - rw//2 + 15 + i * (stripe_w + stripe_gap)
            if x < cx + rw//2 - 15:
                pygame.draw.rect(surface, self.colors['zebra'],
                               (x, y_start, stripe_w, stripe_len))
                               
    def _draw_buildings(self, surface):
        """Draw isometric-style buildings on corners"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        margin = 70
        
        # Building configurations: (x, y, width, depth, height, floors)
        buildings = [
            # Top-left corner
            (50, 50, 140, 100, 180, 6),
            (200, 80, 80, 60, 100, 3),
            
            # Top-right corner
            (self.width - 190, 50, 140, 100, 200, 7),
            (self.width - 280, 90, 70, 60, 80, 2),
            
            # Bottom-left corner
            (50, self.height - 170, 140, 100, 120, 4),
            (200, self.height - 130, 80, 60, 90, 3),
            
            # Bottom-right corner
            (self.width - 190, self.height - 170, 140, 100, 150, 5),
            (self.width - 280, self.height - 130, 70, 60, 70, 2),
        ]
        
        for bx, by, bw, bd, bh, floors in buildings:
            self._draw_building(surface, bx, by, bw, bd, bh, floors)
            
    def _draw_building(self, surface, x, y, width, depth, height, floors):
        """Draw a 3D isometric building"""
        # Shadow
        shadow_offset = 8
        pygame.draw.rect(surface, (50, 50, 50), 
                        (x + shadow_offset, y + shadow_offset, width, depth))
        
        # Front wall
        pygame.draw.rect(surface, self.colors['building_wall'], (x, y, width, depth))
        
        # Right side (3D effect)
        side_w = 20
        side_points = [
            (x + width, y),
            (x + width + side_w, y - 15),
            (x + width + side_w, y + depth - 15),
            (x + width, y + depth)
        ]
        pygame.draw.polygon(surface, self.colors['building_side'], side_points)
        
        # Roof
        roof_points = [
            (x, y),
            (x + side_w, y - 15),
            (x + width + side_w, y - 15),
            (x + width, y)
        ]
        pygame.draw.polygon(surface, self.colors['building_roof'], roof_points)
        
        # Windows
        window_w = 18
        window_h = 22
        window_gap_x = 8
        window_gap_y = 12
        
        cols = max(1, (width - 20) // (window_w + window_gap_x))
        rows = min(floors, (depth - 20) // (window_h + window_gap_y))
        
        start_x = x + (width - cols * (window_w + window_gap_x)) // 2
        start_y = y + 12
        
        for row in range(rows):
            for col in range(cols):
                wx = start_x + col * (window_w + window_gap_x)
                wy = start_y + row * (window_h + window_gap_y)
                
                # Window with reflection effect
                pygame.draw.rect(surface, self.colors['building_window'], 
                               (wx, wy, window_w, window_h))
                pygame.draw.rect(surface, self.colors['building_window_dark'],
                               (wx, wy, window_w // 2, window_h // 2))
                               
    def _draw_trees(self, surface):
        """Draw trees along the roads"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        
        # Tree positions along roads
        tree_positions = []
        
        # Top-left area
        for x in range(80, cx - rw//2 - 60, 60):
            tree_positions.append((x, cy - rw//2 - 50))
        for y in range(80, cy - rw//2 - 60, 60):
            tree_positions.append((cx - rw//2 - 50, y))
            
        # Top-right area
        for x in range(cx + rw//2 + 60, self.width - 80, 60):
            tree_positions.append((x, cy - rw//2 - 50))
        for y in range(80, cy - rw//2 - 60, 60):
            tree_positions.append((cx + rw//2 + 50, y))
            
        # Bottom-left area
        for x in range(80, cx - rw//2 - 60, 60):
            tree_positions.append((x, cy + rw//2 + 50))
        for y in range(cy + rw//2 + 60, self.height - 80, 60):
            tree_positions.append((cx - rw//2 - 50, y))
            
        # Bottom-right area
        for x in range(cx + rw//2 + 60, self.width - 80, 60):
            tree_positions.append((x, cy + rw//2 + 50))
        for y in range(cy + rw//2 + 60, self.height - 80, 60):
            tree_positions.append((cx + rw//2 + 50, y))
        
        for tx, ty in tree_positions:
            self._draw_tree(surface, tx, ty)
            
    def _draw_tree(self, surface, x, y):
        """Draw an isometric tree"""
        # Trunk
        pygame.draw.rect(surface, self.colors['tree_trunk'], (x - 4, y + 5, 8, 18))
        
        # Foliage (conical shape like in reference)
        points = [
            (x, y - 25),      # Top
            (x - 18, y + 8),  # Bottom left
            (x + 18, y + 8),  # Bottom right
        ]
        pygame.draw.polygon(surface, self.colors['tree_leaves'], points)
        
        # Lighter highlight
        highlight_points = [
            (x, y - 25),
            (x - 8, y - 5),
            (x + 2, y - 5),
        ]
        pygame.draw.polygon(surface, self.colors['tree_leaves_light'], highlight_points)
        
    def draw_signals(self, surface, states):
        """Draw traffic signals"""
        cx, cy = self.center_x, self.center_y
        rw = self.road_width
        
        # Signal positions (at corners of intersection)
        signal_positions = {
            0: (cx - rw//2 - 25, cy + rw//2 - 20),   # West approach
            1: (cx - rw//2 + 10, cy - rw//2 - 35),   # North approach
            2: (cx + rw//2 + 5, cy - rw//2 + 10),    # East approach
            3: (cx + rw//2 - 20, cy + rw//2 + 5),    # South approach
        }
        
        for lane, (sx, sy) in signal_positions.items():
            state = states.get(lane, 'red')
            self._draw_signal(surface, sx, sy, state)
            
    def _draw_signal(self, surface, x, y, state):
        """Draw a traffic signal"""
        # Post
        pygame.draw.rect(surface, self.colors['signal_post'], (x + 8, y + 30, 6, 40))
        
        # Signal box
        pygame.draw.rect(surface, (40, 40, 45), (x, y, 22, 50), border_radius=3)
        pygame.draw.rect(surface, (60, 60, 65), (x, y, 22, 50), 2, border_radius=3)
        
        # Lights
        light_colors = {
            'red': [(255, 50, 50), (60, 30, 30), (60, 50, 30)],
            'yellow': [(60, 30, 30), (255, 220, 50), (60, 50, 30)],
            'green': [(60, 30, 30), (60, 50, 30), (50, 255, 50)],
        }
        
        colors = light_colors.get(state, light_colors['red'])
        
        pygame.draw.circle(surface, colors[0], (x + 11, y + 10), 6)
        pygame.draw.circle(surface, colors[1], (x + 11, y + 25), 6)
        pygame.draw.circle(surface, colors[2], (x + 11, y + 40), 6)
        
    def draw_vehicle(self, surface, v_data):
        """Draw a realistic vehicle"""
        x = v_data['x']
        y = v_data['y']
        v_type = v_data['type']
        color = v_data.get('color', (100, 100, 200))
        direction = v_data.get('direction', 0)
        
        if v_type == 'car':
            self._draw_car(surface, x, y, color, direction)
        elif v_type == 'truck':
            self._draw_truck(surface, x, y, color, direction)
        elif v_type == 'bike':
            self._draw_bike(surface, x, y, color, direction)
        elif v_type == 'ambulance':
            self._draw_ambulance(surface, x, y, direction)
            
    def _draw_car(self, surface, x, y, color, direction):
        """Draw a realistic car (isometric style)"""
        # Determine orientation
        horizontal = direction in (0, 2)
        
        if horizontal:
            # Car body dimensions for horizontal
            body_w, body_h = 45, 24
            cabin_w, cabin_h = 22, 18
            cabin_offset = 10
        else:
            # Vertical orientation
            body_w, body_h = 24, 45
            cabin_w, cabin_h = 18, 22
            cabin_offset = 10
        
        # Shadow
        shadow_color = (40, 40, 40)
        pygame.draw.ellipse(surface, shadow_color, 
                           (x - body_w//2 + 4, y - body_h//2 + 4, body_w, body_h))
        
        # Car body (main shape)
        body_rect = pygame.Rect(x - body_w//2, y - body_h//2, body_w, body_h)
        pygame.draw.rect(surface, color, body_rect, border_radius=6)
        
        # Darker shade for 3D effect
        dark_color = tuple(max(0, c - 40) for c in color)
        if horizontal:
            pygame.draw.rect(surface, dark_color, 
                           (x - body_w//2, y, body_w, body_h//2), 
                           border_bottom_left_radius=6, border_bottom_right_radius=6)
        else:
            pygame.draw.rect(surface, dark_color,
                           (x, y - body_h//2, body_w//2, body_h),
                           border_top_right_radius=6, border_bottom_right_radius=6)
        
        # Cabin/roof
        cabin_color = tuple(max(0, c - 25) for c in color)
        if horizontal:
            pygame.draw.rect(surface, cabin_color,
                           (x - cabin_w//2, y - cabin_h//2, cabin_w, cabin_h),
                           border_radius=4)
        else:
            pygame.draw.rect(surface, cabin_color,
                           (x - cabin_w//2, y - cabin_h//2, cabin_w, cabin_h),
                           border_radius=4)
        
        # Windshield
        glass_color = (180, 200, 220)
        if horizontal:
            if direction == 0:  # Going right
                pygame.draw.rect(surface, glass_color, 
                               (x + body_w//2 - 12, y - 6, 8, 12), border_radius=2)
            else:  # Going left
                pygame.draw.rect(surface, glass_color,
                               (x - body_w//2 + 4, y - 6, 8, 12), border_radius=2)
        else:
            if direction == 1:  # Going down
                pygame.draw.rect(surface, glass_color,
                               (x - 6, y - body_h//2 + 4, 12, 8), border_radius=2)
            else:  # Going up
                pygame.draw.rect(surface, glass_color,
                               (x - 6, y + body_h//2 - 12, 12, 8), border_radius=2)
        
        # Wheels (small dark circles)
        wheel_color = (30, 30, 30)
        if horizontal:
            pygame.draw.circle(surface, wheel_color, (x - body_w//3, y + body_h//2 - 2), 4)
            pygame.draw.circle(surface, wheel_color, (x + body_w//3, y + body_h//2 - 2), 4)
        else:
            pygame.draw.circle(surface, wheel_color, (x + body_w//2 - 2, y - body_h//3), 4)
            pygame.draw.circle(surface, wheel_color, (x + body_w//2 - 2, y + body_h//3), 4)
            
    def _draw_truck(self, surface, x, y, color, direction):
        """Draw a realistic truck/van"""
        horizontal = direction in (0, 2)
        
        if horizontal:
            body_w, body_h = 60, 26
            cab_w = 18
        else:
            body_w, body_h = 26, 60
            cab_w = 18
        
        # Shadow
        pygame.draw.ellipse(surface, (40, 40, 40),
                           (x - body_w//2 + 4, y - body_h//2 + 4, body_w, body_h))
        
        # Cargo body
        pygame.draw.rect(surface, color,
                        (x - body_w//2, y - body_h//2, body_w, body_h),
                        border_radius=4)
        
        # Darker bottom
        dark_color = tuple(max(0, c - 50) for c in color)
        if horizontal:
            pygame.draw.rect(surface, dark_color,
                           (x - body_w//2, y + 2, body_w, body_h//2 - 2),
                           border_bottom_left_radius=4, border_bottom_right_radius=4)
        
        # Cabin (front)
        cab_color = tuple(min(255, c + 20) for c in color)
        if horizontal:
            if direction == 0:
                pygame.draw.rect(surface, cab_color,
                               (x + body_w//2 - cab_w, y - body_h//2, cab_w, body_h),
                               border_top_right_radius=5, border_bottom_right_radius=5)
            else:
                pygame.draw.rect(surface, cab_color,
                               (x - body_w//2, y - body_h//2, cab_w, body_h),
                               border_top_left_radius=5, border_bottom_left_radius=5)
        else:
            if direction == 1:
                pygame.draw.rect(surface, cab_color,
                               (x - body_w//2, y - body_h//2, body_w, cab_w),
                               border_top_left_radius=5, border_top_right_radius=5)
            else:
                pygame.draw.rect(surface, cab_color,
                               (x - body_w//2, y + body_h//2 - cab_w, body_w, cab_w),
                               border_bottom_left_radius=5, border_bottom_right_radius=5)
        
        # Windshield
        glass_color = (170, 190, 210)
        if horizontal:
            wx = x + body_w//2 - 14 if direction == 0 else x - body_w//2 + 4
            pygame.draw.rect(surface, glass_color, (wx, y - 8, 10, 16), border_radius=2)
        else:
            wy = y - body_h//2 + 4 if direction == 1 else y + body_h//2 - 14
            pygame.draw.rect(surface, glass_color, (x - 8, wy, 16, 10), border_radius=2)
            
    def _draw_bike(self, surface, x, y, color, direction):
        """Draw a motorcycle"""
        horizontal = direction in (0, 2)
        
        if horizontal:
            w, h = 30, 14
        else:
            w, h = 14, 30
        
        # Shadow
        pygame.draw.ellipse(surface, (40, 40, 40), (x - w//2 + 2, y - h//2 + 2, w, h))
        
        # Body
        pygame.draw.ellipse(surface, color, (x - w//2, y - h//2, w, h))
        
        # Rider (small circle)
        pygame.draw.circle(surface, (60, 60, 70), (x, y - 3), 6)
        pygame.draw.circle(surface, (200, 170, 140), (x, y - 8), 4)  # Head
        
    def _draw_ambulance(self, surface, x, y, direction):
        """Draw an ambulance with flashing lights"""
        horizontal = direction in (0, 2)
        flash = int(time.time() * 5) % 2
        
        if horizontal:
            body_w, body_h = 55, 26
        else:
            body_w, body_h = 26, 55
        
        # Shadow
        pygame.draw.ellipse(surface, (40, 40, 40),
                           (x - body_w//2 + 4, y - body_h//2 + 4, body_w, body_h))
        
        # White body
        pygame.draw.rect(surface, (250, 250, 250),
                        (x - body_w//2, y - body_h//2, body_w, body_h),
                        border_radius=5)
        
        # Red stripe
        if horizontal:
            pygame.draw.rect(surface, (220, 50, 50),
                           (x - body_w//2, y - 2, body_w, 4))
        else:
            pygame.draw.rect(surface, (220, 50, 50),
                           (x - 2, y - body_h//2, 4, body_h))
        
        # Red cross
        pygame.draw.rect(surface, (220, 50, 50), (x - 6, y - 2, 12, 4))
        pygame.draw.rect(surface, (220, 50, 50), (x - 2, y - 6, 4, 12))
        
        # Flashing lights
        light1 = (255, 50, 50) if flash else (100, 100, 255)
        light2 = (100, 100, 255) if flash else (255, 50, 50)
        
        if horizontal:
            pygame.draw.circle(surface, light1, (x - body_w//3, y - body_h//2 - 2), 4)
            pygame.draw.circle(surface, light2, (x + body_w//3, y - body_h//2 - 2), 4)
        else:
            pygame.draw.circle(surface, light1, (x - body_w//2 - 2, y - body_h//3), 4)
            pygame.draw.circle(surface, light2, (x - body_w//2 - 2, y + body_h//3), 4)
            
    def draw_pedestrian(self, surface, x, y, waiting=True):
        """Draw a pedestrian"""
        # Body color
        shirt_colors = [(220, 50, 50), (50, 100, 220), (250, 200, 50), (50, 180, 50), (200, 100, 180)]
        shirt = shirt_colors[hash((x, y)) % len(shirt_colors)]
        
        # Shadow
        pygame.draw.ellipse(surface, (50, 50, 50), (x - 5, y + 8, 10, 6))
        
        # Body
        pygame.draw.rect(surface, shirt, (x - 4, y - 5, 8, 12), border_radius=2)
        
        # Head
        skin = (220, 180, 150)
        pygame.draw.circle(surface, skin, (x, y - 10), 5)
        
        # Legs
        pygame.draw.line(surface, (50, 50, 80), (x - 2, y + 7), (x - 3, y + 14), 2)
        pygame.draw.line(surface, (50, 50, 80), (x + 2, y + 7), (x + 3, y + 14), 2)
        
    def draw_scene(self, signal_states, vehicles, pedestrians=None):
        """Draw complete scene"""
        # Start with pre-rendered background
        surface = self.background.copy()
        
        # Draw signals
        self.draw_signals(surface, signal_states)
        
        # Draw vehicles (sorted by y for depth)
        sorted_vehicles = sorted(vehicles, key=lambda v: v.get('y', 0))
        for v in sorted_vehicles:
            self.draw_vehicle(surface, v)
        
        # Draw pedestrians
        if pedestrians:
            for ped in pedestrians:
                self.draw_pedestrian(surface, ped['x'], ped['y'], ped.get('waiting', True))
        
        return surface
