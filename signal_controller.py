import time
from config import SIGNAL_CONFIG


class SignalController:
    """
    Traffic signal controller with proper ambulance handling.
    If ambulance appears, it handles that lane first, then resumes original lane.
    """
    
    def __init__(self, num_lanes=4):
        self.num_lanes = num_lanes
        self.current_green = 0
        self.time_remaining = SIGNAL_CONFIG['DEFAULT_GREEN']
        self.last_update = time.time()
        
        # Ambulance handling
        self.emergency_mode = False
        self.emergency_lane = None
        self.previous_lane = None  # Lane to resume after ambulance passes
        self.previous_time_remaining = 0  # Time remaining when interrupted
        
        # Accident handling
        self.accident_mode = False
        self.accident_lane = None
        
        # Next lane prediction
        self.next_predicted_lane = 1
        
    def update(self, dt):
        """Update signal timing"""
        if self.time_remaining > 0:
            self.time_remaining -= dt
            
        if self.time_remaining <= 0:
            # Time expired, check if we need to resume previous lane
            if self.emergency_mode:
                # Emergency handled, resume previous lane
                self._resume_after_emergency()
            else:
                # Normal cycle - will be handled by AI decision
                pass
                
    def get_state(self):
        """Get current signal state"""
        return {
            'current_green': self.current_green,
            'time_remaining': max(0, self.time_remaining),
            'emergency_mode': self.emergency_mode,
            'emergency_lane': self.emergency_lane,
            'accident_mode': self.accident_mode,
            'accident_lane': self.accident_lane,
            'next_predicted': self.next_predicted_lane
        }
        
    def set_green(self, lane, duration):
        """Set green signal for a lane (AI decision)"""
        if self.emergency_mode:
            # Can't override emergency mode
            return False
            
        self.previous_lane = self.current_green
        self.current_green = lane
        self.time_remaining = duration
        
        # Predict next lane (simple round-robin for display)
        self.next_predicted_lane = (lane + 1) % self.num_lanes
        
        return True
        
    def trigger_emergency(self, ambulance_lane):
        """
        Handle ambulance emergency.
        Remember current lane to resume after ambulance passes.
        """
        if self.emergency_mode:
            return  # Already handling an emergency
            
        # Save current state to resume later
        self.previous_lane = self.current_green
        self.previous_time_remaining = max(0, self.time_remaining)
        
        # Switch to emergency mode
        self.emergency_mode = True
        self.emergency_lane = ambulance_lane
        
        # Give green to ambulance lane
        self.current_green = ambulance_lane
        self.time_remaining = 30  # Emergency green duration
        
        print(f"🚑 EMERGENCY: Ambulance in Lane {ambulance_lane + 1}. Was in Lane {self.previous_lane + 1}. Will resume after.")
        
    def emergency_cleared(self):
        """Called when ambulance has passed"""
        if not self.emergency_mode:
            return
            
        print(f"🚑 Ambulance passed. Resuming Lane {self.previous_lane + 1}")
        self._resume_after_emergency()
        
    def _resume_after_emergency(self):
        """Resume the lane that was interrupted by emergency"""
        self.emergency_mode = False
        
        if self.previous_lane is not None:
            # Resume the interrupted lane
            self.current_green = self.previous_lane
            # Give remaining time or a fresh cycle
            self.time_remaining = max(self.previous_time_remaining, SIGNAL_CONFIG['DEFAULT_GREEN'])
        else:
            # No previous lane, continue normally
            self.current_green = (self.emergency_lane + 1) % self.num_lanes
            self.time_remaining = SIGNAL_CONFIG['DEFAULT_GREEN']
            
        self.emergency_lane = None
        self.previous_lane = None
        self.previous_time_remaining = 0
        
    def trigger_accident(self, lane):
        """Handle accident in a lane"""
        self.accident_mode = True
        self.accident_lane = lane
        
    def clear_accident(self):
        """Clear accident"""
        self.accident_mode = False
        self.accident_lane = None
        
    def is_lane_blocked(self, lane):
        """Check if a lane is blocked by accident"""
        return self.accident_mode and self.accident_lane == lane
