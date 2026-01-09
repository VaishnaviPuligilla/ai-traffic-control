import numpy as np
import random
from config import (
    SIGNAL_CONFIG, VEHICLE_TYPES, RL_CONFIG, 
    REWARD_WEIGHTS, SPAWN_CONFIG
)

class TrafficEnvironment:
    """
    OpenAI Gym-style environment for traffic signal control
    
    State Space:
        - Lane vehicle densities (weighted by vehicle type)
        - Pedestrian counts per lane
        - Current green lane
        - Time elapsed on current green
        - Emergency flag (-1 if none, lane_id if emergency)
        - Accident flag (-1 if none, lane_id if accident)
        - Last N lanes served (for fairness)
        
    Action Space:
        - Discrete: (lane_id, time_index) encoded as single integer
        - lane_id: 0 to num_lanes-1
        - time_index: 0 to 8 (mapped to actual seconds)
        
    Reward:
        - Negative reward for waiting time
        - Negative reward for congestion
        - Large positive reward for clearing emergency
        - Penalty for lane starvation
    """
    
    def __init__(self, num_lanes=4):
        self.num_lanes = num_lanes
        
        # State tracking
        self.lane_vehicles = {i: [] for i in range(num_lanes)}
        self.lane_pedestrians = {i: 0 for i in range(num_lanes)}
        self.current_green_lane = 0
        self.green_time_elapsed = 0
        self.emergency_lane = -1
        self.accident_lane = -1
        self.lanes_served_history = []
        
        # Action space
        self.time_options = [4, 10, 20, 30, 40, 50, 60, 75, 90]  # seconds
        self.action_size = num_lanes * len(self.time_options)
        
        # State size
        self.state_size = RL_CONFIG['state_size']
        
        # Statistics
        self.total_wait_time = 0
        self.vehicles_passed = 0
        self.step_count = 0
        
    def reset(self):
        """Reset environment to initial state"""
        self.lane_vehicles = {i: [] for i in range(self.num_lanes)}
        self.lane_pedestrians = {i: random.randint(0, 5) for i in range(self.num_lanes)}
        self.current_green_lane = 0
        self.green_time_elapsed = 0
        self.emergency_lane = -1
        self.accident_lane = -1
        self.lanes_served_history = []
        self.total_wait_time = 0
        self.vehicles_passed = 0
        self.step_count = 0
        
        return self.get_state()
    
    def get_state(self):
        """
        Build state vector for RL agent
        
        Returns:
            numpy array of shape (state_size,)
        """
        state = []
        
        # Lane densities (weighted by vehicle type)
        for i in range(self.num_lanes):
            density = self._calculate_lane_weight(i)
            state.append(density / 50.0)  # Normalize
            
        # Pedestrian counts (normalized)
        for i in range(self.num_lanes):
            state.append(self.lane_pedestrians.get(i, 0) / 10.0)
            
        # Current green lane (one-hot could be better, but keeping simple)
        state.append(self.current_green_lane / self.num_lanes)
        
        # Time elapsed on current green (normalized to max)
        state.append(self.green_time_elapsed / SIGNAL_CONFIG['max_green_time'])
        
        # Emergency flag
        state.append(1.0 if self.emergency_lane >= 0 else 0.0)
        state.append(self.emergency_lane / self.num_lanes if self.emergency_lane >= 0 else 0.0)
        
        # Accident flag
        state.append(1.0 if self.accident_lane >= 0 else 0.0)
        
        return np.array(state, dtype=np.float32)
    
    def _calculate_lane_weight(self, lane_id):
        """Calculate weighted vehicle density for a lane"""
        vehicles = self.lane_vehicles.get(lane_id, [])
        total_weight = 0
        
        for v_type, count in vehicles:
            weight = VEHICLE_TYPES.get(v_type, {}).get('weight', 1)
            total_weight += weight * count
            
        return total_weight
    
    def step(self, action):
        """
        Execute action and return next state, reward, done
        
        Args:
            action: integer encoding (lane_id, time_index)
            
        Returns:
            next_state, reward, done, info
        """
        # Decode action
        lane_id = action // len(self.time_options)
        time_index = action % len(self.time_options)
        green_duration = self.time_options[time_index]
        
        # Execute action
        prev_lane = self.current_green_lane
        self.current_green_lane = lane_id
        self.green_time_elapsed = 0
        
        # Update served history
        self.lanes_served_history.append(lane_id)
        if len(self.lanes_served_history) > 10:
            self.lanes_served_history.pop(0)
        
        # Calculate reward
        reward = self._calculate_reward(lane_id, green_duration, prev_lane)
        
        # Simulate time passing
        self._simulate_traffic(green_duration)
        
        self.step_count += 1
        
        # Check if episode is done (e.g., after N steps)
        done = self.step_count >= 100
        
        info = {
            'lane_served': lane_id,
            'duration': green_duration,
            'vehicles_passed': self.vehicles_passed,
            'total_wait_time': self.total_wait_time
        }
        
        return self.get_state(), reward, done, info
    
    def _calculate_reward(self, lane_id, duration, prev_lane):
        """
        Calculate reward based on action taken
        
        NO RULES HERE - only reward shaping!
        The agent learns optimal behavior through rewards.
        """
        reward = 0.0
        
        # 1. Penalty for total waiting time across all lanes
        total_wait = sum(self._calculate_lane_weight(i) for i in range(self.num_lanes))
        reward += REWARD_WEIGHTS['wait_time'] * total_wait
        
        # 2. Penalty for pedestrian waiting
        total_ped_wait = sum(self.lane_pedestrians.values())
        reward += REWARD_WEIGHTS['pedestrian_wait'] * total_ped_wait
        
        # 3. Penalty for congestion variance (unfair distribution)
        weights = [self._calculate_lane_weight(i) for i in range(self.num_lanes)]
        if len(weights) > 1:
            variance = np.var(weights)
            reward += REWARD_WEIGHTS['congestion'] * variance / 100
        
        # 4. Emergency handling
        if self.emergency_lane >= 0:
            if lane_id == self.emergency_lane:
                reward += REWARD_WEIGHTS['emergency_bonus']
            else:
                reward += REWARD_WEIGHTS['emergency_penalty']
                
        # 5. Starvation penalty (if a lane hasn't been served recently)
        if len(self.lanes_served_history) >= 5:
            for i in range(self.num_lanes):
                if i not in self.lanes_served_history[-5:]:
                    lane_weight = self._calculate_lane_weight(i)
                    if lane_weight > 10:  # Only penalize if there's significant traffic
                        reward += REWARD_WEIGHTS['starvation']
        
        # 6. Reward for throughput (vehicles that will pass)
        served_weight = self._calculate_lane_weight(lane_id)
        throughput = min(served_weight, duration / 2)  # Rough estimate
        reward += REWARD_WEIGHTS['throughput'] * throughput
        
        # 7. Accident lane penalty (reduced capacity)
        if self.accident_lane >= 0 and lane_id == self.accident_lane:
            reward -= 5  # Discourage serving accident lane (reduced flow)
            
        return reward
    
    def _simulate_traffic(self, duration):
        """Simulate traffic flow during green signal"""
        # Vehicles pass through the green lane
        green_weight = self._calculate_lane_weight(self.current_green_lane)
        vehicles_passed = min(green_weight, duration / 3)
        self.vehicles_passed += vehicles_passed
        
        # Reduce vehicles in green lane
        self._reduce_lane_vehicles(self.current_green_lane, vehicles_passed)
        
        # Other lanes accumulate more vehicles (waiting)
        for i in range(self.num_lanes):
            if i != self.current_green_lane:
                wait_penalty = duration * self._calculate_lane_weight(i) * 0.1
                self.total_wait_time += wait_penalty
                
        # Randomly spawn new vehicles
        self._random_spawn()
        
        self.green_time_elapsed = duration
        
    def _reduce_lane_vehicles(self, lane_id, amount):
        """Reduce vehicle count in a lane"""
        vehicles = self.lane_vehicles.get(lane_id, [])
        remaining = amount
        
        new_vehicles = []
        for v_type, count in vehicles:
            weight = VEHICLE_TYPES.get(v_type, {}).get('weight', 1)
            can_remove = remaining / weight
            removed = min(count, int(can_remove))
            remaining -= removed * weight
            
            if count - removed > 0:
                new_vehicles.append((v_type, count - removed))
                
        self.lane_vehicles[lane_id] = new_vehicles
        
    def _random_spawn(self):
        """Randomly spawn vehicles in lanes"""
        for lane_id in range(self.num_lanes):
            if random.random() < SPAWN_CONFIG['base_rate'] * 10:
                v_type = random.choice(['car', 'car', 'car', 'bike', 'bike', 'truck'])
                
                # Add to existing or create new entry
                found = False
                for i, (vt, count) in enumerate(self.lane_vehicles[lane_id]):
                    if vt == v_type:
                        self.lane_vehicles[lane_id][i] = (vt, count + 1)
                        found = True
                        break
                        
                if not found:
                    self.lane_vehicles[lane_id].append((v_type, 1))
    
    def set_emergency(self, lane_id):
        """Set emergency vehicle in a lane"""
        self.emergency_lane = lane_id
        # Add ambulance to the lane
        self.lane_vehicles[lane_id].append(('ambulance', 1))
        
    def clear_emergency(self):
        """Clear emergency state"""
        self.emergency_lane = -1
        
    def set_accident(self, lane_id):
        """Set accident in a lane"""
        self.accident_lane = lane_id
        
    def clear_accident(self):
        """Clear accident state"""
        self.accident_lane = -1
        
    def set_lane_vehicles(self, lane_id, vehicles):
        """
        Set vehicles for a lane (from user configuration)
        
        Args:
            lane_id: Lane number
            vehicles: dict like {'truck': 2, 'car': 4, 'bike': 3}
        """
        self.lane_vehicles[lane_id] = [
            (v_type, count) for v_type, count in vehicles.items()
        ]
        
    def set_pedestrians(self, lane_id, count):
        """Set pedestrian count for a lane"""
        self.lane_pedestrians[lane_id] = count
        
    def get_lane_info(self):
        """Get information about all lanes for display"""
        info = {}
        for i in range(self.num_lanes):
            info[i] = {
                'weight': self._calculate_lane_weight(i),
                'vehicles': dict(self.lane_vehicles.get(i, [])),
                'pedestrians': self.lane_pedestrians.get(i, 0),
                'is_emergency': self.emergency_lane == i,
                'is_accident': self.accident_lane == i
            }
        return info
