import pygame

# Window Settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60
TITLE = "AI Traffic Signal Simulation - Reinforcement Learning Demo"

# Colors (RGB)
COLORS = {
    'black': (0, 0, 0),
    'white': (255, 255, 255),
    'gray': (128, 128, 128),
    'dark_gray': (64, 64, 64),
    'light_gray': (192, 192, 192),
    'road': (50, 50, 50),
    'road_marking': (255, 255, 255),
    'grass': (34, 139, 34),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0),
    'orange': (255, 165, 0),
    'blue': (0, 100, 255),
    'light_blue': (135, 206, 235),
    'dark_blue': (0, 0, 139),
    'panel_bg': (30, 30, 40),
    'panel_border': (100, 100, 120),
    'ambulance_red': (220, 20, 60),
    'police_blue': (0, 0, 200),
}

# Vehicle Settings
VEHICLE_TYPES = {
    'truck': {
        'weight': 4,
        'length': 60,
        'width': 30,
        'speed': 2,
        'color': (139, 69, 19),  # Brown
        'name': 'Truck'
    },
    'car': {
        'weight': 2,
        'length': 40,
        'width': 24,
        'speed': 3,
        'color': (65, 105, 225),  # Royal Blue
        'name': 'Car'
    },
    'bike': {
        'weight': 1,
        'length': 25,
        'width': 12,
        'speed': 4,
        'color': (255, 140, 0),  # Dark Orange
        'name': 'Motorcycle'
    },
    'ambulance': {
        'weight': 5,
        'length': 55,
        'width': 28,
        'speed': 5,
        'color': (255, 255, 255),  # White with red cross
        'name': 'Ambulance',
        'priority': True
    },
    'pedestrian': {
        'weight': 1,
        'length': 10,
        'width': 10,
        'speed': 1,
        'color': (255, 182, 193),  # Light Pink
        'name': 'Pedestrian'
    }
}

# Traffic Signal Settings
SIGNAL_CONFIG = {
    'min_green_time': 4,      # Minimum green signal time (seconds)
    'max_green_time': 90,     # Maximum green signal time (seconds)
    'DEFAULT_GREEN': 20,      # Default green signal duration
    'yellow_time': 3,         # Yellow signal duration (seconds)
    'all_red_time': 2,        # All-red clearance time (seconds)
    'pedestrian_time': 15,    # Pedestrian crossing time (seconds)
}

# Lane Configuration
LANE_CONFIG = {
    'width': 50,
    'marking_width': 3,
    'stop_line_distance': 100,
}

# Reinforcement Learning Settings
RL_CONFIG = {
    'state_size': 13,         # Size of state vector
    'action_size': 36,        # 4 lanes * 9 time options
    'gamma': 0.99,            # Discount factor
    'epsilon_start': 1.0,     # Initial exploration rate
    'epsilon_end': 0.01,      # Final exploration rate
    'epsilon_decay': 0.995,   # Exploration decay rate
    'learning_rate': 0.001,
    'batch_size': 64,
    'memory_size': 10000,
    'target_update': 10,      # Update target network every N episodes
}

# Reward Weights
REWARD_WEIGHTS = {
    'wait_time': -0.1,        # Penalty per vehicle waiting
    'pedestrian_wait': -0.15, # Penalty for pedestrian waiting
    'congestion': -0.2,       # Penalty for congestion
    'emergency_bonus': 50.0,  # Bonus for clearing emergency
    'emergency_penalty': -30.0, # Penalty for ignoring emergency
    'starvation': -0.5,       # Penalty for ignoring a lane too long
    'throughput': 0.5,        # Reward for vehicles passing
}

# Spawn Settings
SPAWN_CONFIG = {
    'base_rate': 0.02,        # Base probability of spawning per frame
    'max_vehicles_per_lane': 15,
}

# UI Settings
UI_CONFIG = {
    'panel_width': 350,
    'button_height': 40,
    'font_size': 18,
    'title_font_size': 24,
    'margin': 10,
}

# Database Settings
DB_CONFIG = {
    'db_path': 'traffic_data.db',
}

# Time Settings (game time multiplier)
TIME_SCALE = 1.0  # 1.0 = real-time, 2.0 = 2x speed

# View Modes
VIEW_MODES = ['top_down', 'isometric', 'side']
DEFAULT_VIEW = 'top_down'
