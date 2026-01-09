import os
import sys
import numpy as np
from tqdm import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai import TrafficEnvironment, DQNAgent
from config import RL_CONFIG


def train_agent(num_episodes=500, save_every=50):
    """
    Train the RL agent in headless mode (no graphics)
    
    This allows fast training before running the visual demo.
    """
    print("=" * 50)
    print("🤖 Training Traffic Signal AI Agent")
    print("=" * 50)
    print()
    
    # Initialize environment and agent
    num_lanes = 4
    env = TrafficEnvironment(num_lanes)
    agent = DQNAgent(
        state_size=env.state_size,
        action_size=env.action_size,
        num_lanes=num_lanes
    )
    
    # Training metrics
    episode_rewards = []
    episode_lengths = []
    best_avg_reward = float('-inf')
    
    # Create models directory
    os.makedirs("models", exist_ok=True)
    
    print(f"Training for {num_episodes} episodes...")
    print(f"State size: {env.state_size}, Action size: {env.action_size}")
    print()
    
    for episode in tqdm(range(num_episodes), desc="Training"):
        state = env.reset()
        episode_reward = 0
        steps = 0
        
        # Random initial conditions
        for lane_id in range(num_lanes):
            vehicles = {}
            if np.random.random() < 0.7:
                vehicles['car'] = np.random.randint(1, 8)
            if np.random.random() < 0.4:
                vehicles['truck'] = np.random.randint(1, 4)
            if np.random.random() < 0.5:
                vehicles['bike'] = np.random.randint(1, 6)
            env.set_lane_vehicles(lane_id, vehicles)
            env.set_pedestrians(lane_id, np.random.randint(0, 5))
        
        # Randomly add emergency or accident
        if np.random.random() < 0.1:
            env.set_emergency(np.random.randint(0, num_lanes))
        if np.random.random() < 0.05:
            env.set_accident(np.random.randint(0, num_lanes))
        
        done = False
        while not done:
            # Select action
            action = agent.select_action(state, training=True)
            
            # Take step
            next_state, reward, done, info = env.step(action)
            
            # Store transition
            agent.store_transition(state, action, reward, next_state, done)
            
            # Learn
            agent.learn()
            
            state = next_state
            episode_reward += reward
            steps += 1
            
            # Limit episode length
            if steps >= 100:
                done = True
        
        agent.end_episode()
        episode_rewards.append(episode_reward)
        episode_lengths.append(steps)
        
        # Logging
        if (episode + 1) % 10 == 0:
            avg_reward = np.mean(episode_rewards[-10:])
            avg_length = np.mean(episode_lengths[-10:])
            
            tqdm.write(f"Episode {episode + 1}: Avg Reward = {avg_reward:.2f}, "
                      f"Avg Length = {avg_length:.1f}, Epsilon = {agent.epsilon:.3f}")
        
        # Save best model
        if (episode + 1) % save_every == 0:
            avg_reward = np.mean(episode_rewards[-50:])
            
            if avg_reward > best_avg_reward:
                best_avg_reward = avg_reward
                agent.save("models/traffic_agent_best.pth")
                tqdm.write(f"💾 New best model saved! Avg reward: {avg_reward:.2f}")
            
            # Also save regular checkpoint
            agent.save("models/traffic_agent.pth")
    
    # Final save
    agent.save("models/traffic_agent.pth")
    
    print()
    print("=" * 50)
    print("✅ Training Complete!")
    print(f"   Final Epsilon: {agent.epsilon:.4f}")
    print(f"   Best Avg Reward: {best_avg_reward:.2f}")
    print(f"   Model saved to: models/traffic_agent.pth")
    print("=" * 50)
    
    # Plot training curve
    try:
        import matplotlib.pyplot as plt
        
        # Smooth rewards
        window = 20
        smoothed = np.convolve(episode_rewards, np.ones(window)/window, mode='valid')
        
        plt.figure(figsize=(12, 5))
        
        plt.subplot(1, 2, 1)
        plt.plot(episode_rewards, alpha=0.3, label='Raw')
        plt.plot(range(window-1, len(episode_rewards)), smoothed, label='Smoothed')
        plt.xlabel('Episode')
        plt.ylabel('Reward')
        plt.title('Training Rewards')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        plt.subplot(1, 2, 2)
        plt.plot(agent.training_losses[-500:])
        plt.xlabel('Training Step')
        plt.ylabel('Loss')
        plt.title('Training Loss (last 500 steps)')
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('models/training_curve.png', dpi=150)
        plt.show()
        
        print("📊 Training curve saved to: models/training_curve.png")
        
    except ImportError:
        print("Note: Install matplotlib to see training curves")
    
    return agent


def evaluate_agent(agent, num_episodes=20):
    """Evaluate trained agent"""
    print()
    print("Evaluating agent...")
    
    env = TrafficEnvironment(4)
    total_rewards = []
    
    for _ in range(num_episodes):
        state = env.reset()
        
        # Set up scenario
        for lane_id in range(4):
            vehicles = {'car': np.random.randint(2, 6), 'bike': np.random.randint(0, 3)}
            env.set_lane_vehicles(lane_id, vehicles)
        
        episode_reward = 0
        done = False
        steps = 0
        
        while not done and steps < 100:
            action = agent.select_action(state, training=False)
            state, reward, done, _ = env.step(action)
            episode_reward += reward
            steps += 1
        
        total_rewards.append(episode_reward)
    
    print(f"Evaluation Results:")
    print(f"  Average Reward: {np.mean(total_rewards):.2f} ± {np.std(total_rewards):.2f}")
    print(f"  Min Reward: {np.min(total_rewards):.2f}")
    print(f"  Max Reward: {np.max(total_rewards):.2f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train Traffic Signal AI Agent')
    parser.add_argument('--episodes', type=int, default=500, help='Number of training episodes')
    parser.add_argument('--save-every', type=int, default=50, help='Save model every N episodes')
    parser.add_argument('--evaluate', action='store_true', help='Evaluate after training')
    
    args = parser.parse_args()
    
    agent = train_agent(args.episodes, args.save_every)
    
    if args.evaluate:
        evaluate_agent(agent)
