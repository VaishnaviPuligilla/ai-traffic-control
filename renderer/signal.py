import pygame
from config import COLORS, SIGNAL_CONFIG

class TrafficSignal:
    """Represents a traffic signal for a lane"""
    
    def __init__(self, lane_id, x, y, direction):
        self.lane_id = lane_id
        self.x = x
        self.y = y
        self.direction = direction  # Which way traffic flows
        
        self.state = 'red'  # 'red', 'yellow', 'green'
        self.timer = 0
        self.duration = SIGNAL_CONFIG['min_green_time']
        
        # Visual settings
        self.width = 30
        self.height = 90
        self.light_radius = 10
        
        # Animation
        self.glow_intensity = 0
        self.glow_direction = 1
        
    def update(self, dt):
        """Update signal state and timer"""
        self.timer += dt
        
        # Glow animation
        self.glow_intensity += 0.05 * self.glow_direction
        if self.glow_intensity >= 1:
            self.glow_direction = -1
        elif self.glow_intensity <= 0:
            self.glow_direction = 1
            
    def set_state(self, state, duration=None):
        """Set signal state"""
        self.state = state
        self.timer = 0
        if duration:
            self.duration = duration
            
    def is_expired(self):
        """Check if current signal duration has expired"""
        return self.timer >= self.duration
    
    def get_remaining_time(self):
        """Get remaining time for current state"""
        return max(0, self.duration - self.timer)
    
    def draw(self, screen, view_mode='top_down'):
        """Draw the traffic signal"""
        if view_mode == 'top_down':
            self._draw_top_down(screen)
        elif view_mode == 'isometric':
            self._draw_isometric(screen)
        else:
            self._draw_top_down(screen)
            
    def _draw_top_down(self, screen):
        """Draw signal from top-down view"""
        # Signal housing
        housing_rect = pygame.Rect(
            self.x - self.width // 2,
            self.y - self.height // 2,
            self.width,
            self.height
        )
        
        # Draw housing with 3D effect
        pygame.draw.rect(screen, COLORS['dark_gray'], housing_rect, border_radius=5)
        pygame.draw.rect(screen, COLORS['black'], housing_rect, 2, border_radius=5)
        
        # Light positions
        light_y_offset = self.height // 4
        lights = [
            ('red', self.y - light_y_offset),
            ('yellow', self.y),
            ('green', self.y + light_y_offset)
        ]
        
        for color_name, ly in lights:
            # Determine if this light is on
            is_on = (self.state == color_name)
            
            # Get color with glow effect
            if is_on:
                base_color = COLORS[color_name]
                glow = int(50 * self.glow_intensity)
                color = tuple(min(255, c + glow) for c in base_color)
                
                # Draw glow effect
                glow_radius = self.light_radius + 5
                glow_surface = pygame.Surface((glow_radius * 4, glow_radius * 4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surface, (*base_color, 100), 
                                 (glow_radius * 2, glow_radius * 2), glow_radius * 2)
                screen.blit(glow_surface, 
                           (self.x - glow_radius * 2, ly - glow_radius * 2))
            else:
                # Dim color when off
                base_color = COLORS[color_name]
                color = tuple(c // 4 for c in base_color)
            
            # Draw the light
            pygame.draw.circle(screen, color, (self.x, ly), self.light_radius)
            pygame.draw.circle(screen, COLORS['black'], (self.x, ly), self.light_radius, 2)
            
        # Draw timer
        self._draw_timer(screen)
        
    def _draw_timer(self, screen):
        """Draw countdown timer near signal"""
        remaining = int(self.get_remaining_time())
        font = pygame.font.Font(None, 28)
        
        # Color based on remaining time
        if remaining <= 5:
            timer_color = COLORS['red']
        elif remaining <= 10:
            timer_color = COLORS['yellow']
        else:
            timer_color = COLORS['white']
            
        text = font.render(str(remaining), True, timer_color)
        text_rect = text.get_rect(center=(self.x, self.y + self.height // 2 + 20))
        
        # Background
        bg_rect = text_rect.inflate(10, 6)
        pygame.draw.rect(screen, COLORS['black'], bg_rect, border_radius=3)
        screen.blit(text, text_rect)
        
    def _draw_isometric(self, screen):
        """Draw signal in isometric view"""
        # Convert to isometric coordinates
        iso_x = self.x - self.y * 0.5
        iso_y = self.y * 0.5 + self.x * 0.25
        
        # Draw pole
        pole_height = 100
        pygame.draw.line(screen, COLORS['dark_gray'],
                        (iso_x, iso_y), (iso_x, iso_y - pole_height), 5)
        
        # Draw signal box
        box_y = iso_y - pole_height
        self._draw_3d_signal_box(screen, iso_x, box_y)
        
    def _draw_3d_signal_box(self, screen, x, y):
        """Draw a 3D signal box for isometric view"""
        w, h = 25, 70
        depth = 15
        
        # Front face
        front = [(x - w//2, y), (x + w//2, y),
                (x + w//2, y + h), (x - w//2, y + h)]
        pygame.draw.polygon(screen, COLORS['dark_gray'], front)
        
        # Top face
        top = [(x - w//2, y), (x + w//2, y),
              (x + w//2 + depth, y - depth//2), (x - w//2 + depth, y - depth//2)]
        pygame.draw.polygon(screen, COLORS['gray'], top)
        
        # Side face  
        side = [(x + w//2, y), (x + w//2 + depth, y - depth//2),
               (x + w//2 + depth, y + h - depth//2), (x + w//2, y + h)]
        pygame.draw.polygon(screen, (80, 80, 80), side)
        
        # Draw lights
        light_spacing = h // 4
        for i, (color_name, offset) in enumerate([('red', 1), ('yellow', 2), ('green', 3)]):
            ly = y + light_spacing * offset
            is_on = (self.state == color_name)
            color = COLORS[color_name] if is_on else tuple(c // 4 for c in COLORS[color_name])
            pygame.draw.circle(screen, color, (x, ly), 8)


class SignalController:
    """Controls all traffic signals at an intersection"""
    
    def __init__(self, num_lanes=4):
        self.signals = {}
        self.num_lanes = num_lanes
        self.current_green_lane = 0
        self.phase = 'green'  # 'green', 'yellow', 'all_red', 'pedestrian'
        self.pedestrian_phase = False
        self.pedestrian_timer = 0
        
        # Emergency override
        self.emergency_mode = False
        self.emergency_lane = -1
        self.previous_state = None
        
        # Timing
        self.cycle_count = 0
        
    def setup_signals(self, lane_positions):
        """Setup signals for each lane"""
        for lane_id, (x, y, direction) in lane_positions.items():
            self.signals[lane_id] = TrafficSignal(lane_id, x, y, direction)
            
        # Initialize first lane as green
        if self.signals:
            self.signals[0].set_state('green', SIGNAL_CONFIG['min_green_time'])
            
    def update(self, dt):
        """Update all signals"""
        for signal in self.signals.values():
            signal.update(dt)
            
        # Handle pedestrian phase
        if self.pedestrian_phase:
            self.pedestrian_timer += dt
            if self.pedestrian_timer >= SIGNAL_CONFIG['pedestrian_time']:
                self.end_pedestrian_phase()
                
    def set_lane_green(self, lane_id, duration):
        """Set a specific lane to green (called by RL agent)"""
        if self.emergency_mode and lane_id != self.emergency_lane:
            return False
            
        # First, transition current green to yellow
        if self.current_green_lane != lane_id:
            # Set current lane to red
            if self.current_green_lane in self.signals:
                self.signals[self.current_green_lane].set_state('red')
            
        # Set new lane to green
        duration = max(SIGNAL_CONFIG['min_green_time'], 
                      min(duration, SIGNAL_CONFIG['max_green_time']))
        
        if lane_id in self.signals:
            self.signals[lane_id].set_state('green', duration)
            self.current_green_lane = lane_id
            self.cycle_count += 1
            
        # Set all other lanes to red
        for lid, signal in self.signals.items():
            if lid != lane_id:
                signal.set_state('red')
                
        return True
    
    def trigger_emergency(self, lane_id):
        """Trigger emergency mode for a specific lane"""
        if not self.emergency_mode:
            # Save current state
            self.previous_state = {
                'lane': self.current_green_lane,
                'timer': self.signals[self.current_green_lane].timer if self.current_green_lane in self.signals else 0
            }
            
        self.emergency_mode = True
        self.emergency_lane = lane_id
        
        # Immediately set emergency lane to green
        for lid, signal in self.signals.items():
            if lid == lane_id:
                signal.set_state('green', 60)  # 60 seconds for emergency
            else:
                signal.set_state('red')
                
        self.current_green_lane = lane_id
        
    def clear_emergency(self):
        """Clear emergency mode"""
        self.emergency_mode = False
        self.emergency_lane = -1
        
        # Restore previous state or continue normally
        if self.previous_state:
            # Could restore or just continue with normal operation
            pass
        self.previous_state = None
        
    def start_pedestrian_phase(self):
        """Start pedestrian crossing phase"""
        self.pedestrian_phase = True
        self.pedestrian_timer = 0
        
        # All signals to red
        for signal in self.signals.values():
            signal.set_state('red')
            
    def end_pedestrian_phase(self):
        """End pedestrian crossing phase"""
        self.pedestrian_phase = False
        self.pedestrian_timer = 0
        
    def get_state(self):
        """Get current signal states for RL"""
        return {
            'current_green': self.current_green_lane,
            'emergency_mode': self.emergency_mode,
            'emergency_lane': self.emergency_lane,
            'pedestrian_phase': self.pedestrian_phase,
            'signals': {lid: s.state for lid, s in self.signals.items()}
        }
    
    def draw(self, screen, view_mode='top_down'):
        """Draw all signals"""
        for signal in self.signals.values():
            signal.draw(screen, view_mode)
