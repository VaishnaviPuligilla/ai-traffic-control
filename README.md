# 🚦 AI Traffic Signal Simulation

## Reinforcement Learning-based Traffic Signal Control Demo

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)

A real-time interactive traffic signal simulator demonstrating how **Reinforcement Learning (RL)** can be used to optimize traffic flow. This project showcases decision intelligence without any hard-coded rules - the AI learns optimal behavior through rewards.

---

## 🎯 Key Features

- **Pure Reinforcement Learning**: No rule-based decisions - AI learns through experience
- **Real-time Visualization**: Game-like animated simulation with Pygame
- **Dynamic Vehicle Spawning**: Vehicles appear randomly, creating unique scenarios
- **Emergency Response**: Ambulance priority and accident handling
- **Live Analytics Panel**: Real-time statistics and AI predictions
- **Multiple View Modes**: Top-down and isometric (2.5D) views
- **Pattern Learning**: Stores and learns from historical traffic patterns

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│        (Configuration + Live Simulation)             │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              Traffic Environment                     │
│     (Lanes, Vehicles, Pedestrians, Events)          │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                 State Builder                        │
│        (Observation Vector for RL Agent)            │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│           DQN Reinforcement Learning Agent          │
│      (Deep Q-Network with Experience Replay)        │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│              Signal Decision Engine                  │
│         (Lane Selection + Duration)                  │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│             Event Override System                    │
│       (Emergency & Accident Handling)               │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│                   Database                          │
│     (Patterns + Decisions + Learning History)       │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Run the Simulation

```bash
cd D:\AIT
D:/AIT/.venv/Scripts/python.exe main.py
```

### 2. Pre-train the AI (Optional but Recommended)

```bash
D:/AIT/.venv/Scripts/python.exe train.py --episodes 500
```

---

## 🎮 How to Use

### Step 1: Configuration
1. Choose **4 lanes** or **6 lanes**
2. Select view mode: **Top-down** or **Isometric**
3. Click **Next**

### Step 2: Vehicle Setup
1. Use **+/-** buttons to add vehicles per lane
2. Vehicle types: 🚛 Truck, 🚗 Car, 🏍️ Bike, 🚶 Pedestrian
3. Click **Start Simulation**

### Step 3: Watch the AI Learn
- AI makes signal decisions every cycle
- Watch the analytics panel for real-time stats
- Use buttons to trigger events:
  - 🚑 **Ambulance**: Emergency priority override
  - ⚠️ **Accident**: Triggers alerts, reduces lane capacity

### Controls
| Key/Button | Action |
|------------|--------|
| `SPACE` | Pause/Resume |
| `ESC` | Pause menu |
| Speed button | Toggle 1x/2x/4x speed |
| Save Model | Save trained AI model |
| Reset | Restart simulation |

---

## 🤖 Reinforcement Learning Details

### State Space (What AI Observes)
```python
state = [
    lane_1_vehicle_weight,    # Weighted density of lane 1
    lane_2_vehicle_weight,    # Weighted density of lane 2
    lane_3_vehicle_weight,    # Weighted density of lane 3
    lane_4_vehicle_weight,    # Weighted density of lane 4
    pedestrians_lane_1,       # Pedestrian count
    pedestrians_lane_2,
    pedestrians_lane_3,
    pedestrians_lane_4,
    current_green_lane,       # Which lane is green
    green_time_elapsed,       # How long current green
    emergency_flag,           # Is emergency active?
    emergency_lane,           # Which lane has emergency
    accident_flag             # Is accident active?
]
```

### Action Space (What AI Can Do)
```
Action = (lane_id, time_duration)

lane_id: 0-3 (or 0-5 for 6 lanes)
time_duration: [4, 10, 20, 30, 40, 50, 60, 75, 90] seconds
```

### Reward Function (How AI Learns)
```python
reward = (
    - α × total_vehicle_wait_time      # Penalty for waiting
    - β × pedestrian_wait_time         # Penalty for pedestrians waiting
    - γ × lane_congestion_variance     # Penalty for unfair distribution
    + δ × emergency_clearance_bonus    # Big bonus for clearing ambulance
    - ε × emergency_ignore_penalty     # Big penalty for ignoring emergency
    - ζ × lane_starvation_penalty      # Penalty for ignoring lanes too long
    + η × vehicle_throughput           # Reward for vehicles passing
)
```

### Why This Works
- **No Hard-Coded Rules**: AI doesn't know "give ambulance green"
- **Learns from Rewards**: Gets huge bonus when ambulance clears
- **Discovers Strategy**: Naturally learns to prioritize emergencies
- **Generalizes**: Adapts to any traffic pattern

---

## 📁 Project Structure

```
D:\AIT\
│
├── main.py                 # 🎮 Main entry point
├── train.py                # 🤖 Headless training script
├── config.py               # ⚙️ Configuration settings
│
├── ai/
│   ├── __init__.py
│   ├── environment.py      # 🌍 RL Environment (Gym-style)
│   └── agent.py            # 🧠 DQN Agent
│
├── renderer/
│   ├── __init__.py
│   ├── road.py             # 🛣️ Road and junction rendering
│   ├── vehicle.py          # 🚗 Vehicle classes
│   └── signal.py           # 🚦 Traffic signal classes
│
├── ui/
│   ├── __init__.py
│   ├── components.py       # 🎨 UI widgets (buttons, panels)
│   └── config_screen.py    # 📋 Configuration screen
│
├── database/
│   ├── __init__.py
│   └── db_manager.py       # 💾 SQLite database manager
│
├── utils/
│   ├── __init__.py
│   └── helpers.py          # 🔧 Utility functions
│
├── models/                 # 📦 Saved AI models
│   └── traffic_agent.pth
│
└── traffic_data.db         # 📊 Traffic patterns database
```

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.8+ |
| Graphics | Pygame 2.0+ |
| AI/ML | PyTorch |
| Data | NumPy, SQLite |
| Visualization | Matplotlib (for training curves) |

---

## 📈 Performance Characteristics

| Parameter | Value |
|-----------|-------|
| Min Green Time | 3-4 seconds |
| Max Green Time | 90 seconds |
| Decision Interval | ~5 seconds |
| Pedestrian Window | Mandatory |
| Emergency Override | Immediate |

---

## 🎓 Interview Talking Points

1. **Reinforcement Learning**: "The system uses a Deep Q-Network that learns signal timing purely through rewards, not rules."

2. **State Representation**: "I carefully designed a state vector that captures vehicle density, waiting times, and emergency status."

3. **Reward Engineering**: "The reward function balances multiple objectives: throughput, fairness, and emergency response."

4. **Real-time Constraints**: "The system operates under real traffic constraints: min/max signal times, pedestrian phases."

5. **Emergent Behavior**: "The AI naturally learns to prioritize ambulances because ignoring them results in heavy penalties."

---

## ✅ Pros

- Demonstrates AI decision-making clearly
- No hard-coded traffic rules
- Explainable behavior through rewards
- Handles dynamic events
- Scalable to different configurations
- Real-time visualization

## ❌ Limitations (Be Honest!)

- Not connected to real infrastructure
- Simplified traffic physics
- Assumes accurate vehicle detection
- Single intersection only

---

## 📜 License

MIT License - Feel free to use for learning, interviews, and demonstrations.

---

## 🙏 Acknowledgments

- OpenAI Gym for the environment design pattern
- PyTorch for deep learning framework
- Pygame community for visualization tools

---

**Built with ❤️ for demonstrating AI in traffic control**
