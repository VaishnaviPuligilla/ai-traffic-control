import pygame
import sys
import random
import time
import os
import numpy as np

from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS, COLORS,
    VEHICLE_TYPES, RL_CONFIG, SIGNAL_CONFIG
)
from renderer.isometric_city import IsometricCity
from signal_controller import SignalController
from ai.agent import DQNAgent
from database.db_manager import DatabaseManager
from ui.clean_dashboard import CleanDashboard, VehicleSelector, ControlPanel


class Vehicle:
    """Simple vehicle class for the simulation"""
    
    CAR_COLORS = [(220, 50, 50), (50, 100, 220), (250, 200, 50), (50, 180, 50), 
                  (180, 180, 180), (40, 40, 40), (255, 255, 255), (200, 100, 50)]
    TRUCK_COLORS = [(180, 50, 50), (50, 50, 180), (200, 150, 50), (80, 80, 80), (255, 255, 255)]
    BIKE_COLORS = [(220, 50, 50), (50, 50, 50), (50, 100, 200), (200, 150, 50)]
    
    def __init__(self, lane, vehicle_type, sub_lane=0):
        self.lane = lane
        self.vehicle_type = vehicle_type
        self.sub_lane = sub_lane
        
        # Assign color
        if vehicle_type == 'car':
            self.color = random.choice(self.CAR_COLORS)
        elif vehicle_type == 'truck':
            self.color = random.choice(self.TRUCK_COLORS)
        elif vehicle_type == 'bike':
            self.color = random.choice(self.BIKE_COLORS)
        else:
            self.color = (255, 255, 255)
            
        # Position
        self.x = 0
        self.y = 0
        self.direction = 0  # 0=left, 1=up, 2=right, 3=down
        
        # State
        self.waiting = False
        self.wait_time = 0
        self.passed = False
        self.speed = VEHICLE_TYPES[vehicle_type]['speed']
        
    def update(self, dt, can_move):
        """Update vehicle position"""
        if can_move:
            move_amt = self.speed * dt * 80  # Increased speed multiplier
            if self.direction == 0:  # Left (moving right)
                self.x += move_amt
            elif self.direction == 1:  # Top (moving down)
                self.y += move_amt
            elif self.direction == 2:  # Right (moving left)
                self.x -= move_amt
            elif self.direction == 3:  # Bottom (moving up)
                self.y -= move_amt
            self.waiting = False
        else:
            self.waiting = True
            self.wait_time += dt
            
    def is_off_screen(self, width, height):
        """Check if vehicle left the screen"""
        margin = 100
        return (self.x < -margin or self.x > width + margin or
                self.y < -margin or self.y > height + margin)
                
    def get_data(self):
        """Get data dict for renderer"""
        return {
            'x': self.x,
            'y': self.y,
            'type': self.vehicle_type,
            'color': self.color,
            'direction': self.direction
        }


class Pedestrian:
    """Simple pedestrian class"""
    
    def __init__(self, waiting_for_lane):
        self.x = 0
        self.y = 0
        self.waiting_for_lane = waiting_for_lane
        self.crossed = False


