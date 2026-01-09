import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
import numpy as np
import random
from collections import deque
from config import RL_CONFIG

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class DQN(nn.Module):
    """
    Deep Q-Network for traffic signal control
    
    Architecture:
        - Input: State vector
        - Hidden layers with ReLU activation
        - Output: Q-values for each action
    """
    
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()
        
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, 64)
        self.fc4 = nn.Linear(64, action_size)
        
        # Batch normalization for stability
        self.bn1 = nn.BatchNorm1d(128)
        self.bn2 = nn.BatchNorm1d(128)
        
        # Dropout for regularization
        self.dropout = nn.Dropout(0.1)
        
    def forward(self, x):
        # Handle single sample vs batch
        if x.dim() == 1:
            x = x.unsqueeze(0)
            single = True
        else:
            single = False
            
        x = F.relu(self.fc1(x))
        if x.size(0) > 1:
            x = self.bn1(x)
        x = self.dropout(x)
        
        x = F.relu(self.fc2(x))
        if x.size(0) > 1:
            x = self.bn2(x)
        x = self.dropout(x)
        
        x = F.relu(self.fc3(x))
        x = self.fc4(x)
        
        if single:
            x = x.squeeze(0)
            
        return x


class ReplayMemory:
    """Experience replay buffer for stable learning"""
    
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)
        
    def push(self, state, action, reward, next_state, done):
        """Store a transition"""
        self.memory.append((state, action, reward, next_state, done))
        
    def sample(self, batch_size):
        """Random sample from memory"""
        batch = random.sample(self.memory, batch_size)
        
        states = torch.FloatTensor([t[0] for t in batch]).to(device)
        actions = torch.LongTensor([t[1] for t in batch]).to(device)
        rewards = torch.FloatTensor([t[2] for t in batch]).to(device)
        next_states = torch.FloatTensor([t[3] for t in batch]).to(device)
        dones = torch.FloatTensor([t[4] for t in batch]).to(device)
        
        return states, actions, rewards, next_states, dones
    
    def __len__(self):
        return len(self.memory)


