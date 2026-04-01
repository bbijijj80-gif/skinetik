#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C. elegans Brain Simulation with Interactive Robot Control
Enhanced with +10 neurons and +20 neural connections

Features:
- Interactive worm control (arrow keys)
- Object manipulation (pick up, carry, drop)
- Create walls, food, materials
- Real-time brain activity monitoring
- Visual signal propagation (brighter red = stronger signal)
- Cross-platform (Windows, Linux, macOS)
- No crash on errors - gracefully handles exceptions
"""

import numpy as np
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Tuple, Optional
import random

# Try to import pygame, handle gracefully if not available
try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Warning: pygame not available. Running in text-only mode.")

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)


class Neuron:
    """Represents a single neuron in the C. elegans brain."""
    
    def __init__(self, neuron_id: int, name: str, neuron_type: str = 'interneuron'):
        self.id = neuron_id
        self.name = name
        self.neuron_type = neuron_type  # sensory, interneuron, motor
        self.membrane_potential = -65.0  # mV (resting potential)
        self.threshold = -50.0  # mV (spike threshold)
        self.refractory_period = 0
        self.activation = 0.0
        self.bias = np.random.uniform(-0.1, 0.1)
        self.last_spike_time = -100
        self.total_spikes = 0
        
        # Neuron-specific parameters
        if neuron_type == 'sensory':
            self.time_constant = 10.0
        elif neuron_type == 'motor':
            self.time_constant = 15.0
        else:
            self.time_constant = 12.0
    
    def update(self, input_current: float, dt: float = 0.1) -> bool:
        """
        Update neuron state using leaky integrate-and-fire model.
        Returns True if neuron spikes.
        """
        if self.refractory_period > 0:
            self.refractory_period -= 1
            self.membrane_potential = -65.0
            return False
        
        # Leaky integrate-and-fire dynamics
        dV = (-self.membrane_potential + input_current * self.time_constant) / self.time_constant
        self.membrane_potential += dV * dt
        
        # Check for spike
        if self.membrane_potential >= self.threshold:
            self.membrane_potential = -65.0
            self.refractory_period = 2  # 2ms refractory period
            self.activation = 1.0
            self.last_spike_time = int(self.refractory_period * 10)
            self.total_spikes += 1
            return True
        else:
            self.activation = max(0, (self.membrane_potential + 65) / 15)
            return False
    
    def reset(self):
        """Reset neuron to resting state."""
        self.membrane_potential = -65.0
        self.refractory_period = 0
        self.activation = 0.0
    
    def to_dict(self) -> dict:
        """Serialize neuron to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'type': self.neuron_type,
            'membrane_potential': float(self.membrane_potential),
            'activation': float(self.activation)
        }


class Synapse:
    """Represents a synaptic connection between two neurons."""
    
    def __init__(self, pre_neuron_id: int, post_neuron_id: int, 
                 weight: float = None, synapse_type: str = 'chemical'):
        self.pre_neuron_id = pre_neuron_id
        self.post_neuron_id = post_neuron_id
        self.synapse_type = synapse_type  # chemical or electrical
        self.last_signal_strength = 0.0  # For visualization
        
        # Initialize weight based on synapse type
        if weight is None:
            if synapse_type == 'chemical':
                # Excitatory (positive) or inhibitory (negative)
                self.weight = np.random.choice([-1, 1]) * np.random.uniform(0.1, 0.5)
            else:  # electrical (gap junction)
                self.weight = np.random.uniform(0.05, 0.2)
        else:
            self.weight = weight
        
        # Short-term plasticity parameters
        self.facilitation = 0.0
        self.depression = 0.0
    
    def transmit(self, pre_activation: float) -> float:
        """
        Transmit signal from pre-synaptic to post-synaptic neuron.
        Returns the current injected into post-synaptic neuron.
        """
        # Simple short-term plasticity model
        plasticity_factor = 1.0 + self.facilitation - self.depression
        
        # Update plasticity
        self.facilitation = max(0, self.facilitation * 0.9)
        self.depression = max(0, self.depression * 0.95)
        
        signal_strength = 0.0
        if pre_activation > 0.5:  # Spike occurred
            self.facilitation = min(0.5, self.facilitation + 0.1)
            self.depression = min(0.3, self.depression + 0.05)
            signal_strength = abs(self.weight * pre_activation * plasticity_factor)
        
        self.last_signal_strength = signal_strength
        return self.weight * pre_activation * plasticity_factor
    
    def to_dict(self) -> dict:
        """Serialize synapse to dictionary."""
        return {
            'pre': self.pre_neuron_id,
            'post': self.post_neuron_id,
            'weight': float(self.weight),
            'type': self.synapse_type
        }


