import time


class GameTimer:
    """Manages game time and FPS"""
    
    def __init__(self, fps=60):
        self.fps = fps
        self.clock = None
        self.dt = 0
        self.game_time = 0
        self.real_time_start = 0
        self.paused = False
        self.time_scale = 1.0
        
    def start(self):
        """Start the timer"""
        import pygame
        self.clock = pygame.time.Clock()
        self.real_time_start = time.time()
        
    def tick(self):
        """Update timer (call each frame)"""
        if self.clock is None:
            self.start()
            
        self.dt = self.clock.tick(self.fps) / 1000.0  # Convert to seconds
        
        if not self.paused:
            self.game_time += self.dt * self.time_scale
            
        return self.dt
    
    def get_fps(self):
        """Get current FPS"""
        if self.clock:
            return int(self.clock.get_fps())
        return 0
    
    def pause(self):
        """Pause the game time"""
        self.paused = True
        
    def resume(self):
        """Resume the game time"""
        self.paused = False
        
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        
    def set_speed(self, scale):
        """Set time scale (1.0 = normal, 2.0 = 2x speed)"""
        self.time_scale = max(0.1, min(5.0, scale))


class StatisticsTracker:
    """Tracks and computes simulation statistics"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset all statistics"""
        self.total_vehicles_spawned = 0
        self.total_vehicles_passed = 0
        self.total_wait_time = 0
        self.emergency_count = 0
        self.accident_count = 0
        self.signal_changes = 0
        self.lane_serve_counts = {i: 0 for i in range(6)}
        self.lane_wait_times = {i: 0 for i in range(6)}
        
        # Time series data for graphs
        self.wait_time_history = []
        self.throughput_history = []
        
    def record_vehicle_spawn(self, lane_id):
        """Record a vehicle spawn"""
        self.total_vehicles_spawned += 1
        
    def record_vehicle_passed(self, lane_id, wait_time):
        """Record a vehicle passing through"""
        self.total_vehicles_passed += 1
        self.total_wait_time += wait_time
        self.lane_wait_times[lane_id] = self.lane_wait_times.get(lane_id, 0) + wait_time
        
    def record_signal_change(self, lane_id, duration):
        """Record a signal change"""
        self.signal_changes += 1
        self.lane_serve_counts[lane_id] = self.lane_serve_counts.get(lane_id, 0) + 1
        
    def record_emergency(self):
        """Record an emergency event"""
        self.emergency_count += 1
        
    def record_accident(self):
        """Record an accident event"""
        self.accident_count += 1
        
    def get_average_wait_time(self):
        """Get average wait time per vehicle"""
        if self.total_vehicles_passed == 0:
            return 0
        return self.total_wait_time / self.total_vehicles_passed
    
    def get_throughput(self):
        """Get total throughput"""
        return self.total_vehicles_passed
    
    def get_summary(self):
        """Get statistics summary"""
        return {
            'total_spawned': self.total_vehicles_spawned,
            'total_passed': self.total_vehicles_passed,
            'avg_wait_time': self.get_average_wait_time(),
            'throughput': self.get_throughput(),
            'emergencies': self.emergency_count,
            'accidents': self.accident_count,
            'signal_changes': self.signal_changes,
            'lane_distribution': self.lane_serve_counts
        }


def clamp(value, min_val, max_val):
    """Clamp value between min and max"""
    return max(min_val, min(max_val, value))


def lerp(a, b, t):
    """Linear interpolation between a and b"""
    return a + (b - a) * clamp(t, 0, 1)


def format_time(seconds):
    """Format seconds as MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def weighted_random_choice(choices, weights):
    """Make a weighted random choice"""
    import random
    total = sum(weights)
    r = random.uniform(0, total)
    cumulative = 0
    for choice, weight in zip(choices, weights):
        cumulative += weight
        if r <= cumulative:
            return choice
    return choices[-1]
