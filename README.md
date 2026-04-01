# C. elegans Brain Simulator

Enhanced neural network simulation based on the OpenWorm Analysis Toolbox project.

## Features

- **312 neurons** (original 302 + 10 enhanced neurons)
- **Enhanced synaptic connectivity** (+20 additional connections)
- **Neuromodulation support** - adjust network excitability
- **Cross-platform compatibility** - Windows, Linux, macOS
- **Leaky integrate-and-fire neuron model**
- **Chemical and electrical synapses**
- **Short-term synaptic plasticity**

## Installation

### Windows

```bash
# Install Python 3.7+ from python.org if not already installed
pip install numpy
python setup.py install
# Or run directly
python c_elegans_brain_sim.py
```

### Linux

```bash
# Install dependencies
sudo apt-get install python3 python3-pip python3-numpy  # Debian/Ubuntu
# or
sudo yum install python3 python3-pip python3-numpy      # RHEL/CentOS

# Install the simulator
pip3 install numpy
python3 setup.py install
# Or run directly
python3 c_elegans_brain_sim.py
```

### macOS

#### Option 1: Direct Installation
```bash
# Install dependencies (requires Homebrew)
brew install python3
pip3 install numpy

# Run directly
python3 c_elegans_brain_sim.py
```

#### Option 2: PKG Installer
```bash
# Create the .pkg installer
chmod +x create_pkg.sh
./create_pkg.sh

# This creates C_Elegans_Brain_Simulator.pkg
# Double-click to install, or use:
sudo installer -pkg C_Elegans_Brain_Simulator.pkg -target /
```

## Usage

### Basic Simulation

```bash
python c_elegans_brain_sim.py
```

### Programmatic Usage

```python
from c_elegans_brain_sim import CElegansBrain

# Create brain with default modulation
brain = CElegansBrain(modulation_level=1.0)

# Apply neuromodulation (0.5 = less excitable, 2.0 = more excitable)
brain.apply_modulation(1.5)

# Run simulation
results = brain.run_simulation(steps=1000, stimulus_pattern='random')

# Get statistics
stats = brain.get_network_statistics()
print(f"Total neurons: {stats['total_neurons']}")
print(f"Total synapses: {stats['total_synapses']}")

# Save network configuration
brain.save_to_file('network_config.json')
```

## Network Statistics

The enhanced network includes:

| Component | Count | Description |
|-----------|-------|-------------|
| Sensory Neurons | 99 | Input processing |
| Interneurons | 132 | Signal integration |
| Motor Neurons | 80 | Output control |
| Modulatory Neurons | 1 | Global modulation |
| **Total Neurons** | **312** | **+10 from original** |
| Chemical Synapses | ~1100 | Neurotransmitter-based |
| Electrical Synapses | ~330 | Gap junctions |
| **Total Synapses** | **~1450** | **+20+ from base** |

## Modulation Effects

The simulation demonstrates how neuromodulation affects network activity:

| Modulation Level | Spike Rate | Effect |
|-----------------|------------|--------|
| 0.5x | Low | Reduced excitability |
| 1.0x | Normal | Baseline activity |
| 1.5x | Elevated | Increased responsiveness |
| 2.0x | High | Hyperexcitable state |

## Files

- `c_elegans_brain_sim.py` - Main simulation script
- `setup.py` - Python package installation
- `create_pkg.sh` - macOS PKG creator
- `package_info.json` - Package metadata
- `c_elegans_brain_network.json` - Saved network configuration (generated)

## Requirements

- Python 3.7 or higher
- NumPy

Optional:
- Matplotlib (for advanced visualization)
- SciPy (for additional analysis)

## License

MIT License - See LICENSE file in the OpenWorm Analysis Toolbox repository.

## Credits

Based on the [OpenWorm Analysis Toolbox](https://github.com/openworm/open-worm-analysis-toolbox) project.

This enhanced version adds:
- 10 new neurons (EN1-EN10)
- 20+ additional synaptic connections
- Neuromodulation capabilities
- Cross-platform installation support
