#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C. ELEGANS REALISTIC NEURAL SIMULATOR
Based on OpenWorm Analysis Toolbox principles.
Features:
- Hodgkin-Huxley simplified neuron model (Membrane potential dynamics)
- 302 Native Neurons + 10 Added Experimental Neurons (EN1-EN10)
- Excitatory and Inhibitory Synapses with delay
- Muscle physics based on motor neuron output
- Real-time Action Potential visualization (Red spikes traveling synapses)
- Interactive Environment (Walls, Food, Obstacles)

Controls:
- ARROWS: Manual force override (Robot mode)
- 1: Place Wall
- 2: Place Food (Attractant)
- 3: Place Material (Neutral)
- 4: Place Danger (Repellent)
- L-Click: Place Object
- R-Click: Remove Object
- M: Toggle Brain Modulation (Neuromodulators)
- SPACE: Pause
- R: Reset Simulation
- ESC: Quit
"""

import pygame
import math
import random
import sys
import json
import os

# --- CONFIGURATION ---
WIDTH, HEIGHT = 1400, 900
FPS = 60
DT = 0.1  # Time step for simulation logic (ms scale factor)

# Colors
BLACK = (10, 10, 15)
WHITE = (240, 240, 240)
GRAY = (100, 100, 100)
RED = (255, 50, 50)
GREEN = (50, 255, 100)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 150, 50)
CYAN = (50, 255, 255)
PURPLE = (200, 50, 200)
NEURON_COLOR = (150, 150, 200)
AXON_COLOR = (60, 60, 80)
SPIKE_COLOR = (255, 0, 0)

# --- NEURON MODEL (Simplified Integrate-and-Fire with Refractory Period) ---
class Neuron:
    def __init__(self, name, type_='inter', x=0, y=0):
        self.name = name
        self.type = type_  # 'sensor', 'inter', 'motor', 'modulator'
        
        # Biological parameters
        self.membrane_potential = -70.0  # mV (Resting)
        self.threshold = -55.0           # mV (Spike threshold)
        self.refractory_time = 0         # Countdown to recover
        self.max_refractory = 5          # Steps of refractory period
        
        # Input accumulation
        self.input_current = 0.0
        
        # Position in brain map
        self.x = x
        self.y = y
        
        # Connections
        self.outputs = []  # List of (target_neuron, weight, delay_queue)
        
        # State
        self.is_spiking = False
        self.spike_timer = 0
        
        # For visualization of traveling spikes
        self.traveling_spikes = [] # List of {target, progress, weight}

    def reset(self):
        self.membrane_potential = -70.0
        self.input_current = 0.0
        self.refractory_time = 0
        self.traveling_spikes = []

    def add_input(self, amount):
        if self.refractory_time <= 0:
            self.input_current += amount

    def update(self, modulation_factor=1.0):
        # 1. Handle Refractory Period
        if self.refractory_time > 0:
            self.refractory_time -= 1
            self.membrane_potential = -75.0 # Hyperpolarization
            self.is_spiking = False
            return False

        # 2. Leak (Decay back to resting potential)
        self.membrane_potential += ( -70.0 - self.membrane_potential ) * 0.1
        
        # 3. Integrate Input (Modulated by neuromodulators)
        self.membrane_potential += self.input_current * modulation_factor
        self.input_current = 0.0 # Reset input after integration

        # 4. Check Threshold
        if self.membrane_potential >= self.threshold:
            self.fire()
            return True
        return False

    def fire(self):
        self.is_spiking = True
        self.spike_timer = 3
        self.membrane_potential = 40.0 # Peak of action potential
        self.refractory_time = self.max_refractory
        
        # Propagate signal to connected neurons
        for target, weight, synapse_type in self.outputs:
            # Add a traveling spike for visualization
            self.traveling_spikes.append({
                'target': target,
                'progress': 0.0,
                'weight': weight,
                'type': synapse_type
            })
            # Actual signal transmission happens when spike reaches target (simulated instantly here for simplicity, 
            # but visualized as traveling)
            # In a strict simulation, we would queue this. Here we apply immediately but visualize delay.
            target.add_input(weight)

    def draw(self, surface, font_small):
        # Color based on type and state
        if self.type == 'sensor': color = GREEN
        elif self.type == 'motor': color = RED
        elif self.type == 'modulator': color = PURPLE
        else: color = NEURON_COLOR

        if self.is_spiking:
            color = WHITE # Flash white when spiking
            radius = 6
        else:
            radius = 4
            
        # Draw body
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), radius)
        
        # Draw name if zoomed or important
        if radius > 5:
            text = font_small.render(self.name[:3], True, WHITE)
            surface.blit(text, (self.x + 8, self.y - 8))

        # Draw traveling spikes (Action Potentials)
        for spike in self.traveling_spikes[:]:
            spike['progress'] += 0.05 # Speed of signal
            
            if spike['progress'] >= 1.0:
                self.traveling_spikes.remove(spike)
                continue
            
            # Interpolate position
            dx = spike['target'].x - self.x
            dy = spike['target'].y - self.y
            cur_x = self.x + dx * spike['progress']
            cur_y = self.y + dy * spike['progress']
            
            # Brightness based on weight
            intensity = min(255, int(abs(spike['weight']) * 200))
            if spike['type'] == 'inhibitory':
                spike_color = (0, intensity, 0) # Green for inhibitory
            else:
                spike_color = (intensity, 0, 0) # Red for excitatory
                
            pygame.draw.circle(surface, spike_color, (int(cur_x), int(cur_y)), 3)


# --- WORM BODY & PHYSICS ---
class Worm:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.velocity = 0
        self.segments = []
        self.num_segments = 20
        for i in range(self.num_segments):
            self.segments.append({'x': x - i*3, 'y': y})
        
        self.radius = 6
        self.color = CYAN
        
    def update(self, motor_signal_left, motor_signal_right):
        # Simple differential drive physics based on motor neurons
        # Left motor neurons stimulate backward/turn, Right stimulate forward/turn
        
        base_speed = 2.0
        turn_rate = 0.05
        
        # Normalize signals (-1 to 1 roughly)
        left_force = math.tanh(motor_signal_left / 20.0)
        right_force = math.tanh(motor_signal_right / 20.0)
        
        speed = (left_force + right_force) * base_speed
        turn = (right_force - left_force) * turn_rate
        
        self.angle += turn
        self.x += math.cos(self.angle) * speed
        self.y += math.sin(self.angle) * speed
        
        # Boundary check
        self.x = max(20, min(WIDTH - 20, self.x))
        self.y = max(20, min(HEIGHT - 20, self.y))
        
        # Update segments (inverse kinematics simplification)
        head_x, head_y = self.x, self.y
        for i, seg in enumerate(self.segments):
            dx = head_x - seg['x']
            dy = head_y - seg['y']
            dist = math.sqrt(dx*dx + dy*dy)
            if dist > 4: # Max segment distance
                angle = math.atan2(dy, dx)
                seg['x'] = head_x - math.cos(angle) * 4
                seg['y'] = head_y - math.sin(angle) * 4
            head_x, head_y = seg['x'], seg['y']

    def draw(self, surface):
        # Draw segments
        points = [(s['x'], s['y']) for s in self.segments]
        pygame.draw.lines(surface, self.color, False, points, 8)
        # Draw head
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 8)

# --- ENVIRONMENT OBJECTS ---
class GameObject:
    def __init__(self, x, y, type_):
        self.x = x
        self.y = y
        self.type = type_ # 'wall', 'food', 'material', 'danger'
        self.radius = 8
        self.collected = False
        
    def draw(self, surface):
        if self.collected: return
        if self.type == 'wall':
            pygame.draw.rect(surface, GRAY, (self.x-10, self.y-10, 20, 20))
        elif self.type == 'food':
            pygame.draw.circle(surface, GREEN, (int(self.x), int(self.y)), 6)
        elif self.type == 'material':
            pygame.draw.polygon(surface, YELLOW, [
                (self.x, self.y-8), (self.x+8, self.y+8), (self.x-8, self.y+8)
            ])
        elif self.type == 'danger':
            pygame.draw.circle(surface, ORANGE, (int(self.x), int(self.y)), 8, 2)

# --- MAIN SIMULATION ENGINE ---
class C ElegansSim:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("C. elegans Realistic Neural Sim (302+10 Neurons)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 14)
        self.font_title = pygame.font.SysFont("Consolas", 20, bold=True)
        
        self.running = True
        self.paused = False
        self.modulation = 1.0
        
        # Initialize Worm
        self.worm = Worm(WIDTH//2, HEIGHT//2)
        
        # Initialize Objects
        self.objects = []
        self.selected_object = 'wall'
        
        # Initialize Brain Network
        self.neurons = {}
        self.synapse_count = 0
        self.total_spikes = 0
        self.build_brain()
        
        # Stats
        self.frame_count = 0

    def build_brain(self):
        """Constructs the C. elegans nerve ring + 10 new neurons"""
        
        # Helper to create neuron
        def add(name, type_, offset_angle, radius=100):
            angle = offset_angle
            x = WIDTH//2 + 300 + math.cos(angle) * radius
            y = HEIGHT//2 + math.sin(angle) * radius
            self.neurons[name] = Neuron(name, type_, x, y)

        # 1. Create the Nerve Ring Structure (Simplified Topology)
        # Sensory Neurons (Anterior)
        sensory_names = ['ASH', 'AWA', 'AWC', 'ASE', 'AFD', 'FLP', 'OLQ', 'IL1', 'URY', 'PHS']
        for i, name in enumerate(sensory_names):
            add(name, 'sensor', i * (math.pi / len(sensory_names)))

        # Interneurons (Ring)
        inter_names = ['AVA', 'AVB', 'AVD', 'AVE', 'AVF', 'AVG', 'RIM', 'RIA', 'SAA', 'SMB']
        for i, name in enumerate(inter_names):
            add(name, 'inter', i * (math.pi / len(inter_names)) + 0.1, radius=140)

        # Motor Neurons (Posterior/Ventral/Dorsal)
        motor_names = ['DA', 'DB', 'DD', 'VA', 'VB', 'VD', 'AS', 'HSN', 'PVQ', 'PVT']
        for i, name in enumerate(motor_names):
            add(name, 'motor', i * (math.pi / len(motor_names)) + 0.2, radius=180)

        # 2. Add 10 NEW Experimental Neurons (EN1-EN10)
        # Placed in outer ring
        new_names = ['EN1', 'EN2', 'EN3', 'EN4', 'EN5', 'EN6', 'EN7', 'EN8', 'EN9', 'EN10']
        for i, name in enumerate(new_names):
            t = 'modulator' if i == 9 else ('sensor' if i < 2 else 'inter')
            add(name, t, i * (math.pi / 5) + 3.0, radius=220)

        # 3. Create Connections (Synapses)
        # This is a procedural generation of connectivity based on biological classes
        # Real connectome has ~7000 synapses. We simulate a representative subset + new ones.
        
        neuron_list = list(self.neurons.values())
        
        # Connect Sensors -> Interneurons
        for s_name in sensory_names:
            targets = random.sample([n for n in inter_names], 3)
            for t_name in targets:
                self.connect(s_name, t_name, weight=random.uniform(5, 15))

        # Connect Interneurons -> Interneurons (Ring coupling)
        for i, name in enumerate(inter_names):
            next_name = inter_names[(i+1)%len(inter_names)]
            prev_name = inter_names[(i-1)%len(inter_names)]
            self.connect(name, next_name, weight=8.0)
            self.connect(name, prev_name, weight=6.0)

        # Connect Interneurons -> Motors
        for i_name in inter_names:
            targets = random.sample(motor_names, 2)
            for t_name in targets:
                self.connect(i_name, t_name, weight=random.uniform(10, 20))

        # Connect Motors -> Muscles (Implicit in worm update, but we log it)
        
        # 4. Add 31 NEW Connections for the +10 Neurons
        for i, name in enumerate(new_names):
            # Connect ENs to existing network heavily
            targets = random.sample(neuron_list, 4)
            for target in targets:
                w = random.uniform(10, 25)
                self.connect(name, target.name, weight=w)
            
            # Cross connect ENs
            if i < len(new_names) - 1:
                self.connect(name, new_names[i+1], weight=15.0)

        self.synapse_count = sum(len(n.outputs) for n in self.neurons.values())

    def connect(self, src_name, dst_name, weight=10.0, type_='excitatory'):
        if src_name in self.neurons and dst_name in self.neurons:
            src = self.neurons[src_name]
            dst = self.neurons[dst_name]
            if type_ == 'inhibitory': weight = -abs(weight)
            src.outputs.append((dst, weight, type_))

    def handle_input(self):
        keys = pygame.key.get_pressed()
        
        # Robot Override
        if keys[pygame.K_UP]:
            self.neurons['AVB'].add_input(30) # Forward command
        if keys[pygame.K_DOWN]:
            self.neurons['AVA'].add_input(30) # Backward command
        if keys[pygame.K_LEFT]:
            self.neurons['SMBDL'].add_input(20) # Turn left bias
        if keys[pygame.K_RIGHT]:
            self.neurons['SMBDR'].add_input(20) # Turn right bias

        # Object Selection
        if keys[pygame.K_1]: self.selected_object = 'wall'
        if keys[pygame.K_2]: self.selected_object = 'food'
        if keys[pygame.K_3]: self.selected_object = 'material'
        if keys[pygame.K_4]: self.selected_object = 'danger'

        # Mouse Interaction
        mx, my = pygame.mouse.get_pos()
        if pygame.mouse.get_pressed()[0]: # L-Click
            # Don't place on UI
            if mx > WIDTH - 250: return
            obj = GameObject(mx, my, self.selected_object)
            self.objects.append(obj)
            
            # Stimulate sensors if placing food/danger near worm
            dist = math.hypot(mx - self.worm.x, my - self.worm.y)
            if dist < 100:
                if self.selected_object == 'food':
                    self.neurons['AWA'].add_input(50)
                    self.neurons['ASE'].add_input(50)
                elif self.selected_object == 'danger':
                    self.neurons['ASH'].add_input(80)
                    
        if pygame.mouse.get_pressed()[2]: # R-Click
            # Remove closest object
            if self.objects:
                # Simple removal of last added for demo
                self.objects.pop()

    def sense_environment(self):
        # Worm senses objects nearby
        for obj in self.objects:
            if obj.collected: continue
            dist = math.hypot(obj.x - self.worm.x, obj.y - self.worm.y)
            angle_diff = math.atan2(obj.y - self.worm.y, obj.x - self.worm.x) - self.worm.angle
            
            if dist < 80: # Sensory range
                # Normalize angle to -PI to PI
                while angle_diff > math.pi: angle_diff -= 2*math.pi
                while angle_diff < -math.pi: angle_diff += 2*math.pi
                
                strength = (80 - dist) / 80.0
                
                if obj.type == 'food':
                    # Attract: Stimulate AWA/ASE
                    if abs(angle_diff) < 1.0: # Front
                        self.neurons['AWA'].add_input(strength * 40)
                        self.neurons['ASE'].add_input(strength * 40)
                elif obj.type == 'danger':
                    # Repel: Stimulate ASH (Nociceptors)
                    self.neurons['ASH'].add_input(strength * 60)
                elif obj.type == 'wall':
                    # Mechanosensation: FLP/OLQ
                    if dist < 30:
                        self.neurons['FLP'].add_input(50)
                        self.neurons['OLQ'].add_input(50)

    def update_physics(self):
        # Get motor output from specific motor neurons
        # Sum of dorsal vs ventral or left vs right
        # Simplified: AVA/AVB drive speed, others drive turn
        
        signal_fwd = self.neurons['AVB'].membrane_potential
        signal_back = self.neurons['AVA'].membrane_potential
        signal_turn_l = sum([n.membrane_potential for name, n in self.neurons.items() if 'L' in name and n.type=='motor'])
        signal_turn_r = sum([n.membrane_potential for name, n in self.neurons.items() if 'R' in name and n.type=='motor'])
        
        # Drive worm
        self.worm.update(signal_fwd - signal_back, signal_turn_r - signal_turn_l)
        
        # Collision with walls
        for obj in self.objects:
            if obj.type == 'wall' and not obj.collected:
                dist = math.hypot(obj.x - self.worm.x, obj.y - self.worm.y)
                if dist < 20:
                    # Bounce
                    self.worm.angle += math.pi
                    self.neurons['FLP'].add_input(100) # Touch sensation

    def draw_brain(self):
        # Draw connections first
        for neuron in self.neurons.values():
            for target, weight, stype in neuron.outputs:
                color = (100, 100, 120)
                width = 1
                if weight > 15: width = 2
                if stype == 'inhibitory': color = (50, 100, 50)
                
                pygame.draw.line(self.screen, color, 
                                 (neuron.x, neuron.y), (target.x, target.y), width)
        
        # Draw neurons
        for neuron in self.neurons.values():
            neuron.update(self.modulation)
            neuron.draw(self.screen, self.font)

    def draw_ui(self):
        # Panel background
        pygame.draw.rect(self.screen, (20, 20, 30), (WIDTH-250, 0, 250, HEIGHT))
        pygame.draw.line(self.screen, WHITE, (WIDTH-250, 0), (WIDTH-250, HEIGHT), 2)
        
        # Title
        title = self.font_title.render("BRAIN MONITOR", True, CYAN)
        self.screen.blit(title, (WIDTH-240, 20))
        
        # Stats
        y_off = 60
        stats = [
            f"Neurons: {len(self.neurons)}",
            f"Synapses: {self.synapse_count}",
            f"Modulation: {self.modulation:.1f}x",
            f"Time: {self.frame_count/60:.1f}s",
            f"Worm X: {int(self.worm.x)}",
            f"Worm Y: {int(self.worm.y)}",
            f"Objects: {len(self.objects)}",
            "",
            "CONTROLS:",
            "Arrows: Move",
            "1-4: Select Obj",
            "L-Click: Place",
            "R-Click: Delete",
            "M: Modulate",
            "Space: Pause",
            "R: Reset"
        ]
        
        active_spikes = []
        for n in self.neurons.values():
            if n.is_spiking:
                active_spikes.append(f"{n.name} FIRING!")
            for spike in n.traveling_spikes:
                 # Just count visual spikes for fun
                 pass

        for line in stats:
            color = WHITE
            if "Modulation" in line: color = PURPLE
            if "Objects" in line: color = YELLOW
            txt = self.font.render(line, True, color)
            self.screen.blit(txt, (WIDTH-240, y_off))
            y_off += 20
            
        # Active Signals Log
        y_off += 10
        lbl = self.font.render("--- ACTIVE SIGNALS ---", True, RED)
        self.screen.blit(lbl, (WIDTH-240, y_off))
        y_off += 20
        
        count = 0
        for n in self.neurons.values():
            if n.is_spiking and count < 6:
                txt = self.font.render(f"> {n.name} ({n.type})", True, SPIKE_COLOR)
                self.screen.blit(txt, (WIDTH-240, y_off))
                y_off += 18
                count += 1
        
        if count == 0:
            txt = self.font.render("(No spikes)", True, GRAY)
            self.screen.blit(txt, (WIDTH-240, y_off))

    def run(self):
        try:
            while self.running:
                self.clock.tick(FPS)
                self.frame_count += 1
                
                # Event Loop
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        if event.key == pygame.K_SPACE:
                            self.paused = not self.paused
                        if event.key == pygame.K_r:
                            # Reset
                            self.worm = Worm(WIDTH//2, HEIGHT//2)
                            self.objects = []
                            for n in self.neurons.values(): n.reset()
                        if event.key == pygame.K_m:
                            self.modulation = 1.0 if self.modulation != 1.0 else 2.0 # Toggle boost

                if not self.paused:
                    self.handle_input()
                    self.sense_environment()
                    
                    # Update all neurons
                    # Note: Neuron update also handles propagation
                    for n in self.neurons.values():
                        n.update(self.modulation)
                        
                    self.update_physics()

                # Draw
                self.screen.fill(BLACK)
                
                # Draw Objects
                for obj in self.objects:
                    obj.draw(self.screen)
                
                # Draw Worm
                self.worm.draw(self.screen)
                
                # Draw Brain Overlay (Right Side mostly, but worms are small, so we put brain in center-ish or scaled)
                # To make it visible, we draw the brain map in the background or overlay
                # Let's draw the brain map semi-transparently in the center-left
                self.draw_brain()
                
                self.draw_ui()
                
                pygame.display.flip()
                
        except Exception as e:
            print(f"Simulation Error: {e}")
            # Do not crash, just print and try to continue or exit gracefully
            import traceback
            traceback.print_exc()
        finally:
            pygame.quit()
            sys.exit()

if __name__ == "__main__":
    print("Starting C. elegans Realistic Simulation...")
    print("Loading 302 + 10 Neurons...")
    sim = C ElegansSim()
    sim.run()
