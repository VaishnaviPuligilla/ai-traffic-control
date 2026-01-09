import pygame
import math


class CityRenderer:
    """Simple isometric city renderer for traffic simulation"""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Center of intersection
        self.cx = width // 2
        self.cy = height // 2
        
        # Road dimensions
        self.road_width = 200  # 4 lanes wide
        self.lane_width = 50   # Width per lane
        
        # Colors
        self.colors = {
            'bg': (70, 120, 70),           # Grass background
            'road': (55, 58, 65),          # Road surface
            'sidewalk': (170, 165, 155),   # Sidewalk
            'marking': (230, 230, 230),    # Road markings
            'yellow': (255, 210, 50),      # Yellow lines
            'zebra': (240, 240, 240),      # Zebra crossing
            'building': (180, 170, 200),   # Building walls
            'building_side': (140, 130, 160),
            'roof': (180, 90, 90),         # Roof
            'window': (150, 190, 220),     # Windows
            'tree': (40, 120, 40),         # Trees
            'tree_dark': (30, 90, 30),
        }
        
        # Prerender static elements
        self.static_surface = None
        self._prerender_static()
        
    def _prerender_static(self):
        """Pre-render static elements (roads, buildings, trees)"""
        self.static_surface = pygame.Surface((self.width, self.height))
        
        # Draw grass background
        self.static_surface.fill(self.colors['bg'])
        
        # Draw roads
        self._draw_roads(self.static_surface)
        
        # Draw buildings
        self._draw_buildings(self.static_surface)
        
        # Draw trees
        self._draw_trees(self.static_surface)
        
    def _draw_roads(self, surface):
        """Draw the intersection roads"""
        cx, cy = self.cx, self.cy
        rw = self.road_width
        
        # Sidewalk (drawn first, wider than road)
        sw = 15  # Sidewalk width
        pygame.draw.rect(surface, self.colors['sidewalk'],
                        (0, cy - rw//2 - sw, self.width, rw + sw*2))
        pygame.draw.rect(surface, self.colors['sidewalk'],
                        (cx - rw//2 - sw, 0, rw + sw*2, self.height))
        
        # Main roads
        # Horizontal road
        pygame.draw.rect(surface, self.colors['road'],
                        (0, cy - rw//2, self.width, rw))
        # Vertical road
        pygame.draw.rect(surface, self.colors['road'],
                        (cx - rw//2, 0, rw, self.height))
        
        # Draw lane markings
        self._draw_lane_markings(surface)
        
        # Draw zebra crossings
        self._draw_zebra_crossings(surface)
        
        # Draw direction arrows
        self._draw_arrows(surface)
        
    def _draw_lane_markings(self, surface):
        """Draw road lane markings"""
        cx, cy = self.cx, self.cy
        rw = self.road_width
        lw = self.lane_width
        
        # Yellow center line (dashed)
        for x in range(0, cx - rw//2 - 20, 40):
            pygame.draw.line(surface, self.colors['yellow'],
                           (x, cy), (x + 25, cy), 3)
        for x in range(cx + rw//2 + 20, self.width, 40):
            pygame.draw.line(surface, self.colors['yellow'],
                           (x, cy), (x + 25, cy), 3)
            
        for y in range(0, cy - rw//2 - 20, 40):
            pygame.draw.line(surface, self.colors['yellow'],
                           (cx, y), (cx, y + 25), 3)
        for y in range(cy + rw//2 + 20, self.height, 40):
            pygame.draw.line(surface, self.colors['yellow'],
                           (cx, y), (cx, y + 25), 3)
        
        # White lane dividers
        lane_offsets = [-lw, lw]  # Between lanes
        
        for offset in lane_offsets:
            # Horizontal road (skip intersection)
            for x in range(0, cx - rw//2 - 20, 30):
                pygame.draw.line(surface, self.colors['marking'],
                               (x, cy + offset), (x + 18, cy + offset), 2)
            for x in range(cx + rw//2 + 20, self.width, 30):
                pygame.draw.line(surface, self.colors['marking'],
                               (x, cy + offset), (x + 18, cy + offset), 2)
            
            # Vertical road
            for y in range(0, cy - rw//2 - 20, 30):
                pygame.draw.line(surface, self.colors['marking'],
                               (cx + offset, y), (cx + offset, y + 18), 2)
            for y in range(cy + rw//2 + 20, self.height, 30):
                pygame.draw.line(surface, self.colors['marking'],
                               (cx + offset, y), (cx + offset, y + 18), 2)
                
    def _draw_zebra_crossings(self, surface):
        """Draw zebra crossings at intersection"""
        cx, cy = self.cx, self.cy
        rw = self.road_width
        
        stripe_w = 12
        stripe_h = 40
        gap = 8
        
        # Left crossing (Lane 0)
        x = cx - rw//2 - stripe_h - 5
        for i in range(8):
            y = cy - rw//2 + 10 + i * (stripe_w + gap)
            pygame.draw.rect(surface, self.colors['zebra'],
                           (x, y, stripe_h, stripe_w))
        
        # Right crossing (Lane 2)
        x = cx + rw//2 + 5
        for i in range(8):
            y = cy - rw//2 + 10 + i * (stripe_w + gap)
            pygame.draw.rect(surface, self.colors['zebra'],
                           (x, y, stripe_h, stripe_w))
        
        # Top crossing (Lane 1)
        y = cy - rw//2 - stripe_h - 5
        for i in range(8):
            x = cx - rw//2 + 10 + i * (stripe_w + gap)
            pygame.draw.rect(surface, self.colors['zebra'],
                           (x, y, stripe_w, stripe_h))
        
        # Bottom crossing (Lane 3)
        y = cy + rw//2 + 5
        for i in range(8):
            x = cx - rw//2 + 10 + i * (stripe_w + gap)
            pygame.draw.rect(surface, self.colors['zebra'],
                           (x, y, stripe_w, stripe_h))
                           
    def _draw_arrows(self, surface):
        """Draw direction arrows on lanes"""
        cx, cy = self.cx, self.cy
        rw = self.road_width
        
        arrow_color = (180, 180, 180)
        
        # Helper to draw arrow
        def draw_arrow(x, y, direction):
            if direction == 'right':
                points = [(x, y), (x + 20, y + 10), (x, y + 20)]
            elif direction == 'left':
                points = [(x + 20, y), (x, y + 10), (x + 20, y + 20)]
            elif direction == 'up':
                points = [(x, y + 20), (x + 10, y), (x + 20, y + 20)]
            else:  # down
                points = [(x, y), (x + 10, y + 20), (x + 20, y)]
            pygame.draw.polygon(surface, arrow_color, points)
        
        # Arrows for each lane approach
        # Left approach (going right)
        draw_arrow(100, cy - 75, 'right')
        draw_arrow(100, cy + 55, 'right')
        
        # Right approach (going left)
        draw_arrow(self.width - 130, cy - 75, 'left')
        draw_arrow(self.width - 130, cy + 55, 'left')
        
        # Top approach (going down)
        draw_arrow(cx - 75, 100, 'down')
        draw_arrow(cx + 55, 100, 'down')
        
        # Bottom approach (going up)
        draw_arrow(cx - 75, self.height - 130, 'up')
        draw_arrow(cx + 55, self.height - 130, 'up')
        
    def _draw_buildings(self, surface):
        """Draw buildings in corners"""
        buildings = [
            # (x, y, width, height, floors)
            (30, 30, 120, 100, 4),      # Top-left
            (180, 50, 80, 80, 3),
            
            (self.width - 150, 30, 120, 100, 5),  # Top-right
            (self.width - 230, 60, 70, 70, 2),
            
            (30, self.height - 130, 120, 100, 4),  # Bottom-left
            (180, self.height - 110, 80, 80, 3),
            
            (self.width - 150, self.height - 130, 120, 100, 4),  # Bottom-right
            (self.width - 230, self.height - 100, 70, 70, 2),
        ]
        
        for bx, by, bw, bh, floors in buildings:
            self._draw_building(surface, bx, by, bw, bh, floors)
            
    def _draw_building(self, surface, x, y, w, h, floors):
        """Draw a simple 2.5D building"""
        # Shadow
        pygame.draw.rect(surface, (40, 40, 40), (x + 5, y + 5, w, h))
        
        # Main wall
        pygame.draw.rect(surface, self.colors['building'], (x, y, w, h))
        
        # Side (3D effect)
        side_w = 15
        side_points = [
            (x + w, y),
            (x + w + side_w, y - 10),
            (x + w + side_w, y + h - 10),
            (x + w, y + h)
        ]
        pygame.draw.polygon(surface, self.colors['building_side'], side_points)
        
        # Roof
        roof_points = [
            (x, y),
            (x + side_w, y - 10),
            (x + w + side_w, y - 10),
            (x + w, y)
        ]
        pygame.draw.polygon(surface, self.colors['roof'], roof_points)
        
        # Windows
        window_w = 15
        window_h = 20
        window_gap = 8
        
        cols = max(1, (w - 20) // (window_w + window_gap))
        rows = min(floors, (h - 20) // (window_h + window_gap))
        
        start_x = x + (w - cols * (window_w + window_gap)) // 2
        start_y = y + 15
        
        for row in range(rows):
            for col in range(cols):
                wx = start_x + col * (window_w + window_gap)
                wy = start_y + row * (window_h + window_gap)
                pygame.draw.rect(surface, self.colors['window'], (wx, wy, window_w, window_h))
                
    def _draw_trees(self, surface):
        """Draw decorative trees"""
        tree_positions = [
            (20, 160), (160, 170), (200, 30),
            (self.width - 60, 170), (self.width - 200, 160),
            (20, self.height - 170), (160, self.height - 160),
            (self.width - 60, self.height - 170), (self.width - 200, self.height - 160),
        ]
        
        for tx, ty in tree_positions:
            self._draw_tree(surface, tx, ty)
            
    def _draw_tree(self, surface, x, y):
        """Draw a simple tree"""
        # Trunk
        pygame.draw.rect(surface, (101, 67, 33), (x - 5, y + 15, 10, 20))
        
        # Foliage (circles)
        pygame.draw.circle(surface, self.colors['tree_dark'], (x, y + 10), 20)
        pygame.draw.circle(surface, self.colors['tree'], (x, y), 22)
        pygame.draw.circle(surface, self.colors['tree'], (x - 10, y + 5), 15)
        pygame.draw.circle(surface, self.colors['tree'], (x + 10, y + 5), 15)
        
    def draw_signals(self, surface, states):
        """Draw traffic signals"""
        cx, cy = self.cx, self.cy
        rw = self.road_width
        
        signal_positions = {
            0: (cx - rw//2 - 30, cy - 20),  # Left approach
            1: (cx - 20, cy - rw//2 - 30),  # Top approach  
            2: (cx + rw//2 + 10, cy - 20),  # Right approach
            3: (cx - 20, cy + rw//2 + 10),  # Bottom approach
        }
        
        for lane, (sx, sy) in signal_positions.items():
            state = states.get(lane, 'red')
            
            # Signal box
            pygame.draw.rect(surface, (30, 30, 30), (sx, sy, 20, 45), border_radius=4)
            
            # Lights
            colors = {
                'red': ((255, 60, 60), (60, 30, 30), (60, 60, 30)),
                'yellow': ((60, 30, 30), (255, 220, 60), (60, 60, 30)),
                'green': ((60, 30, 30), (60, 60, 30), (60, 255, 60)),
            }
            r, y, g = colors.get(state, colors['red'])
            
            pygame.draw.circle(surface, r, (sx + 10, sy + 8), 5)
            pygame.draw.circle(surface, y, (sx + 10, sy + 22), 5)
            pygame.draw.circle(surface, g, (sx + 10, sy + 36), 5)
            
    def draw_vehicle(self, surface, vehicle_data):
        """Draw a vehicle"""
        x = vehicle_data['x']
        y = vehicle_data['y']
        v_type = vehicle_data['type']
        direction = vehicle_data.get('direction', 0)
        
        if v_type == 'car':
            self._draw_car(surface, x, y, vehicle_data.get('color', (65, 105, 225)), direction)
        elif v_type == 'truck':
            self._draw_truck(surface, x, y, vehicle_data.get('color', (139, 90, 43)), direction)
        elif v_type == 'bike':
            self._draw_bike(surface, x, y, vehicle_data.get('color', (255, 140, 0)), direction)
        elif v_type == 'ambulance':
            self._draw_ambulance(surface, x, y, direction)
            
    def _draw_car(self, surface, x, y, color, direction):
        """Draw a car"""
        if direction in (0, 2):  # Horizontal
            w, h = 40, 22
        else:  # Vertical
            w, h = 22, 40
            
        # Shadow
        pygame.draw.ellipse(surface, (30, 30, 30, 100), (x - w//2 + 3, y - h//2 + 3, w, h))
        
        # Body
        pygame.draw.rect(surface, color, (x - w//2, y - h//2, w, h), border_radius=5)
        
        # Roof/cabin
        if direction in (0, 2):
            pygame.draw.rect(surface, tuple(max(0, c - 30) for c in color), 
                           (x - 8, y - 6, 16, 12), border_radius=3)
        else:
            pygame.draw.rect(surface, tuple(max(0, c - 30) for c in color),
                           (x - 6, y - 8, 12, 16), border_radius=3)
            
        # Windshield
        pygame.draw.rect(surface, (180, 200, 220), (x - 5, y - 4, 10, 8), border_radius=2)
        
    def _draw_truck(self, surface, x, y, color, direction):
        """Draw a truck"""
        if direction in (0, 2):  # Horizontal
            w, h = 55, 24
            cab_w, cab_h = 18, 20
        else:  # Vertical
            w, h = 24, 55
            cab_w, cab_h = 20, 18
            
        # Shadow
        pygame.draw.ellipse(surface, (30, 30, 30, 100), (x - w//2 + 3, y - h//2 + 3, w, h))
        
        # Cargo area
        pygame.draw.rect(surface, color, (x - w//2, y - h//2, w, h), border_radius=3)
        
        # Cabin
        if direction in (0, 2):
            cabin_x = x + w//2 - cab_w if direction == 0 else x - w//2
            pygame.draw.rect(surface, tuple(max(0, c - 40) for c in color),
                           (cabin_x, y - cab_h//2, cab_w, cab_h), border_radius=2)
        else:
            cabin_y = y + h//2 - cab_h if direction == 3 else y - h//2
            pygame.draw.rect(surface, tuple(max(0, c - 40) for c in color),
                           (x - cab_w//2, cabin_y, cab_w, cab_h), border_radius=2)
            
    def _draw_bike(self, surface, x, y, color, direction):
        """Draw a motorcycle/bike"""
        if direction in (0, 2):
            w, h = 25, 12
        else:
            w, h = 12, 25
            
        # Body
        pygame.draw.ellipse(surface, color, (x - w//2, y - h//2, w, h))
        
        # Rider
        pygame.draw.circle(surface, (60, 60, 60), (x, y), 5)
        
    def _draw_ambulance(self, surface, x, y, direction):
        """Draw an ambulance with flashing lights"""
        import time
        flash = int(time.time() * 4) % 2
        
        if direction in (0, 2):
            w, h = 50, 24
        else:
            w, h = 24, 50
            
        # Body (white)
        pygame.draw.rect(surface, (250, 250, 250), (x - w//2, y - h//2, w, h), border_radius=4)
        
        # Red stripe
        if direction in (0, 2):
            pygame.draw.rect(surface, (220, 50, 50), (x - w//2, y - 2, w, 4))
        else:
            pygame.draw.rect(surface, (220, 50, 50), (x - 2, y - h//2, 4, h))
            
        # Red cross
        pygame.draw.rect(surface, (220, 50, 50), (x - 5, y - 2, 10, 4))
        pygame.draw.rect(surface, (220, 50, 50), (x - 2, y - 5, 4, 10))
        
        # Flashing lights
        light_color = (255, 0, 0) if flash else (0, 0, 255)
        pygame.draw.circle(surface, light_color, (x - w//4, y - h//2), 4)
        pygame.draw.circle(surface, (255, 0, 0) if not flash else (0, 0, 255), 
                          (x + w//4, y - h//2), 4)
                          
    def draw_pedestrian(self, surface, x, y, waiting=True):
        """Draw a pedestrian"""
        color = (200, 150, 100) if waiting else (100, 150, 200)
        
        # Body
        pygame.draw.circle(surface, color, (x, y - 8), 5)  # Head
        pygame.draw.line(surface, (60, 60, 60), (x, y - 3), (x, y + 8), 3)  # Body
        pygame.draw.line(surface, (60, 60, 60), (x, y + 8), (x - 4, y + 15), 2)  # Left leg
        pygame.draw.line(surface, (60, 60, 60), (x, y + 8), (x + 4, y + 15), 2)  # Right leg
        
    def draw_scene(self, signal_states, vehicles, pedestrians=None):
        """Draw complete scene"""
        # Start with pre-rendered static elements
        surface = self.static_surface.copy()
        
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
