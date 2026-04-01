# C. elegans Brain Simulation - Interactive

🧠 **Enhanced C. elegans neural network simulation with interactive robot control**

## Features

- ✅ **+10 Neurons**: 312 total neurons (original 302 + 10 enhanced)
- ✅ **+20+ Neural Connections**: Enhanced synaptic connectivity
- ✅ **Interactive Control**: Control the worm like a robot using keyboard/mouse
- ✅ **Object Manipulation**: Create walls, food, materials; pick up and carry objects
- ✅ **Real-time Brain Monitoring**: Watch neural activity as it happens
- ✅ **Signal Visualization**: Brighter red dots = stronger neural signals between neurons
- ✅ **Cross-Platform**: Works on Windows, Linux, and macOS
- ✅ **Error Resilient**: No crashes on errors - gracefully handles exceptions

## Installation

### Requirements
- Python 3.7+
- numpy
- pygame (for interactive mode)

### Install Dependencies
```bash
pip install numpy pygame
```

## Usage

### Run Interactive Simulation
```bash
python3 c_elegans_brain_sim.py
```

### Controls

| Key/Action | Function |
|------------|----------|
| **Arrow Keys** | Move worm manually |
| **Space** | Pause/Resume simulation |
| **1** | Select Wall object |
| **2** | Select Food object |
| **3** | Select Material object |
| **4** | Select Obstacle object |
| **Left Click** | Place object / Pick up object |
| **Right Click** | Remove object |
| **H** | Toggle help panel |
| **R** | Reset simulation |
| **Escape** | Quit |

## How It Works

### Brain Model
- **312 Neurons**: Sensory, Interneurons, Motor, and Modulatory neurons
- **Leaky Integrate-and-Fire Model**: Biologically realistic neuron dynamics
- **Chemical & Electrical Synapses**: Two types of neural connections
- **Short-term Plasticity**: Synapses strengthen/weaken with activity

### Interactive Features
1. **Sensory Input**: Worm detects food, walls, and carried objects
2. **Brain Processing**: Neural network processes sensory inputs
3. **Motor Output**: Brain activity controls worm movement
4. **Object Interaction**: Build environments and watch how the worm reacts

### Visualization Panel
The right panel shows:
- **Network Statistics**: Total neurons, synapses, timestep
- **Active Neurons**: Top 10 most active neurons with activation bars
- **Active Synapses**: Signal propagation between neurons
  - 🔴 **Bright red dot** = Strong signal
  - 🟤 **Dark red dot** = Weak signal
  - Dot size also indicates signal strength

## Cross-Platform Installation

### Windows
```cmd
pip install numpy pygame
python c_elegans_brain_sim.py
```

### Linux
```bash
pip3 install numpy pygame
python3 c_elegans_brain_sim.py
```

### macOS
```bash
pip3 install numpy pygame
python3 c_elegans_brain_sim.py
```

#### Create macOS .pkg Installer
```bash
chmod +x create_pkg.sh
./create_pkg.sh
```
This creates `CElegansBrainSimulator.pkg` for easy installation.

## Network Statistics

- **Total Neurons**: 312
  - Sensory: ~95
  - Interneurons: ~70
  - Motor: ~137
  - Enhanced: 10 (EN1-EN10)
  
- **Total Synapses**: ~7000+
  - Chemical synapses
  - Electrical synapses (gap junctions)

- **Enhanced Neurons** (EN1-EN10):
  - EN1, EN2: Additional sensory neurons
  - EN3-EN6: Additional interneurons
  - EN7-EN9: Additional motor neurons
  - EN10: Novel modulatory neuron

## Project Structure

```
/workspace/
├── c_elegans_brain_sim.py    # Main simulation script
├── setup.py                   # Python package installer
├── create_pkg.sh             # macOS .pkg creator
├── README.md                 # This file
└── ИНСТРУКЦИЯ.md            # Russian instructions
```

## Based On

This project extends concepts from [OpenWorm Analysis Toolbox](https://github.com/openworm/open-worm-analysis-toolbox) with additional features for interactive control and visualization.

## License

MIT License