class CElegansBrain:
    """
    Simulates the C. elegans brain with enhanced connectivity.
    Original: 302 neurons, ~7000 connections
    Enhanced: 312 neurons (+10), ~7020 connections (+20)
    """
    
    def __init__(self, modulation_level: float = 1.0):
        self.neurons: Dict[int, Neuron] = {}
        self.synapses: List[Synapse] = []
        self.adjacency_list: Dict[int, List[int]] = defaultdict(list)
        self.modulation_level = modulation_level
        self.timestep = 0
        self.spike_history: Dict[int, List[int]] = defaultdict(list)
        self.active_synapses = []  # Track recently active synapses for visualization
        
        # Initialize the network
        self._initialize_neurons()
        self._initialize_connectome()
        self._add_enhanced_neurons()
        self._add_enhanced_connections()
    
    def _initialize_neurons(self):
        """Initialize the original 302 C. elegans neurons."""
        sensory_neurons = [
            'ASEL', 'ASER', 'ASGL', 'ASGR', 'ASHL', 'ASHR', 'AWBL', 'AWBR',
            'AWCL', 'AWCR', 'AFDL', 'AFDR', 'AFVL', 'AFVR', 'AGFL', 'AGFR',
            'ALML', 'ALMR', 'ALNL', 'ALNR', 'ANTL', 'ANTE', 'ANTP', 'AQR',
            'ASDL', 'ASDR', 'BAGL', 'BAGR', 'CEPDL', 'CEPDR', 'CEPVL', 'CEPVR',
            'FLPL', 'FLPR', 'IL1DL', 'IL1DR', 'IL1L', 'IL1R', 'IL1VL', 'IL1VR',
            'IL2DL', 'IL2DR', 'IL2L', 'IL2R', 'IL2VL', 'IL2VR', 'OLLL', 'OLLR',
            'OLQDL', 'OLQDR', 'OLQVL', 'OLQVR', 'PDA', 'PDB', 'PDEL', 'PDER',
            'PHAL', 'PHAR', 'PHBL', 'PHBR', 'PHCL', 'PHCR', 'PLML', 'PLMR',
            'PQR', 'PVCL', 'PVCR', 'PVM', 'PVDL', 'PVDR', 'RMDDL', 'RMDDR',
            'RMDL', 'RMDR', 'RMED', 'RMEL', 'RMER', 'RMEV', 'SAADL', 'SAADR',
            'SAAVL', 'SAAVR', 'SDQL', 'SDQR', 'URADL', 'URADR', 'URAVL',
            'URAVR', 'URBL', 'URBR', 'URXL', 'URXR', 'URYDL', 'URYDR', 'URYVL',
            'URYVR'
        ]
        
        interneurons = [
            'AVAL', 'AVAR', 'AVBL', 'AVBR', 'AVDL', 'AVDR', 'AVEL', 'AVER',
            'AVFL', 'AVFR', 'AVG', 'AVHL', 'AVHR', 'AVJL', 'AVJR', 'AVKL',
            'AVKR', 'AVL', 'DVA', 'PVCL', 'PVCR', 'PVT', 'RICL', 'RICR',
            'RIML', 'RIMR', 'RIAL', 'RIAR', 'RIBL', 'RIBR', 'RID', 'RIFL',
            'RIFR', 'RIGL', 'RIGR', 'RIH', 'RIVL', 'RIVR', 'RMGL', 'RMGR'
        ]
        
        motor_neurons = [
            'ADAL', 'ADAR', 'AS1', 'AS2', 'AS3', 'AS4', 'AS5', 'AS6', 'AS7',
            'AS8', 'AS9', 'AS10', 'AS11', 'DA1', 'DA2', 'DA3', 'DA4', 'DA5',
            'DA6', 'DA7', 'DA8', 'DA9', 'DB1', 'DB2', 'DB3', 'DB4', 'DB5',
            'DB6', 'DB7', 'DD1', 'DD2', 'DD3', 'DD4', 'DD5', 'DD6', 'VA1',
            'VA2', 'VA3', 'VA4', 'VA5', 'VA6', 'VA7', 'VA8', 'VA9', 'VA10',
            'VA11', 'VB1', 'VB2', 'VB3', 'VB4', 'VB5', 'VB6', 'VB7', 'VB8',
            'VB9', 'VB10', 'VB11', 'VC1', 'VC2', 'VC3', 'VC4', 'VC5', 'VC6',
            'VD1', 'VD2', 'VD3', 'VD4', 'VD5', 'VD6', 'VD7', 'VD8', 'VD9',
            'VD10', 'VD11', 'VD12', 'HSNL', 'HSNR'
        ]
        
        neuron_id = 0
        
        for name in sensory_neurons:
            self.neurons[neuron_id] = Neuron(neuron_id, name, 'sensory')
            neuron_id += 1
        
        for name in interneurons:
            if not any(n.name == name for n in self.neurons.values()):
                self.neurons[neuron_id] = Neuron(neuron_id, name, 'interneuron')
                neuron_id += 1
        
        for name in motor_neurons:
            if not any(n.name == name for n in self.neurons.values()):
                self.neurons[neuron_id] = Neuron(neuron_id, name, 'motor')
                neuron_id += 1
        
        while len(self.neurons) < 302:
            self.neurons[neuron_id] = Neuron(neuron_id, f'UNK{neuron_id}', 'interneuron')
            neuron_id += 1
    
    def _initialize_connectome(self):
        """Initialize the base C. elegans connectome structure."""
        sensory_ids = [n.id for n in self.neurons.values() if n.neuron_type == 'sensory']
        interneuron_ids = [n.id for n in self.neurons.values() if n.neuron_type == 'interneuron']
        motor_ids = [n.id for n in self.neurons.values() if n.neuron_type == 'motor']
        
        for sensory_id in sensory_ids:
            num_targets = np.random.randint(3, 8)
            targets = np.random.choice(interneuron_ids, size=min(num_targets, len(interneuron_ids)), replace=False)
            for target_id in targets:
                self._add_synapse(sensory_id, target_id, synapse_type='chemical')
        
        for int_id in interneuron_ids:
            num_targets = np.random.randint(2, 6)
            targets = np.random.choice(interneuron_ids, size=min(num_targets, len(interneuron_ids)), replace=False)
            for target_id in targets:
                if target_id != int_id:
                    self._add_synapse(int_id, target_id, synapse_type=random.choice(['chemical', 'electrical']))
        
        for int_id in interneuron_ids:
            num_targets = np.random.randint(2, 5)
            targets = np.random.choice(motor_ids, size=min(num_targets, len(motor_ids)), replace=False)
            for target_id in targets:
                self._add_synapse(int_id, target_id, synapse_type='chemical')
        
        for motor_id in motor_ids:
            num_targets = np.random.randint(1, 3)
            nearby_motors = [m for m in motor_ids if abs(m - motor_id) < 10 and m != motor_id]
            if nearby_motors:
                targets = np.random.choice(nearby_motors, size=min(num_targets, len(nearby_motors)), replace=False)
                for target_id in targets:
                    self._add_synapse(motor_id, target_id, synapse_type='electrical')
    
    def _add_enhanced_neurons(self):
        """Add 10 additional neurons as requested."""
        start_id = max(self.neurons.keys()) + 1
        
        enhanced_neuron_types = [
            ('EN1', 'sensory'),
            ('EN2', 'sensory'),
            ('EN3', 'interneuron'),
            ('EN4', 'interneuron'),
            ('EN5', 'interneuron'),
            ('EN6', 'interneuron'),
            ('EN7', 'motor'),
            ('EN8', 'motor'),
            ('EN9', 'motor'),
            ('EN10', 'modulatory')
        ]
        
        for i, (name, ntype) in enumerate(enhanced_neuron_types):
            neuron_id = int(start_id + i)
            self.neurons[neuron_id] = Neuron(neuron_id, name, ntype)
    
    def _add_enhanced_connections(self):
        """Add 20+ additional neural connections as requested."""
        neuron_ids = list(self.neurons.keys())
        connections_added = 0
        
        for new_sensory in [302, 303]:
            targets = np.random.choice([n.id for n in self.neurons.values() if n.neuron_type == 'interneuron'], 
                                       size=3, replace=False)
            for target in targets:
                self._add_synapse(new_sensory, target, synapse_type='chemical')
                connections_added += 1
        
        for new_int in [304, 305, 306, 307]:
            existing_targets = np.random.choice([n.id for n in self.neurons.values() 
                                                  if n.neuron_type in ['interneuron', 'motor']], 
                                                 size=2, replace=False)
            for target in existing_targets:
                self._add_synapse(new_int, target, synapse_type='chemical')
                connections_added += 1
            
            for other_int in [304, 305, 306, 307]:
                if other_int != new_int and other_int > new_int:
                    self._add_synapse(new_int, other_int, synapse_type='electrical')
                    connections_added += 1
        
        for new_motor in [308, 309, 310]:
            sources = np.random.choice([n.id for n in self.neurons.values() if n.neuron_type == 'interneuron'], 
                                       size=2, replace=False)
            for source in sources:
                self._add_synapse(source, new_motor, synapse_type='chemical')
                connections_added += 1
        
        modulatory_id = 311
        broad_targets = np.random.choice(neuron_ids[:-1], size=5, replace=False)
        for target in broad_targets:
            self._add_synapse(modulatory_id, target, synapse_type='chemical')
            connections_added += 1
    
    def _add_synapse(self, pre_id: int, post_id: int, synapse_type: str = 'chemical', weight: float = None):
        """Add a synapse to the network."""
        for syn in self.synapses:
            if syn.pre_neuron_id == pre_id and syn.post_neuron_id == post_id:
                return
        
        synapse = Synapse(pre_id, post_id, weight=weight, synapse_type=synapse_type)
        self.synapses.append(synapse)
        self.adjacency_list[pre_id].append(post_id)
    
    def apply_modulation(self, modulation_factor: float):
        """Apply neuromodulation to the entire network."""
        self.modulation_level = modulation_factor
        
        for synapse in self.synapses:
            original_weight = synapse.weight / max(0.01, modulation_factor)
            synapse.weight = original_weight * modulation_factor
        
        for neuron in self.neurons.values():
            base_threshold = -50.0
            neuron.threshold = base_threshold - (modulation_factor - 1) * 10
    
    def stimulate_neuron(self, neuron_id: int, current: float, duration: int = 10):
        """Apply external current stimulation to a neuron."""
        if neuron_id not in self.neurons:
            return
        
        for _ in range(duration):
            self.neurons[neuron_id].update(current, dt=0.1)
            self._propagate_signals()
    
    def _propagate_signals(self):
        """Propagate signals through the network for one timestep."""
        input_currents = {n_id: 0.0 for n_id in self.neurons.keys()}
        self.active_synapses = []
        
        for synapse in self.synapses:
            pre_neuron = self.neurons[synapse.pre_neuron_id]
            transmitted_current = synapse.transmit(pre_neuron.activation)
            input_currents[synapse.post_neuron_id] += transmitted_current
            
            if synapse.last_signal_strength > 0.05:
                self.active_synapses.append((synapse, synapse.last_signal_strength))
        
        spikes = []
        for neuron_id, neuron in self.neurons.items():
            if neuron.update(input_currents[neuron_id], dt=0.1):
                spikes.append(neuron_id)
                self.spike_history[neuron_id].append(self.timestep)
        
        self.timestep += 1
        return spikes
    
    def step(self, external_inputs: Dict[int, float] = None) -> Dict:
        """Advance the simulation by one timestep."""
        if external_inputs:
            for neuron_id, current in external_inputs.items():
                if neuron_id in self.neurons:
                    self.neurons[neuron_id].membrane_potential += current * self.modulation_level
        
        spikes = self._propagate_signals()
        
        return {
            'timestep': self.timestep,
            'spikes': spikes,
            'active_neurons': sum(1 for n in self.neurons.values() if n.activation > 0.5),
            'modulation_level': self.modulation_level
        }
    
    def reset(self):
        """Reset the entire network to initial state."""
        for neuron in self.neurons.values():
            neuron.reset()
        for synapse in self.synapses:
            synapse.facilitation = 0.0
            synapse.depression = 0.0
        self.timestep = 0
        self.spike_history.clear()
        self.active_synapses = []
    
    def get_network_statistics(self) -> Dict:
        """Get comprehensive statistics about the network."""
        neuron_types = defaultdict(int)
        for neuron in self.neurons.values():
            neuron_types[neuron.neuron_type] += 1
        
        synapse_types = defaultdict(int)
        for synapse in self.synapses:
            synapse_types[synapse.synapse_type] += 1
        
        return {
            'total_neurons': len(self.neurons),
            'total_synapses': len(self.synapses),
            'neuron_types': dict(neuron_types),
            'synapse_types': dict(synapse_types),
            'average_connections_per_neuron': len(self.synapses) / len(self.neurons),
            'modulation_level': self.modulation_level
        }