class DQNAgent:
    """
    DQN Agent for traffic signal control
    
    Features:
        - Double DQN for stable learning
        - Experience replay
        - Epsilon-greedy exploration
        - Target network for stability
    """
    
    def __init__(self, state_size, action_size, num_lanes=4):
        self.state_size = state_size
        self.action_size = action_size
        self.num_lanes = num_lanes
        
        # Time options for decoding actions
        self.time_options = [4, 10, 20, 30, 40, 50, 60, 75, 90]
        
        # Networks
        self.policy_net = DQN(state_size, action_size).to(device)
        self.target_net = DQN(state_size, action_size).to(device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.policy_net.parameters(),
            lr=RL_CONFIG['learning_rate']
        )
        
        # Replay memory
        self.memory = ReplayMemory(RL_CONFIG['memory_size'])
        
        # Exploration parameters
        self.epsilon = RL_CONFIG['epsilon_start']
        self.epsilon_end = RL_CONFIG['epsilon_end']
        self.epsilon_decay = RL_CONFIG['epsilon_decay']
        
        # Training parameters
        self.gamma = RL_CONFIG['gamma']
        self.batch_size = RL_CONFIG['batch_size']
        self.target_update = RL_CONFIG['target_update']
        
        # Statistics
        self.steps_done = 0
        self.episodes_done = 0
        self.training_losses = []
        
    def select_action(self, state, training=True):
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: Current state vector
            training: If True, use exploration; if False, greedy only
            
        Returns:
            action: Integer representing (lane_id, time_index)
        """
        # Exploration vs exploitation
        if training and random.random() < self.epsilon:
            # Random action
            action = random.randrange(self.action_size)
        else:
            # Greedy action
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).to(device)
                self.policy_net.eval()
                q_values = self.policy_net(state_tensor)
                self.policy_net.train()
                action = q_values.argmax().item()
                
        self.steps_done += 1
        return action
    
    def select_action_with_emergency(self, state, emergency_lane=-1):
        """
        Select action with emergency override consideration
        
        The reward structure already handles this, but we can add
        a soft bias during inference for safety.
        """
        if emergency_lane >= 0:
            # Strong bias towards emergency lane during inference
            # But still let the learned policy have influence
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).to(device)
                self.policy_net.eval()
                q_values = self.policy_net(state_tensor).cpu().numpy()
                self.policy_net.train()
                
                # Add bonus to emergency lane actions
                for time_idx in range(len(self.time_options)):
                    action_idx = emergency_lane * len(self.time_options) + time_idx
                    q_values[action_idx] += 100  # Large bonus
                    
                return np.argmax(q_values)
        else:
            return self.select_action(state, training=False)
    
    def decode_action(self, action):
        """
        Decode action integer to (lane_id, green_duration)
        
        Returns:
            lane_id: Which lane gets green
            duration: How long in seconds
        """
        lane_id = action // len(self.time_options)
        time_index = action % len(self.time_options)
        duration = self.time_options[time_index]
        return lane_id, duration
    
    def store_transition(self, state, action, reward, next_state, done):
        """Store transition in replay memory"""
        self.memory.push(state, action, reward, next_state, done)
        
    def learn(self):
        """
        Perform one step of learning
        
        Uses Double DQN update rule for stability
        """
        if len(self.memory) < self.batch_size:
            return None
            
        # Sample from memory
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Current Q values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Double DQN: use policy net to select action, target net to evaluate
        with torch.no_grad():
            # Select best actions using policy network
            best_actions = self.policy_net(next_states).argmax(1, keepdim=True)
            # Evaluate using target network
            next_q = self.target_net(next_states).gather(1, best_actions)
            # Compute target
            target_q = rewards.unsqueeze(1) + (1 - dones.unsqueeze(1)) * self.gamma * next_q
            
        # Compute loss
        loss = F.smooth_l1_loss(current_q, target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        # Gradient clipping for stability
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        self.training_losses.append(loss.item())
        return loss.item()
    
    def update_target_network(self):
        """Copy policy network weights to target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
        
    def end_episode(self):
        """Called at the end of each episode"""
        self.episodes_done += 1
        
        # Update target network periodically
        if self.episodes_done % self.target_update == 0:
            self.update_target_network()
            
    def save(self, filepath):
        """Save model to file"""
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done,
            'episodes_done': self.episodes_done,
        }, filepath)
        
    def load(self, filepath):
        """Load model from file"""
        checkpoint = torch.load(filepath, map_location=device)
        self.policy_net.load_state_dict(checkpoint['policy_net'])
        self.target_net.load_state_dict(checkpoint['target_net'])
        self.optimizer.load_state_dict(checkpoint['optimizer'])
        self.epsilon = checkpoint['epsilon']
        self.steps_done = checkpoint['steps_done']
        self.episodes_done = checkpoint['episodes_done']
        
    def get_q_values(self, state):
        """Get Q-values for all actions (for visualization)"""
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).to(device)
            self.policy_net.eval()
            q_values = self.policy_net(state_tensor).cpu().numpy()
            self.policy_net.train()
            return q_values
            
    def get_action_probabilities(self, state, temperature=1.0):
        """Get softmax probabilities for actions (for visualization)"""
        q_values = self.get_q_values(state)
        exp_q = np.exp((q_values - np.max(q_values)) / temperature)
        return exp_q / exp_q.sum()
    
    def get_stats(self):
        """Get training statistics"""
        return {
            'epsilon': self.epsilon,
            'steps': self.steps_done,
            'episodes': self.episodes_done,
            'memory_size': len(self.memory),
            'avg_loss': np.mean(self.training_losses[-100:]) if self.training_losses else 0
        }


class SimpleRuleBasedAgent:
    """
    Simple rule-based agent for comparison
    
    This is NOT used in the main system - only for baseline comparison
    to show how much better RL performs.
    """
    
    def __init__(self, num_lanes=4):
        self.num_lanes = num_lanes
        self.time_options = [4, 10, 20, 30, 40, 50, 60, 75, 90]
        self.current_lane = 0
        
    def select_action(self, state):
        """Round-robin lane selection with fixed timing"""
        # Simple round-robin
        lane = self.current_lane
        self.current_lane = (self.current_lane + 1) % self.num_lanes
        
        # Fixed 30 second timing
        time_idx = self.time_options.index(30)
        
        return lane * len(self.time_options) + time_idx
    
    def decode_action(self, action):
        lane_id = action // len(self.time_options)
        time_index = action % len(self.time_options)
        duration = self.time_options[time_index]
        return lane_id, duration
