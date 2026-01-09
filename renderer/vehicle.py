import pygame
import random
import math
from config import VEHICLE_TYPES, COLORS

class Vehicle:
    """Represents a vehicle in the simulation"""
    
    def __init__(self, lane_id, v_type, x, y, direction):
        self.lane_id = lane_id
        self.type = v_type
        self.config = VEHICLE_TYPES[v_type]
        
        self.x = x
        self.y = y
        self.direction = direction  # 'up', 'down', 'left', 'right'
        
        self.speed = self.config['speed']
        self.max_speed = self.config['speed']
        self.weight = self.config['weight']
        self.length = self.config['length']
        self.width = self.config['width']
        self.color = self.config['color']
        
        self.waiting = False
        self.wait_time = 0
        self.passed = False
        self.stopped_at_signal = False
        
        # For smooth movement
        self.target_speed = self.max_speed
        self.acceleration = 0.1
        self.deceleration = 0.2
        
        # Generate unique color variation for cars
        if v_type == 'car':
            self.color = self._random_car_color()
        
        # Animation properties
        self.blink_timer = 0
        self.is_ambulance = (v_type == 'ambulance')
        
    def _random_car_color(self):
        """Generate random car colors for variety"""
        car_colors = [
            (65, 105, 225),   # Royal Blue
            (220, 20, 60),    # Crimson
            (34, 139, 34),    # Forest Green
            (148, 0, 211),    # Dark Violet
            (255, 215, 0),    # Gold
            (70, 130, 180),   # Steel Blue
            (199, 21, 133),   # Medium Violet Red
            (0, 128, 128),    # Teal
            (128, 128, 128),  # Gray
            (25, 25, 112),    # Midnight Blue
        ]
        return random.choice(car_colors)
    
    def update(self, can_move, dt):
        """Update vehicle position and state"""
        if can_move and not self.stopped_at_signal:
            # Accelerate towards max speed
            if self.speed < self.target_speed:
                self.speed = min(self.speed + self.acceleration, self.target_speed)
            
            # Move based on direction
            if self.direction == 'up':
                self.y -= self.speed
            elif self.direction == 'down':
                self.y += self.speed
            elif self.direction == 'left':
                self.x -= self.speed
            elif self.direction == 'right':
                self.x += self.speed
                
            self.waiting = False
        else:
            # Decelerate to stop
            self.speed = max(0, self.speed - self.deceleration)
            if self.speed == 0:
                self.waiting = True
                self.wait_time += dt
        
        # Ambulance light animation
        if self.is_ambulance:
            self.blink_timer += dt
            
    def draw(self, screen, view_mode='top_down'):
        """Draw the vehicle on screen"""
        if view_mode == 'top_down':
            self._draw_top_down(screen)
        elif view_mode == 'isometric':
            self._draw_isometric(screen)
        else:
            self._draw_top_down(screen)
            
    def _draw_top_down(self, screen):
        """Draw vehicle from top-down view"""
        # Calculate rectangle based on direction
        if self.direction in ['up', 'down']:
            rect = pygame.Rect(
                self.x - self.width // 2,
                self.y - self.length // 2,
                self.width,
                self.length
            )
        else:
            rect = pygame.Rect(
                self.x - self.length // 2,
                self.y - self.width // 2,
                self.length,
                self.width
            )
        
        # Draw vehicle body
        pygame.draw.rect(screen, self.color, rect, border_radius=5)
        pygame.draw.rect(screen, COLORS['dark_gray'], rect, 2, border_radius=5)
        
        # Draw vehicle-specific details
        if self.type == 'truck':
            self._draw_truck_details(screen, rect)
        elif self.type == 'ambulance':
            self._draw_ambulance_details(screen, rect)
        elif self.type == 'bike':
            self._draw_bike_details(screen, rect)
        elif self.type == 'pedestrian':
            self._draw_pedestrian(screen)
            
    def _draw_truck_details(self, screen, rect):
        """Draw truck cabin"""
        cabin_color = (100, 50, 20)
        if self.direction in ['up', 'down']:
            cabin_h = rect.height // 4
            if self.direction == 'up':
                cabin_rect = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, cabin_h)
            else:
                cabin_rect = pygame.Rect(rect.x + 2, rect.bottom - cabin_h - 2, rect.width - 4, cabin_h)
        else:
            cabin_w = rect.width // 4
            if self.direction == 'left':
                cabin_rect = pygame.Rect(rect.x + 2, rect.y + 2, cabin_w, rect.height - 4)
            else:
                cabin_rect = pygame.Rect(rect.right - cabin_w - 2, rect.y + 2, cabin_w, rect.height - 4)
        pygame.draw.rect(screen, cabin_color, cabin_rect, border_radius=2)
        
    def _draw_ambulance_details(self, screen, rect):
        """Draw ambulance cross and lights"""
        # Draw red cross
        cross_color = COLORS['red']
        cx, cy = rect.centerx, rect.centery
        cross_size = min(rect.width, rect.height) // 3
        
        # Horizontal bar
        pygame.draw.rect(screen, cross_color, 
                        (cx - cross_size, cy - cross_size//3, cross_size*2, cross_size//1.5))
        # Vertical bar
        pygame.draw.rect(screen, cross_color,
                        (cx - cross_size//3, cy - cross_size, cross_size//1.5, cross_size*2))
        
        # Blinking lights
        if int(self.blink_timer * 4) % 2 == 0:
            light_color = COLORS['red']
        else:
            light_color = COLORS['blue']
        
        # Draw lights at corners
        light_radius = 4
        pygame.draw.circle(screen, light_color, (rect.x + 5, rect.y + 5), light_radius)
        pygame.draw.circle(screen, light_color, (rect.right - 5, rect.y + 5), light_radius)
        
    def _draw_bike_details(self, screen, rect):
        """Draw motorcycle details"""
        # Draw wheels
        wheel_color = COLORS['black']
        if self.direction in ['up', 'down']:
            pygame.draw.circle(screen, wheel_color, (rect.centerx, rect.y + 5), 4)
            pygame.draw.circle(screen, wheel_color, (rect.centerx, rect.bottom - 5), 4)
        else:
            pygame.draw.circle(screen, wheel_color, (rect.x + 5, rect.centery), 4)
            pygame.draw.circle(screen, wheel_color, (rect.right - 5, rect.centery), 4)
            
    def _draw_pedestrian(self, screen):
        """Draw pedestrian as a circle"""
        pygame.draw.circle(screen, self.config['color'], (int(self.x), int(self.y)), 8)
        pygame.draw.circle(screen, COLORS['black'], (int(self.x), int(self.y)), 8, 2)
        # Draw head
        pygame.draw.circle(screen, (255, 220, 180), (int(self.x), int(self.y) - 5), 4)
        
    def _draw_isometric(self, screen):
        """Draw vehicle in isometric 2.5D view"""
        # Convert coordinates to isometric
        iso_x = self.x - self.y
        iso_y = (self.x + self.y) / 2
        
        # Draw shadow
        shadow_offset = 5
        pygame.draw.ellipse(screen, (30, 30, 30, 100),
                          (iso_x - self.width//2, iso_y + shadow_offset,
                           self.width, self.length//2))
        
        # Draw vehicle body (simplified 3D box)
        height_3d = 15
        
        # Top surface
        points_top = [
            (iso_x - self.width//2, iso_y - height_3d),
            (iso_x + self.width//2, iso_y - height_3d),
            (iso_x + self.width//2, iso_y + self.length//2 - height_3d),
            (iso_x - self.width//2, iso_y + self.length//2 - height_3d)
        ]
        pygame.draw.polygon(screen, self.color, points_top)
        pygame.draw.polygon(screen, COLORS['black'], points_top, 2)
        
        # Side surface
        points_side = [
            (iso_x + self.width//2, iso_y - height_3d),
            (iso_x + self.width//2, iso_y),
            (iso_x + self.width//2, iso_y + self.length//2),
            (iso_x + self.width//2, iso_y + self.length//2 - height_3d)
        ]
        darker_color = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.polygon(screen, darker_color, points_side)
        pygame.draw.polygon(screen, COLORS['black'], points_side, 2)
        
    def get_rect(self):
        """Get bounding rectangle for collision detection"""
        if self.direction in ['up', 'down']:
            return pygame.Rect(
                self.x - self.width // 2,
                self.y - self.length // 2,
                self.width,
                self.length
            )
        else:
            return pygame.Rect(
                self.x - self.length // 2,
                self.y - self.width // 2,
                self.length,
                self.width
            )
    
    def check_collision(self, other_vehicle, min_distance=20):
        """Check if too close to another vehicle"""
        dx = self.x - other_vehicle.x
        dy = self.y - other_vehicle.y
        distance = math.sqrt(dx*dx + dy*dy)
        safe_distance = (self.length + other_vehicle.length) / 2 + min_distance
        return distance < safe_distance


class VehicleManager:
    """Manages all vehicles in the simulation"""
    
    def __init__(self):
        self.vehicles = {i: [] for i in range(6)}  # Support up to 6 lanes
        self.passed_vehicles = []
        self.total_spawned = 0
        self.total_passed = 0
        
    def spawn_vehicle(self, lane_id, v_type, x, y, direction):
        """Spawn a new vehicle in the specified lane"""
        vehicle = Vehicle(lane_id, v_type, x, y, direction)
        self.vehicles[lane_id].append(vehicle)
        self.total_spawned += 1
        return vehicle
    
    def update(self, signals, dt, junction_bounds):
        """Update all vehicles"""
        for lane_id, lane_vehicles in self.vehicles.items():
            for vehicle in lane_vehicles[:]:  # Copy list for safe removal
                # Check if vehicle can move based on signal
                can_move = self._can_vehicle_move(vehicle, signals, junction_bounds)
                
                # Check collision with vehicle ahead
                if can_move:
                    can_move = self._check_vehicle_ahead(vehicle, lane_vehicles)
                
                vehicle.update(can_move, dt)
                
                # Remove vehicles that have left the screen
                if self._is_off_screen(vehicle):
                    lane_vehicles.remove(vehicle)
                    self.passed_vehicles.append(vehicle)
                    self.total_passed += 1
                    
    def _can_vehicle_move(self, vehicle, signals, junction_bounds):
        """Check if vehicle can move based on signal state"""
        # Ambulances always have priority
        if vehicle.is_ambulance:
            return True
            
        # Check if vehicle is approaching junction
        if not self._is_near_junction(vehicle, junction_bounds):
            vehicle.stopped_at_signal = False
            return True
            
        # Check signal for this lane
        signal = signals.get(vehicle.lane_id)
        if signal and signal.state == 'green':
            vehicle.stopped_at_signal = False
            return True
        else:
            vehicle.stopped_at_signal = True
            return False
            
    def _check_vehicle_ahead(self, vehicle, lane_vehicles):
        """Check if there's a vehicle ahead blocking movement"""
        for other in lane_vehicles:
            if other is vehicle:
                continue
            if vehicle.check_collision(other, min_distance=30):
                # Check if other vehicle is ahead
                if vehicle.direction == 'up' and other.y < vehicle.y:
                    return False
                elif vehicle.direction == 'down' and other.y > vehicle.y:
                    return False
                elif vehicle.direction == 'left' and other.x < vehicle.x:
                    return False
                elif vehicle.direction == 'right' and other.x > vehicle.x:
                    return False
        return True
    
    def _is_near_junction(self, vehicle, junction_bounds):
        """Check if vehicle is near the junction"""
        margin = 100
        jx, jy, jw, jh = junction_bounds
        
        if vehicle.direction == 'up':
            return vehicle.y > jy and vehicle.y < jy + jh + margin
        elif vehicle.direction == 'down':
            return vehicle.y < jy + jh and vehicle.y > jy - margin
        elif vehicle.direction == 'left':
            return vehicle.x > jx and vehicle.x < jx + jw + margin
        elif vehicle.direction == 'right':
            return vehicle.x < jx + jw and vehicle.x > jx - margin
        return False
    
    def _is_off_screen(self, vehicle, margin=100):
        """Check if vehicle has left the visible area"""
        from config import WINDOW_WIDTH, WINDOW_HEIGHT
        return (vehicle.x < -margin or vehicle.x > WINDOW_WIDTH + margin or
                vehicle.y < -margin or vehicle.y > WINDOW_HEIGHT + margin)
    
    def get_lane_stats(self, lane_id):
        """Get statistics for a specific lane"""
        vehicles = self.vehicles.get(lane_id, [])
        stats = {
            'count': len(vehicles),
            'waiting': sum(1 for v in vehicles if v.waiting),
            'total_wait_time': sum(v.wait_time for v in vehicles),
            'weight': sum(v.weight for v in vehicles),
            'by_type': {}
        }
        
        for v in vehicles:
            stats['by_type'][v.type] = stats['by_type'].get(v.type, 0) + 1
            
        return stats
    
    def get_total_waiting_time(self):
        """Get total waiting time across all vehicles"""
        total = 0
        for lane_vehicles in self.vehicles.values():
            total += sum(v.wait_time for v in lane_vehicles)
        return total
    
    def has_emergency(self):
        """Check if any ambulance is waiting"""
        for lane_id, vehicles in self.vehicles.items():
            for v in vehicles:
                if v.is_ambulance and v.waiting:
                    return lane_id
        return -1
    
    def draw(self, screen, view_mode='top_down'):
        """Draw all vehicles"""
        for lane_vehicles in self.vehicles.values():
            for vehicle in lane_vehicles:
                vehicle.draw(screen, view_mode)
