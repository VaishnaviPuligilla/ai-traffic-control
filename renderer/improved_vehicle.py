import pygame
import random
import math
from config import VEHICLE_TYPES, COLORS


class Vehicle:
    """Represents a vehicle in the simulation with realistic isometric graphics"""
    
    # Class-level car colors for variety
    CAR_COLORS = [
        (220, 50, 50),    # Red
        (50, 100, 220),   # Blue
        (250, 200, 50),   # Yellow
        (50, 180, 50),    # Green
        (180, 180, 180),  # Silver
        (40, 40, 40),     # Black
        (255, 255, 255),  # White
        (200, 100, 50),   # Orange
        (150, 50, 150),   # Purple
        (50, 150, 150),   # Teal
    ]
    
    TRUCK_COLORS = [
        (180, 50, 50),    # Red
        (50, 50, 180),    # Blue
        (200, 150, 50),   # Yellow/Orange
        (80, 80, 80),     # Gray
        (255, 255, 255),  # White
    ]
    
    BIKE_COLORS = [
        (220, 50, 50),    # Red
        (50, 50, 50),     # Black
        (50, 100, 200),   # Blue
        (200, 150, 50),   # Orange
        (50, 150, 50),    # Green
    ]
    
    def __init__(self, lane_id, sub_lane, v_type, x, y, direction):
        self.lane_id = lane_id
        self.sub_lane = sub_lane  # 0-3 for 4 sub-lanes
        self.type = v_type
        self.config = VEHICLE_TYPES.get(v_type, VEHICLE_TYPES['car'])
        
        self.x = x
        self.y = y
        self.direction = direction  # 'up', 'down', 'left', 'right'
        
        self.speed = self.config['speed']
        self.max_speed = self.config['speed']
        self.weight = self.config['weight']
        self.length = self.config['length']
        self.width = self.config['width']
        
        # Assign random color based on vehicle type
        if v_type == 'car':
            self.color = random.choice(self.CAR_COLORS)
        elif v_type == 'truck':
            self.color = random.choice(self.TRUCK_COLORS)
        elif v_type == 'bike':
            self.color = random.choice(self.BIKE_COLORS)
        elif v_type == 'ambulance':
            self.color = (255, 255, 255)
        else:
            self.color = self.config.get('color', (150, 150, 150))
        
        self.waiting = False
        self.wait_time = 0
        self.passed = False
        self.stopped_at_signal = False
        
        # For smooth movement
        self.target_speed = self.max_speed
        self.acceleration = 0.15
        self.deceleration = 0.25
        
        # Animation
        self.blink_timer = 0
        self.is_ambulance = (v_type == 'ambulance')
        self.is_pedestrian = (v_type == 'pedestrian')
        
        # Unique ID for tracking
        self.id = random.randint(10000, 99999)
        
    def update(self, can_move, dt):
        """Update vehicle position and state"""
        if can_move and not self.stopped_at_signal:
            # Accelerate towards max speed
            if self.speed < self.target_speed:
                self.speed = min(self.speed + self.acceleration, self.target_speed)
            
            # Move based on direction
            move_speed = self.speed * dt * 60  # Normalize to 60fps
            
            if self.direction == 'up':
                self.y -= move_speed
            elif self.direction == 'down':
                self.y += move_speed
            elif self.direction == 'left':
                self.x -= move_speed
            elif self.direction == 'right':
                self.x += move_speed
                
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
            
    def get_iso_position(self, renderer):
        """Get isometric screen position"""
        return renderer.cart_to_iso(self.x, self.y)
    
    def draw(self, screen, renderer):
        """Draw the vehicle using isometric renderer"""
        from renderer.isometric_renderer import IsometricVehicle
        
        iso_x, iso_y = renderer.cart_to_iso(self.x, self.y)
        
        if self.type == 'car':
            IsometricVehicle.draw_car(screen, iso_x, iso_y, self.color, self.direction)
        elif self.type == 'truck':
            IsometricVehicle.draw_truck(screen, iso_x, iso_y, self.color, self.direction)
        elif self.type == 'bike':
            IsometricVehicle.draw_bike(screen, iso_x, iso_y, self.color, self.direction)
        elif self.type == 'ambulance':
            blink = int(self.blink_timer * 4) % 2 == 0
            IsometricVehicle.draw_ambulance(screen, iso_x, iso_y, self.direction, blink)
        elif self.type == 'pedestrian':
            IsometricVehicle.draw_pedestrian(screen, iso_x, iso_y)
            
    def check_collision(self, other, min_gap=40):
        """Check if too close to another vehicle in same lane"""
        if self.lane_id != other.lane_id or self.sub_lane != other.sub_lane:
            return False
            
        dx = abs(self.x - other.x)
        dy = abs(self.y - other.y)
        
        if self.direction in ['up', 'down']:
            return dy < min_gap
        else:
            return dx < min_gap
            
    def is_ahead(self, other):
        """Check if other vehicle is ahead of this one"""
        if self.direction == 'up':
            return other.y < self.y
        elif self.direction == 'down':
            return other.y > self.y
        elif self.direction == 'left':
            return other.x < self.x
        else:  # right
            return other.x > self.x


