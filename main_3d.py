import pygame
import sys
import time
import random
import math
from collections import deque

# Initialize pygame
pygame.init()
pygame.font.init()

# Import our components
from renderer.isometric_3d import Isometric3DCity
from ai.agent import DQNAgent
from ai.environment import TrafficEnvironment
from database.db_manager import DatabaseManager
from config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FPS,
    SIGNAL_CONFIG, VEHICLE_TYPES
)


class TrafficSimulation3D:
    """Main simulation with 3D isometric view"""
    
    def __init__(self):
        # Display setup
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("AI Traffic Signal Control - 3D Isometric View")
        self.clock = pygame.time.Clock()
        
        # Initialize 3D renderer
        self.renderer = Isometric3DCity(WINDOW_WIDTH - 350, WINDOW_HEIGHT)
        
        # Initialize RL components
        self.env = TrafficEnvironment()
        self.agent = DQNAgent(state_size=13, action_size=36)
        self.db = DatabaseManager()
        
        # Try to load trained model
        try:
            self.agent.load("models/traffic_agent.pth")
            print("✅ Loaded trained model")
        except:
            print("⚠️ No saved model found, using random actions")
        
        # Simulation state
        self.running = True
        self.paused = False
        
        # Vehicles list with world coordinates
        self.vehicles = []
        self.vehicle_id_counter = 0
        
        # Emergency vehicles
        self.ambulances = []
        self.police_cars = []
        
        # Pedestrians with crosswalk walking
        self.pedestrians = []
        self.last_pedestrian_spawn = time.time()
        self.pedestrian_spawn_interval = 3.0  # Every 3 seconds
        
        # Crosswalk definitions (start_x, start_y, end_x, end_y, direction)
        self.crosswalks = [
            {'start_x': -130, 'start_y': -80, 'end_x': -130, 'end_y': 80, 'dir': 'vertical'},   # West crosswalk
            {'start_x': 130, 'start_y': -80, 'end_x': 130, 'end_y': 80, 'dir': 'vertical'},     # East crosswalk
            {'start_x': -80, 'start_y': -130, 'end_x': 80, 'end_y': -130, 'dir': 'horizontal'}, # North crosswalk
            {'start_x': -80, 'start_y': 130, 'end_x': 80, 'end_y': 130, 'dir': 'horizontal'},   # South crosswalk
        ]
        
        # Emergency alerts
        self.emergency_alerts = []
        
        # Lane configuration with world coordinates
        # Lane 0: West (coming from left, going east)
        # Lane 1: North (coming from top, going south)
        # Lane 2: East (coming from right, going west)
        # Lane 3: South (coming from bottom, going north)
        self.lane_config = {
            0: {
                'start_x': -450, 'start_y': 35,
                'direction': 0,  # East
                'dx': 1, 'dy': 0,
                'stop_line': -100,
                'exit_line': 450,
                'lanes': [25, 55],  # Two sub-lanes
            },
            1: {
                'start_x': -35, 'start_y': -450,
                'direction': 1,  # South
                'dx': 0, 'dy': 1,
                'stop_line': -100,
                'exit_line': 450,
                'lanes': [-50, -20],
            },
            2: {
                'start_x': 450, 'start_y': -35,
                'direction': 2,  # West
                'dx': -1, 'dy': 0,
                'stop_line': 100,
                'exit_line': -450,
                'lanes': [-55, -25],
            },
            3: {
                'start_x': 35, 'start_y': 450,
                'direction': 3,  # North
                'dx': 0, 'dy': -1,
                'stop_line': 100,
                'exit_line': -450,
                'lanes': [20, 50],
            },
        }
        
        # Signal states
        self.signal_states = {0: 'red', 1: 'red', 2: 'red', 3: 'red'}
        self.current_green_lane = 0
        self.signal_states[0] = 'green'
        self.signal_timer = time.time()
        self.green_duration = SIGNAL_CONFIG.get('DEFAULT_GREEN', 20)
        self.time_remaining = self.green_duration  # Countdown timer
        self.next_lane = 1  # Next lane to get green
        
        # Spawn timers
        self.last_spawn_time = time.time()
        self.spawn_interval = 0.5  # Spawn every 0.5 seconds
        
        # Lane vehicle counts (for dashboard)
        self.lane_counts = {
            0: {'car': 0, 'truck': 0, 'bike': 0},
            1: {'car': 0, 'truck': 0, 'bike': 0},
            2: {'car': 0, 'truck': 0, 'bike': 0},
            3: {'car': 0, 'truck': 0, 'bike': 0},
        }
        
        # RL STATE: Accumulated wait time per lane (in seconds)
        # This is the KEY for proper RL - tracks how long each lane has been waiting
        self.lane_wait_times = {0: 0.0, 1: 0.0, 2: 0.0, 3: 0.0}
        self.last_wait_update = time.time()
        self.dynamic_threshold = 30
        
        self.VEHICLE_WEIGHT = {
            'truck': 3,
            'car': 2,
            'bike': 1,
        }
        
        self.G_MIN = 13
        self.G_MAX = 90
        self.ALPHA = 0.5
        self.BETA = 0.5
        
        self.MIN_GREEN = self.G_MIN
        self.MAX_GREEN = self.G_MAX
        
        self.ADAPTIVE_MIN_GREEN = 12
        
        self.CROSSING_TIME = {
            'bike': 3,
            'car': 5,
            'truck': 7,
        }
        
        self.signal_switches = []
        self.max_switches_per_window = 6
        self.switch_window = 30
        
        self.total_reward = 0.0
        self.reward_components = {
            'flow': 0.0,
            'waiting': 0.0,
            'emergency': 0.0,
            'accident': 0.0,
            'pedestrian': 0.0,
            'stability': 0.0
        }
        self.vehicles_passed_this_green = 0
        
        # Vehicles waiting at stop line (not far away)
        self.lane_waiting_at_stop = {0: 0, 1: 0, 2: 0, 3: 0}
        
        # Accident state
        self.active_accident = None  # {'wx': x, 'wy': y, 'time': t, 'severe': bool}
        self.accident_alerted = False
        self.pre_accident_lane = None  # Lane that was green before accident
        self.pre_accident_time = None  # Time remaining before accident
        self.hospital_highlight = False  # Highlight nearest hospital during accident
        
        # Lane selection mode for emergency
        self.selecting_lane = False
        self.emergency_type_pending = None
        
        # Emergency priority tracking (persists through accidents)
        self.active_emergency_lane = None  # Lane where emergency vehicle is waiting
        
        # Stats
        self.stats = {
            'total_vehicles': 0,
            'vehicles_passed': 0,
            'avg_wait_time': 0,
            'accidents': 0,
            'emergency_responses': 0,
        }
        
        # Speed multiplier (lower = slower vehicles)
        self.speed_mult = 40
        
        # Show emergency stations
        self.show_stations = True
        
        # Font
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        
        self.test_mode = False
        self.current_scenario = 0
        self.scenario_name = ""
        self.auto_test_mode = False
        self.auto_test_timer = 0
        self.auto_test_interval = 30
        self.test_scenarios = self._define_test_scenarios()
        self.scenario_input = ""
        self.scenario_input_timer = 0
        
        print("✅ Simulation initialized")
        print("📋 Press T to toggle TEST MODE, then type number (1-75) + ENTER to jump to scenario")
        print("📋 Or use [ / ] to cycle scenarios, R for AUTO-RUN mode")
    
    def _define_test_scenarios(self):
        """Define all test scenarios"""
        from itertools import product
        
        normal_cases = []
        edge_cases = []
        
        normal_cases.append({
            'name': 'Normal: W(2T,3C,2B) N(1T,2C,1B) E(1C,1B) S(1C)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 2), ('car', 3), ('bike', 2)], 
                     1: [('truck', 1), ('car', 2), ('bike', 1)], 
                     2: [('car', 1), ('bike', 1)], 
                     3: [('car', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(1T,2C,1B) N(2T,2C,2B) E(2C,1B) S(1T)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 1), ('car', 2), ('bike', 1)], 
                     1: [('truck', 2), ('car', 2), ('bike', 2)], 
                     2: [('car', 2), ('bike', 1)], 
                     3: [('truck', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(3C,1B) N(2T,1C) E(1T,2B) S(2C)',
            'category': 'Normal Traffic',
            'lanes': {0: [('car', 3), ('bike', 1)], 
                     1: [('truck', 2), ('car', 1)], 
                     2: [('truck', 1), ('bike', 2)], 
                     3: [('car', 2)]}
        })
        normal_cases.append({
            'name': 'Normal: W(2T,2C) N(1T,1C,1B) E(1C,2B) S(1T,1C)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 2), ('car', 2)], 
                     1: [('truck', 1), ('car', 1), ('bike', 1)], 
                     2: [('car', 1), ('bike', 2)], 
                     3: [('truck', 1), ('car', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(1T,3C) N(2C,1B) E(1T,1C,1B) S(2B)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 1), ('car', 3)], 
                     1: [('car', 2), ('bike', 1)], 
                     2: [('truck', 1), ('car', 1), ('bike', 1)], 
                     3: [('bike', 2)]}
        })
        normal_cases.append({
            'name': 'Normal: W(2B) N(2C) E(1T,1C) S(1C,1B)',
            'category': 'Normal Traffic',
            'lanes': {0: [('bike', 2)], 
                     1: [('car', 2)], 
                     2: [('truck', 1), ('car', 1)], 
                     3: [('car', 1), ('bike', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(1T) N(1C) E(2B) S(1T,2C)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 1)], 
                     1: [('car', 1)], 
                     2: [('bike', 2)], 
                     3: [('truck', 1), ('car', 2)]}
        })
        normal_cases.append({
            'name': 'Normal: W(2C,1B) N(1T,1C) E(1T,2C) S(1B)',
            'category': 'Normal Traffic',
            'lanes': {0: [('car', 2), ('bike', 1)], 
                     1: [('truck', 1), ('car', 1)], 
                     2: [('truck', 1), ('car', 2)], 
                     3: [('bike', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(1T,2B) N(1T,1C,1B) E(2C) S(1C,1B)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 1), ('bike', 2)], 
                     1: [('truck', 1), ('car', 1), ('bike', 1)], 
                     2: [('car', 2)], 
                     3: [('car', 1), ('bike', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(2C,1T) N(1C,1B) E(1T,1B) S(2C)',
            'category': 'Normal Traffic',
            'lanes': {0: [('car', 2), ('truck', 1)], 
                     1: [('car', 1), ('bike', 1)], 
                     2: [('truck', 1), ('bike', 1)], 
                     3: [('car', 2)]}
        })
        # More normal cases - balanced 4-way traffic
        normal_cases.append({
            'name': 'Normal: All lanes 2C each',
            'category': 'Normal Traffic',
            'lanes': {0: [('car', 2)], 1: [('car', 2)], 2: [('car', 2)], 3: [('car', 2)]}
        })
        normal_cases.append({
            'name': 'Normal: All lanes 1T,1C,1B',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 1), ('car', 1), ('bike', 1)], 
                     1: [('truck', 1), ('car', 1), ('bike', 1)], 
                     2: [('truck', 1), ('car', 1), ('bike', 1)], 
                     3: [('truck', 1), ('car', 1), ('bike', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: W(1T,2C) N(2C,1B) E(1C,2B) S(1T,1B)',
            'category': 'Normal Traffic',
            'lanes': {0: [('truck', 1), ('car', 2)], 
                     1: [('car', 2), ('bike', 1)], 
                     2: [('car', 1), ('bike', 2)], 
                     3: [('truck', 1), ('bike', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: Light traffic - W(1C) N(1B) E(1C) S(1T)',
            'category': 'Normal Traffic',
            'lanes': {0: [('car', 1)], 1: [('bike', 1)], 2: [('car', 1)], 3: [('truck', 1)]}
        })
        normal_cases.append({
            'name': 'Normal: Medium - W(2C,2B) N(1T,2C) E(3C) S(1T,1C,1B)',
            'category': 'Normal Traffic',
            'lanes': {0: [('car', 2), ('bike', 2)], 
                     1: [('truck', 1), ('car', 2)], 
                     2: [('car', 3)], 
                     3: [('truck', 1), ('car', 1), ('bike', 1)]}
        })
        
        edge_cases.append({
            'name': 'EDGE: Only 1 truck in West',
            'category': 'Single Vehicle',
            'lanes': {0: [('truck', 1)], 1: [], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: Only 1 car in North',
            'category': 'Single Vehicle',
            'lanes': {0: [], 1: [('car', 1)], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: Only 1 bike in East',
            'category': 'Single Vehicle',
            'lanes': {0: [], 1: [], 2: [('bike', 1)], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: Only 1 truck in South',
            'category': 'Single Vehicle',
            'lanes': {0: [], 1: [], 2: [], 3: [('truck', 1)]}
        })
        # All empty
        edge_cases.append({
            'name': 'EDGE: All lanes EMPTY',
            'category': 'Empty Road',
            'lanes': {0: [], 1: [], 2: [], 3: []}
        })
        # Single lane full
        edge_cases.append({
            'name': 'EDGE: West 5T only (others empty)',
            'category': 'Single Lane Full',
            'lanes': {0: [('truck', 5)], 1: [], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: North 5C only (others empty)',
            'category': 'Single Lane Full',
            'lanes': {0: [], 1: [('car', 5)], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: East 5B only (others empty)',
            'category': 'Single Lane Full',
            'lanes': {0: [], 1: [], 2: [('bike', 5)], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: South 5T only (others empty)',
            'category': 'Single Lane Full',
            'lanes': {0: [], 1: [], 2: [], 3: [('truck', 5)]}
        })
        
        edge_cases.append({
            'name': 'EDGE: 10 trucks West only - EXTREME',
            'category': 'Stress Test',
            'lanes': {0: [('truck', 10)], 1: [], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: 10 bikes East - sudden spike',
            'category': 'Stress Test',
            'lanes': {0: [], 1: [], 2: [('bike', 10)], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: 20 trucks West - MEGA LOAD',
            'category': 'Extreme Stress',
            'lanes': {0: [('truck', 20)], 1: [], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: 15 trucks + 10 cars West',
            'category': 'Extreme Stress',
            'lanes': {0: [('truck', 15), ('car', 10)], 1: [], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: All 4 lanes FULL trucks (8 each)',
            'category': 'Stress Test',
            'lanes': {0: [('truck', 8)], 1: [('truck', 8)], 2: [('truck', 8)], 3: [('truck', 8)]}
        })
        edge_cases.append({
            'name': 'EDGE: All 4 lanes FULL mixed (3T,3C,3B each)',
            'category': 'Stress Test',
            'lanes': {0: [('truck', 3), ('car', 3), ('bike', 3)], 
                     1: [('truck', 3), ('car', 3), ('bike', 3)], 
                     2: [('truck', 3), ('car', 3), ('bike', 3)], 
                     3: [('truck', 3), ('car', 3), ('bike', 3)]}
        })
        edge_cases.append({
            'name': 'EDGE: 12T each lane - TOTAL GRIDLOCK',
            'category': 'Extreme Stress',
            'lanes': {0: [('truck', 12)], 1: [('truck', 12)], 2: [('truck', 12)], 3: [('truck', 12)]}
        })
        edge_cases.append({
            'name': 'EDGE: W(10T,8C,5B) - MEGA MIXED',
            'category': 'Extreme Stress',
            'lanes': {0: [('truck', 10), ('car', 8), ('bike', 5)], 1: [], 2: [], 3: []}
        })
        
        # High-density scenarios
        edge_cases.append({
            'name': 'EDGE: W(5T,4C,2B) N(3T,5C,4B) E(2T,3C,5B)',
            'category': 'High-Density',
            'lanes': {0: [('truck', 5), ('car', 4), ('bike', 2)], 
                     1: [('truck', 3), ('car', 5), ('bike', 4)], 
                     2: [('truck', 2), ('car', 3), ('bike', 5)], 
                     3: []}
        })
        edge_cases.append({
            'name': 'EDGE: Trucks only - W(4T) N(3T) E(2T) S(5T)',
            'category': 'High-Density',
            'lanes': {0: [('truck', 4)], 1: [('truck', 3)], 2: [('truck', 2)], 3: [('truck', 5)]}
        })
        edge_cases.append({
            'name': 'EDGE: Bikes only - W(5B) N(4B) E(3B) S(6B)',
            'category': 'High-Density',
            'lanes': {0: [('bike', 5)], 1: [('bike', 4)], 2: [('bike', 3)], 3: [('bike', 6)]}
        })
        # Imbalanced
        edge_cases.append({
            'name': 'EDGE: Heavy South only - W(1B) N(1B) E(1B) S(8T)',
            'category': 'Imbalanced',
            'lanes': {0: [('bike', 1)], 1: [('bike', 1)], 2: [('bike', 1)], 3: [('truck', 8)]}
        })
        edge_cases.append({
            'name': 'EDGE: W(15T) vs others(1B each) - EXTREME IMBALANCE',
            'category': 'Extreme Imbalance',
            'lanes': {0: [('truck', 15)], 1: [('bike', 1)], 2: [('bike', 1)], 3: [('bike', 1)]}
        })
        edge_cases.append({
            'name': 'EDGE: Priority test - W(6T) N(4C) E(2B) S(1T,1C,1B)',
            'category': 'Priority Test',
            'lanes': {0: [('truck', 6)], 
                     1: [('car', 4)], 
                     2: [('bike', 2)], 
                     3: [('truck', 1), ('car', 1), ('bike', 1)]}
        })
        # Dynamic clearing scenarios
        edge_cases.append({
            'name': 'EDGE: W(5T) - test 50s allocation',
            'category': 'Dynamic Clearing',
            'lanes': {0: [('truck', 5)], 1: [], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: N(3C) - test 25s allocation',
            'category': 'Dynamic Clearing',
            'lanes': {0: [], 1: [('car', 3)], 2: [], 3: []}
        })
        edge_cases.append({
            'name': 'EDGE: E(2B) - test minimal allocation',
            'category': 'Dynamic Clearing',
            'lanes': {0: [], 1: [], 2: [('bike', 2)], 3: []}
        })
        
        patterns = {
            '0': [],
            'T': [('truck', 1)],
            'C': [('car', 1)],
            'B': [('bike', 1)],
            'TT': [('truck', 2)],
            'CC': [('car', 2)],
            'BB': [('bike', 2)],
            'TC': [('truck', 1), ('car', 1)],
            'TB': [('truck', 1), ('bike', 1)],
            'CB': [('car', 1), ('bike', 1)],
            'TCB': [('truck', 1), ('car', 1), ('bike', 1)],
            '3T': [('truck', 3)],
            '3C': [('car', 3)],
            '3B': [('bike', 3)],
        }
        
        # Generate some key combinations for comprehensive testing
        combo_patterns = [
            # Single type variations
            ('T', '0', '0', '0'), ('0', 'T', '0', '0'), ('0', '0', 'T', '0'), ('0', '0', '0', 'T'),
            ('C', '0', '0', '0'), ('0', 'C', '0', '0'), ('0', '0', 'C', '0'), ('0', '0', '0', 'C'),
            ('B', '0', '0', '0'), ('0', 'B', '0', '0'), ('0', '0', 'B', '0'), ('0', '0', '0', 'B'),
            # Two lanes with vehicles
            ('T', 'C', '0', '0'), ('T', '0', 'C', '0'), ('T', '0', '0', 'C'),
            ('C', 'B', '0', '0'), ('C', '0', 'B', '0'), ('0', 'C', 'B', '0'),
            ('TT', 'CC', '0', '0'), ('TT', '0', 'BB', '0'), ('0', 'CC', 'BB', '0'),
            # Three lanes
            ('T', 'C', 'B', '0'), ('T', 'C', '0', 'B'), ('T', '0', 'C', 'B'), ('0', 'T', 'C', 'B'),
            ('TC', 'CB', 'TB', '0'), ('TC', 'CB', '0', 'TB'),
            # All four lanes
            ('T', 'C', 'B', 'T'), ('C', 'C', 'C', 'C'), ('B', 'B', 'B', 'B'), ('T', 'T', 'T', 'T'),
            ('TC', 'TC', 'TC', 'TC'), ('TCB', 'TCB', 'TCB', 'TCB'),
            # Heavy one side
            ('3T', 'C', 'B', '0'), ('T', '3C', 'B', '0'), ('T', 'C', '3B', '0'),
            ('3T', '0', '0', 'B'), ('0', '3C', '0', 'B'), ('0', '0', '3B', 'T'),
        ]
        
        for i, combo in enumerate(combo_patterns):
            lanes_data = {}
            for lane_idx, pattern_key in enumerate(combo):
                lanes_data[lane_idx] = patterns.get(pattern_key, [])
            
            # Determine if this is edge or normal
            total_vehicles = sum(sum(count for _, count in lane) for lane in lanes_data.values())
            empty_lanes = sum(1 for lane in lanes_data.values() if not lane)
            
            if total_vehicles <= 1 or empty_lanes >= 3 or total_vehicles >= 10:
                cat = 'Edge-Combo'
                edge_cases.append({
                    'name': f'Combo-{i+1}: W({combo[0]}) N({combo[1]}) E({combo[2]}) S({combo[3]})',
                    'category': cat,
                    'lanes': lanes_data
                })
            else:
                cat = 'Normal-Combo'
                normal_cases.append({
                    'name': f'Combo-{i+1}: W({combo[0]}) N({combo[1]}) E({combo[2]}) S({combo[3]})',
                    'category': cat,
                    'lanes': lanes_data
                })
        
        scenarios = []
        max_len = max(len(normal_cases), len(edge_cases))
        
        for i in range(max_len):
            # Add normal case
            if i < len(normal_cases):
                scenario = normal_cases[i].copy()
                scenario['name'] = f'{len(scenarios)+1}. {scenario["name"]}'
                scenarios.append(scenario)
            
            # Add edge case
            if i < len(edge_cases):
                scenario = edge_cases[i].copy()
                scenario['name'] = f'{len(scenarios)+1}. {scenario["name"]}'
                scenarios.append(scenario)
        
        print(f"📋 Generated {len(scenarios)} test scenarios ({len(normal_cases)} normal, {len(edge_cases)} edge)")
        return scenarios
    
    def spawn_scenario_vehicles(self, scenario):
        """Spawn vehicles according to scenario configuration"""
        # Clear existing vehicles (except emergency)
        self.vehicles = [v for v in self.vehicles if v.get('is_emergency', False)]
        
        # Reset lane counts and wait times
        self.lane_vehicles = {0: 0, 1: 0, 2: 0, 3: 0}
        self.lane_wait_times = {0: 0, 1: 0, 2: 0, 3: 0}
        self.lane_waiting_at_stop = {0: 0, 1: 0, 2: 0, 3: 0}
        
        # Vehicle colors by type
        type_colors = {
            'truck': [(200, 150, 100), (180, 180, 180), (150, 100, 50), (100, 80, 60)],
            'car': [(220, 50, 50), (50, 100, 220), (250, 200, 50), (50, 180, 100), (250, 250, 250)],
            'bike': [(80, 80, 80), (60, 60, 60), (100, 100, 100)]
        }
        
        lanes_config = scenario['lanes']
        
        for lane, vehicles_list in lanes_config.items():
            config = self.lane_config[lane]
            spawn_offset = 0
            
            for v_type, count in vehicles_list:
                for i in range(count):
                    # Choose sub-lane (alternate between sub-lanes)
                    sub_lane = config['lanes'][spawn_offset % len(config['lanes'])]
                    
                    # Calculate spawn position with spacing
                    spacing = 70 if v_type == 'truck' else 50 if v_type == 'car' else 40
                    
                    if lane in (0, 2):  # East-West lanes
                        if lane == 0:  # West (coming from left)
                            start_x = config['start_x'] + (spawn_offset * spacing)
                        else:  # East (coming from right)
                            start_x = config['start_x'] - (spawn_offset * spacing)
                        start_y = sub_lane
                    else:  # North-South lanes
                        start_x = sub_lane
                        if lane == 1:  # North (coming from top)
                            start_y = config['start_y'] + (spawn_offset * spacing)
                        else:  # South (coming from bottom)
                            start_y = config['start_y'] - (spawn_offset * spacing)
                    
                    # Pick color for vehicle type
                    color = random.choice(type_colors[v_type])
                    
                    # Create vehicle
                    vehicle = {
                        'id': self.vehicle_id_counter,
                        'wx': start_x,
                        'wy': start_y,
                        'type': v_type,
                        'color': color,
                        'lane': lane,
                        'direction': config['direction'],
                        'speed': random.uniform(0.8, 1.2),
                        'waiting': False,
                        'spawn_time': time.time(),
                    }
                    
                    self.vehicles.append(vehicle)
                    self.vehicle_id_counter += 1
                    spawn_offset += 1
        
        # Update stats
        self.stats['total_vehicles'] = len(self.vehicles)
        self.scenario_name = scenario['name']
        print(f"📋 Loaded scenario: {scenario['name']}")
        
    def spawn_vehicles(self):
        """Spawn vehicles on all lanes"""
        # Don't auto-spawn in test mode
        if self.test_mode:
            return
            
        current_time = time.time()
        
        if current_time - self.last_spawn_time < self.spawn_interval:
            return
            
        self.last_spawn_time = current_time
        
        # Spawn on random lane
        lane = random.randint(0, 3)
        config = self.lane_config[lane]
        
        # Vehicle types with colors
        vehicle_types = [
            ('car', (220, 50, 50)),    # Red car
            ('car', (50, 100, 220)),   # Blue car
            ('car', (250, 200, 50)),   # Yellow car
            ('car', (250, 250, 250)),  # White car
            ('car', (60, 60, 60)),     # Black car
            ('car', (50, 180, 100)),   # Green car
            ('truck', (200, 150, 100)),  # Brown truck
            ('truck', (180, 180, 180)),  # Gray truck
            ('bike', (80, 80, 80)),    # Motorcycle
        ]
        
        v_type, color = random.choice(vehicle_types)
        
        # Choose sub-lane
        sub_lane = random.choice(config['lanes'])
        
        # Calculate start position
        if lane in (0, 2):  # East-West
            start_x = config['start_x']
            start_y = sub_lane
        else:  # North-South
            start_x = sub_lane
            start_y = config['start_y']
            
        # Check for collision at spawn point
        for v in self.vehicles:
            dist = math.sqrt((v['wx'] - start_x)**2 + (v['wy'] - start_y)**2)
            if dist < 60:
                return  # Too close to another vehicle
        
        # Create vehicle
        vehicle = {
            'id': self.vehicle_id_counter,
            'wx': start_x,
            'wy': start_y,
            'type': v_type,
            'color': color,
            'lane': lane,
            'direction': config['direction'],
            'speed': random.uniform(0.8, 1.2),
            'waiting': False,
            'spawn_time': current_time,
        }
        
        self.vehicles.append(vehicle)
        self.vehicle_id_counter += 1
        self.stats['total_vehicles'] += 1
        
    def spawn_emergency_in_lane(self, emergency_type, lane):
        """Spawn emergency vehicle in specific lane"""
        config = self.lane_config[lane]
        
        if lane in (0, 2):
            wx = config['start_x']
            wy = config['lanes'][0]
        else:
            wx = config['lanes'][0]
            wy = config['start_y']
        
        vehicle = {
            'id': self.vehicle_id_counter,
            'wx': wx,
            'wy': wy,
            'type': emergency_type,
            'color': (255, 255, 255),
            'lane': lane,
            'direction': config['direction'],
            'speed': 1.8,  # Faster
            'waiting': False,
            'spawn_time': time.time(),
            'is_emergency': True,
        }
        
        lane_names = ['West', 'North', 'East', 'South']
        
        if emergency_type == 'ambulance':
            self.ambulances.append(vehicle)
            alert = f"🚑 AMBULANCE → {lane_names[lane]} Lane"
        else:
            self.police_cars.append(vehicle)
            alert = f"🚔 POLICE → {lane_names[lane]} Lane"
            
        self.vehicles.append(vehicle)
        self.vehicle_id_counter += 1
        
        # Add alert
        self.emergency_alerts.append(alert)
        if len(self.emergency_alerts) > 5:
            self.emergency_alerts.pop(0)
            
        # Save previous lane before emergency (only if not already saved)
        if not hasattr(self, 'pre_emergency_lane') or self.pre_emergency_lane is None:
            self.pre_emergency_lane = self.current_green_lane
            self.pre_emergency_time_remaining = self.time_remaining
        
        # Track active emergency lane - this persists through accidents
        self.active_emergency_lane = lane
            
        # Make emergency lane green (even during accident)
        self._set_emergency_green(lane)
        self.stats['emergency_responses'] += 1
        
    def trigger_accident(self):
        """Trigger an accident scene and alert emergency services"""
        # Save pre-accident state (only if no emergency is pending)
        if self.pre_accident_lane is None and self.active_emergency_lane is None:
            self.pre_accident_lane = self.current_green_lane
            self.pre_accident_time = self.time_remaining
        
        # Create accident at intersection
        self.active_accident = {
            'wx': random.randint(-50, 50),
            'wy': random.randint(-50, 50),
            'time': time.time(),
            'severe': random.choice([True, False])
        }
        
        # Highlight hospital
        self.hospital_highlight = True
        
        # Alert emergency services (don't spawn vehicles, just alert)
        self.emergency_alerts = [
            "🚨 ACCIDENT DETECTED!",
            "📍 Location: Main Intersection",
            "🏥 NEAREST HOSPITAL ALERTED!",
            "🚔 Alerting nearest Police Station...",
            "⚠️ Press A for Ambulance, P for Police"
        ]
        
        self.accident_alerted = True
        self.stats['accidents'] += 1
        
        # Stop all traffic temporarily (but check if emergency vehicle exists)
        if self.active_emergency_lane is not None:
            # Emergency vehicle has priority - keep its lane green
            for lane in range(4):
                self.signal_states[lane] = 'red'
            self.signal_states[self.active_emergency_lane] = 'green'
            self.emergency_alerts.append(f"🚨 Emergency vehicle has priority!")
        else:
            # No emergency - all red
            for lane in range(4):
                self.signal_states[lane] = 'red'
        
    def spawn_pedestrians(self):
        """Spawn pedestrians on crosswalks"""
        current_time = time.time()
        
        if current_time - self.last_pedestrian_spawn < self.pedestrian_spawn_interval:
            return
            
        self.last_pedestrian_spawn = current_time
        
        # Only spawn if we have fewer than 8 pedestrians
        if len(self.pedestrians) >= 8:
            return
            
        # Choose a random crosswalk
        crosswalk = random.choice(self.crosswalks)
        
        # Determine which signals need to be red for safe crossing
        # Vertical crosswalks need E-W traffic stopped (lanes 0, 2)
        # Horizontal crosswalks need N-S traffic stopped (lanes 1, 3)
        if crosswalk['dir'] == 'vertical':
            can_cross = self.signal_states[0] == 'red' and self.signal_states[2] == 'red'
        else:
            can_cross = self.signal_states[1] == 'red' and self.signal_states[3] == 'red'
            
        if not can_cross:
            return  # Don't spawn if traffic is moving through
            
        # Random start position along crosswalk edge
        if crosswalk['dir'] == 'vertical':
            # Start from top or bottom
            start_from_top = random.choice([True, False])
            wx = crosswalk['start_x'] + random.randint(-15, 15)
            if start_from_top:
                wy = crosswalk['start_y']
                target_y = crosswalk['end_y']
                dy = 1
            else:
                wy = crosswalk['end_y']
                target_y = crosswalk['start_y']
                dy = -1
            dx = 0
        else:
            # Start from left or right
            start_from_left = random.choice([True, False])
            wy = crosswalk['start_y'] + random.randint(-15, 15)
            if start_from_left:
                wx = crosswalk['start_x']
                target_x = crosswalk['end_x']
                dx = 1
            else:
                wx = crosswalk['end_x']
                target_x = crosswalk['start_x']
                dx = -1
            dy = 0
            
        pedestrian = {
            'id': len(self.pedestrians),
            'wx': wx,
            'wy': wy,
            'dx': dx,
            'dy': dy,
            'speed': random.uniform(0.3, 0.6),
            'crosswalk': crosswalk,
            'crossing': True,
        }
        
        self.pedestrians.append(pedestrian)
        
    def update_pedestrians(self, dt):
        """Update pedestrian positions on crosswalks"""
        pedestrians_to_remove = []
        
        for p in self.pedestrians:
            crosswalk = p['crosswalk']
            
            # Check if safe to continue crossing
            if crosswalk['dir'] == 'vertical':
                safe = self.signal_states[0] == 'red' and self.signal_states[2] == 'red'
            else:
                safe = self.signal_states[1] == 'red' and self.signal_states[3] == 'red'
                
            # If pedestrian is in middle of crosswalk, keep moving even if signal changed
            in_middle = False
            if crosswalk['dir'] == 'vertical':
                in_middle = abs(p['wy']) < 60  # In the intersection area
            else:
                in_middle = abs(p['wx']) < 60
                
            if safe or in_middle:
                # Move pedestrian
                speed = p['speed'] * self.speed_mult * dt
                p['wx'] += p['dx'] * speed
                p['wy'] += p['dy'] * speed
                
            # Check if finished crossing
            finished = False
            if crosswalk['dir'] == 'vertical':
                if p['dy'] > 0 and p['wy'] > crosswalk['end_y'] + 20:
                    finished = True
                elif p['dy'] < 0 and p['wy'] < crosswalk['start_y'] - 20:
                    finished = True
            else:
                if p['dx'] > 0 and p['wx'] > crosswalk['end_x'] + 20:
                    finished = True
                elif p['dx'] < 0 and p['wx'] < crosswalk['start_x'] - 20:
                    finished = True
                    
            if finished:
                pedestrians_to_remove.append(p)
                
        for p in pedestrians_to_remove:
            self.pedestrians.remove(p)
        
    def _set_emergency_green(self, lane):
        """Set lane green for emergency vehicle"""
        for l in range(4):
            self.signal_states[l] = 'red'
        self.signal_states[lane] = 'green'
        self.current_green_lane = lane
        self.signal_timer = time.time()
        self.time_remaining = 15  # Emergency gets 15 seconds
        
    def _count_vehicles_in_lane(self, lane):
        """Count vehicles waiting in a lane"""
        count = 0
        for v in self.vehicles:
            if v['lane'] == lane and not v.get('is_emergency'):
                count += 1
        return count
    
    def _count_vehicles_at_stop_line(self, lane):
        """Count vehicles actually WAITING at stop line (not far away still coming)
        This is crucial for RL - only waiting vehicles should get priority, not distant ones
        """
        count = 0
        for v in self.vehicles:
            if v['lane'] != lane or v.get('is_emergency'):
                continue
            
            # Check if vehicle is near stop line (waiting zone)
            # Lane 0 (West→East): stop line at x=-80, waiting zone is -200 to -80
            # Lane 1 (North→South): stop line at y=-80, waiting zone is -200 to -80
            # Lane 2 (East→West): stop line at x=80, waiting zone is 80 to 200
            # Lane 3 (South→North): stop line at y=80, waiting zone is 80 to 200
            
            at_stop = False
            if lane == 0 and -200 <= v['wx'] <= -60:
                at_stop = True
            elif lane == 1 and -200 <= v['wy'] <= -60:
                at_stop = True
            elif lane == 2 and 60 <= v['wx'] <= 200:
                at_stop = True
            elif lane == 3 and 60 <= v['wy'] <= 200:
                at_stop = True
                
            if at_stop:
                count += 1
        return count
    
    def _get_weighted_waiting_at_stop(self, lane):
        """Get weighted count of vehicles WAITING at stop line only
        Trucks=4, Cars=2, Bikes=1 - but only for vehicles actually waiting
        """
        weight = 0
        for v in self.vehicles:
            if v['lane'] != lane or v.get('is_emergency'):
                continue
            
            # Check if vehicle is near stop line
            at_stop = False
            if lane == 0 and -200 <= v['wx'] <= -60:
                at_stop = True
            elif lane == 1 and -200 <= v['wy'] <= -60:
                at_stop = True
            elif lane == 2 and 60 <= v['wx'] <= 200:
                at_stop = True
            elif lane == 3 and 60 <= v['wy'] <= 200:
                at_stop = True
                
            if at_stop:
                v_type = v['type']
                if v_type == 'truck':
                    weight += 4
                elif v_type == 'car':
                    weight += 2
                else:  # bike
                    weight += 1
        return weight
    
    def update_wait_times(self, dt):
        """Update accumulated wait times per lane - CORE RL PHYSICS
        
        RULE: Lanes with red signal: wait time increases in REAL SECONDS
        RULE: Lanes with green signal: wait time stays at 0 (already reset when switched)
        
        Wait time represents how long vehicles have been waiting at red light.
        Uses same timing as green signal countdown for consistency.
        """
        # Use dt directly - same rate as green signal timer
        # dt is ~0.016s at 60fps, so 60 frames = 1 second
        
        for lane in range(4):
            if self.signal_states[lane] == 'red':
                # Check if any vehicles in this lane (at stop OR approaching)
                total_vehicles = self._count_vehicles_in_lane(lane)
                
                if total_vehicles > 0:
                    # Accumulate wait time: same rate as green timer countdown
                    self.lane_wait_times[lane] += dt
            # Green lane: keep at 0 (already reset when switched to green)
        
        # Update waiting at stop counts for dashboard
        for lane in range(4):
            self.lane_waiting_at_stop[lane] = self._count_vehicles_at_stop_line(lane)
    
    def _calculate_reward(self, action_type, lane_served=None):
        """Calculate RL reward based on current state"""
        reward = 0.0
        
        if hasattr(self, 'vehicles_passed_this_green'):
            self.reward_components['flow'] = self.vehicles_passed_this_green * 1.0
            reward += self.reward_components['flow']
            self.vehicles_passed_this_green = 0
        
        waiting_penalty = 0.0
        for lane in range(4):
            if self.signal_states[lane] == 'red':
                W = self.lane_wait_times.get(lane, 0)
                
                # Get vehicle counts for this lane
                counts = self.lane_counts.get(lane, {'car': 0, 'truck': 0, 'bike': 0})
                n_trucks = counts.get('truck', 0)
                n_cars = counts.get('car', 0)
                n_bikes = counts.get('bike', 0)
                
                # RL Formula: penalty based on wait time AND vehicle weights
                # Trucks penalize most (coefficient 1.0), cars less (0.7), bikes least (0.5)
                vehicle_penalty = (n_trucks * 1.0) + (n_cars * 0.7) + (n_bikes * 0.5)
                wait_penalty = W * self.BETA
                
                lane_penalty = -(wait_penalty + vehicle_penalty)
                waiting_penalty += lane_penalty
                
        self.reward_components['waiting'] = waiting_penalty
        reward += waiting_penalty
        
        # R_emergency: +100 if ambulance served immediately, -50 if delayed
        emergency_on_road = any(v.get('is_emergency') for v in self.vehicles)
        if emergency_on_road:
            for v in self.vehicles:
                if v.get('is_emergency'):
                    if self.signal_states[v['lane']] == 'green':
                        self.reward_components['emergency'] = 100
                    else:
                        self.reward_components['emergency'] = -50
                    break
            reward += self.reward_components['emergency']
        else:
            self.reward_components['emergency'] = 0
        
        # R_accident: +50 if all-red during accident, -100 if green during accident
        if self.active_accident:
            all_red = all(s == 'red' for s in self.signal_states.values())
            emergency_green = any(v.get('is_emergency') and self.signal_states[v['lane']] == 'green' for v in self.vehicles)
            if all_red or emergency_green:
                self.reward_components['accident'] = 50
            else:
                self.reward_components['accident'] = -100
            reward += self.reward_components['accident']
        else:
            self.reward_components['accident'] = 0
        
        # R_pedestrian: +5 per crossing, -5 per excess wait second
        ped_reward = 0.0
        for ped in self.pedestrians:
            if ped.get('crossed', False):
                ped_reward += 5
        self.reward_components['pedestrian'] = ped_reward
        reward += ped_reward
        
        # R_stability: -5 if too many switches in time window
        current_time = time.time()
        recent_switches = [s for s in self.signal_switches if current_time - s[0] < self.switch_window]
        if len(recent_switches) > self.max_switches_per_window:
            self.reward_components['stability'] = -5
        else:
            self.reward_components['stability'] = 0
        reward += self.reward_components['stability']
        
        self.total_reward += reward
        return reward
        
    def _get_next_lane_with_vehicles(self, start_lane):
        """Find next lane that has vehicles waiting"""
        for i in range(4):
            lane = (start_lane + i) % 4
            if self._count_vehicles_in_lane(lane) > 0:
                return lane
        return start_lane  # If all empty, stay on current
        
    def update_lane_counts(self):
        """Update vehicle counts per lane for dashboard"""
        # Reset counts
        for lane in range(4):
            self.lane_counts[lane] = {'car': 0, 'truck': 0, 'bike': 0}
            
        # Count vehicles
        for v in self.vehicles:
            if v.get('is_emergency'):
                continue
            v_type = v['type']
            lane = v['lane']
            if v_type in self.lane_counts[lane]:
                self.lane_counts[lane][v_type] += 1
        
    def _get_lane_weighted_priority(self, lane):
        """Calculate weighted priority score for a lane based on vehicle types
        Heavy vehicles (trucks) get more weight than light vehicles (bikes)
        This is used for RL-based intelligent signal timing
        """
        counts = self.lane_counts.get(lane, {'car': 0, 'truck': 0, 'bike': 0})
        
        # Weighted scoring using RL weights: truck=3, car=2, bike=1
        weight = (counts.get('truck', 0) * self.VEHICLE_WEIGHT['truck'] + 
                  counts.get('car', 0) * self.VEHICLE_WEIGHT['car'] + 
                  counts.get('bike', 0) * self.VEHICLE_WEIGHT['bike'])
        return weight
    
    def _calculate_lane_score(self, lane):
        """
        RL FORMULA: LaneScore = (N_truck * w_truck) + (N_car * w_car) + (N_motor * w_motor)
        
        This represents the DENSITY FACTOR of a lane based on vehicle types.
        Heavy vehicles contribute more to the score.
        """
        counts = self.lane_counts.get(lane, {'car': 0, 'truck': 0, 'bike': 0})
        
        lane_score = (counts.get('truck', 0) * self.VEHICLE_WEIGHT['truck'] +
                      counts.get('car', 0) * self.VEHICLE_WEIGHT['car'] +
                      counts.get('bike', 0) * self.VEHICLE_WEIGHT['bike'])
        
        return lane_score
    
    def _calculate_lane_priority(self, lane):
        """
        RL FORMULA: LanePriority = LaneScore + (alpha * WaitTime)
        
        Lanes with longer waiting times get higher priority.
        alpha = 0.5 (hyperparameter to scale waiting time importance)
        """
        lane_score = self._calculate_lane_score(lane)
        wait_time = self.lane_wait_times.get(lane, 0)
        
        lane_priority = lane_score + (self.ALPHA * wait_time)
        
        return lane_priority
    
    def _get_normalized_priority(self, lane):
        """
        RL FORMULA: P_i = LanePriority_i / sum(all LanePriorities)
        
        Returns relative probability of lane getting green.
        Higher P_i → higher chance lane i gets green.
        """
        total_priority = sum(self._calculate_lane_priority(l) for l in range(4))
        
        if total_priority == 0:
            return 0.25  # Equal probability if no vehicles
        
        return self._calculate_lane_priority(lane) / total_priority
    
    def _calculate_rl_priority_score(self, lane):
        """
        CORE RL PRIORITY FUNCTION - Uses proper RL formulas!
        
        Score = LaneScore + (alpha * WaitTime) + (wait_time^2 penalty)
        
        This makes the agent naturally prioritize:
        - Heavy traffic lanes (trucks > cars > bikes)
        - Long-waiting lanes (exponential penalty for long waits)
        
        Interview answer: "We use weighted vehicle counts combined with 
        wait time penalties. Heavy vehicles get priority because they 
        take longer to clear. Long waits get exponential penalties to 
        prevent starvation."
        """
        # 1. Lane Score based on vehicle weights
        lane_score = self._calculate_lane_score(lane)
        
        # 2. Wait time component
        wait_time = self.lane_wait_times.get(lane, 0)
        
        # 3. Combined priority with exponential wait penalty
        # Normal priority from formula + squared wait penalty for urgency
        priority = lane_score + (self.ALPHA * wait_time)
        
        # Add exponential penalty for very long waits (prevents starvation)
        wait_penalty = (wait_time / 30.0) ** 2 * 5  # 30s=1.7, 60s=6.7, 90s=15
        
        score = priority + wait_penalty
        
        return score
    
    def _get_highest_priority_lane(self, start_lane):
        """Find lane with highest RL priority score
        Uses accumulated wait time + vehicles at stop line
        This is TRUE RL - no rules, only learned consequences!
        """
        best_lane = start_lane
        best_score = -1
        
        for i in range(4):
            lane = (start_lane + i) % 4
            if lane == self.current_green_lane:
                continue  # Skip current lane
            
            # Use RL-based priority score
            score = self._calculate_rl_priority_score(lane)
            
            if score > best_score:
                best_score = score
                best_lane = lane
                
        # If no vehicles anywhere, return next in sequence
        if best_score <= 0:
            return (self.current_green_lane + 1) % 4
            
        return best_lane
        
    def update_signals(self):
        """Update traffic signals with countdown timer - RL-based priority"""
        current_time = time.time()
        elapsed = current_time - self.signal_timer
        
        # Update countdown timer (always keep running)
        self.time_remaining = max(0, int(self.green_duration - elapsed))
        
        # Check if any emergency vehicles exist on road
        emergency_on_road = any(v.get('is_emergency') for v in self.vehicles)
        
        # Find which lane has the emergency vehicle
        emergency_vehicle_lane = None
        for v in self.vehicles:
            if v.get('is_emergency'):
                emergency_vehicle_lane = v['lane']
                break
        
        # PRIORITY 1: Handle active accidents
        if self.active_accident:
            accident_duration = current_time - self.active_accident['time']
            
            # Accident clears after 5 seconds
            if accident_duration > 5:
                self.active_accident = None
                self.accident_alerted = False
                self.hospital_highlight = False
                self.emergency_alerts.append("✅ Accident scene cleared.")
                
                # After accident: Check if emergency vehicle is still waiting
                if emergency_on_road and emergency_vehicle_lane is not None:
                    # Emergency still on road - give it green
                    for l in range(4):
                        self.signal_states[l] = 'red'
                    self.signal_states[emergency_vehicle_lane] = 'green'
                    self.current_green_lane = emergency_vehicle_lane
                    self.signal_timer = current_time
                    self.green_duration = 15
                    self.time_remaining = 15
                    self.emergency_alerts.append(f"🚨 Emergency vehicle resuming priority!")
                    return
                else:
                    # No emergency - restore pre-accident or pre-emergency state
                    if self.pre_accident_lane is not None:
                        self.current_green_lane = self.pre_accident_lane
                        for l in range(4):
                            self.signal_states[l] = 'red'
                        self.signal_states[self.current_green_lane] = 'green'
                        self.signal_timer = current_time
                        self.green_duration = max(5, self.pre_accident_time or 10)
                        self.time_remaining = self.green_duration
                        self.pre_accident_lane = None
                        self.pre_accident_time = None
                    elif hasattr(self, 'pre_emergency_lane') and self.pre_emergency_lane is not None:
                        self.current_green_lane = self.pre_emergency_lane
                        for l in range(4):
                            self.signal_states[l] = 'red'
                        self.signal_states[self.current_green_lane] = 'green'
                        self.signal_timer = current_time
                        self.green_duration = max(5, getattr(self, 'pre_emergency_time_remaining', 10))
                        self.time_remaining = self.green_duration
                        self.pre_emergency_lane = None
                return
            
            # Accident still active - check emergency vehicle priority
            if emergency_on_road and emergency_vehicle_lane is not None:
                # Emergency vehicle exists - keep its lane green during accident
                for l in range(4):
                    self.signal_states[l] = 'red'
                self.signal_states[emergency_vehicle_lane] = 'green'
                self.current_green_lane = emergency_vehicle_lane
            else:
                # No emergency - all red during accident
                for l in range(4):
                    self.signal_states[l] = 'red'
            return
        
        # PRIORITY 2: Handle emergency vehicles (no accident)
        if emergency_on_road and emergency_vehicle_lane is not None:
            # Make sure emergency lane is green
            if self.signal_states[emergency_vehicle_lane] != 'green':
                for l in range(4):
                    self.signal_states[l] = 'red'
                self.signal_states[emergency_vehicle_lane] = 'green'
                self.current_green_lane = emergency_vehicle_lane
                self.signal_timer = current_time
                self.green_duration = 15
            
            # Keep timer running
            self.time_remaining = max(0, int(self.green_duration - elapsed))
            return
        
        # PRIORITY 3: Emergency just cleared - restore previous state
        if hasattr(self, 'pre_emergency_lane') and self.pre_emergency_lane is not None and not emergency_on_road:
            # Clear emergency tracking
            self.active_emergency_lane = None
            
            # Restore previous green lane
            for l in range(4):
                self.signal_states[l] = 'red'
            self.current_green_lane = self.pre_emergency_lane
            self.signal_states[self.current_green_lane] = 'green'
            self.signal_timer = current_time
            self.green_duration = max(5, getattr(self, 'pre_emergency_time_remaining', 10))
            self.time_remaining = self.green_duration
            self.emergency_alerts.append(f"✅ Resuming normal traffic flow")
            self.pre_emergency_lane = None
            self.pre_emergency_time_remaining = None
            return
            
        # PRIORITY 4: Normal RL-based signal cycle
        
        # Get current lane status
        current_at_stop = self._count_vehicles_at_stop_line(self.current_green_lane)
        current_total = self._count_vehicles_in_lane(self.current_green_lane)
        old_green_lane = self.current_green_lane  # Track for later
        
        lane_names = ['West', 'North', 'East', 'South']
        
        # Calculate DYNAMIC MAX THRESHOLD based on current max wait time
        max_wait = max(self.lane_wait_times.values()) if max(self.lane_wait_times.values()) > 0 else 30
        self.dynamic_threshold = max(20, min(60, max_wait + 10))  # Adaptive threshold
        
        # Check if MIN_GREEN has elapsed (safety constraint)
        min_green_elapsed = elapsed >= self.MIN_GREEN
        
        highest_wait_lane = None
        highest_wait = 0
        for lane in range(4):
            if lane == self.current_green_lane:
                continue
            wait = self.lane_wait_times.get(lane, 0)
            total_vehicles = self._count_vehicles_in_lane(lane)
            if total_vehicles > 0 and wait > highest_wait:
                highest_wait = wait
                highest_wait_lane = lane
        
        if highest_wait_lane is not None and highest_wait > self.dynamic_threshold:
            self._switch_to_lane(highest_wait_lane, f"🚨 URGENT (waited:{highest_wait:.0f}s)")
            return
        
        adaptive_min_elapsed = elapsed >= self.ADAPTIVE_MIN_GREEN
        
        if current_at_stop == 0 and adaptive_min_elapsed:
            # Find lane with highest RL score (wait time + vehicles)
            best_lane = self._find_best_lane_with_vehicles_at_stop(exclude_lane=self.current_green_lane)
            
            if best_lane is not None:
                wait = self.lane_wait_times.get(best_lane, 0)
                time_saved = self.green_duration - elapsed
                self._switch_to_lane(best_lane, f"⚡ Early→ (saved:{time_saved:.0f}s)")
                return
            else:
                # No lane has vehicles - check if current lane also empty
                if current_total == 0:
                    if elapsed >= self.green_duration:
                        # Rotate to next
                        next_lane = (self.current_green_lane + 1) % 4
                        self._switch_to_lane(next_lane, "🔄 Rotate")
                    return
        
        if elapsed >= self.green_duration:
            # Find lane with HIGHEST RL score (wait time dominates)
            best_lane = self._find_best_lane_with_vehicles_at_stop(exclude_lane=old_green_lane)
            
            if best_lane is None:
                # All other lanes empty - rotate to next
                best_lane = (old_green_lane + 1) % 4
            
            wait = self.lane_wait_times.get(best_lane, 0)
            self._switch_to_lane(best_lane, f"⏱️ RL→ (waited:{wait:.0f}s)")
            return
    
    def _calculate_green_duration(self, weight_at_stop):
        """Calculate dynamic green time based on lane priority"""
        lane = self.current_green_lane
        
        lane_priorities = {}
        total_priority = 0
        
        for l in range(4):
            priority = self._calculate_lane_priority(l)
            lane_priorities[l] = priority
            total_priority += priority
        
        if total_priority == 0:
            return self.G_MIN
        
        this_lane_priority = lane_priorities[lane]
        relative_priority = this_lane_priority / total_priority
        
        green_time = self.G_MIN + (relative_priority * (self.G_MAX - self.G_MIN))
        
        counts = self.lane_counts.get(lane, {'car': 0, 'truck': 0, 'bike': 0})
        n_trucks = counts.get('truck', 0)
        n_cars = counts.get('car', 0)
        n_bikes = counts.get('bike', 0)
        total_vehicles = n_trucks + n_cars + n_bikes
        
        crossing_time_needed = (n_trucks * 7) + (n_cars * 5) + (n_bikes * 3)
        if total_vehicles > 1:
            crossing_time_needed += (total_vehicles - 1) * 1
        
        final_green_time = max(green_time, crossing_time_needed)
        # G_MIN = 13 seconds (ALWAYS, even for 1 bike)
        # G_MAX = 90 seconds (prevent starvation)
        final_green_time = max(self.G_MIN, min(self.G_MAX, final_green_time))
        
        # Log for debugging (interview demo)
        if total_vehicles > 0:
            lane_names = ['West', 'North', 'East', 'South']
            print(f"📊 {lane_names[lane]}: {n_trucks}T/{n_cars}C/{n_bikes}B | "
                  f"Priority:{this_lane_priority:.1f} ({relative_priority*100:.0f}%) | "
                  f"CrossTime:{crossing_time_needed}s → Green:{int(final_green_time)}s")
        
        return int(final_green_time)
    
    def _switch_to_lane(self, new_lane, reason=""):
        """Helper to switch green signal to a new lane with tracking
        
        RULE: Tracks switches for stability monitoring
        RULE: Resets wait time of new green lane to 0
        """
        current_time = time.time()
        old_lane = self.current_green_lane
        
        # Record the switch for stability tracking
        self.signal_switches.append((current_time, old_lane, new_lane))
        # Keep only recent switches
        self.signal_switches = [s for s in self.signal_switches if current_time - s[0] < self.switch_window]
        
        # Calculate reward before switch
        self._calculate_reward('switch', lane_served=old_lane)
        
        # Perform the switch
        self.signal_states[old_lane] = 'red'
        self.lane_wait_times[new_lane] = 0  # Reset NEW lane wait time to 0
        self.current_green_lane = new_lane
        self.signal_states[new_lane] = 'green'
        self.signal_timer = current_time
        
        # Calculate green duration
        weight_at_stop = self._get_weighted_waiting_at_stop(new_lane)
        self.green_duration = self._calculate_green_duration(weight_at_stop)
        self.time_remaining = self.green_duration
        
        # Reset passed counter for new green
        self.vehicles_passed_this_green = 0
        
        # Update next_lane prediction
        predicted_next = self._find_best_lane_with_vehicles_at_stop(exclude_lane=new_lane)
        if predicted_next is not None:
            self.next_lane = predicted_next
        else:
            # Fallback: cycle to next lane
            self.next_lane = (new_lane + 1) % 4
        
        # Log the switch
        lane_names = ['West', 'North', 'East', 'South']
        if reason:
            alert = f"{reason}→{lane_names[new_lane]} ({self.green_duration}s)"
        else:
            alert = f"→{lane_names[new_lane]} ({self.green_duration}s)"
        
        self.emergency_alerts.append(alert)
        if len(self.emergency_alerts) > 5:
            self.emergency_alerts.pop(0)
    
    def _find_best_lane_with_vehicles_at_stop(self, exclude_lane=None):
        """Find best lane based on RL priority score
        
        TRUE RL: Uses wait time + vehicle count to determine priority
        Lanes with longer wait times get MUCH higher scores (squared penalty)
        """
        best_lane = None
        best_score = -1
        
        for lane in range(4):
            if lane == exclude_lane:
                continue
            
            # Check if lane has ANY vehicles (at stop or approaching)
            total_vehicles = self._count_vehicles_in_lane(lane)
            if total_vehicles == 0:
                continue  # Skip empty lanes
            
            # RL Score: wait time is the PRIMARY factor
            # Score = wait_time_squared + vehicle_weight
            wait_time = self.lane_wait_times.get(lane, 0)
            vehicles_at_stop = self._count_vehicles_at_stop_line(lane)
            
            # Wait time is PRIMARY - squared for exponential urgency
            # A lane with 60s wait has 4x the score of 30s wait
            wait_score = (wait_time / 10.0) ** 2  # 10s=1, 20s=4, 40s=16, 60s=36
            
            # Vehicles add bonus but wait time dominates
            vehicle_score = vehicles_at_stop * 2 + (total_vehicles - vehicles_at_stop) * 0.5
            
            score = wait_score + vehicle_score
            
            if score > best_score:
                best_score = score
                best_lane = lane
        
        return best_lane
            
    def update_vehicles(self, dt):
        """Update all vehicle positions"""
        vehicles_to_remove = []
        
        for v in self.vehicles:
            config = self.lane_config[v['lane']]
            
            # Check if should stop at red light
            should_stop = False
            
            # RED LIGHT LOGIC - Stop before crossing intersection
            if self.signal_states[v['lane']] != 'green':
                # Lane 0: Coming from West, going East - stop before x=-80
                if v['lane'] == 0:
                    if v['wx'] < -80 and v['wx'] > -300:
                        should_stop = True
                # Lane 1: Coming from North, going South - stop before y=-80  
                elif v['lane'] == 1:
                    if v['wy'] < -80 and v['wy'] > -300:
                        should_stop = True
                # Lane 2: Coming from East, going West - stop before x=80
                elif v['lane'] == 2:
                    if v['wx'] > 80 and v['wx'] < 300:
                        should_stop = True
                # Lane 3: Coming from South, going North - stop before y=80
                elif v['lane'] == 3:
                    if v['wy'] > 80 and v['wy'] < 300:
                        should_stop = True
            
            # Emergency vehicles don't stop at red lights
            if v.get('is_emergency'):
                should_stop = False
                
            # Check for vehicle ahead
            for other in self.vehicles:
                if other['id'] == v['id']:
                    continue
                if other['lane'] != v['lane']:
                    continue
                    
                # Calculate distance
                dist = 0
                if v['lane'] in (0, 2):
                    dist = abs(other['wx'] - v['wx'])
                    ahead = (v['lane'] == 0 and other['wx'] > v['wx']) or \
                           (v['lane'] == 2 and other['wx'] < v['wx'])
                else:
                    dist = abs(other['wy'] - v['wy'])
                    ahead = (v['lane'] == 1 and other['wy'] > v['wy']) or \
                           (v['lane'] == 3 and other['wy'] < v['wy'])
                    
                if ahead and dist < 50:
                    should_stop = True
                    break
            
            v['waiting'] = should_stop
            
            if not should_stop:
                # Move vehicle
                speed = v['speed'] * self.speed_mult * dt
                v['wx'] += config['dx'] * speed
                v['wy'] += config['dy'] * speed
                
            # Check if exited
            exited = False
            if v['lane'] == 0 and v['wx'] > config['exit_line']:
                exited = True
            elif v['lane'] == 1 and v['wy'] > config['exit_line']:
                exited = True
            elif v['lane'] == 2 and v['wx'] < config['exit_line']:
                exited = True
            elif v['lane'] == 3 and v['wy'] < config['exit_line']:
                exited = True
                
            if exited:
                vehicles_to_remove.append(v)
                self.stats['vehicles_passed'] += 1
                
                # RL: Track vehicles passed for reward (weighted by type)
                if v['type'] == 'truck':
                    self.vehicles_passed_this_green += 3
                elif v['type'] == 'car':
                    self.vehicles_passed_this_green += 1
                else:  # bike
                    self.vehicles_passed_this_green += 0.5
                
        # Remove exited vehicles
        for v in vehicles_to_remove:
            self.vehicles.remove(v)
            if v in self.ambulances:
                self.ambulances.remove(v)
            if v in self.police_cars:
                self.police_cars.remove(v)
                
    def draw_dashboard(self):
        """Draw improved control dashboard with lane counts and timer"""
        # Dashboard background
        dash_x = WINDOW_WIDTH - 340
        pygame.draw.rect(self.screen, (35, 40, 48), (dash_x, 0, 340, WINDOW_HEIGHT))
        pygame.draw.line(self.screen, (60, 65, 75), (dash_x, 0), (dash_x, WINDOW_HEIGHT), 2)
        
        y = 15
        
        # Title
        title = self.font.render("🚦 AI Traffic Control", True, (255, 255, 255))
        self.screen.blit(title, (dash_x + 20, y))
        y += 35
        
        # COUNTDOWN TIMER (big and prominent)
        pygame.draw.rect(self.screen, (45, 50, 58), (dash_x + 10, y, 320, 90), border_radius=8)
        
        # Find active green lane
        active_lane = -1
        lane_names = ['West', 'North', 'East', 'South']
        for i, state in self.signal_states.items():
            if state == 'green':
                active_lane = i
                break
        
        if active_lane >= 0:
            timer_color = (50, 255, 50) if self.time_remaining > 5 else (255, 100, 50)
            lane_text = self.font.render(f"🟢 {lane_names[active_lane]} Lane", True, (100, 255, 100))
            self.screen.blit(lane_text, (dash_x + 20, y + 10))
            
            # Big countdown number
            big_font = pygame.font.Font(None, 48)
            timer_text = big_font.render(f"{self.time_remaining}s", True, timer_color)
            self.screen.blit(timer_text, (dash_x + 220, y + 15))
            
            # Next lane indicator
            next_lane_text = self.small_font.render(f"⏭ Next: {lane_names[self.next_lane]} Lane", True, (180, 180, 100))
            self.screen.blit(next_lane_text, (dash_x + 20, y + 50))
        else:
            # All red (accident or empty)
            lane_text = self.font.render("🔴 ALL RED", True, (255, 100, 100))
            self.screen.blit(lane_text, (dash_x + 20, y + 10))
            
            if self.active_accident:
                acc_text = self.small_font.render("⚠️ Accident in progress...", True, (255, 150, 100))
                self.screen.blit(acc_text, (dash_x + 20, y + 40))
            
        y += 100
        
        # ALL 4 LANES STATUS - Show each lane's waiting status
        pygame.draw.rect(self.screen, (40, 50, 65), (dash_x + 10, y, 320, 145), border_radius=8)
        pygame.draw.rect(self.screen, (80, 100, 120), (dash_x + 10, y, 320, 145), 2, border_radius=8)
        y += 8
        
        # Dynamic threshold info with MIN/MAX constraints
        max_wait = max(self.lane_wait_times.values()) if max(self.lane_wait_times.values()) > 0 else 0
        dyn_thresh = getattr(self, 'dynamic_threshold', 30)
        header = self.font.render(f"🚦 Lanes (Min:{self.MIN_GREEN}s  Max:{self.MAX_GREEN}s)", True, (150, 200, 255))
        self.screen.blit(header, (dash_x + 15, y))
        y += 22
        
        # Show each lane: Name | At Stop/Total | Wait Time | Status
        for i, name in enumerate(['West', 'North', 'East', 'South']):
            at_stop = self._count_vehicles_at_stop_line(i)
            total = self._count_vehicles_in_lane(i)
            wait = self.lane_wait_times.get(i, 0)
            
            # Status indicator
            is_green = self.signal_states[i] == 'green'
            is_urgent = wait > dyn_thresh and at_stop > 0
            
            if is_green:
                status_color = (50, 255, 50)
                status = "🟢"
                # Green lane: show 0 (wait time was reset when it got green)
                display_wait = 0
            elif is_urgent:
                status_color = (255, 100, 100)
                status = "⚠️"
                display_wait = wait
            elif at_stop > 0:
                status_color = (255, 200, 100)
                status = "🟡"
                display_wait = wait
            elif total > 0:
                status_color = (200, 200, 150)
                status = "🔸"  # Has vehicles but not at stop
                display_wait = wait
            else:
                status_color = (150, 150, 150)
                status = "⚪"
                display_wait = wait
            
            # Wait time color (red if high, yellow if medium, green if low)
            if display_wait > 40:
                wait_color = (255, 80, 80)
            elif display_wait > 20:
                wait_color = (255, 200, 100)
            elif display_wait > 5:
                wait_color = (200, 255, 150)
            else:
                wait_color = (100, 255, 100)
            
            # Format: 🟢 West: 15s (only show waiting time)
            lane_info = f"{status} {name}:"
            wait_info = f"{int(display_wait)}s"
            
            txt1 = self.small_font.render(lane_info, True, status_color)
            txt2 = self.small_font.render(wait_info, True, wait_color)
            self.screen.blit(txt1, (dash_x + 20, y))
            self.screen.blit(txt2, (dash_x + 120, y))
            y += 24
        
        y += 3
        
        # RL REWARD TRACKING (new section)
        pygame.draw.rect(self.screen, (40, 45, 55), (dash_x + 10, y, 320, 50), border_radius=8)
        y += 5
        
        reward_text = self.small_font.render(f"RL Reward: {self.total_reward:.1f}", True, (100, 200, 255))
        self.screen.blit(reward_text, (dash_x + 20, y))
        
        # Show stability (switches in window)
        recent_switches = len([s for s in self.signal_switches if time.time() - s[0] < self.switch_window])
        stability_color = (255, 100, 100) if recent_switches > self.max_switches_per_window else (100, 255, 100)
        stability_text = self.small_font.render(f"Switches: {recent_switches}/{self.max_switches_per_window}", True, stability_color)
        self.screen.blit(stability_text, (dash_x + 180, y))
        y += 18
        
        # Reward components
        r_flow = self.reward_components.get('flow', 0)
        r_wait = self.reward_components.get('waiting', 0)
        comp_text = self.small_font.render(f"Flow:{r_flow:.0f} Wait:{r_wait:.0f} Emrg:{self.reward_components.get('emergency', 0):.0f}", True, (160, 160, 160))
        self.screen.blit(comp_text, (dash_x + 20, y))
        y += 28
        
        # SIGNAL STATUS (compact row)
        pygame.draw.rect(self.screen, (45, 50, 58), (dash_x + 10, y, 320, 55), border_radius=8)
        y += 5
        
        signal_text = self.small_font.render("Signals", True, (150, 200, 255))
        self.screen.blit(signal_text, (dash_x + 20, y))
        y += 18
        
        # Draw signals in a row
        directions = ['W', 'N', 'E', 'S']
        x_offset = dash_x + 30
        for i, dir_name in enumerate(directions):
            state = self.signal_states[i]
            color = (50, 220, 50) if state == 'green' else (220, 50, 50)
            pygame.draw.circle(self.screen, color, (x_offset, y + 5), 10)
            dir_text = self.small_font.render(dir_name, True, (200, 200, 200))
            self.screen.blit(dir_text, (x_offset - 5, y + 18))
            x_offset += 75
            
        y += 38
        
        # STATISTICS (very compact)
        pygame.draw.rect(self.screen, (45, 50, 58), (dash_x + 10, y, 320, 50), border_radius=8)
        y += 5
        
        stat_line1 = self.small_font.render(
            f"Total: {self.stats['total_vehicles']} | Passed: {self.stats['vehicles_passed']} | Road: {len(self.vehicles)}", 
            True, (180, 180, 180))
        self.screen.blit(stat_line1, (dash_x + 15, y))
        y += 16
        
        stat_line2 = self.small_font.render(
            f"Acc: {self.stats['accidents']} | Emrg: {self.stats['emergency_responses']} | Ped: {len(self.pedestrians)} | {self.speed_mult}x", 
            True, (180, 180, 180))
        self.screen.blit(stat_line2, (dash_x + 15, y))
        y += 30
        
        # CONTROLS (compact)
        pygame.draw.rect(self.screen, (45, 50, 58), (dash_x + 10, y, 320, 50), border_radius=8)
        y += 8
        
        if self.test_mode:
            # Test mode controls
            text = self.small_font.render("TEST: [/]-Cycle  ENTER-Load  C-Clear", True, (100, 255, 150))
            self.screen.blit(text, (dash_x + 15, y))
            y += 16
            text2 = self.small_font.render("R-AutoRun  ↑↓-Interval  T-Exit", True, (255, 200, 100))
            self.screen.blit(text2, (dash_x + 15, y))
        else:
            controls = "SPACE-Pause | A-Ambulance | P-Police | X-Accident | S-Stations | +/- Speed"
            text = self.small_font.render("SPACE-Pause  A-Ambulance  P-Police", True, (160, 160, 160))
            self.screen.blit(text, (dash_x + 15, y))
            y += 16
            text2 = self.small_font.render("X-Accident  S-Stations  T-Test  +/-Speed", True, (160, 160, 160))
            self.screen.blit(text2, (dash_x + 15, y))
        y += 22
        
        # TEST MODE PANEL (show when in test mode)
        if self.test_mode:
            has_input = bool(self.scenario_input)
            # Increased panel height for lane breakdown display
            panel_height = 150 if self.auto_test_mode else (130 if has_input else 115)
            bg_color = (60, 100, 60) if self.auto_test_mode else (60, 80, 60)
            border_color = (100, 255, 100) if not self.auto_test_mode else (255, 200, 100)
            
            pygame.draw.rect(self.screen, bg_color, (dash_x + 10, y, 320, panel_height), border_radius=8)
            pygame.draw.rect(self.screen, border_color, (dash_x + 10, y, 320, panel_height), 2, border_radius=8)
            y += 8
            
            # Title with auto-run indicator
            if self.auto_test_mode:
                test_title = self.font.render("🔄 AUTO-RUN MODE", True, (255, 200, 100))
            else:
                test_title = self.font.render("🧪 TEST MODE", True, (150, 255, 150))
            self.screen.blit(test_title, (dash_x + 20, y))
            y += 22
            
            # Show input field if typing
            if has_input:
                # Blinking cursor effect
                cursor = "_" if int(time.time() * 3) % 2 == 0 else " "
                input_text = self.font.render(f"Go to: {self.scenario_input}{cursor} (ENTER)", True, (255, 255, 100))
                self.screen.blit(input_text, (dash_x + 20, y))
                y += 20
            
            # Current scenario
            scenario = self.test_scenarios[self.current_scenario]
            num_text = self.small_font.render(f"Scenario {self.current_scenario + 1}/{len(self.test_scenarios)} | Type 1-{len(self.test_scenarios)}", True, (200, 255, 200))
            self.screen.blit(num_text, (dash_x + 20, y))
            y += 18
            
            # Scenario name (truncate if too long)
            name = scenario['name'][:35] + "..." if len(scenario['name']) > 35 else scenario['name']
            name_text = self.small_font.render(name, True, (255, 255, 200))
            self.screen.blit(name_text, (dash_x + 20, y))
            y += 18
            
            # Show vehicle counts per lane for current scenario
            lanes_data = scenario.get('lanes', {})
            lane_summary = []
            for lid, lname in enumerate(['W', 'N', 'E', 'S']):
                lane_vehicles = lanes_data.get(lid, [])
                parts = []
                for vtype, count in lane_vehicles:
                    if count > 0:
                        parts.append(f"{count}{vtype[0].upper()}")
                if parts:
                    lane_summary.append(f"{lname}:{'|'.join(parts)}")
                else:
                    lane_summary.append(f"{lname}:0")
            
            vehicles_text = self.small_font.render("  ".join(lane_summary), True, (200, 255, 200))
            self.screen.blit(vehicles_text, (dash_x + 20, y))
            y += 18
            
            cat_text = self.small_font.render(f"Category: {scenario['category']}", True, (180, 180, 180))
            self.screen.blit(cat_text, (dash_x + 20, y))
            y += 18
            
            # Auto-run timer
            if self.auto_test_mode:
                remaining = self.auto_test_interval - self.auto_test_timer
                timer_text = self.small_font.render(f"Next in: {int(remaining)}s / {self.auto_test_interval}s", True, (255, 200, 100))
                self.screen.blit(timer_text, (dash_x + 20, y))
                y += 18
            
            y += 10
        
        # EMERGENCY ALERTS
        if self.emergency_alerts or self.hospital_highlight:
            bg_color = (150, 40, 40) if self.hospital_highlight else (100, 40, 40)
            pygame.draw.rect(self.screen, bg_color, (dash_x + 10, y, 320, 120), border_radius=8)
            
            # Blinking hospital highlight during accident
            if self.hospital_highlight and int(time.time() * 3) % 2 == 0:
                pygame.draw.rect(self.screen, (255, 100, 100), (dash_x + 10, y, 320, 120), 3, border_radius=8)
            
            y += 8
            
            if self.hospital_highlight:
                hospital_text = self.font.render("🏥 HOSPITAL ALERTED!", True, (255, 255, 100))
                self.screen.blit(hospital_text, (dash_x + 20, y))
                y += 22
            
            alert_title = self.small_font.render("🚨 EMERGENCY ALERTS", True, (255, 150, 150))
            self.screen.blit(alert_title, (dash_x + 20, y))
            y += 20
            
            for alert in self.emergency_alerts[-3:]:
                text = self.small_font.render(alert[:38], True, (255, 220, 220))
                self.screen.blit(text, (dash_x + 20, y))
                y += 18
                
        # Lane selection popup
        if self.selecting_lane:
            self._draw_lane_selection_popup()
                
        # Paused indicator
        if self.paused:
            pygame.draw.rect(self.screen, (200, 150, 50), (dash_x + 100, WINDOW_HEIGHT - 40, 140, 30), border_radius=5)
            pause_text = self.font.render("⏸ PAUSED", True, (50, 50, 50))
            self.screen.blit(pause_text, (dash_x + 120, WINDOW_HEIGHT - 35))
            
    def _draw_lane_selection_popup(self):
        """Draw lane selection popup for emergency vehicles"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        
        # Popup box
        popup_w, popup_h = 350, 200
        popup_x = (WINDOW_WIDTH - 350 - popup_w) // 2
        popup_y = (WINDOW_HEIGHT - popup_h) // 2
        
        pygame.draw.rect(self.screen, (45, 50, 60), (popup_x, popup_y, popup_w, popup_h), border_radius=10)
        pygame.draw.rect(self.screen, (100, 150, 200), (popup_x, popup_y, popup_w, popup_h), 3, border_radius=10)
        
        # Title
        title = "🚑 AMBULANCE" if self.emergency_type_pending == 'ambulance' else "🚔 POLICE"
        title_text = self.font.render(f"Select Lane for {title}", True, (255, 255, 255))
        self.screen.blit(title_text, (popup_x + 30, popup_y + 20))
        
        # Instructions
        inst_text = self.small_font.render("Press 1-4 to select lane:", True, (200, 200, 200))
        self.screen.blit(inst_text, (popup_x + 30, popup_y + 55))
        
        # Lane options
        lanes = [
            ("1 - West Lane (→)", (255, 200, 100)),
            ("2 - North Lane (↓)", (100, 200, 255)),
            ("3 - East Lane (←)", (100, 255, 150)),
            ("4 - South Lane (↑)", (255, 150, 200)),
        ]
        
        y_off = popup_y + 85
        for lane_text, color in lanes:
            text = self.font.render(lane_text, True, color)
            self.screen.blit(text, (popup_x + 50, y_off))
            y_off += 28
            
    def handle_events(self):
        """Handle keyboard/mouse events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Only X button closes the window
                self.running = False
                
            elif event.type == pygame.KEYDOWN:
                # If in lane selection mode
                if self.selecting_lane:
                    if event.key == pygame.K_1:
                        self.spawn_emergency_in_lane(self.emergency_type_pending, 0)
                        self.selecting_lane = False
                    elif event.key == pygame.K_2:
                        self.spawn_emergency_in_lane(self.emergency_type_pending, 1)
                        self.selecting_lane = False
                    elif event.key == pygame.K_3:
                        self.spawn_emergency_in_lane(self.emergency_type_pending, 2)
                        self.selecting_lane = False
                    elif event.key == pygame.K_4:
                        self.spawn_emergency_in_lane(self.emergency_type_pending, 3)
                        self.selecting_lane = False
                    elif event.key == pygame.K_ESCAPE:
                        self.selecting_lane = False
                    continue
                
                # Normal controls
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    
                elif event.key == pygame.K_a:
                    # Open lane selection for ambulance
                    self.selecting_lane = True
                    self.emergency_type_pending = 'ambulance'
                    
                elif event.key == pygame.K_p:
                    # Open lane selection for police
                    self.selecting_lane = True
                    self.emergency_type_pending = 'police'
                    
                elif event.key == pygame.K_x:
                    self.trigger_accident()
                    
                elif event.key == pygame.K_s:
                    self.show_stations = not self.show_stations
                    
                elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                    self.speed_mult = min(200, self.speed_mult + 20)
                    
                elif event.key == pygame.K_MINUS:
                    self.speed_mult = max(20, self.speed_mult - 20)
                
                # TEST MODE CONTROLS
                elif event.key == pygame.K_t:
                    self.test_mode = not self.test_mode
                    if self.test_mode:
                        print("🧪 TEST MODE ENABLED - Use [ and ] to cycle scenarios, ENTER to load")
                        print(f"📋 {len(self.test_scenarios)} scenarios available")
                    else:
                        print("🧪 TEST MODE DISABLED - Normal spawning resumed")
                        self.scenario_name = ""
                
                elif event.key == pygame.K_LEFTBRACKET and self.test_mode:
                    # Previous scenario
                    self.current_scenario = (self.current_scenario - 1) % len(self.test_scenarios)
                    print(f"📋 Scenario {self.current_scenario + 1}/{len(self.test_scenarios)}: {self.test_scenarios[self.current_scenario]['name']}")
                
                elif event.key == pygame.K_RIGHTBRACKET and self.test_mode:
                    # Next scenario
                    self.current_scenario = (self.current_scenario + 1) % len(self.test_scenarios)
                    print(f"📋 Scenario {self.current_scenario + 1}/{len(self.test_scenarios)}: {self.test_scenarios[self.current_scenario]['name']}")
                
                elif event.key == pygame.K_RETURN and self.test_mode:
                    # Load scenario - either typed number or current
                    if self.scenario_input:
                        try:
                            scenario_num = int(self.scenario_input)
                            if 1 <= scenario_num <= len(self.test_scenarios):
                                self.current_scenario = scenario_num - 1
                                self.spawn_scenario_vehicles(self.test_scenarios[self.current_scenario])
                                print(f"✅ Loaded scenario #{scenario_num}: {self.test_scenarios[self.current_scenario]['name']}")
                            else:
                                print(f"❌ Invalid scenario number! Enter 1-{len(self.test_scenarios)}")
                        except ValueError:
                            print(f"❌ Invalid input: '{self.scenario_input}'")
                        self.scenario_input = ""
                    else:
                        self.spawn_scenario_vehicles(self.test_scenarios[self.current_scenario])
                
                # Number keys for direct scenario input (0-9)
                elif self.test_mode and event.key in [pygame.K_0, pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                                                       pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9]:
                    digit = chr(event.key)
                    self.scenario_input += digit
                    self.scenario_input_timer = 0
                    print(f"🔢 Typing scenario: {self.scenario_input}_ (press ENTER to load)")
                
                # Numpad number keys
                elif self.test_mode and event.key in [pygame.K_KP0, pygame.K_KP1, pygame.K_KP2, pygame.K_KP3, pygame.K_KP4,
                                                       pygame.K_KP5, pygame.K_KP6, pygame.K_KP7, pygame.K_KP8, pygame.K_KP9]:
                    digit = str(event.key - pygame.K_KP0)
                    self.scenario_input += digit
                    self.scenario_input_timer = 0
                    print(f"🔢 Typing scenario: {self.scenario_input}_ (press ENTER to load)")
                
                # Backspace to clear input
                elif self.test_mode and event.key == pygame.K_BACKSPACE:
                    if self.scenario_input:
                        self.scenario_input = self.scenario_input[:-1]
                        if self.scenario_input:
                            print(f"🔢 Typing scenario: {self.scenario_input}_")
                        else:
                            print("🔢 Input cleared")
                
                elif event.key == pygame.K_c and self.test_mode:
                    # Clear all vehicles
                    self.vehicles = [v for v in self.vehicles if v.get('is_emergency', False)]
                    self.lane_vehicles = {0: 0, 1: 0, 2: 0, 3: 0}
                    self.lane_wait_times = {0: 0, 1: 0, 2: 0, 3: 0}
                    print("🗑️ Cleared all vehicles")
                
                elif event.key == pygame.K_r and self.test_mode:
                    # Toggle auto-run mode
                    self.auto_test_mode = not self.auto_test_mode
                    if self.auto_test_mode:
                        self.auto_test_timer = 0
                        self.spawn_scenario_vehicles(self.test_scenarios[self.current_scenario])
                        print(f"🔄 AUTO-RUN ENABLED - Cycling every {self.auto_test_interval}s")
                    else:
                        print("🔄 AUTO-RUN DISABLED")
                
                elif event.key == pygame.K_UP and self.test_mode:
                    # Increase auto-run interval
                    self.auto_test_interval = min(120, self.auto_test_interval + 5)
                    print(f"⏱️ Auto-run interval: {self.auto_test_interval}s")
                
                elif event.key == pygame.K_DOWN and self.test_mode:
                    # Decrease auto-run interval
                    self.auto_test_interval = max(10, self.auto_test_interval - 5)
                    print(f"⏱️ Auto-run interval: {self.auto_test_interval}s")
                    
    def run(self):
        """Main simulation loop"""
        print("🚗 Starting simulation...")
        
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            # Handle events
            self.handle_events()
            
            if not self.paused:
                # Clear scenario input after 3 seconds of inactivity
                if self.test_mode and self.scenario_input:
                    self.scenario_input_timer += dt
                    if self.scenario_input_timer >= 3.0:
                        self.scenario_input = ""
                        self.scenario_input_timer = 0
                
                # Auto-run test scenarios
                if self.test_mode and self.auto_test_mode:
                    self.auto_test_timer += dt
                    if self.auto_test_timer >= self.auto_test_interval:
                        self.auto_test_timer = 0
                        # Move to next scenario
                        self.current_scenario = (self.current_scenario + 1) % len(self.test_scenarios)
                        self.spawn_scenario_vehicles(self.test_scenarios[self.current_scenario])
                        print(f"🔄 Auto-loaded: {self.test_scenarios[self.current_scenario]['name']}")
                
                # Update simulation
                self.spawn_vehicles()
                self.spawn_pedestrians()
                self.update_wait_times(dt)  # RL: Update accumulated wait times
                self.update_signals()
                self.update_vehicles(dt)
                self.update_pedestrians(dt)
                self.update_lane_counts()  # Update counts for dashboard
                
            # Render scene
            scene = self.renderer.render(
                self.signal_states,
                self.vehicles,
                self.pedestrians,
                self.show_stations,
                self.emergency_alerts if len(self.emergency_alerts) > 0 else None,
                self.hospital_highlight  # Pass hospital highlight flag for blinking effect
            )
            
            # Draw accident if active
            if self.active_accident:
                self.renderer.draw_accident(scene, 
                    self.active_accident['wx'],
                    self.active_accident['wy'],
                    self.active_accident)
            
            # Draw scene
            self.screen.blit(scene, (0, 0))
            
            # Draw dashboard
            self.draw_dashboard()
            
            # Update display
            pygame.display.flip()
            
        # Cleanup
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    sim = TrafficSimulation3D()
    sim.run()
