import pygame
import math
import time
import random


class Isometric3DCity:
    """
    True isometric 3D city view matching the reference image
    with proper perspective, 3D buildings, vehicles, and emergency services
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Isometric angles (30 degree projection)
        self.angle = math.radians(30)
        self.cos_a = math.cos(self.angle)
        self.sin_a = math.sin(self.angle)
        
        # Scale for isometric projection
        self.scale = 1.2
        
        # Origin point (where roads meet) - shifted for better view
        self.origin_x = width // 2
        self.origin_y = height // 2 + 100
        
        # Road dimensions
        self.road_width = 160
        self.lane_width = 40
        
        # Pre-render static elements
        self.static_bg = None
        self._init_static_background()
        
        # Emergency stations positions (in world coords)
        self.ambulance_stations = [
            {'x': -250, 'y': -250, 'name': 'Hospital North'},
            {'x': 300, 'y': 250, 'name': 'Hospital South'},
        ]
        self.police_stations = [
            {'x': 300, 'y': -250, 'name': 'Police HQ'},
            {'x': -250, 'y': 250, 'name': 'Police Station'},
        ]
        
    def world_to_screen(self, wx, wy, wz=0):
        """Convert world 3D coordinates to screen 2D coordinates (isometric projection)"""
        # Isometric projection formula
        sx = (wx - wy) * self.cos_a * self.scale
        sy = (wx + wy) * self.sin_a * self.scale - wz * self.scale
        
        # Translate to screen center
        screen_x = self.origin_x + sx
        screen_y = self.origin_y + sy
        
        return int(screen_x), int(screen_y)
    
    def _init_static_background(self):
        """Pre-render the static background"""
        self.static_bg = pygame.Surface((self.width, self.height))
        self.static_bg.fill((100, 160, 100))  # Grass base
        
        # Draw grass with texture
        self._draw_grass(self.static_bg)
        
        # Draw roads
        self._draw_roads(self.static_bg)
        
        # Draw buildings
        self._draw_buildings(self.static_bg)
        
        # Draw trees
        self._draw_trees(self.static_bg)
        
    def _draw_grass(self, surface):
        """Draw grass background with isometric tiles"""
        tile_size = 40
        
        for i in range(-20, 30):
            for j in range(-20, 30):
                wx = i * tile_size
                wy = j * tile_size
                
                # Skip road areas
                if abs(wx) < 100 or abs(wy) < 100:
                    continue
                
                # Draw isometric tile
                p1 = self.world_to_screen(wx, wy)
                p2 = self.world_to_screen(wx + tile_size, wy)
                p3 = self.world_to_screen(wx + tile_size, wy + tile_size)
                p4 = self.world_to_screen(wx, wy + tile_size)
                
                color = (80 + (i + j) % 2 * 20, 150 + (i + j) % 2 * 20, 80)
                pygame.draw.polygon(surface, color, [p1, p2, p3, p4])
                
    def _draw_roads(self, surface):
        """Draw isometric roads with markings"""
        road_color = (70, 72, 78)
        road_dark = (55, 57, 62)
        marking = (255, 255, 255)
        yellow = (255, 220, 50)
        
        rw = self.road_width // 2
        road_len = 500
        
        # Horizontal road (East-West)
        h_road = [
            self.world_to_screen(-road_len, -rw),
            self.world_to_screen(road_len, -rw),
            self.world_to_screen(road_len, rw),
            self.world_to_screen(-road_len, rw),
        ]
        pygame.draw.polygon(surface, road_color, h_road)
        
        # Vertical road (North-South)
        v_road = [
            self.world_to_screen(-rw, -road_len),
            self.world_to_screen(rw, -road_len),
            self.world_to_screen(rw, road_len),
            self.world_to_screen(-rw, road_len),
        ]
        pygame.draw.polygon(surface, road_color, v_road)
        
        # Center intersection (darker)
        center = [
            self.world_to_screen(-rw, -rw),
            self.world_to_screen(rw, -rw),
            self.world_to_screen(rw, rw),
            self.world_to_screen(-rw, rw),
        ]
        pygame.draw.polygon(surface, road_dark, center)
        
        # Draw zebra crossings
        self._draw_zebra_crossings(surface, rw)
        
        # Draw lane markings
        self._draw_lane_markings(surface, rw, road_len)
        
        # Draw green dividers
        self._draw_dividers(surface, rw, road_len)
        
    def _draw_zebra_crossings(self, surface, rw):
        """Draw zebra crossings at intersection"""
        stripe_color = (250, 250, 250)
        stripe_w = 8
        stripe_gap = 10
        
        # Each crossing
        crossings = [
            (-rw - 50, -rw + 10, 'v'),   # West
            (rw + 10, -rw + 10, 'v'),    # East  
            (-rw + 10, -rw - 50, 'h'),   # North
            (-rw + 10, rw + 10, 'h'),    # South
        ]
        
        for cx, cy, orient in crossings:
            for i in range(8):
                if orient == 'v':
                    # Vertical stripes
                    s1 = self.world_to_screen(cx, cy + i * (stripe_w + stripe_gap))
                    s2 = self.world_to_screen(cx + 40, cy + i * (stripe_w + stripe_gap))
                    s3 = self.world_to_screen(cx + 40, cy + i * (stripe_w + stripe_gap) + stripe_w)
                    s4 = self.world_to_screen(cx, cy + i * (stripe_w + stripe_gap) + stripe_w)
                else:
                    # Horizontal stripes
                    s1 = self.world_to_screen(cx + i * (stripe_w + stripe_gap), cy)
                    s2 = self.world_to_screen(cx + i * (stripe_w + stripe_gap) + stripe_w, cy)
                    s3 = self.world_to_screen(cx + i * (stripe_w + stripe_gap) + stripe_w, cy + 40)
                    s4 = self.world_to_screen(cx + i * (stripe_w + stripe_gap), cy + 40)
                    
                pygame.draw.polygon(surface, stripe_color, [s1, s2, s3, s4])
                
    def _draw_lane_markings(self, surface, rw, road_len):
        """Draw road lane markings"""
        white = (240, 240, 240)
        yellow = (255, 220, 50)
        
        # Dashed center lines
        dash_len = 30
        gap_len = 20
        
        # Horizontal road center line (yellow)
        for x in range(-road_len, -rw - 60, dash_len + gap_len):
            p1 = self.world_to_screen(x, 0)
            p2 = self.world_to_screen(x + dash_len, 0)
            pygame.draw.line(surface, yellow, p1, p2, 3)
            
        for x in range(rw + 60, road_len, dash_len + gap_len):
            p1 = self.world_to_screen(x, 0)
            p2 = self.world_to_screen(x + dash_len, 0)
            pygame.draw.line(surface, yellow, p1, p2, 3)
            
        # Vertical road center line (yellow)
        for y in range(-road_len, -rw - 60, dash_len + gap_len):
            p1 = self.world_to_screen(0, y)
            p2 = self.world_to_screen(0, y + dash_len)
            pygame.draw.line(surface, yellow, p1, p2, 3)
            
        for y in range(rw + 60, road_len, dash_len + gap_len):
            p1 = self.world_to_screen(0, y)
            p2 = self.world_to_screen(0, y + dash_len)
            pygame.draw.line(surface, yellow, p1, p2, 3)
            
    def _draw_dividers(self, surface, rw, road_len):
        """Draw green median dividers"""
        divider_color = (50, 140, 50)
        divider_dark = (40, 110, 40)
        dw = 10  # Divider width
        
        # West divider
        for x in range(-road_len + 50, -rw - 80, 60):
            p1 = self.world_to_screen(x, -dw)
            p2 = self.world_to_screen(x + 40, -dw)
            p3 = self.world_to_screen(x + 40, dw)
            p4 = self.world_to_screen(x, dw)
            pygame.draw.polygon(surface, divider_color, [p1, p2, p3, p4])
            # Small bush
            bp = self.world_to_screen(x + 20, 0, 5)
            pygame.draw.circle(surface, (60, 150, 60), bp, 6)
            
        # East divider
        for x in range(rw + 80, road_len - 50, 60):
            p1 = self.world_to_screen(x, -dw)
            p2 = self.world_to_screen(x + 40, -dw)
            p3 = self.world_to_screen(x + 40, dw)
            p4 = self.world_to_screen(x, dw)
            pygame.draw.polygon(surface, divider_color, [p1, p2, p3, p4])
            bp = self.world_to_screen(x + 20, 0, 5)
            pygame.draw.circle(surface, (60, 150, 60), bp, 6)
            
        # North divider
        for y in range(-road_len + 50, -rw - 80, 60):
            p1 = self.world_to_screen(-dw, y)
            p2 = self.world_to_screen(dw, y)
            p3 = self.world_to_screen(dw, y + 40)
            p4 = self.world_to_screen(-dw, y + 40)
            pygame.draw.polygon(surface, divider_color, [p1, p2, p3, p4])
            bp = self.world_to_screen(0, y + 20, 5)
            pygame.draw.circle(surface, (60, 150, 60), bp, 6)
            
        # South divider
        for y in range(rw + 80, road_len - 50, 60):
            p1 = self.world_to_screen(-dw, y)
            p2 = self.world_to_screen(dw, y)
            p3 = self.world_to_screen(dw, y + 40)
            p4 = self.world_to_screen(-dw, y + 40)
            pygame.draw.polygon(surface, divider_color, [p1, p2, p3, p4])
            bp = self.world_to_screen(0, y + 20, 5)
            pygame.draw.circle(surface, (60, 150, 60), bp, 6)
            
    def _draw_buildings(self, surface):
        """Draw 3D isometric buildings"""
        # Building configs: (wx, wy, width, depth, height, color)
        buildings = [
            # Northwest quadrant
            (-350, -350, 120, 100, 150, (200, 195, 190)),
            (-200, -300, 80, 70, 100, (180, 175, 170)),
            (-350, -200, 70, 80, 80, (190, 185, 180)),
            
            # Northeast quadrant  
            (180, -350, 130, 110, 180, (195, 190, 185)),
            (350, -300, 90, 80, 120, (185, 180, 175)),
            (200, -200, 80, 70, 90, (175, 170, 165)),
            
            # Southwest quadrant
            (-350, 180, 110, 90, 100, (190, 185, 180)),
            (-200, 250, 80, 80, 130, (180, 175, 170)),
            (-350, 320, 100, 70, 70, (170, 165, 160)),
            
            # Southeast quadrant
            (180, 180, 120, 100, 140, (185, 180, 175)),
            (350, 250, 80, 70, 90, (175, 170, 165)),
            (200, 350, 90, 80, 110, (180, 175, 170)),
        ]
        
        # Sort by depth for proper drawing order
        buildings.sort(key=lambda b: b[0] + b[1])
        
        for wx, wy, w, d, h, color in buildings:
            self._draw_3d_building(surface, wx, wy, w, d, h, color)
            
    def _draw_3d_building(self, surface, wx, wy, width, depth, height, color):
        """Draw a 3D isometric building with windows"""
        # Calculate colors for different faces
        top_color = tuple(min(255, c + 30) for c in color)
        right_color = tuple(max(0, c - 30) for c in color)
        left_color = color
        
        # Get corner points at ground level
        bl = self.world_to_screen(wx, wy + depth)           # Back left
        br = self.world_to_screen(wx + width, wy + depth)   # Back right
        fr = self.world_to_screen(wx + width, wy)           # Front right
        fl = self.world_to_screen(wx, wy)                   # Front left
        
        # Get corner points at top level
        bl_t = self.world_to_screen(wx, wy + depth, height)
        br_t = self.world_to_screen(wx + width, wy + depth, height)
        fr_t = self.world_to_screen(wx + width, wy, height)
        fl_t = self.world_to_screen(wx, wy, height)
        
        # Draw back faces first (left and back)
        # Left face
        pygame.draw.polygon(surface, left_color, [fl, bl, bl_t, fl_t])
        pygame.draw.polygon(surface, (50, 50, 50), [fl, bl, bl_t, fl_t], 1)
        
        # Back face
        pygame.draw.polygon(surface, right_color, [bl, br, br_t, bl_t])
        pygame.draw.polygon(surface, (50, 50, 50), [bl, br, br_t, bl_t], 1)
        
        # Draw front faces
        # Right face
        pygame.draw.polygon(surface, right_color, [fr, br, br_t, fr_t])
        pygame.draw.polygon(surface, (50, 50, 50), [fr, br, br_t, fr_t], 1)
        
        # Front face
        pygame.draw.polygon(surface, left_color, [fl, fr, fr_t, fl_t])
        pygame.draw.polygon(surface, (50, 50, 50), [fl, fr, fr_t, fl_t], 1)
        
        # Top face
        pygame.draw.polygon(surface, top_color, [fl_t, fr_t, br_t, bl_t])
        pygame.draw.polygon(surface, (50, 50, 50), [fl_t, fr_t, br_t, bl_t], 1)
        
        # Draw windows on front face
        window_color = (140, 180, 210)
        window_dark = (100, 140, 170)
        
        floors = height // 35
        windows_per_floor = width // 30
        
        for floor in range(floors):
            for win in range(windows_per_floor):
                # Window position
                win_x = wx + 15 + win * 28
                win_y = wy + 5
                win_z = 20 + floor * 35
                
                # Window corners
                w1 = self.world_to_screen(win_x, win_y, win_z)
                w2 = self.world_to_screen(win_x + 18, win_y, win_z)
                w3 = self.world_to_screen(win_x + 18, win_y, win_z + 22)
                w4 = self.world_to_screen(win_x, win_y, win_z + 22)
                
                pygame.draw.polygon(surface, window_color, [w1, w2, w3, w4])
                # Window reflection
                pygame.draw.polygon(surface, window_dark, [w1, 
                    ((w1[0] + w2[0])//2, (w1[1] + w2[1])//2),
                    ((w3[0] + w4[0])//2, (w3[1] + w4[1])//2), w4])
                    
    def _draw_trees(self, surface):
        """Draw 3D isometric trees"""
        tree_positions = []
        
        # Along roads (not on road)
        for x in range(-400, -120, 70):
            tree_positions.append((x, -120))
            tree_positions.append((x, 120))
        for x in range(120, 400, 70):
            tree_positions.append((x, -120))
            tree_positions.append((x, 120))
        for y in range(-400, -120, 70):
            tree_positions.append((-120, y))
            tree_positions.append((120, y))
        for y in range(120, 400, 70):
            tree_positions.append((-120, y))
            tree_positions.append((120, y))
            
        tree_positions.sort(key=lambda p: p[0] + p[1])
        
        for tx, ty in tree_positions:
            self._draw_3d_tree(surface, tx, ty)
            
    def _draw_3d_tree(self, surface, wx, wy):
        """Draw a 3D isometric conical tree"""
        trunk_color = (90, 65, 40)
        leaf_color = (45, 130, 45)
        leaf_light = (60, 160, 60)
        
        # Trunk
        t1 = self.world_to_screen(wx - 4, wy - 4, 0)
        t2 = self.world_to_screen(wx + 4, wy - 4, 0)
        t3 = self.world_to_screen(wx + 4, wy + 4, 0)
        t4 = self.world_to_screen(wx - 4, wy + 4, 0)
        t1t = self.world_to_screen(wx - 4, wy - 4, 25)
        t2t = self.world_to_screen(wx + 4, wy - 4, 25)
        t3t = self.world_to_screen(wx + 4, wy + 4, 25)
        t4t = self.world_to_screen(wx - 4, wy + 4, 25)
        
        pygame.draw.polygon(surface, trunk_color, [t1, t2, t2t, t1t])
        pygame.draw.polygon(surface, trunk_color, [t2, t3, t3t, t2t])
        
        # Conical foliage (3 layers)
        for layer, (size, z_base) in enumerate([(25, 20), (20, 35), (15, 50)]):
            top = self.world_to_screen(wx, wy, z_base + 25)
            
            # Create cone points
            points = []
            for angle in range(0, 360, 60):
                rad = math.radians(angle)
                px = wx + math.cos(rad) * size
                py = wy + math.sin(rad) * size
                points.append(self.world_to_screen(px, py, z_base))
                
            # Draw cone faces
            for i in range(len(points)):
                p1 = points[i]
                p2 = points[(i + 1) % len(points)]
                color = leaf_light if i % 2 == 0 else leaf_color
                pygame.draw.polygon(surface, color, [p1, p2, top])
                
    def draw_3d_vehicle(self, surface, wx, wy, v_type, color, direction):
        """Draw a 3D isometric vehicle"""
        if v_type == 'car':
            self._draw_3d_car(surface, wx, wy, color, direction)
        elif v_type == 'truck':
            self._draw_3d_truck(surface, wx, wy, color, direction)
        elif v_type == 'bike':
            self._draw_3d_bike(surface, wx, wy, color, direction)
        elif v_type == 'ambulance':
            self._draw_3d_ambulance(surface, wx, wy, direction)
        elif v_type == 'police':
            self._draw_3d_police(surface, wx, wy, direction)
            
    def _draw_3d_car(self, surface, wx, wy, color, direction):
        """Draw a realistic 3D isometric car"""
        # Car dimensions
        if direction in (0, 2):  # East-West
            length, width, height = 35, 18, 12
            cabin_h = 10
        else:  # North-South
            length, width, height = 18, 35, 12
            cabin_h = 10
            
        dark = tuple(max(0, c - 40) for c in color)
        light = tuple(min(255, c + 20) for c in color)
        
        # Shadow
        shadow_points = [
            self.world_to_screen(wx - length//2 + 3, wy - width//2 + 3),
            self.world_to_screen(wx + length//2 + 3, wy - width//2 + 3),
            self.world_to_screen(wx + length//2 + 3, wy + width//2 + 3),
            self.world_to_screen(wx - length//2 + 3, wy + width//2 + 3),
        ]
        pygame.draw.polygon(surface, (40, 40, 40), shadow_points)
        
        # Car body - bottom
        b1 = self.world_to_screen(wx - length//2, wy - width//2, 2)
        b2 = self.world_to_screen(wx + length//2, wy - width//2, 2)
        b3 = self.world_to_screen(wx + length//2, wy + width//2, 2)
        b4 = self.world_to_screen(wx - length//2, wy + width//2, 2)
        
        # Car body - top of lower section
        t1 = self.world_to_screen(wx - length//2, wy - width//2, height)
        t2 = self.world_to_screen(wx + length//2, wy - width//2, height)
        t3 = self.world_to_screen(wx + length//2, wy + width//2, height)
        t4 = self.world_to_screen(wx - length//2, wy + width//2, height)
        
        # Draw body sides
        pygame.draw.polygon(surface, color, [b1, b2, t2, t1])  # Front
        pygame.draw.polygon(surface, dark, [b2, b3, t3, t2])   # Right
        pygame.draw.polygon(surface, dark, [b3, b4, t4, t3])   # Back
        pygame.draw.polygon(surface, color, [b4, b1, t1, t4])  # Left
        pygame.draw.polygon(surface, light, [t1, t2, t3, t4])  # Top
        
        # Cabin/roof
        cabin_inset = 5
        c1 = self.world_to_screen(wx - length//2 + cabin_inset, wy - width//2 + cabin_inset//2, height)
        c2 = self.world_to_screen(wx + length//2 - cabin_inset, wy - width//2 + cabin_inset//2, height)
        c3 = self.world_to_screen(wx + length//2 - cabin_inset, wy + width//2 - cabin_inset//2, height)
        c4 = self.world_to_screen(wx - length//2 + cabin_inset, wy + width//2 - cabin_inset//2, height)
        
        ct1 = self.world_to_screen(wx - length//2 + cabin_inset, wy - width//2 + cabin_inset//2, height + cabin_h)
        ct2 = self.world_to_screen(wx + length//2 - cabin_inset, wy - width//2 + cabin_inset//2, height + cabin_h)
        ct3 = self.world_to_screen(wx + length//2 - cabin_inset, wy + width//2 - cabin_inset//2, height + cabin_h)
        ct4 = self.world_to_screen(wx - length//2 + cabin_inset, wy + width//2 - cabin_inset//2, height + cabin_h)
        
        # Cabin windows (glass color)
        glass = (150, 190, 220)
        pygame.draw.polygon(surface, glass, [c1, c2, ct2, ct1])
        pygame.draw.polygon(surface, (120, 160, 190), [c2, c3, ct3, ct2])
        pygame.draw.polygon(surface, (120, 160, 190), [c3, c4, ct4, ct3])
        pygame.draw.polygon(surface, glass, [c4, c1, ct1, ct4])
        pygame.draw.polygon(surface, (100, 140, 170), [ct1, ct2, ct3, ct4])  # Roof
        
        # Wheels (simple circles at corners)
        wheel_color = (30, 30, 30)
        wheel_positions = [
            (wx - length//3, wy - width//2),
            (wx + length//3, wy - width//2),
            (wx - length//3, wy + width//2),
            (wx + length//3, wy + width//2),
        ]
        for wpx, wpy in wheel_positions:
            wp = self.world_to_screen(wpx, wpy, 4)
            pygame.draw.circle(surface, wheel_color, wp, 5)
            pygame.draw.circle(surface, (60, 60, 60), wp, 3)
            
    def _draw_3d_truck(self, surface, wx, wy, color, direction):
        """Draw a 3D isometric truck/van"""
        if direction in (0, 2):
            length, width, height = 50, 22, 22
        else:
            length, width, height = 22, 50, 22
            
        dark = tuple(max(0, c - 50) for c in color)
        light = tuple(min(255, c + 15) for c in color)
        
        # Shadow
        shadow = [
            self.world_to_screen(wx - length//2 + 4, wy - width//2 + 4),
            self.world_to_screen(wx + length//2 + 4, wy - width//2 + 4),
            self.world_to_screen(wx + length//2 + 4, wy + width//2 + 4),
            self.world_to_screen(wx - length//2 + 4, wy + width//2 + 4),
        ]
        pygame.draw.polygon(surface, (40, 40, 40), shadow)
        
        # Cargo box
        b1 = self.world_to_screen(wx - length//2, wy - width//2, 4)
        b2 = self.world_to_screen(wx + length//2, wy - width//2, 4)
        b3 = self.world_to_screen(wx + length//2, wy + width//2, 4)
        b4 = self.world_to_screen(wx - length//2, wy + width//2, 4)
        
        t1 = self.world_to_screen(wx - length//2, wy - width//2, height)
        t2 = self.world_to_screen(wx + length//2, wy - width//2, height)
        t3 = self.world_to_screen(wx + length//2, wy + width//2, height)
        t4 = self.world_to_screen(wx - length//2, wy + width//2, height)
        
        pygame.draw.polygon(surface, color, [b1, b2, t2, t1])
        pygame.draw.polygon(surface, dark, [b2, b3, t3, t2])
        pygame.draw.polygon(surface, dark, [b3, b4, t4, t3])
        pygame.draw.polygon(surface, color, [b4, b1, t1, t4])
        pygame.draw.polygon(surface, light, [t1, t2, t3, t4])
        
        # Cabin windshield
        glass = (150, 190, 220)
        if direction == 0:  # Going East
            wp = self.world_to_screen(wx + length//2 - 8, wy - width//2 + 3, height - 8)
            pygame.draw.circle(surface, glass, wp, 8)
        elif direction == 2:  # Going West
            wp = self.world_to_screen(wx - length//2 + 8, wy - width//2 + 3, height - 8)
            pygame.draw.circle(surface, glass, wp, 8)
            
    def _draw_3d_bike(self, surface, wx, wy, color, direction):
        """Draw a realistic 3D motorcycle with rider"""
        # Motorcycle dimensions based on direction
        if direction in (0, 2):  # East-West
            length, width = 30, 12
            wheel_offset = 10
        else:  # North-South
            length, width = 12, 30
            wheel_offset = 10
            
        dark = tuple(max(0, c - 50) for c in color)
        chrome = (180, 180, 190)
        
        # Shadow
        shadow = self.world_to_screen(wx + 3, wy + 3, 0)
        pygame.draw.ellipse(surface, (40, 40, 40), (shadow[0] - 12, shadow[1] - 6, 24, 12))
        
        # Wheels (black tires with chrome hub)
        if direction in (0, 2):
            # Front wheel
            fw = self.world_to_screen(wx + wheel_offset, wy, 5)
            pygame.draw.circle(surface, (30, 30, 30), fw, 7)
            pygame.draw.circle(surface, chrome, fw, 4)
            pygame.draw.circle(surface, (50, 50, 50), fw, 2)
            
            # Back wheel
            bw = self.world_to_screen(wx - wheel_offset, wy, 5)
            pygame.draw.circle(surface, (30, 30, 30), bw, 7)
            pygame.draw.circle(surface, chrome, bw, 4)
            pygame.draw.circle(surface, (50, 50, 50), bw, 2)
        else:
            # Front wheel
            fw = self.world_to_screen(wx, wy + wheel_offset, 5)
            pygame.draw.circle(surface, (30, 30, 30), fw, 7)
            pygame.draw.circle(surface, chrome, fw, 4)
            
            # Back wheel  
            bw = self.world_to_screen(wx, wy - wheel_offset, 5)
            pygame.draw.circle(surface, (30, 30, 30), bw, 7)
            pygame.draw.circle(surface, chrome, bw, 4)
        
        # Bike frame/body
        if direction in (0, 2):
            # Horizontal bike body
            b1 = self.world_to_screen(wx - 10, wy - 4, 6)
            b2 = self.world_to_screen(wx + 8, wy - 4, 6)
            b3 = self.world_to_screen(wx + 8, wy + 4, 6)
            b4 = self.world_to_screen(wx - 10, wy + 4, 6)
            
            t1 = self.world_to_screen(wx - 8, wy - 3, 12)
            t2 = self.world_to_screen(wx + 5, wy - 3, 12)
            t3 = self.world_to_screen(wx + 5, wy + 3, 12)
            t4 = self.world_to_screen(wx - 8, wy + 3, 12)
        else:
            # Vertical bike body
            b1 = self.world_to_screen(wx - 4, wy - 10, 6)
            b2 = self.world_to_screen(wx + 4, wy - 10, 6)
            b3 = self.world_to_screen(wx + 4, wy + 8, 6)
            b4 = self.world_to_screen(wx - 4, wy + 8, 6)
            
            t1 = self.world_to_screen(wx - 3, wy - 8, 12)
            t2 = self.world_to_screen(wx + 3, wy - 8, 12)
            t3 = self.world_to_screen(wx + 3, wy + 5, 12)
            t4 = self.world_to_screen(wx - 3, wy + 5, 12)
            
        # Draw bike body (fuel tank and seat)
        pygame.draw.polygon(surface, color, [b1, b2, t2, t1])
        pygame.draw.polygon(surface, dark, [b2, b3, t3, t2])
        pygame.draw.polygon(surface, dark, [b3, b4, t4, t3])
        pygame.draw.polygon(surface, color, [b4, b1, t1, t4])
        
        # Fuel tank (top, rounded)
        tank_pos = self.world_to_screen(wx, wy, 13)
        pygame.draw.ellipse(surface, color, (tank_pos[0] - 6, tank_pos[1] - 4, 12, 8))
        pygame.draw.ellipse(surface, tuple(min(255, c + 40) for c in color), (tank_pos[0] - 4, tank_pos[1] - 2, 4, 3))
        
        # Handlebar
        if direction in (0, 2):
            h1 = self.world_to_screen(wx + 8, wy - 6, 14)
            h2 = self.world_to_screen(wx + 8, wy + 6, 14)
            pygame.draw.line(surface, chrome, h1, h2, 3)
            # Headlight
            hl = self.world_to_screen(wx + 12, wy, 10)
            pygame.draw.circle(surface, (255, 255, 200), hl, 4)
        else:
            h1 = self.world_to_screen(wx - 6, wy + 8, 14)
            h2 = self.world_to_screen(wx + 6, wy + 8, 14)
            pygame.draw.line(surface, chrome, h1, h2, 3)
            hl = self.world_to_screen(wx, wy + 12, 10)
            pygame.draw.circle(surface, (255, 255, 200), hl, 4)
        
        # Exhaust pipe
        if direction in (0, 2):
            ex = self.world_to_screen(wx - 12, wy + 3, 6)
            pygame.draw.circle(surface, chrome, ex, 3)
        else:
            ex = self.world_to_screen(wx + 3, wy - 12, 6)
            pygame.draw.circle(surface, chrome, ex, 3)
        
        # Rider
        rider_x, rider_y = wx, wy
        
        # Rider body (torso)
        body_bottom = self.world_to_screen(rider_x, rider_y, 14)
        body_top = self.world_to_screen(rider_x, rider_y, 26)
        pygame.draw.line(surface, (40, 40, 50), body_bottom, body_top, 6)
        
        # Rider jacket
        jacket_colors = [(40, 40, 50), (30, 30, 35), (60, 30, 30)]
        jacket = jacket_colors[hash((int(wx), int(wy))) % len(jacket_colors)]
        pygame.draw.line(surface, jacket, body_bottom, body_top, 5)
        
        # Rider head with helmet
        helmet_pos = self.world_to_screen(rider_x, rider_y, 30)
        pygame.draw.circle(surface, (30, 30, 35), helmet_pos, 6)  # Helmet
        # Visor
        visor_color = (80, 120, 140)
        pygame.draw.arc(surface, visor_color, 
                       (helmet_pos[0] - 5, helmet_pos[1] - 4, 10, 8), 
                       3.14, 6.28, 2)
        
        # Arms on handlebar
        if direction in (0, 2):
            arm_end = self.world_to_screen(wx + 6, wy, 15)
        else:
            arm_end = self.world_to_screen(wx, wy + 6, 15)
        shoulder = self.world_to_screen(rider_x, rider_y, 23)
        pygame.draw.line(surface, (40, 40, 50), shoulder, arm_end, 3)
        
    def draw_accident(self, surface, wx, wy, accident_data):
        """Draw realistic accident scene"""
        # Smoke/dust cloud
        for i in range(5):
            smoke_x = wx + random.randint(-20, 20)
            smoke_y = wy + random.randint(-20, 20)
            smoke_z = random.randint(5, 30)
            smoke_pos = self.world_to_screen(smoke_x, smoke_y, smoke_z)
            smoke_size = random.randint(8, 20)
            smoke_alpha = random.randint(100, 180)
            pygame.draw.circle(surface, (smoke_alpha, smoke_alpha, smoke_alpha), smoke_pos, smoke_size)
        
        # Damaged vehicles (tilted/crashed)
        # Car 1 - tilted
        car1_x = wx - 15
        car1_y = wy - 10
        self._draw_crashed_car(surface, car1_x, car1_y, (180, 50, 50), 15)
        
        # Car 2 - crashed into car 1
        car2_x = wx + 15
        car2_y = wy + 5
        self._draw_crashed_car(surface, car2_x, car2_y, (50, 80, 180), -10)
        
        # Debris on ground
        debris_color = (60, 60, 60)
        for i in range(8):
            dx = wx + random.randint(-30, 30)
            dy = wy + random.randint(-30, 30)
            dp = self.world_to_screen(dx, dy, 1)
            pygame.draw.circle(surface, debris_color, dp, random.randint(2, 4))
            
        # Glass shards (light blue)
        for i in range(5):
            gx = wx + random.randint(-25, 25)
            gy = wy + random.randint(-25, 25)
            gp = self.world_to_screen(gx, gy, 1)
            pygame.draw.polygon(surface, (150, 200, 230), [
                gp,
                (gp[0] + random.randint(3, 6), gp[1] + random.randint(-3, 3)),
                (gp[0] + random.randint(-3, 3), gp[1] + random.randint(3, 6))
            ])
            
        # Fire/sparks (if severe)
        if accident_data.get('severe', False):
            fire_pos = self.world_to_screen(wx, wy, 15)
            # Flame colors
            pygame.draw.circle(surface, (255, 100, 0), fire_pos, 12)
            pygame.draw.circle(surface, (255, 200, 0), fire_pos, 8)
            pygame.draw.circle(surface, (255, 255, 100), fire_pos, 4)
            
        # Warning triangle
        tri_x = wx - 40
        tri_y = wy
        tri_base = self.world_to_screen(tri_x, tri_y, 0)
        pygame.draw.polygon(surface, (255, 100, 0), [
            (tri_base[0], tri_base[1] - 15),
            (tri_base[0] - 10, tri_base[1] + 5),
            (tri_base[0] + 10, tri_base[1] + 5)
        ])
        pygame.draw.polygon(surface, (255, 50, 0), [
            (tri_base[0], tri_base[1] - 15),
            (tri_base[0] - 10, tri_base[1] + 5),
            (tri_base[0] + 10, tri_base[1] + 5)
        ], 2)
        
    def _draw_crashed_car(self, surface, wx, wy, color, tilt_angle):
        """Draw a crashed/damaged car"""
        dark = tuple(max(0, c - 40) for c in color)
        
        # Tilted car body
        length, width, height = 35, 18, 10
        
        # Apply tilt offset
        tilt_z = abs(tilt_angle) // 3
        
        # Crumpled front
        b1 = self.world_to_screen(wx - length//2, wy - width//2, 2 + tilt_z)
        b2 = self.world_to_screen(wx + length//2 - 5, wy - width//2, 2)  # Crumpled
        b3 = self.world_to_screen(wx + length//2 - 5, wy + width//2, 2)
        b4 = self.world_to_screen(wx - length//2, wy + width//2, 2 + tilt_z)
        
        t1 = self.world_to_screen(wx - length//2, wy - width//2, height + tilt_z)
        t2 = self.world_to_screen(wx + length//2 - 8, wy - width//2, height - 3)  # Crushed roof
        t3 = self.world_to_screen(wx + length//2 - 8, wy + width//2, height - 3)
        t4 = self.world_to_screen(wx - length//2, wy + width//2, height + tilt_z)
        
        # Draw damaged body
        pygame.draw.polygon(surface, color, [b1, b2, t2, t1])
        pygame.draw.polygon(surface, dark, [b2, b3, t3, t2])
        pygame.draw.polygon(surface, (80, 80, 80), [t1, t2, t3, t4])  # Damaged roof
        
        # Broken window
        pygame.draw.polygon(surface, (100, 130, 150), [t1, t2, t3, t4])
        # Cracks
        crack_start = ((t1[0] + t3[0])//2, (t1[1] + t3[1])//2)
        for i in range(3):
            pygame.draw.line(surface, (200, 200, 200), crack_start,
                           (crack_start[0] + random.randint(-15, 15), 
                            crack_start[1] + random.randint(-10, 10)), 1)
        rider_pos = self.world_to_screen(wx, wy, 15)
        pygame.draw.circle(surface, (60, 60, 70), rider_pos, 7)
        head_pos = self.world_to_screen(wx, wy, 22)
        pygame.draw.circle(surface, (220, 180, 150), head_pos, 5)
        
    def _draw_3d_ambulance(self, surface, wx, wy, direction):
        """Draw a 3D ambulance with flashing lights"""
        flash = int(time.time() * 5) % 2
        
        if direction in (0, 2):
            length, width, height = 50, 22, 22
        else:
            length, width, height = 22, 50, 22
            
        # Shadow
        shadow = [
            self.world_to_screen(wx - length//2 + 4, wy - width//2 + 4),
            self.world_to_screen(wx + length//2 + 4, wy - width//2 + 4),
            self.world_to_screen(wx + length//2 + 4, wy + width//2 + 4),
            self.world_to_screen(wx - length//2 + 4, wy + width//2 + 4),
        ]
        pygame.draw.polygon(surface, (40, 40, 40), shadow)
        
        # White body
        b1 = self.world_to_screen(wx - length//2, wy - width//2, 4)
        b2 = self.world_to_screen(wx + length//2, wy - width//2, 4)
        b3 = self.world_to_screen(wx + length//2, wy + width//2, 4)
        b4 = self.world_to_screen(wx - length//2, wy + width//2, 4)
        
        t1 = self.world_to_screen(wx - length//2, wy - width//2, height)
        t2 = self.world_to_screen(wx + length//2, wy - width//2, height)
        t3 = self.world_to_screen(wx + length//2, wy + width//2, height)
        t4 = self.world_to_screen(wx - length//2, wy + width//2, height)
        
        pygame.draw.polygon(surface, (250, 250, 250), [b1, b2, t2, t1])
        pygame.draw.polygon(surface, (230, 230, 230), [b2, b3, t3, t2])
        pygame.draw.polygon(surface, (230, 230, 230), [b3, b4, t4, t3])
        pygame.draw.polygon(surface, (250, 250, 250), [b4, b1, t1, t4])
        pygame.draw.polygon(surface, (240, 240, 240), [t1, t2, t3, t4])
        
        # Red stripe
        stripe_z = height // 2 + 4
        s1 = self.world_to_screen(wx - length//2, wy - width//2, stripe_z - 3)
        s2 = self.world_to_screen(wx + length//2, wy - width//2, stripe_z - 3)
        s3 = self.world_to_screen(wx + length//2, wy - width//2, stripe_z + 3)
        s4 = self.world_to_screen(wx - length//2, wy - width//2, stripe_z + 3)
        pygame.draw.polygon(surface, (220, 50, 50), [s1, s2, s3, s4])
        
        # Red cross on side
        cross_center = self.world_to_screen(wx, wy - width//2, height - 6)
        pygame.draw.line(surface, (220, 50, 50), 
                        (cross_center[0] - 8, cross_center[1]), 
                        (cross_center[0] + 8, cross_center[1]), 4)
        pygame.draw.line(surface, (220, 50, 50),
                        (cross_center[0], cross_center[1] - 8),
                        (cross_center[0], cross_center[1] + 8), 4)
        
        # Flashing lights
        light1_pos = self.world_to_screen(wx - length//4, wy, height + 5)
        light2_pos = self.world_to_screen(wx + length//4, wy, height + 5)
        
        color1 = (255, 50, 50) if flash else (50, 50, 255)
        color2 = (50, 50, 255) if flash else (255, 50, 50)
        
        pygame.draw.circle(surface, color1, light1_pos, 5)
        pygame.draw.circle(surface, color2, light2_pos, 5)
        
        # Glow effect
        if flash:
            pygame.draw.circle(surface, (255, 100, 100), light1_pos, 8, 2)
            pygame.draw.circle(surface, (100, 100, 255), light2_pos, 8, 2)
            
    def _draw_3d_police(self, surface, wx, wy, direction):
        """Draw a 3D police car"""
        flash = int(time.time() * 6) % 2
        
        if direction in (0, 2):
            length, width, height = 40, 18, 14
        else:
            length, width, height = 18, 40, 14
            
        # Shadow
        shadow = [
            self.world_to_screen(wx - length//2 + 3, wy - width//2 + 3),
            self.world_to_screen(wx + length//2 + 3, wy - width//2 + 3),
            self.world_to_screen(wx + length//2 + 3, wy + width//2 + 3),
            self.world_to_screen(wx - length//2 + 3, wy + width//2 + 3),
        ]
        pygame.draw.polygon(surface, (40, 40, 40), shadow)
        
        # Black and white body
        b1 = self.world_to_screen(wx - length//2, wy - width//2, 2)
        b2 = self.world_to_screen(wx + length//2, wy - width//2, 2)
        b3 = self.world_to_screen(wx + length//2, wy + width//2, 2)
        b4 = self.world_to_screen(wx - length//2, wy + width//2, 2)
        
        t1 = self.world_to_screen(wx - length//2, wy - width//2, height)
        t2 = self.world_to_screen(wx + length//2, wy - width//2, height)
        t3 = self.world_to_screen(wx + length//2, wy + width//2, height)
        t4 = self.world_to_screen(wx - length//2, wy + width//2, height)
        
        # White top, black bottom pattern
        pygame.draw.polygon(surface, (250, 250, 250), [b1, b2, t2, t1])
        pygame.draw.polygon(surface, (30, 30, 30), [b2, b3, t3, t2])
        pygame.draw.polygon(surface, (30, 30, 30), [b3, b4, t4, t3])
        pygame.draw.polygon(surface, (250, 250, 250), [b4, b1, t1, t4])
        pygame.draw.polygon(surface, (240, 240, 240), [t1, t2, t3, t4])
        
        # Light bar on top
        lb1 = self.world_to_screen(wx - 8, wy - width//3, height)
        lb2 = self.world_to_screen(wx + 8, wy - width//3, height)
        lb3 = self.world_to_screen(wx + 8, wy + width//3, height)
        lb4 = self.world_to_screen(wx - 8, wy + width//3, height)
        lb1t = self.world_to_screen(wx - 8, wy - width//3, height + 4)
        lb2t = self.world_to_screen(wx + 8, wy - width//3, height + 4)
        lb3t = self.world_to_screen(wx + 8, wy + width//3, height + 4)
        lb4t = self.world_to_screen(wx - 8, wy + width//3, height + 4)
        
        pygame.draw.polygon(surface, (40, 40, 40), [lb1, lb2, lb2t, lb1t])
        pygame.draw.polygon(surface, (40, 40, 40), [lb2, lb3, lb3t, lb2t])
        
        # Flashing lights
        light1 = self.world_to_screen(wx - 5, wy, height + 5)
        light2 = self.world_to_screen(wx + 5, wy, height + 5)
        
        color1 = (255, 50, 50) if flash else (50, 50, 255)
        color2 = (50, 50, 255) if flash else (255, 50, 50)
        
        pygame.draw.circle(surface, color1, light1, 4)
        pygame.draw.circle(surface, color2, light2, 4)
        
    def draw_traffic_signal(self, surface, wx, wy, state):
        """Draw a 3D traffic signal"""
        pole_color = (60, 60, 65)
        
        # Pole
        p_base = self.world_to_screen(wx, wy, 0)
        p_top = self.world_to_screen(wx, wy, 50)
        pygame.draw.line(surface, pole_color, p_base, p_top, 4)
        
        # Signal box
        box_z = 35
        box = [
            self.world_to_screen(wx - 8, wy - 4, box_z),
            self.world_to_screen(wx + 8, wy - 4, box_z),
            self.world_to_screen(wx + 8, wy + 4, box_z),
            self.world_to_screen(wx - 8, wy + 4, box_z),
        ]
        box_top = [
            self.world_to_screen(wx - 8, wy - 4, box_z + 30),
            self.world_to_screen(wx + 8, wy - 4, box_z + 30),
            self.world_to_screen(wx + 8, wy + 4, box_z + 30),
            self.world_to_screen(wx - 8, wy + 4, box_z + 30),
        ]
        
        pygame.draw.polygon(surface, (40, 42, 45), [box[0], box[1], box_top[1], box_top[0]])
        pygame.draw.polygon(surface, (35, 37, 40), [box[1], box[2], box_top[2], box_top[1]])
        pygame.draw.polygon(surface, (30, 32, 35), box_top)
        
        # Lights
        colors = {
            'red': [(255, 50, 50), (60, 30, 30), (60, 50, 30)],
            'yellow': [(60, 30, 30), (255, 220, 50), (60, 50, 30)],
            'green': [(60, 30, 30), (60, 50, 30), (50, 255, 50)],
        }
        
        light_colors = colors.get(state, colors['red'])
        
        for i, c in enumerate(light_colors):
            light_z = box_z + 25 - i * 9
            light_pos = self.world_to_screen(wx, wy - 4, light_z)
            pygame.draw.circle(surface, c, light_pos, 4)
            
    def draw_pedestrian(self, surface, wx, wy):
        """Draw a 3D pedestrian"""
        # Random appearance based on position
        shirt_colors = [(220, 50, 50), (50, 100, 220), (250, 200, 50), (50, 180, 50), (200, 100, 180)]
        shirt = shirt_colors[hash((int(wx), int(wy))) % len(shirt_colors)]
        
        # Shadow
        shadow = self.world_to_screen(wx + 2, wy + 2, 0)
        pygame.draw.ellipse(surface, (50, 50, 50), (shadow[0] - 5, shadow[1] - 3, 10, 6))
        
        # Legs
        leg1 = self.world_to_screen(wx - 2, wy, 0)
        leg1_top = self.world_to_screen(wx - 2, wy, 12)
        leg2 = self.world_to_screen(wx + 2, wy, 0)
        leg2_top = self.world_to_screen(wx + 2, wy, 12)
        pygame.draw.line(surface, (50, 50, 80), leg1, leg1_top, 3)
        pygame.draw.line(surface, (50, 50, 80), leg2, leg2_top, 3)
        
        # Body
        body_bottom = self.world_to_screen(wx, wy, 12)
        body_top = self.world_to_screen(wx, wy, 22)
        pygame.draw.line(surface, shirt, body_bottom, body_top, 6)
        
        # Head
        head_pos = self.world_to_screen(wx, wy, 26)
        pygame.draw.circle(surface, (220, 180, 150), head_pos, 5)
        
    def draw_emergency_station(self, surface, station_type, wx, wy, highlighted=False):
        """Draw emergency station building"""
        if station_type == 'hospital':
            color = (250, 250, 250)
            accent = (220, 50, 50)
        else:  # police
            color = (200, 200, 220)
            accent = (50, 50, 200)
        
        # Blinking highlight effect during emergencies
        if highlighted and int(time.time() * 4) % 2 == 0:
            # Bright red glow for hospital
            color = (255, 200, 200)
            accent = (255, 0, 0)
            
        # Building
        self._draw_3d_building(surface, wx, wy, 100, 80, 60, color)
        
        # Sign on top
        sign_pos = self.world_to_screen(wx + 50, wy, 65)
        if station_type == 'hospital':
            # Red cross
            cross_size = 16 if highlighted else 12
            pygame.draw.line(surface, accent, (sign_pos[0] - cross_size, sign_pos[1]), 
                           (sign_pos[0] + cross_size, sign_pos[1]), 6)
            pygame.draw.line(surface, accent, (sign_pos[0], sign_pos[1] - cross_size),
                           (sign_pos[0], sign_pos[1] + cross_size), 6)
            
            # Draw "🏥" indicator when highlighted
            if highlighted:
                font = pygame.font.Font(None, 36)
                text = font.render("🏥 RESPONDING", True, (255, 50, 50))
                surface.blit(text, (sign_pos[0] - 60, sign_pos[1] - 50))
        else:
            # Police star/badge
            pygame.draw.circle(surface, accent, sign_pos, 10)
            pygame.draw.circle(surface, (255, 220, 50), sign_pos, 6)
            
    def render(self, signal_states, vehicles, pedestrians=None, 
               show_emergency_stations=False, emergency_alerts=None,
               hospital_highlight=False):
        """Render complete scene"""
        # Start with static background
        surface = self.static_bg.copy()
        
        # Draw emergency stations if needed
        if show_emergency_stations:
            for station in self.ambulance_stations:
                is_highlighted = hospital_highlight  # Highlight all hospitals during accident
                self.draw_emergency_station(surface, 'hospital', station['x'], station['y'], is_highlighted)
            for station in self.police_stations:
                self.draw_emergency_station(surface, 'police', station['x'], station['y'], False)
        
        # Draw traffic signals
        signal_positions = {
            0: (-90, 90),   # West
            1: (90, -90),   # North
            2: (90, 90),    # East
            3: (-90, 90),   # South (actually same corner, different facing)
        }
        
        for lane, (sx, sy) in signal_positions.items():
            state = signal_states.get(lane, 'red')
            self.draw_traffic_signal(surface, sx, sy, state)
        
        # Collect all drawable entities for depth sorting
        entities = []
        
        # Add vehicles
        for v in vehicles:
            entities.append(('vehicle', v['wx'], v['wy'], v))
            
        # Add pedestrians
        if pedestrians:
            for p in pedestrians:
                entities.append(('pedestrian', p['wx'], p['wy'], p))
        
        # Sort by depth (wx + wy for isometric)
        entities.sort(key=lambda e: e[1] + e[2])
        
        # Draw entities
        for entity_type, wx, wy, data in entities:
            if entity_type == 'vehicle':
                self.draw_3d_vehicle(surface, wx, wy, 
                                    data['type'], data.get('color', (100, 100, 200)),
                                    data['direction'])
            elif entity_type == 'pedestrian':
                self.draw_pedestrian(surface, wx, wy)
        
        # Draw emergency alerts
        if emergency_alerts:
            self._draw_emergency_alerts(surface, emergency_alerts)
                
        return surface
        
    def _draw_emergency_alerts(self, surface, alerts):
        """Draw emergency alert indicators"""
        font = pygame.font.Font(None, 24)
        
        y_offset = 10
        for alert in alerts:
            text = font.render(f"🚨 {alert}", True, (255, 50, 50))
            surface.blit(text, (10, y_offset))
            y_offset += 25