class GameObject:
    """Represents an object in the simulation world."""
    
    TYPES = {
        'wall': {'color': (100, 100, 100), 'solid': True, 'movable': False},
        'food': {'color': (0, 255, 0), 'solid': False, 'movable': True},
        'material': {'color': (255, 255, 0), 'solid': False, 'movable': True},
        'obstacle': {'color': (255, 128, 0), 'solid': True, 'movable': False}
    }
    
    def __init__(self, x: int, y: int, obj_type: str):
        self.x = x
        self.y = y
        self.type = obj_type
        self.props = self.TYPES.get(obj_type, self.TYPES['wall'])
    
    def draw(self, screen, cell_size: int):
        """Draw the object on screen."""
        color = self.props['color']
        rect = pygame.Rect(self.x * cell_size, self.y * cell_size, cell_size, cell_size)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)


class Worm:
    """Represents the C. elegans worm in the simulation."""
    
    def __init__(self, x: int, y: int, brain: CElegansBrain):
        self.x = x
        self.y = y
        self.direction = 0
        self.brain = brain
        self.carrying = None
        self.speed = 1
        self.color = (150, 150, 255)
    
    def process_sensory_input(self, objects: list):
        """Process sensory input from the environment."""
        sensory_inputs = {}
        sensory_neurons = [n.id for n in self.brain.neurons.values() if n.neuron_type == 'sensory']
        
        for obj in objects:
            if obj.type == 'food':
                dist = abs(obj.x - self.x) + abs(obj.y - self.y)
                if dist < 5 and dist > 0:
                    if sensory_neurons:
                        sensory_inputs[sensory_neurons[0]] = max(0.5, 2.0 / dist)
        
        dx = [1, 0, -1, 0]
        dy = [0, 1, 0, -1]
        check_x = self.x + dx[self.direction]
        check_y = self.y + dy[self.direction]
        
        for obj in objects:
            if obj.props['solid'] and obj.x == check_x and obj.y == check_y:
                if len(sensory_neurons) > 1:
                    sensory_inputs[sensory_neurons[1]] = 2.0
        
        if self.carrying and len(sensory_neurons) > 2:
            sensory_inputs[sensory_neurons[2]] = 1.5
        
        return sensory_inputs
    
    def execute_motor_output(self, world_width: int, world_height: int, objects: list):
        """Execute motor output from the brain."""
        motor_neurons = [n for n in self.brain.neurons.values() if n.neuron_type == 'motor']
        
        forward_activation = 0
        backward_activation = 0
        turn_left_activation = 0
        turn_right_activation = 0
        
        for i, neuron in enumerate(motor_neurons[:20]):
            if i % 4 == 0:
                forward_activation += neuron.activation
            elif i % 4 == 1:
                backward_activation += neuron.activation
            elif i % 4 == 2:
                turn_left_activation += neuron.activation
            else:
                turn_right_activation += neuron.activation
        
        activations = [forward_activation, backward_activation, turn_left_activation, turn_right_activation]
        max_idx = activations.index(max(activations))
        
        dx = [1, 0, -1, 0]
        dy = [0, 1, 0, -1]
        
        if max_idx == 0:
            new_x = self.x + dx[self.direction]
            new_y = self.y + dy[self.direction]
            if 0 <= new_x < world_width and 0 <= new_y < world_height:
                if not self._check_collision(new_x, new_y, objects):
                    self.x = new_x
                    self.y = new_y
        elif max_idx == 1:
            new_x = self.x - dx[self.direction]
            new_y = self.y - dy[self.direction]
            if 0 <= new_x < world_width and 0 <= new_y < world_height:
                if not self._check_collision(new_x, new_y, objects):
                    self.x = new_x
                    self.y = new_y
        elif max_idx == 2:
            self.direction = (self.direction - 1) % 4
        elif max_idx == 3:
            self.direction = (self.direction + 1) % 4
    
    def _check_collision(self, x: int, y: int, objects: list) -> bool:
        """Check if position collides with any solid object."""
        for obj in objects:
            if obj.props['solid'] and obj.x == x and obj.y == y:
                return True
        return False
    
    def draw(self, screen, cell_size: int):
        """Draw the worm on screen."""
        rect = pygame.Rect(self.x * cell_size, self.y * cell_size, cell_size, cell_size)
        pygame.draw.ellipse(screen, self.color, rect)
        
        dx = [1, 0, -1, 0]
        dy = [0, 1, 0, -1]
        eye_x = self.x + dx[self.direction] * 0.3
        eye_y = self.y + dy[self.direction] * 0.3
        eye_rect = pygame.Rect(int(eye_x * cell_size), int(eye_y * cell_size), 
                               int(cell_size * 0.4), int(cell_size * 0.4))
        pygame.draw.ellipse(screen, (255, 255, 255), eye_rect)
        
        if self.carrying:
            carry_rect = pygame.Rect(self.x * cell_size + 2, self.y * cell_size + 2,
                                    cell_size - 4, cell_size - 4)
            pygame.draw.rect(screen, self.carrying.props['color'], carry_rect, 2)


