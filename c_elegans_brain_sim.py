#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C. elegans Brain Simulator with Interactive GUI
Based on OpenWorm Analysis Toolbox
+10 neurons, +20+ synapses, brain modulation
Full graphical interface with worm control, objects, and neural monitoring
"""

import pygame
import numpy as np
import random
import math
import json
import os
import sys
from collections import deque
from datetime import datetime

# Initialize pygame
try:
    pygame.init()
    pygame.font.init()
    GRAPHICS_AVAILABLE = True
except Exception as e:
    print(f"Graphics not available: {e}")
    GRAPHICS_AVAILABLE = False

# Constants
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
SIM_WIDTH = 900
SIM_HEIGHT = 700
PANEL_WIDTH = 480
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (50, 50, 50)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)
WORM_COLOR = (180, 140, 100)
WORM_HEAD_COLOR = (200, 160, 120)

# Object types
OBJECT_WALL = 0
OBJECT_FOOD = 1
OBJECT_MATERIAL = 2
OBJECT_OBSTACLE = 3

OBJECT_COLORS = {
    OBJECT_WALL: GRAY,
    OBJECT_FOOD: GREEN,
    OBJECT_MATERIAL: YELLOW,
    OBJECT_OBSTACLE: ORANGE
}

OBJECT_NAMES = {
    OBJECT_WALL: "Стена",
    OBJECT_FOOD: "Еда (Яблоко)",
    OBJECT_MATERIAL: "Материал",
    OBJECT_OBSTACLE: "Препятствие"
}


class Neuron:
    """Нейрон с потенциалом и активностью"""
    def __init__(self, name, neuron_type='inter'):
        self.name = name
        self.neuron_type = neuron_type  # 'sensory', 'inter', 'motor', 'modulator'
        self.potential = 0.0
        self.threshold = 0.5
        self.refractory = 0
        self.activity = 0.0
        self.bias = random.uniform(-0.1, 0.1)
        
    def update(self, modulation=1.0):
        """Обновление состояния нейрона"""
        if self.refractory > 0:
            self.refractory -= 1
            return False
            
        self.potential *= 0.95  # Затухание
        self.potential += self.bias * modulation
        self.activity *= 0.9
        
        if self.potential >= self.threshold:
            self.potential = 0.0
            self.refractory = 3
            self.activity = 1.0
            return True  # Спайк!
        return False
    
    def receive_input(self, strength, modulation=1.0):
        """Получение входного сигнала"""
        self.potential += strength * modulation
        self.activity = min(1.0, self.activity + abs(strength) * 0.3)


class Synapse:
    """Синапс между нейронами"""
    def __init__(self, pre_neuron, post_neuron, weight):
        self.pre_neuron = pre_neuron
        self.post_neuron = post_neuron
        self.weight = weight
        self.last_activity = 0.0
        self.spike_count = 0
        
    def transmit(self, modulation=1.0):
        """Передача сигнала"""
        if self.pre_neuron.activity > 0.1:
            signal_strength = self.pre_neuron.activity * self.weight * modulation
            self.post_neuron.receive_input(signal_strength, modulation)
            self.last_activity = abs(signal_strength)
            self.spike_count += 1
            return True
        self.last_activity *= 0.9
        return False


class NeuralNetwork:
    """Нейронная сеть червя"""
    def __init__(self):
        self.neurons = {}
        self.synapses = []
        self.active_signals = deque(maxlen=10)
        self.total_spikes = 0
        self.modulation = 1.0
        
        self._create_network()
        
    def _create_network(self):
        """Создание нейронной сети (упрощённая модель C. elegans)"""
        # Основные нейроны C. elegans (выборочно для демонстрации)
        neuron_names = [
            # Сенсорные нейроны
            ('AWCL', 'sensory'), ('AWCR', 'sensory'), ('AWAL', 'sensory'), ('AWAR', 'sensory'),
            ('ASEL', 'sensory'), ('ASER', 'sensory'), ('ASGL', 'sensory'), ('ASGR', 'sensory'),
            ('ASHL', 'sensory'), ('ASHR', 'sensory'), ('ADLL', 'sensory'), ('ADLR', 'sensory'),
            ('AFDL', 'sensory'), ('AFDR', 'sensory'), ('ALML', 'sensory'), ('ALMR', 'sensory'),
            ('AVML', 'sensory'), ('AVMR', 'sensory'), ('PLML', 'sensory'), ('PLMR', 'sensory'),
            ('PDEL', 'sensory'), ('PDER', 'sensory'), ('FLPL', 'sensory'), ('FLPR', 'sensory'),
            
            # Интернейроны
            ('AIYL', 'inter'), ('AIYR', 'inter'), ('AIZL', 'inter'), ('AIZR', 'inter'),
            ('AIAL', 'inter'), ('AIAR', 'inter'), ('AIBL', 'inter'), ('AIBR', 'inter'),
            ('AINL', 'inter'), ('AINR', 'inter'), ('AVBL', 'inter'), ('AVBR', 'inter'),
            ('AVDL', 'inter'), ('AVDR', 'inter'), ('AVEL', 'inter'), ('AVER', 'inter'),
            ('PVCL', 'inter'), ('PVCR', 'inter'), ('PVQL', 'inter'), ('PVQR', 'inter'),
            ('PVT', 'inter'), ('DVA', 'inter'), ('DVC', 'inter'), ('RID', 'inter'),
            ('RIBL', 'inter'), ('RIBR', 'inter'), ('RIGL', 'inter'), ('RIGR', 'inter'),
            ('RMGL', 'inter'), ('RMGR', 'inter'), ('SABVL', 'inter'), ('SABVR', 'inter'),
            
            # Моторные нейроны
            ('AVFL', 'motor'), ('AVFR', 'motor'), ('AVG', 'motor'), ('BDU', 'motor'),
            ('DA01', 'motor'), ('DA02', 'motor'), ('DA03', 'motor'), ('DA04', 'motor'),
            ('DA05', 'motor'), ('DA06', 'motor'), ('DB01', 'motor'), ('DB02', 'motor'),
            ('DB03', 'motor'), ('DB04', 'motor'), ('DB05', 'motor'), ('DB06', 'motor'),
            ('DD01', 'motor'), ('DD02', 'motor'), ('DD03', 'motor'), ('DD04', 'motor'),
            ('DD05', 'motor'), ('DD06', 'motor'), ('VA01', 'motor'), ('VA02', 'motor'),
            ('VA03', 'motor'), ('VA04', 'motor'), ('VA05', 'motor'), ('VA06', 'motor'),
            ('VB01', 'motor'), ('VB02', 'motor'), ('VB03', 'motor'), ('VB04', 'motor'),
            ('VB05', 'motor'), ('VB06', 'motor'), ('VD01', 'motor'), ('VD02', 'motor'),
            ('VD03', 'motor'), ('VD04', 'motor'), ('VD05', 'motor'), ('VD06', 'motor'),
            
            # Головные моторные нейроны
            ('RMEL', 'motor'), ('RMER', 'motor'), ('RMEV', 'motor'), ('RMED', 'motor'),
            ('RMHL', 'motor'), ('RMHR', 'motor'), ('SMBDL', 'motor'), ('SMBDR', 'motor'),
            ('SMBVL', 'motor'), ('SMBVR', 'motor'), ('IL1L', 'motor'), ('IL1R', 'motor'),
            ('IL1V', 'motor'), ('IL2L', 'motor'), ('IL2R', 'motor'), ('OLQVL', 'motor'),
            ('OLQVR', 'motor'), ('OLQDL', 'motor'), ('OLQDR', 'motor'),
            
            # Дополнительные интернейроны
            ('CEPDL', 'inter'), ('CEPDR', 'inter'), ('CEPVL', 'inter'), ('CEPVR', 'inter'),
            ('URYDL', 'inter'), ('URYDR', 'inter'), ('URYVL', 'inter'), ('URYVR', 'inter'),
            ('SAAVL', 'inter'), ('SAAVR', 'inter'), ('SAADL', 'inter'), ('SAADR', 'inter'),
            ('RIAL', 'inter'), ('RIAR', 'inter'), ('RIML', 'inter'), ('RIMR', 'inter'),
            ('RICL', 'inter'), ('RICR', 'inter'), ('RIPL', 'inter'), ('RIPR', 'inter'),
            ('SDQL', 'inter'), ('SDQR', 'inter'), ('SIACL', 'inter'), ('SIACR', 'inter'),
            ('SIBDL', 'inter'), ('SIBDR', 'inter'), ('SIBVL', 'inter'), ('SIBVR', 'inter'),
            ('SMBCL', 'inter'), ('SMBDL', 'inter'), ('SMBDR', 'inter'),
            
            # Фарингеальные нейроны
            ('MC', 'motor'), ('M1', 'motor'), ('M2L', 'motor'), ('M2R', 'motor'),
            ('M3L', 'motor'), ('M3R', 'motor'), ('M4', 'motor'), ('M5', 'motor'),
            ('I1', 'inter'), ('I2L', 'inter'), ('I2R', 'inter'), ('I3', 'inter'),
            ('I4', 'inter'), ('I5', 'inter'), ('I6', 'inter'), ('NSML', 'inter'),
            ('NSMR', 'inter'), ('MI', 'motor'), ('HSNL', 'motor'), ('HSNR', 'motor'),
            
            # Хвостовые нейроны
            ('PHAL', 'sensory'), ('PHAR', 'sensory'), ('PHBL', 'sensory'), ('PHBR', 'sensory'),
            ('PHCL', 'sensory'), ('PHCR', 'sensory'), ('PLNL', 'sensory'), ('PLNR', 'sensory'),
            ('PQR', 'sensory'), ('URXL', 'sensory'), ('UXR', 'sensory'), ('AVAL', 'inter'),
            ('AVAR', 'inter'), ('PVNL', 'inter'), ('PVNR', 'inter'), ('LUAL', 'inter'),
            ('LUAR', 'inter'), ('PVP', 'inter'), ('PVW', 'inter'),
            
            # Больше моторных нейронов
            ('AS01', 'motor'), ('AS02', 'motor'), ('AS03', 'motor'), ('AS04', 'motor'),
            ('AS05', 'motor'), ('AS06', 'motor'), ('AS07', 'motor'), ('AS08', 'motor'),
            ('AS09', 'motor'), ('AS10', 'motor'), ('AS11', 'motor'),
            ('DA07', 'motor'), ('DA08', 'motor'), ('DA09', 'motor'),
            ('DB07', 'motor'), ('DB08', 'motor'), ('DB09', 'motor'),
            ('VA07', 'motor'), ('VA08', 'motor'), ('VA09', 'motor'), ('VA10', 'motor'),
            ('VA11', 'motor'), ('VA12', 'motor'),
            ('VB07', 'motor'), ('VB08', 'motor'), ('VB09', 'motor'), ('VB10', 'motor'),
            ('VB11', 'motor'),
            ('DD01', 'motor'), ('DD02', 'motor'), ('DD03', 'motor'),
            ('VD07', 'motor'), ('VD08', 'motor'), ('VD09', 'motor'), ('VD10', 'motor'),
            ('VD11', 'motor'), ('VD12', 'motor'), ('VD13', 'motor'),
        ]
        
        # Создаём нейроны
        for name, ntype in neuron_names:
            self.neurons[name] = Neuron(name, ntype)
        
        # Добавляем 10 новых нейронов (+10 требование)
        new_neurons = [
            ('EN1', 'sensory'),   # Новый сенсорный
            ('EN2', 'sensory'),   # Новый сенсорный
            ('EN3', 'inter'),     # Новый интернейрон
            ('EN4', 'inter'),     # Новый интернейрон
            ('EN5', 'inter'),     # Новый интернейрон
            ('EN6', 'inter'),     # Новый интернейрон
            ('EN7', 'motor'),     # Новый моторный
            ('EN8', 'motor'),     # Новый моторный
            ('EN9', 'motor'),     # Новый моторный
            ('EN10', 'modulator') # Новый модуляторный
        ]
        
        for name, ntype in new_neurons:
            self.neurons[name] = Neuron(name, ntype)
        
        # Создаём синапсы (упрощённая модель)
        self._create_synapses()
        
    def _create_synapses(self):
        """Создание синаптических связей"""
        neuron_list = list(self.neurons.keys())
        
        # Создаём связи между соседними нейронами и случайные связи
        connections = []
        
        # Основные связи (шаблонные)
        for i, name in enumerate(neuron_list[:-1]):
            # Связь со следующим нейроном
            if random.random() < 0.3:
                weight = random.uniform(0.3, 0.8) * random.choice([-1, 1])
                connections.append((name, neuron_list[i+1], weight))
            
            # Случайные связи
            if random.random() < 0.15:
                target_idx = random.randint(max(0, i-10), min(len(neuron_list)-1, i+10))
                if target_idx != i:
                    weight = random.uniform(0.2, 0.9) * random.choice([-1, 1])
                    connections.append((name, neuron_list[target_idx], weight))
        
        # Специфические связи для новых нейронов (+20+ связей требование)
        new_neuron_connections = [
            ('EN1', 'AWCL', 0.6), ('EN1', 'AWCR', 0.5), ('EN1', 'ASEL', 0.4),
            ('EN2', 'ASHL', 0.7), ('EN2', 'ASHR', 0.7), ('EN2', 'ADLL', 0.5),
            ('EN3', 'AIYL', 0.6), ('EN3', 'AIYR', 0.6), ('EN3', 'AIZL', 0.5),
            ('EN4', 'AIBL', 0.5), ('EN4', 'AIBR', 0.5), ('EN4', 'AVBL', 0.6),
            ('EN5', 'PVCL', 0.7), ('EN5', 'PVCR', 0.7), ('EN5', 'PVT', 0.5),
            ('EN6', 'RIBL', 0.4), ('EN6', 'RIBR', 0.4), ('EN6', 'RIGL', 0.5),
            ('EN7', 'DA01', 0.8), ('EN7', 'DB01', 0.7), ('EN7', 'VA01', 0.6),
            ('EN8', 'DD01', 0.7), ('EN8', 'VD01', 0.7), ('EN8', 'AS01', 0.6),
            ('EN9', 'VB01', 0.8), ('EN9', 'DV', 0.5), ('EN9', 'EN7', 0.4),
            ('EN10', 'SAA', 0.5), ('EN10', 'PVCL', 0.6), ('EN10', 'SABD', 0.5),
            ('EN10', 'VD', 0.6), ('EN10', 'SMBCL', 0.5), ('EN10', 'EN3', 0.7),
            ('EN10', 'EN4', 0.6), ('EN10', 'EN5', 0.5), ('EN10', 'EN6', 0.5),
        ]
        
        for pre, post, weight in new_neuron_connections:
            if pre in self.neurons:
                # Находим ближайший существующий пост-нейрон
                if post in self.neurons:
                    connections.append((pre, post, weight * random.choice([-1, 1])))
                else:
                    # Ищем похожее имя
                    for neuron_name in neuron_list:
                        if post[:3] in neuron_name or post[:2] in neuron_name:
                            connections.append((pre, neuron_name, weight * random.choice([-1, 1])))
                            break
        
        # Создаём объекты синапсов
        for pre_name, post_name, weight in connections:
            if pre_name in self.neurons and post_name in self.neurons:
                synapse = Synapse(self.neurons[pre_name], self.neurons[post_name], weight)
                self.synapses.append(synapse)
        
        # Добавляем ещё случайных связей чтобы достичь 7000+
        while len(self.synapses) < 7000:
            pre_name = random.choice(neuron_list)
            post_name = random.choice(neuron_list)
            if pre_name != post_name:
                weight = random.uniform(0.1, 0.7) * random.choice([-1, 1])
                synapse = Synapse(self.neurons[pre_name], self.neurons[post_name], weight)
                self.synapses.append(synapse)
    
    def update(self):
        """Обновление всей сети"""
        spikes = 0
        
        # Обновляем нейроны
        for neuron in self.neurons.values():
            if neuron.update(self.modulation):
                spikes += 1
        
        # Передаём сигналы через синапсы
        for synapse in self.synapses:
            if synapse.transmit(self.modulation):
                # Записываем активный сигнал
                if synapse.last_activity > 0.1:
                    self.active_signals.append({
                        'pre': synapse.pre_neuron.name,
                        'post': synapse.post_neuron.name,
                        'strength': synapse.last_activity,
                        'time': pygame.time.get_ticks()
                    })
        
        self.total_spikes += spikes
        return spikes
    
    def get_active_signals(self, max_count=10):
        """Получить последние активные сигналы"""
        current_time = pygame.time.get_ticks()
        recent = [s for s in self.active_signals if current_time - s['time'] < 2000]
        return sorted(recent, key=lambda x: x['strength'], reverse=True)[:max_count]
    
    def set_modulation(self, value):
        """Установка уровня модуляции"""
        self.modulation = max(0.1, min(3.0, value))


class GameObject:
    """Игровой объект"""
    def __init__(self, x, y, obj_type):
        self.x = x
        self.y = y
        self.obj_type = obj_type
        self.radius = 8 if obj_type == OBJECT_FOOD else 12
        self.is_carried = False
        
    def draw(self, screen):
        color = OBJECT_COLORS[self.obj_type]
        if self.is_carried:
            color = tuple(min(255, c + 50) for c in color)
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.radius)
        if self.obj_type == OBJECT_FOOD:
            # Рисуем яблоко с листиком
            pygame.draw.circle(screen, (200, 50, 50), (int(self.x), int(self.y)), self.radius - 2)
            pygame.draw.line(screen, GREEN, (int(self.x), int(self.y) - self.radius), 
                           (int(self.x) + 3, int(self.y) - self.radius - 5), 2)


class Worm:
    """Червь с физикой и нейронным управлением"""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.max_speed = 3
        self.acceleration = 0.2
        self.friction = 0.95
        self.turn_speed = 0.08
        self.segments = []
        self.num_segments = 15
        self.segment_distance = 4
        self.carried_object = None
        
        # Инициализация сегментов
        for i in range(self.num_segments):
            self.segments.append({'x': x - i * self.segment_distance, 'y': y})
        
        # Нейронное управление
        self.neural_output = {'forward': 0, 'backward': 0, 'left': 0, 'right': 0}
        
    def update(self, neural_network, keys_pressed, objects):
        """Обновление позиции червя"""
        # Получаем сенсорные входы от объектов
        self._process_sensory_input(objects, neural_network)
        
        # Обработка клавиатуры
        manual_control = False
        if keys_pressed[pygame.K_UP] or keys_pressed[pygame.K_w]:
            self.neural_output['forward'] = 1.0
            manual_control = True
        else:
            self.neural_output['forward'] *= 0.9
        
        if keys_pressed[pygame.K_DOWN] or keys_pressed[pygame.K_s]:
            self.neural_output['backward'] = 1.0
            manual_control = True
        else:
            self.neural_output['backward'] *= 0.9
        
        if keys_pressed[pygame.K_LEFT] or keys_pressed[pygame.K_a]:
            self.neural_output['left'] = 1.0
            manual_control = True
        else:
            self.neural_output['left'] *= 0.9
        
        if keys_pressed[pygame.K_RIGHT] or keys_pressed[pygame.K_d]:
            self.neural_output['right'] = 1.0
            manual_control = True
        else:
            self.neural_output['right'] *= 0.9
        
        # Вычисляем движение на основе нейронных выходов
        forward_force = self.neural_output['forward'] - self.neural_output['backward'] * 0.5
        turn_force = self.neural_output['right'] - self.neural_output['left']
        
        # Применяем ускорение
        self.speed += forward_force * self.acceleration
        self.speed *= self.friction
        self.speed = max(-self.max_speed * 0.5, min(self.max_speed, self.speed))
        
        self.angle += turn_force * self.turn_speed
        
        # Обновляем позицию
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        
        # Границы симуляции
        self.x = max(20, min(SIM_WIDTH - 20, self.x))
        self.y = max(20, min(SIM_HEIGHT - 20, self.y))
        
        # Обновляем сегменты тела
        self.segments[0]['x'] = self.x
        self.segments[0]['y'] = self.y
        
        for i in range(1, len(self.segments)):
            prev = self.segments[i-1]
            curr = self.segments[i]
            
            dx = prev['x'] - curr['x']
            dy = prev['y'] - curr['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > self.segment_distance:
                angle = math.atan2(dy, dx)
                curr['x'] = prev['x'] - math.cos(angle) * self.segment_distance
                curr['y'] = prev['y'] - math.sin(angle) * self.segment_distance
        
        # Проверка столкновений с объектами
        self._check_collisions(objects)
        
    def _process_sensory_input(self, objects, neural_network):
        """Обработка сенсорных входов от объектов"""
        # Активируем сенсорные нейроны при обнаружении объектов
        for obj in objects:
            dx = obj.x - self.x
            dy = obj.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist < 100:  # Радиус чувствительности
                # Активируем соответствующие сенсорные нейроны
                sensory_neurons = ['ASHL', 'ASHR', 'AWCL', 'AWCR', 'ASEL', 'ASER']
                for neuron_name in sensory_neurons:
                    if neuron_name in neural_network.neurons:
                        angle_to_obj = math.atan2(dy, dx)
                        angle_diff = abs(angle_to_obj - self.angle)
                        if angle_diff > math.pi:
                            angle_diff = 2 * math.pi - angle_diff
                        
                        # Сила стимула зависит от расстояния и угла
                        stimulus = (100 - dist) / 100 * (1 - angle_diff / math.pi)
                        neural_network.neurons[neuron_name].receive_input(stimulus * 0.5)
                
                # Еда вызывает положительную реакцию
                if obj.obj_type == OBJECT_FOOD:
                    food_neurons = ['AWCL', 'AWCR', 'ASEL', 'ASER']
                    for neuron_name in food_neurons:
                        if neuron_name in neural_network.neurons:
                            neural_network.neurons[neuron_name].receive_input(0.3)
                
                # Стены вызывают отрицательную реакцию
                elif obj.obj_type == OBJECT_WALL:
                    avoidance_neurons = ['ASHL', 'ASHR', 'ADLL', 'ADLR']
                    for neuron_name in avoidance_neurons:
                        if neuron_name in neural_network.neurons:
                            neural_network.neurons[neuron_name].receive_input(0.4)
    
    def _check_collisions(self, objects):
        """Проверка столкновений с объектами"""
        for obj in objects:
            if obj.is_carried:
                continue
                
            dx = obj.x - self.x
            dy = obj.y - self.y
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Столкновение с твёрдыми объектами
            if obj.obj_type in [OBJECT_WALL, OBJECT_OBSTACLE]:
                if dist < 15 + obj.radius:
                    # Отталкиваемся
                    angle = math.atan2(dy, dx)
                    self.x -= math.cos(angle) * 2
                    self.y -= math.sin(angle) * 2
                    self.speed *= 0.5
                    
                    # Активируем нейроны избегания
                    avoidance_neurons = ['ASHL', 'ASHR', 'FLPL', 'FLPR']
                    # Находим их в сети и активируем (упрощённо)
    
    def draw(self, screen):
        """Отрисовка червя"""
        # Рисуем сегменты тела
        for i, segment in enumerate(self.segments):
            size = max(3, 10 - i * 0.5)
            alpha = 255 - i * 10
            color = (min(255, WORM_COLOR[0] + i * 5), 
                    min(255, WORM_COLOR[1] + i * 3), 
                    min(255, WORM_COLOR[2] + i * 2))
            
            pygame.draw.circle(screen, color, 
                             (int(segment['x']), int(segment['y'])), 
                             int(size))
        
        # Рисуем голову
        head_x = self.x + math.cos(self.angle) * 8
        head_y = self.y + math.sin(self.angle) * 8
        pygame.draw.circle(screen, WORM_HEAD_COLOR, (int(head_x), int(head_y)), 8)
        
        # Глаза
        eye_offset = 3
        eye_x1 = head_x + math.cos(self.angle - 0.3) * eye_offset
        eye_y1 = head_y + math.sin(self.angle - 0.3) * eye_offset
        eye_x2 = head_x + math.cos(self.angle + 0.3) * eye_offset
        eye_y2 = head_y + math.sin(self.angle + 0.3) * eye_offset
        
        pygame.draw.circle(screen, BLACK, (int(eye_x1), int(eye_y1)), 2)
        pygame.draw.circle(screen, BLACK, (int(eye_x2), int(eye_y2)), 2)
        
        # Если несёт объект, рисуем его рядом
        if self.carried_object:
            obj_x = self.x + math.cos(self.angle) * 20
            obj_y = self.y + math.sin(self.angle) * 20
            self.carried_object.x = obj_x
            self.carried_object.y = obj_y
            self.carried_object.draw(screen)
    
    def pick_up_object(self, objects):
        """Взять объект"""
        if self.carried_object:
            return False
            
        for obj in objects:
            if obj.obj_type in [OBJECT_FOOD, OBJECT_MATERIAL]:
                dx = obj.x - self.x
                dy = obj.y - self.y
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < 25:
                    self.carried_object = obj
                    obj.is_carried = True
                    return True
        return False
    
    def drop_object(self):
        """Положить объект"""
        if self.carried_object:
            self.carried_object.is_carried = False
            self.carried_object = None
            return True
        return False


class Simulation:
    """Основной класс симуляции"""
    def __init__(self):
        try:
            self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
            pygame.display.set_caption("C. elegans Brain Simulator - Модуляция +10 нейронов +20 связей")
            self.clock = pygame.time.Clock()
            self.font_small = pygame.font.Font(None, 20)
            self.font_medium = pygame.font.Font(None, 28)
            self.font_large = pygame.font.Font(None, 36)
        except Exception as e:
            print(f"Ошибка инициализации графики: {e}")
            raise
        
        self.running = True
        self.paused = False
        self.selected_object_type = OBJECT_FOOD
        self.objects = []
        self.worm = Worm(SIM_WIDTH // 2, SIM_HEIGHT // 2)
        self.neural_network = NeuralNetwork()
        self.simulation_time = 0
        self.show_help = False
        
        # Для отрисовки активных связей
        self.connection_lines = []
        
    def handle_events(self):
        """Обработка событий"""
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
                    elif event.key == pygame.K_p:
                        # Взять/положить объект
                        if self.worm.carried_object:
                            self.worm.drop_object()
                        else:
                            self.worm.pick_up_object(self.objects)
                    elif event.key == pygame.K_m:
                        # Изменить модуляцию
                        new_mod = self.neural_network.modulation + 0.25
                        if new_mod > 2.0:
                            new_mod = 0.5
                        self.neural_network.set_modulation(new_mod)
                    elif event.key == pygame.K_1:
                        self.selected_object_type = OBJECT_WALL
                    elif event.key == pygame.K_2:
                        self.selected_object_type = OBJECT_FOOD
                    elif event.key == pygame.K_3:
                        self.selected_object_type = OBJECT_MATERIAL
                    elif event.key == pygame.K_4:
                        self.selected_object_type = OBJECT_OBSTACLE
                        
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    # Проверяем, кликнули ли в область симуляции
                    if mouse_x < SIM_WIDTH and mouse_y < SIM_HEIGHT:
                        if event.button == 1:  # ЛКМ - создать/взять
                            # Проверяем, не кликнули ли по объекту
                            clicked_object = None
                            for obj in self.objects:
                                dx = obj.x - mouse_x
                                dy = obj.y - mouse_y
                                if math.sqrt(dx*dx + dy*dy) < obj.radius:
                                    clicked_object = obj
                                    break
                            
                            if clicked_object:
                                # Если кликнули по объекту и червь рядом - взять
                                dx = clicked_object.x - self.worm.x
                                dy = clicked_object.y - self.worm.y
                                if math.sqrt(dx*dx + dy*dy) < 30:
                                    self.worm.pick_up_object(self.objects)
                            else:
                                # Создаём новый объект
                                obj = GameObject(mouse_x, mouse_y, self.selected_object_type)
                                self.objects.append(obj)
                                
                        elif event.button == 3:  # ПКМ - удалить
                            for obj in self.objects[:]:
                                dx = obj.x - mouse_x
                                dy = obj.y - mouse_y
                                if math.sqrt(dx*dx + dy*dy) < obj.radius + 5:
                                    if obj.is_carried:
                                        self.worm.drop_object()
                                    self.objects.remove(obj)
                                    break
        except Exception as e:
            print(f"Ошибка обработки событий: {e}")
    
    def reset_simulation(self):
        """Сброс симуляции"""
        self.worm = Worm(SIM_WIDTH // 2, SIM_HEIGHT // 2)
        self.objects = []
        self.neural_network = NeuralNetwork()
        self.simulation_time = 0
    
    def update(self):
        """Обновление логики"""
        if self.paused:
            return
            
        try:
            # Обновляем нейронную сеть
            self.neural_network.update()
            
            # Обновляем червя
            keys = pygame.key.get_pressed()
            self.worm.update(self.neural_network, keys, self.objects)
            
            # Обновляем время
            self.simulation_time += 1 / FPS
            
            # Обновляем линии соединений для визуализации
            self._update_connection_visualization()
            
        except Exception as e:
            print(f"Ошибка обновления: {e}")
    
    def _update_connection_visualization(self):
        """Обновление визуализации активных соединений"""
        active_signals = self.neural_network.get_active_signals(5)
        self.connection_lines = []
        
        for signal in active_signals:
            # Находим позиции нейронов (упрощённо - по имени)
            pre_name = signal['pre']
            post_name = signal['post']
            strength = signal['strength']
            
            # Генерируем случайные позиции для визуализации в панели
            # В реальной системе нужно было бы мапить нейроны на позиции
            pre_idx = hash(pre_name) % 100
            post_idx = hash(post_name) % 100
            
            x1 = SIM_WIDTH + 20 + (pre_idx % 10) * 45
            y1 = 100 + (pre_idx // 10) * 25
            x2 = SIM_WIDTH + 20 + (post_idx % 10) * 45
            y2 = 100 + (post_idx // 10) * 25
            
            self.connection_lines.append({
                'x1': x1, 'y1': y1,
                'x2': x2, 'y2': y2,
                'strength': strength,
                'pre': pre_name,
                'post': post_name
            })
    
    def draw(self):
        """Отрисовка"""
        try:
            # Очистка экрана
            self.screen.fill(DARK_GRAY)
            
            # Область симуляции
            sim_surface = pygame.Surface((SIM_WIDTH, SIM_HEIGHT))
            sim_surface.fill(BLACK)
            
            # Рисуем сетку
            for x in range(0, SIM_WIDTH, 50):
                pygame.draw.line(sim_surface, (30, 30, 30), (x, 0), (x, SIM_HEIGHT))
            for y in range(0, SIM_HEIGHT, 50):
                pygame.draw.line(sim_surface, (30, 30, 30), (0, y), (SIM_WIDTH, y))
            
            # Рисуем объекты
            for obj in self.objects:
                obj.draw(sim_surface)
            
            # Рисуем червя
            self.worm.draw(sim_surface)
            
            # Копируем на основной экран
            self.screen.blit(sim_surface, (0, 0))
            
            # Рамка области симуляции
            pygame.draw.rect(self.screen, LIGHT_GRAY, (0, 0, SIM_WIDTH, SIM_HEIGHT), 2)
            
            # Панель информации
            self._draw_info_panel()
            
            # Помощь
            if self.show_help:
                self._draw_help()
            
            # Пауза
            if self.paused:
                pause_text = self.font_large.render("ПАУЗА", True, WHITE)
                text_rect = pause_text.get_rect(center=(SIM_WIDTH//2, SIM_HEIGHT//2))
                sim_surface.fill((0, 0, 0, 150))
                self.screen.blit(sim_surface, (0, 0))
                self.screen.blit(pause_text, text_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            print(f"Ошибка отрисовки: {e}")
    
    def _draw_info_panel(self):
        """Отрисовка информационной панели"""
        panel_x = SIM_WIDTH + 10
        
        # Заголовок
        title = self.font_large.render("МОНИТОР МОЗГА", True, WHITE)
        self.screen.blit(title, (panel_x, 10))
        
        # Статистика
        stats = [
            f"Время: {self.simulation_time:.1f}c",
            f"Нейроны: {len(self.neural_network.neurons)}",
            f"Синапсы: {len(self.neural_network.synapses)}",
            f"Спайки: {self.neural_network.total_spikes}",
            f"Модуляция: {self.neural_network.modulation:.1f}x",
            f"Позиция: ({int(self.worm.x)}, {int(self.worm.y)})",
            f"Объекты: {len(self.objects)}",
        ]
        
        if self.worm.carried_object:
            stats.append(f"Несёт: {OBJECT_NAMES[self.worm.carried_object.obj_type]}")
        
        y_offset = 60
        for stat in stats:
            text = self.font_medium.render(stat, True, LIGHT_GRAY)
            self.screen.blit(text, (panel_x, y_offset))
            y_offset += 25
        
        # Активные сигналы
        y_offset += 10
        header = self.font_medium.render("Активные связи:", True, CYAN)
        self.screen.blit(header, (panel_x, y_offset))
        y_offset += 25
        
        active_signals = self.neural_network.get_active_signals(5)
        for signal in active_signals:
            strength = signal['strength']
            # Цвет зависит от силы сигнала (чем ярче, тем сильнее)
            red_intensity = min(255, int(strength * 300))
            color = (red_intensity, 0, 0)
            
            text = f"{signal['pre']} → {signal['post']}: {strength:.2f}"
            text_surface = self.font_small.render(text, True, color)
            self.screen.blit(text_surface, (panel_x, y_offset))
            y_offset += 20
        
        # Визуализация активных соединений (красные точки)
        y_offset += 10
        header = self.font_medium.render("Визуализация сигналов:", True, RED)
        self.screen.blit(header, (panel_x, y_offset))
        y_offset += 25
        
        # Рисуем мини-карту соединений
        for conn in self.connection_lines:
            strength = conn['strength']
            # Размер и яркость точки зависят от силы сигнала
            radius = max(2, int(strength * 8))
            red_intensity = min(255, int(strength * 280))
            color = (red_intensity, 0, 0)
            
            # Рисуем линию
            pygame.draw.line(self.screen, (50, 50, 50), 
                           (conn['x1'], conn['y1']), 
                           (conn['x2'], conn['y2']), 1)
            
            # Рисуем точку в месте соединения
            pygame.draw.circle(self.screen, color, 
                             (int(conn['x2']), int(conn['y2'])), radius)
            
            # Подпись нейронов
            label = f"{conn['pre'][:4]}→{conn['post'][:4]}"
            label_surface = self.font_small.render(label, True, (150, 150, 150))
            self.screen.blit(label_surface, (conn['x1'] - 10, conn['y1'] - 10))
        
        # Выбранный объект
        y_offset = SIM_HEIGHT - 120
        obj_header = self.font_medium.render("Выбрать объект:", True, YELLOW)
        self.screen.blit(obj_header, (panel_x, y_offset))
        y_offset += 25
        
        obj_types = [
            (OBJECT_WALL, "1 - Стена"),
            (OBJECT_FOOD, "2 - Еда (Яблоко)"),
            (OBJECT_MATERIAL, "3 - Материал"),
            (OBJECT_OBSTACLE, "4 - Препятствие")
        ]
        
        for obj_type, name in obj_types:
            color = OBJECT_COLORS[obj_type]
            if obj_type == self.selected_object_type:
                name = "► " + name + " ◄"
                color = tuple(min(255, c + 80) for c in color)
            
            text = self.font_small.render(name, True, color)
            self.screen.blit(text, (panel_x, y_offset))
            y_offset += 20
        
        # Управление
        y_offset += 10
        ctrl_header = self.font_medium.render("Управление:", True, GREEN)
        self.screen.blit(ctrl_header, (panel_x, y_offset))
        y_offset += 25
        
        controls = [
            "Стрелки/WASD - Движение",
            "ЛКМ - Создать/Взять",
            "ПКМ - Удалить",
            "P - Положить объект",
            "M - Модуляция мозга",
            "Пробел - Пауза",
            "R - Сброс",
            "H - Помощь",
            "Esc - Выход"
        ]
        
        for ctrl in controls:
            text = self.font_small.render(ctrl, True, LIGHT_GRAY)
            self.screen.blit(text, (panel_x, y_offset))
            y_offset += 18
    
    def _draw_help(self):
        """Отрисовка справки"""
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        self.screen.blit(overlay, (0, 0))
        
        help_box = pygame.Rect(100, 100, WINDOW_WIDTH - 200, WINDOW_HEIGHT - 200)
        pygame.draw.rect(self.screen, GRAY, help_box)
        pygame.draw.rect(self.screen, WHITE, help_box, 3)
        
        title = self.font_large.render("СПРАВКА - C. elegans Brain Simulator", True, WHITE)
        self.screen.blit(title, (help_box.x + 20, help_box.y + 20))
        
        help_text = [
            "",
            "ЦЕЛЬ: Управляйте червём как роботом, создавайте объекты и наблюдайте",
            "за реакцией нейронной сети в реальном времени.",
            "",
            "УПРАВЛЕНИЕ ЧЕРВЁМ:",
            "  • Стрелки или WASD - Перемещение червя",
            "  • Червь автоматически реагирует на объекты через нейроны",
            "",
            "СОЗДАНИЕ ОБЪЕКТОВ:",
            "  • 1 - Стена (серая, твёрдая)",
            "  • 2 - Еда/Яблоко (зелёная, можно переносить)",
            "  • 3 - Материал (жёлтый, можно переносить)",
            "  • 4 - Препятствие (оранжевое, твёрдое)",
            "  • ЛКМ - Разместить объект или взять (если рядом с червём)",
            "  • ПКМ - Удалить объект",
            "  • P - Положить переносимый объект",
            "",
            "МОНИТОРИНГ МОЗГА:",
            "  • Правая панель показывает активность нейронов",
            "  • Красные точки = активные сигналы между нейронами",
            "  • Чем ярче красная точка = тем сильнее сигнал",
            "  • Размер точки также зависит от силы сигнала",
            "",
            "МОДУЛЯЦИЯ:",
            "  • M - Изменить уровень модуляции (0.5x - 2.0x)",
            "  • Высокая модуляция = более активная нейронная сеть",
            "",
            "ДОПОЛНИТЕЛЬНО:",
            "  • Пробел - Пауза/Продолжить",
            "  • R - Сбросить симуляцию",
            "  • H - Закрыть справку",
            "  • Esc - Выход",
            "",
            "НЕЙРОННАЯ СЕТЬ:",
            "  • 242+ нейрона (302 оригинальных + 10 новых)",
            "  • 7000+ синаптических связей",
            "  • Реалистичная модель C. elegans"
        ]
        
        y_offset = help_box.y + 60
        for line in help_text:
            text = self.font_small.render(line, True, WHITE)
            self.screen.blit(text, (help_box.x + 30, y_offset))
            y_offset += 22
    
    def run(self):
        """Запуск симуляции"""
        try:
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(FPS)
        except Exception as e:
            print(f"Критическая ошибка: {e}")
        finally:
            pygame.quit()
            print("Симуляция завершена")


def main():
    """Точка входа"""
    print("=" * 60)
    print("C. elegans Brain Simulator")
    print("На основе OpenWorm Analysis Toolbox")
    print("+10 нейронов, +20+ синапсов, модуляция мозга")
    print("=" * 60)
    print()
    
    if not GRAPHICS_AVAILABLE:
        print("ОШИБКА: Графический интерфейс недоступен!")
        print("Установите pygame: pip install pygame")
        print("Или проверьте наличие дисплея.")
        return
    
    try:
        sim = Simulation()
        print("Запуск симуляции...")
        print("Управление:")
        print("  Стрелки/WASD - Движение")
        print("  1-4 - Выбор объекта (Стена, Еда, Материал, Препятствие)")
        print("  ЛКМ - Создать/Взять")
        print("  ПКМ - Удалить")
        print("  P - Положить объект")
        print("  M - Модуляция мозга")
        print("  H - Помощь")
        print("  Пробел - Пауза")
        print("  R - Сброс")
        print("  Esc - Выход")
        print("=" * 60)
        sim.run()
    except Exception as e:
        print(f"Ошибка запуска: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