class Pedestrian:
    """Represents a pedestrian"""
    
    def __init__(self, x, y, target_x, target_y, crossing_id):
        self.x = x
        self.y = y
        self.target_x = target_x
        self.target_y = target_y
        self.crossing_id = crossing_id
        self.speed = 1.5
        self.waiting = True
        self.wait_time = 0
        self.crossed = False
        
        # Random appearance
        self.shirt_color = (
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        )
        
    def update(self, can_cross, dt):
        """Update pedestrian position"""
        if can_cross and not self.crossed:
            self.waiting = False
            
            # Move towards target
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 2:
                self.x += (dx / dist) * self.speed
                self.y += (dy / dist) * self.speed
            else:
                self.crossed = True
        else:
            if not self.crossed:
                self.waiting = True
                self.wait_time += dt
                
    def draw(self, screen, renderer):
        """Draw pedestrian"""
        from renderer.isometric_renderer import IsometricVehicle
        iso_x, iso_y = renderer.cart_to_iso(self.x, self.y)
        IsometricVehicle.draw_pedestrian(screen, iso_x, iso_y)


class ImprovedVehicleManager:
    """Manages all vehicles with 4 sub-lanes per direction"""
    
    def __init__(self, num_lanes=4):
        self.num_lanes = num_lanes
        self.vehicles = {i: [] for i in range(num_lanes)}
        self.pedestrians = []
        self.passed_vehicles = []
        self.passed_pedestrians = []
        
        self.total_spawned = 0
        self.total_passed = 0
        
        # User's selected vehicle types to spawn
        self.allowed_vehicle_types = {'car', 'truck', 'bike'}
        
        # Lane configuration
        # Each lane has 4 sub-lanes (positions)
        self.sub_lane_offsets = [-37, -12, 12, 37]  # Offsets from lane center
        
    def set_allowed_vehicles(self, vehicle_types):
        """Set which vehicle types can spawn (based on user selection)"""
        self.allowed_vehicle_types = set(vehicle_types)
        
    def get_spawn_position(self, lane_id, sub_lane, lane_config):
        """Get spawn position for a vehicle in a specific sub-lane"""
        base_x, base_y = lane_config['spawn']
        direction = lane_config['direction']
        
        offset = self.sub_lane_offsets[sub_lane]
        
        if direction in ['up', 'down']:
            return base_x + offset, base_y
        else:
            return base_x, base_y + offset
            
    def spawn_vehicle(self, lane_id, sub_lane, v_type, lane_config):
        """Spawn a vehicle in a specific sub-lane"""
        x, y = self.get_spawn_position(lane_id, sub_lane, lane_config)
        direction = lane_config['direction']
        
        vehicle = Vehicle(lane_id, sub_lane, v_type, x, y, direction)
        self.vehicles[lane_id].append(vehicle)
        self.total_spawned += 1
        
        return vehicle
        
    def spawn_pedestrian(self, crossing_id, start_x, start_y, end_x, end_y):
        """Spawn a pedestrian at a crossing"""
        pedestrian = Pedestrian(start_x, start_y, end_x, end_y, crossing_id)
        self.pedestrians.append(pedestrian)
        return pedestrian
        
    def update(self, signals, dt, junction_bounds, renderer):
        """Update all vehicles and pedestrians"""
        for lane_id, lane_vehicles in self.vehicles.items():
            # Sort vehicles by position (front first)
            signal = signals.get(lane_id)
            is_green = signal and signal.state == 'green'
            
            for vehicle in lane_vehicles[:]:
                # Check if vehicle can move
                can_move = self._can_vehicle_move(vehicle, is_green, junction_bounds)
                
                # Check for vehicle ahead
                if can_move:
                    for other in lane_vehicles:
                        if other.id != vehicle.id and vehicle.check_collision(other, 50):
                            if vehicle.is_ahead(other):
                                continue
                            can_move = False
                            break
                
                vehicle.update(can_move, dt)
                
                # Remove if off screen
                if self._is_off_screen(vehicle):
                    lane_vehicles.remove(vehicle)
                    self.passed_vehicles.append(vehicle)
                    self.total_passed += 1
                    
        # Update pedestrians
        # Pedestrians can cross when all signals are red (pedestrian phase)
        pedestrian_can_cross = all(
            s.state == 'red' for s in signals.values()
        )
        
        for ped in self.pedestrians[:]:
            ped.update(pedestrian_can_cross, dt)
            if ped.crossed:
                self.pedestrians.remove(ped)
                self.passed_pedestrians.append(ped)
                
    def _can_vehicle_move(self, vehicle, is_green, junction_bounds):
        """Check if vehicle can move"""
        # Ambulances always move
        if vehicle.is_ambulance:
            return True
            
        # Check if near junction
        jx, jy, jw, jh = junction_bounds
        margin = 80
        
        near_junction = False
        stop_position = 0
        
        if vehicle.direction == 'down':
            stop_position = jy - margin
            near_junction = vehicle.y > stop_position - 50 and vehicle.y < jy + jh
        elif vehicle.direction == 'up':
            stop_position = jy + jh + margin
            near_junction = vehicle.y < stop_position + 50 and vehicle.y > jy
        elif vehicle.direction == 'right':
            stop_position = jx - margin
            near_junction = vehicle.x > stop_position - 50 and vehicle.x < jx + jw
        elif vehicle.direction == 'left':
            stop_position = jx + jw + margin
            near_junction = vehicle.x < stop_position + 50 and vehicle.x > jx
            
        if near_junction:
            vehicle.stopped_at_signal = not is_green
            return is_green
        else:
            vehicle.stopped_at_signal = False
            return True
            
    def _is_off_screen(self, vehicle, margin=100):
        """Check if vehicle left the visible area"""
        return (vehicle.x < -margin or vehicle.x > 700 or
                vehicle.y < -margin or vehicle.y > 700)
                
    def get_lane_stats(self, lane_id):
        """Get statistics for a lane"""
        vehicles = self.vehicles.get(lane_id, [])
        
        stats = {
            'count': len(vehicles),
            'waiting': sum(1 for v in vehicles if v.waiting),
            'total_wait_time': sum(v.wait_time for v in vehicles),
            'weight': sum(v.weight for v in vehicles),
            'by_type': {},
            'has_ambulance': any(v.is_ambulance for v in vehicles)
        }
        
        for v in vehicles:
            stats['by_type'][v.type] = stats['by_type'].get(v.type, 0) + 1
            
        return stats
        
    def get_total_stats(self):
        """Get total statistics"""
        total_vehicles = sum(len(v) for v in self.vehicles.values())
        total_waiting = sum(
            sum(1 for v in vlist if v.waiting)
            for vlist in self.vehicles.values()
        )
        total_weight = sum(
            sum(v.weight for v in vlist)
            for vlist in self.vehicles.values()
        )
        
        return {
            'total_vehicles': total_vehicles,
            'total_waiting': total_waiting,
            'total_weight': total_weight,
            'total_passed': self.total_passed,
            'pedestrians_waiting': sum(1 for p in self.pedestrians if p.waiting),
            'pedestrians_total': len(self.pedestrians)
        }
        
    def has_ambulance_in_lane(self, lane_id):
        """Check if lane has an ambulance"""
        return any(v.is_ambulance for v in self.vehicles.get(lane_id, []))
        
    def get_ambulance_lane(self):
        """Get lane ID with ambulance, or -1"""
        for lane_id, vehicles in self.vehicles.items():
            for v in vehicles:
                if v.is_ambulance and v.waiting:
                    return lane_id
        return -1
        
    def draw(self, screen, renderer):
        """Draw all vehicles and pedestrians"""
        # Collect all entities for depth sorting
        all_entities = []
        
        for lane_vehicles in self.vehicles.values():
            for vehicle in lane_vehicles:
                all_entities.append(('vehicle', vehicle))
                
        for ped in self.pedestrians:
            all_entities.append(('pedestrian', ped))
            
        # Sort by y position for proper depth (isometric)
        all_entities.sort(key=lambda e: e[1].y)
        
        for entity_type, entity in all_entities:
            entity.draw(screen, renderer)