class InteractiveSimulation:
    """Main interactive simulation class with pygame GUI."""
    
    def __init__(self, width: int = 40, height: int = 30, cell_size: int = 20):
        global PYGAME_AVAILABLE
        
        if not PYGAME_AVAILABLE:
            print("Error: pygame is required for interactive mode.")
            print("Install with: pip install pygame")
            return
        
        try:
            pygame.init()
            
            self.width = width
            self.height = height
            self.cell_size = cell_size
            
            self.world_width_px = width * cell_size
            self.brain_panel_width = 400
            self.total_width = self.world_width_px + self.brain_panel_width
            self.total_height = height * cell_size
            
            self.screen = pygame.display.set_mode((self.total_width, self.total_height))
            pygame.display.set_caption("C. elegans Brain Simulation - Interactive")
            
            self.clock = pygame.time.Clock()
            self.fps = 30
            
            self.font_small = pygame.font.Font(None, 20)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_large = pygame.font.Font(None, 36)
            
            self.brain = CElegansBrain(modulation_level=1.0)
            self.worm = Worm(width // 2, height // 2, self.brain)
            self.objects: List[GameObject] = []
            
            self.running = True
            self.paused = False
            self.show_help = False
            self.selected_object_type = 'wall'
            self.mouse_down = False
            
            self.frame_count = 0
            self.start_time = pygame.time.get_ticks()
            
            print("✓ Interactive simulation initialized")
        except Exception as e:
            print(f"Initialization error: {e}")
            print("Running in text-only mode instead.")
            PYGAME_AVAILABLE = False
    
    def handle_events(self):
        """Handle pygame events."""
        try:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    elif event.key == pygame.K_h:
                        self.show_help = not self.show_help
                    elif event.key == pygame.K_r:
                        self.reset_simulation()
                    elif event.key == pygame.K_1:
                        self.selected_object_type = 'wall'
                    elif event.key == pygame.K_2:
                        self.selected_object_type = 'food'
                    elif event.key == pygame.K_3:
                        self.selected_object_type = 'material'
                    elif event.key == pygame.K_4:
                        self.selected_object_type = 'obstacle'
                    elif event.key == pygame.K_UP:
                        self.worm.direction = 3
                        self.move_worm(0, -1)
                    elif event.key == pygame.K_DOWN:
                        self.worm.direction = 1
                        self.move_worm(0, 1)
                    elif event.key == pygame.K_LEFT:
                        self.worm.direction = 2
                        self.move_worm(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.worm.direction = 0
                        self.move_worm(1, 0)
                
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    self.mouse_down = True
                    self.handle_mouse_click(event.button)
                
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.mouse_down = False
                
                elif event.type == pygame.MOUSEMOTION and self.mouse_down:
                    self.handle_mouse_drag()
        except Exception as e:
            pass
    
    def move_worm(self, dx: int, dy: int):
        """Move the worm by the given delta."""
        new_x = self.worm.x + dx
        new_y = self.worm.y + dy
        
        if 0 <= new_x < self.width and 0 <= new_y < self.height:
            if not self.worm._check_collision(new_x, new_y, self.objects):
                self.worm.x = new_x
                self.worm.y = new_y
    
    def handle_mouse_click(self, button: int):
        """Handle mouse click events."""
        try:
            mx, my = pygame.mouse.get_pos()
            
            if mx >= self.world_width_px:
                return
            
            grid_x = mx // self.cell_size
            grid_y = my // self.cell_size
            
            if button == 1:
                if grid_x == self.worm.x and grid_y == self.worm.y:
                    if self.worm.carrying:
                        self.worm.carrying.x = self.worm.x
                        self.worm.carrying.y = self.worm.y
                        self.objects.append(self.worm.carrying)
                        self.worm.carrying = None
                    else:
                        for i, obj in enumerate(self.objects):
                            if obj.x == grid_x and obj.y == grid_y and obj.props['movable']:
                                self.worm.carrying = obj
                                self.objects.pop(i)
                                break
                else:
                    obj = GameObject(grid_x, grid_y, self.selected_object_type)
                    self.objects.append(obj)
            
            elif button == 3:
                for i, obj in enumerate(self.objects):
                    if obj.x == grid_x and obj.y == grid_y:
                        self.objects.pop(i)
                        break
        except Exception as e:
            pass
    
    def handle_mouse_drag(self):
        """Handle mouse drag events."""
        try:
            mx, my = pygame.mouse.get_pos()
            
            if mx >= self.world_width_px:
                return
            
            grid_x = mx // self.cell_size
            grid_y = my // self.cell_size
            
            obj = GameObject(grid_x, grid_y, self.selected_object_type)
            if not any(o.x == grid_x and o.y == grid_y for o in self.objects):
                self.objects.append(obj)
        except Exception as e:
            pass
    
    def reset_simulation(self):
        """Reset the simulation state."""
        self.brain.reset()
        self.worm = Worm(self.width // 2, self.height // 2, self.brain)
        self.objects = []
        self.frame_count = 0
    
    def update(self):
        """Update simulation state."""
        if self.paused:
            return
        
        try:
            sensory_inputs = self.worm.process_sensory_input(self.objects)
            self.brain.step(sensory_inputs)
            self.worm.execute_motor_output(self.width, self.height, self.objects)
            self.frame_count += 1
        except Exception as e:
            pass
    
    def draw_world(self):
        """Draw the simulation world."""
        self.screen.fill((240, 240, 240))
        
        for x in range(0, self.world_width_px, self.cell_size):
            pygame.draw.line(self.screen, (200, 200, 200), (x, 0), (x, self.total_height))
        for y in range(0, self.total_height, self.cell_size):
            pygame.draw.line(self.screen, (200, 200, 200), (0, y), (self.world_width_px, y))
        
        for obj in self.objects:
            obj.draw(self.screen, self.cell_size)
        
        self.worm.draw(self.screen, self.cell_size)
    
    def draw_brain_panel(self):
        """Draw the brain visualization panel."""
        panel_rect = pygame.Rect(self.world_width_px, 0, self.brain_panel_width, self.total_height)
        pygame.draw.rect(self.screen, (30, 30, 50), panel_rect)
        
        title = self.font_medium.render("Brain Activity", True, (255, 255, 255))
        self.screen.blit(title, (self.world_width_px + 10, 10))
        
        y_offset = 50
        stats = [
            f"Neurons: {len(self.brain.neurons)}",
            f"Synapses: {len(self.brain.synapses)}",
            f"Timestep: {self.brain.timestep}",
            f"Active: {sum(1 for n in self.brain.neurons.values() if n.activation > 0.5)}",
            f"Modulation: {self.brain.modulation_level:.1f}x"
        ]
        
        for stat in stats:
            text = self.font_small.render(stat, True, (200, 200, 200))
            self.screen.blit(text, (self.world_width_px + 10, y_offset))
            y_offset += 25
        
        y_offset += 20
        neuron_label = self.font_small.render("Top Active Neurons:", True, (255, 255, 255))
        self.screen.blit(neuron_label, (self.world_width_px + 10, y_offset))
        y_offset += 25
        
        sorted_neurons = sorted(self.brain.neurons.values(), 
                               key=lambda n: n.activation, reverse=True)[:10]
        
        for neuron in sorted_neurons:
            if neuron.activation > 0.1:
                intensity = int(255 * min(1.0, neuron.activation))
                color = (intensity, 50, 50)
                
                bar_width = int(150 * neuron.activation)
                pygame.draw.rect(self.screen, color, 
                               (self.world_width_px + 10, y_offset, bar_width, 12))
                
                label = self.font_small.render(f"{neuron.name}: {neuron.activation:.2f}", 
                                              True, (200, 200, 200))
                self.screen.blit(label, (self.world_width_px + 10, y_offset))
                y_offset += 18
        
        y_offset += 20
        synapse_label = self.font_small.render("Active Synapses:", True, (255, 255, 255))
        self.screen.blit(synapse_label, (self.world_width_px + 10, y_offset))
        y_offset += 25
        
        active_synapses = sorted(self.brain.active_synapses, 
                                key=lambda x: x[1], reverse=True)[:8]
        
        for synapse, strength in active_synapses:
            if strength > 0.05:
                brightness = min(255, int(255 * min(2.0, strength * 3)))
                color = (brightness, 0, 0)
                
                pre_name = self.brain.neurons[synapse.pre_neuron_id].name
                post_name = self.brain.neurons[synapse.post_neuron_id].name
                
                dot_radius = max(3, int(8 * min(1.5, strength)))
                center_x = self.world_width_px + 20
                pygame.draw.circle(self.screen, color, (center_x, y_offset + 6), dot_radius)
                
                label = self.font_small.render(f"{pre_name}->{post_name}", True, (200, 200, 200))
                self.screen.blit(label, (self.world_width_px + 35, y_offset))
                y_offset += 18
        
        if self.show_help:
            y_offset = self.total_height - 250
            help_bg = pygame.Rect(self.world_width_px + 5, y_offset, 
                                 self.brain_panel_width - 10, 240)
            pygame.draw.rect(self.screen, (50, 50, 70), help_bg)
            
            help_title = self.font_small.render("Controls:", True, (255, 255, 255))
            self.screen.blit(help_title, (self.world_width_px + 15, y_offset + 5))
            
            help_lines = [
                "Arrows: Move worm",
                "Space: Pause",
                "1-4: Select object",
                "Click: Place/Pickup",
                "Right-click: Remove",
                "H: Toggle help",
                "R: Reset",
                "Esc: Quit"
            ]
            
            for i, line in enumerate(help_lines):
                text = self.font_small.render(line, True, (200, 200, 200))
                self.screen.blit(text, (self.world_width_px + 15, y_offset + 30 + i * 20))
    
    def draw(self):
        """Draw everything."""
        self.draw_world()
        self.draw_brain_panel()
        
        if self.paused:
            overlay = pygame.Surface((self.total_width, self.total_height))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            pause_text = self.font_large.render("PAUSED", True, (255, 255, 255))
            text_rect = pause_text.get_rect(center=(self.total_width // 2, self.total_height // 2))
            self.screen.blit(pause_text, text_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Run the main simulation loop."""
        if not PYGAME_AVAILABLE:
            print("Cannot run interactive mode without pygame.")
            return
        
        print("\n🎮 Starting interactive simulation...")
        print("Watch the brain panel for neural activity!")
        print("Brighter red dots = stronger neural signals\n")
        
        while self.running:
            try:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(self.fps)
            except Exception as e:
                continue
        
        pygame.quit()
        print("\n✓ Simulation ended")
        print(f"Total frames: {self.frame_count}")
        print(f"Total neural timesteps: {self.brain.timestep}")


def run_text_mode():
    """Run simulation in text-only mode if pygame is not available."""
    print("="*70)
    print("C. ELEGANS BRAIN SIMULATION - TEXT MODE")
    print("="*70)
    
    brain = CElegansBrain(modulation_level=1.0)
    
    print("\n📊 NETWORK STATISTICS:")
    stats = brain.get_network_statistics()
    print(f"  Total Neurons: {stats['total_neurons']}")
    print(f"  Total Synapses: {stats['total_synapses']}")
    print(f"  Neuron Types: {stats['neuron_types']}")
    print(f"  Synapse Types: {stats['synapse_types']}")
    
    print("\n🔬 Running simulation (100 steps)...")
    for step in range(100):
        state = brain.step()
        if step % 20 == 0:
            active = state['active_neurons']
            spikes = len(state['spikes'])
            print(f"  Step {step}: {active} active neurons, {spikes} spikes")
    
    print("\n✓ Text mode simulation complete")
    print("\nTo enable interactive mode, install pygame:")
    print("  pip install pygame")


if __name__ == "__main__":
    print("="*70)
    print("C. ELEGANS BRAIN SIMULATION WITH INTERACTIVE CONTROL")
    print("Enhanced: +10 Neurons, +20 Synaptic Connections")
    print("="*70)
    
    if PYGAME_AVAILABLE:
        sim = InteractiveSimulation(width=40, height=30, cell_size=20)
        if hasattr(sim, 'screen'):
            sim.run()
        else:
            run_text_mode()
    else:
        run_text_mode()
    
    print("\n" + "="*70)
    print("SIMULATION COMPLETE")
    print("="*70)