class TrafficSimulation:
    """Main simulation with isometric city view"""
    
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🚦 AI Traffic Signal Simulation")
        
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        
        # Layout
        self.sim_width = 1080
        self.sim_height = WINDOW_HEIGHT
        self.dashboard_x = self.sim_width
        
        # Junction center
        self.cx = self.sim_width // 2
        self.cy = self.sim_height // 2
        self.road_width = 200
        
        # Components
        self.renderer = IsometricCity(self.sim_width, self.sim_height)
        self.signal_controller = SignalController(num_lanes=4)
        
        # AI
        self.agent = DQNAgent(state_size=13, action_size=36)
        self.db_manager = DatabaseManager()
        
        # Try load model
        try:
            self.agent.load("models/traffic_agent.pth")
            print("✅ Loaded trained model")
        except:
            print("ℹ️ Starting fresh")
            
        # UI
        self.dashboard = CleanDashboard(
            self.dashboard_x + 10, 10,
            WINDOW_WIDTH - self.dashboard_x - 20, 500
        )
        self.vehicle_selector = VehicleSelector(
            self.dashboard_x + 10, 520,
            WINDOW_WIDTH - self.dashboard_x - 20
        )
        self.control_panel = ControlPanel(
            self.dashboard_x + 10, 700,
            WINDOW_WIDTH - self.dashboard_x - 20
        )
        
        # Vehicles & pedestrians
        self.vehicles = []
        self.pedestrians = []
        self.total_passed = 0
        
        # State
        self.state = 'config'  # 'config', 'simulation', 'paused'
        self.simulation_time = 0
        self.last_spawn_time = 0
        self.spawn_interval = 0.8  # Spawn more frequently
        
        # Selected vehicle types
        self.allowed_types = ['truck', 'car', 'bike']
        
        # Ambulance tracking
        self.ambulance_active = False
        
        # Sub-lane offsets for 4 horizontal positions per lane
        self.sub_lane_offsets = [-60, -20, 20, 60]
        
        # Lane spawn/stop positions
        self._setup_lane_config()
        
        # Session
        self.session_id = self.db_manager.start_session(num_lanes=4)
        
    def _setup_lane_config(self):
        """Setup lane spawn positions and stop lines"""
        cx, cy = self.cx, self.cy
        rw = self.road_width
        
        # Lane config: direction=0 is left approach, 1=top, 2=right, 3=bottom
        # Vehicles spawn off-screen and move toward intersection
        self.lane_config = {
            0: {  # Left approach (vehicles go right toward center)
                'spawn_x': -80,
                'spawn_y': cy + 45,  # Bottom lanes (going right)
                'stop_x': cx - rw // 2 - 50,
                'direction': 0,
            },
            1: {  # Top approach (vehicles go down toward center)
                'spawn_x': cx + 45,  # Right lanes (going down)
                'spawn_y': -80,
                'stop_y': cy - rw // 2 - 50,
                'direction': 1,
            },
            2: {  # Right approach (vehicles go left toward center)
                'spawn_x': self.sim_width + 80,
                'spawn_y': cy - 45,  # Top lanes (going left)
                'stop_x': cx + rw // 2 + 50,
                'direction': 2,
            },
            3: {  # Bottom approach (vehicles go up toward center)
                'spawn_x': cx - 45,  # Left lanes (going up)
                'spawn_y': self.sim_height + 80,
                'stop_y': cy + rw // 2 + 50,
                'direction': 3,
            }
        }
        
    def run(self):
        """Main game loop"""
        running = True
        last_time = time.time()
        
        while running:
            current_time = time.time()
            dt = min(current_time - last_time, 0.1)  # Cap dt
            last_time = current_time
            
            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self._handle_event(event)
                
            # Update
            if self.state == 'simulation':
                self._update(dt)
                
            # Render
            self._render()
            
            self.clock.tick(FPS)
            
        self._cleanup()
        
    def _handle_event(self, event):
        """Handle input events"""
        self.vehicle_selector.handle_event(event)
        
        action = self.control_panel.handle_event(event)
        if action:
            self._handle_control(action)
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.state == 'config':
                    self._start_simulation()
                elif self.state == 'simulation':
                    self.state = 'paused'
                    self.control_panel.set_pause_text(True)
                elif self.state == 'paused':
                    self.state = 'simulation'
                    self.control_panel.set_pause_text(False)
            elif event.key == pygame.K_ESCAPE:
                pygame.event.post(pygame.event.Event(pygame.QUIT))
                
    def _handle_control(self, action):
        """Handle control panel actions"""
        if action == 'pause':
            if self.state == 'simulation':
                self.state = 'paused'
                self.control_panel.set_pause_text(True)
            elif self.state == 'paused':
                self.state = 'simulation'
                self.control_panel.set_pause_text(False)
        elif action == 'ambulance':
            if self.state in ('simulation', 'paused') and not self.ambulance_active:
                self._spawn_ambulance()
        elif action == 'accident':
            if self.state in ('simulation', 'paused'):
                self._toggle_accident()
        elif action == 'pedestrian':
            if self.state in ('simulation', 'paused'):
                self._spawn_pedestrians()
                
    def _start_simulation(self):
        """Start the simulation"""
        self.allowed_types = self.vehicle_selector.get_selected()
        if not self.allowed_types:
            self.allowed_types = ['car']
        self.state = 'simulation'
        print(f"🚦 Started with vehicles: {self.allowed_types}")
        
    def _update(self, dt):
        """Update simulation"""
        self.simulation_time += dt
        
        # Update signal
        self.signal_controller.update(dt)
        
        # AI decision when timer expires
        if self.signal_controller.time_remaining <= 0 and not self.signal_controller.emergency_mode:
            self._make_ai_decision()
            
        # Spawn vehicles
        if self.simulation_time - self.last_spawn_time > self.spawn_interval:
            self._spawn_vehicles()
            self.last_spawn_time = self.simulation_time
            
        # Update vehicles
        self._update_vehicles(dt)
        
        # Check ambulance cleared
        if self.ambulance_active:
            has_ambulance = any(v.vehicle_type == 'ambulance' for v in self.vehicles)
            if not has_ambulance:
                self.signal_controller.emergency_cleared()
                self.ambulance_active = False
                print("🚑 Ambulance cleared - resuming previous lane")
                
        # Update pedestrians
        self._update_pedestrians(dt)
        
    def _make_ai_decision(self):
        """AI selects next lane and duration"""
        state = self._build_state()
        action = self.agent.select_action(state, training=False)
        
        lane = action // 9
        duration_idx = action % 9
        duration = 4 + duration_idx * 10  # 4 to 84 seconds
        
        self.signal_controller.set_green(lane, duration)
        
        self.db_manager.log_decision(
            self.session_id, state.tolist(), action, lane, duration
        )
        
    def _build_state(self):
        """Build state vector for AI"""
        lane_stats = self._get_lane_stats()
        
        # Lane weights normalized
        weights = [lane_stats.get(i, {}).get('weight', 0) / 20.0 for i in range(4)]
        
        # One-hot current green
        current = [0, 0, 0, 0]
        current[self.signal_controller.current_green] = 1
        
        # Time elapsed
        time_elapsed = (90 - self.signal_controller.time_remaining) / 90.0
        
        # Pedestrians
        total_peds = len([p for p in self.pedestrians if not p.crossed]) / 10.0
        
        # Emergency flags
        emergency = 1.0 if self.signal_controller.emergency_mode else 0.0
        accident = 1.0 if self.signal_controller.accident_mode else 0.0
        
        return np.array(weights + current + [time_elapsed, total_peds, emergency, accident], dtype=np.float32)
        
    def _get_lane_stats(self):
        """Get stats per lane"""
        stats = {}
        for lane in range(4):
            lane_vehicles = [v for v in self.vehicles if v.lane == lane and v.waiting]
            by_type = {}
            weight = 0
            for v in lane_vehicles:
                by_type[v.vehicle_type] = by_type.get(v.vehicle_type, 0) + 1
                weight += VEHICLE_TYPES[v.vehicle_type]['weight']
            stats[lane] = {'count': len(lane_vehicles), 'by_type': by_type, 'weight': weight}
        return stats
        
    def _spawn_vehicles(self):
        """Spawn vehicles in random lane"""
        # Spawn multiple vehicles at once for better traffic
        for _ in range(random.randint(1, 3)):
            lane = random.randint(0, 3)
            
            if self.signal_controller.is_lane_blocked(lane):
                continue
                
            if not self.allowed_types:
                continue
                
            v_type = random.choice(self.allowed_types)
            sub_lane = random.randint(0, 1)  # 2 sub-lanes per direction
            
            vehicle = Vehicle(lane, v_type, sub_lane)
            
            cfg = self.lane_config[lane]
            
            # Position based on lane and sub-lane
            # Sub-lanes are offset from the lane center
            sub_offset = [-25, 25][sub_lane]  # Two lanes per direction
            
            if lane == 0:  # Left (going right)
                vehicle.x = cfg['spawn_x'] - random.randint(0, 150)
                vehicle.y = cfg['spawn_y'] + sub_offset
            elif lane == 1:  # Top (going down)
                vehicle.x = cfg['spawn_x'] + sub_offset
                vehicle.y = cfg['spawn_y'] - random.randint(0, 150)
            elif lane == 2:  # Right (going left)
                vehicle.x = cfg['spawn_x'] + random.randint(0, 150)
                vehicle.y = cfg['spawn_y'] + sub_offset
            elif lane == 3:  # Bottom (going up)
                vehicle.x = cfg['spawn_x'] + sub_offset
                vehicle.y = cfg['spawn_y'] + random.randint(0, 150)
                
            vehicle.direction = cfg['direction']
            
            self.vehicles.append(vehicle)
        
    def _spawn_ambulance(self):
        """Spawn ambulance"""
        lane = random.randint(0, 3)
        sub_lane = random.randint(0, 1)
        
        vehicle = Vehicle(lane, 'ambulance', sub_lane)
        cfg = self.lane_config[lane]
        
        sub_offset = [-25, 25][sub_lane]
        
        if lane == 0:
            vehicle.x = cfg['spawn_x']
            vehicle.y = cfg['spawn_y'] + sub_offset
        elif lane == 1:
            vehicle.x = cfg['spawn_x'] + sub_offset
            vehicle.y = cfg['spawn_y']
        elif lane == 2:
            vehicle.x = cfg['spawn_x']
            vehicle.y = cfg['spawn_y'] + sub_offset
        elif lane == 3:
            vehicle.x = cfg['spawn_x'] + sub_offset
            vehicle.y = cfg['spawn_y']
            
        vehicle.direction = cfg['direction']
        
        self.vehicles.append(vehicle)
        self.ambulance_active = True
        
        self.signal_controller.trigger_emergency(lane)
        self.db_manager.log_event(self.session_id, 'emergency', {'lane': lane})
        
    def _toggle_accident(self):
        """Toggle accident"""
        if self.signal_controller.accident_mode:
            self.signal_controller.clear_accident()
        else:
            lane = random.randint(0, 3)
            self.signal_controller.trigger_accident(lane)
            self.db_manager.log_event(self.session_id, 'accident', {'lane': lane})
            
    def _spawn_pedestrians(self):
        """Spawn pedestrians"""
        for _ in range(random.randint(2, 5)):
            lane = random.randint(0, 3)
            ped = Pedestrian(lane)
            ped.x = self.cx + random.randint(-100, 100)
            ped.y = self.cy + random.randint(-100, 100)
            self.pedestrians.append(ped)
            
    def _update_vehicles(self, dt):
        """Update all vehicles"""
        current_green = self.signal_controller.current_green
        
        for vehicle in self.vehicles[:]:
            can_move = self._can_vehicle_move(vehicle, current_green)
            vehicle.update(dt, can_move)
            
            if vehicle.is_off_screen(self.sim_width, self.sim_height):
                self.vehicles.remove(vehicle)
                self.total_passed += 1
                
    def _can_vehicle_move(self, vehicle, green_lane):
        """Check if vehicle can move"""
        # Ambulance always moves
        if vehicle.vehicle_type == 'ambulance':
            return True
            
        cfg = self.lane_config[vehicle.lane]
        cx, cy = self.cx, self.cy
        rw = self.road_width
        
        # Check distance to intersection
        at_stop = False
        
        if vehicle.direction == 0:  # Going right
            stop_line = cx - rw // 2 - 50
            at_stop = vehicle.x >= stop_line - 60 and vehicle.x < stop_line + 20
        elif vehicle.direction == 1:  # Going down
            stop_line = cy - rw // 2 - 50
            at_stop = vehicle.y >= stop_line - 60 and vehicle.y < stop_line + 20
        elif vehicle.direction == 2:  # Going left
            stop_line = cx + rw // 2 + 50
            at_stop = vehicle.x <= stop_line + 60 and vehicle.x > stop_line - 20
        elif vehicle.direction == 3:  # Going up
            stop_line = cy + rw // 2 + 50
            at_stop = vehicle.y <= stop_line + 60 and vehicle.y > stop_line - 20
            
        if at_stop:
            return vehicle.lane == green_lane
        return True
        
    def _update_pedestrians(self, dt):
        """Update pedestrians"""
        green = self.signal_controller.current_green
        for ped in self.pedestrians[:]:
            if ped.waiting_for_lane == green:
                ped.crossed = True
                self.pedestrians.remove(ped)
                
    def _render(self):
        """Render everything"""
        self.screen.fill((20, 25, 35))
        
        # Get signal states
        green = self.signal_controller.current_green
        states = {i: 'green' if i == green else 'red' for i in range(4)}
        
        # Get vehicle data
        vehicle_data = [v.get_data() for v in self.vehicles]
        
        # Get pedestrian data
        ped_data = [{'x': p.x, 'y': p.y, 'waiting': not p.crossed} for p in self.pedestrians]
        
        # Draw scene
        scene = self.renderer.draw_scene(states, vehicle_data, ped_data)
        self.screen.blit(scene, (0, 0))
        
        # Update and draw dashboard
        lane_stats = self._get_lane_stats()
        self.dashboard.update({
            'current_green': green,
            'time_remaining': self.signal_controller.time_remaining,
            'next_lane': self.signal_controller.next_predicted_lane,
            'lane_stats': lane_stats,
            'emergency_active': self.signal_controller.emergency_mode,
            'emergency_lane': self.signal_controller.emergency_lane,
            'accident_active': self.signal_controller.accident_mode,
            'accident_lane': self.signal_controller.accident_lane,
            'pedestrians_waiting': len(self.pedestrians),
            'total_stats': {
                'total_vehicles': len(self.vehicles),
                'total_passed': self.total_passed,
                'total_waiting': sum(1 for v in self.vehicles if v.waiting)
            }
        })
        self.dashboard.draw(self.screen)
        
        # Draw selectors and controls
        self.vehicle_selector.draw(self.screen)
        self.control_panel.draw(self.screen)
        
        # State indicator
        self._draw_state_indicator()
        
        pygame.display.flip()
        
    def _draw_state_indicator(self):
        """Draw state text"""
        font = pygame.font.Font(None, 28)
        
        if self.state == 'config':
            text = "Press SPACE to Start"
            color = (100, 200, 100)
        elif self.state == 'paused':
            text = "⏸️ PAUSED - Press SPACE to Resume"
            color = (255, 200, 100)
        else:
            text = f"Running: {int(self.simulation_time)}s"
            color = (150, 200, 255)
            
        rendered = font.render(text, True, color)
        self.screen.blit(rendered, (self.dashboard_x + 15, WINDOW_HEIGHT - 45))
        
    def _cleanup(self):
        """Cleanup"""
        os.makedirs("models", exist_ok=True)
        self.agent.save("models/traffic_agent.pth")
        self.db_manager.end_session(self.session_id)
        pygame.quit()


def main():
    sim = TrafficSimulation()
    sim.run()


if __name__ == "__main__":
    main()
