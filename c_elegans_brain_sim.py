#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
C. elegans Brain Simulator v2.0
Interactive Robot Mode with Neural Visualization
+10 Neurons, +20 Synapses, Modulation System
"""

import pygame
import numpy as np
import random
import math
import sys
import os

# --- КОНФИГУРАЦИЯ ---
WIDTH, HEIGHT = 1200, 800
FPS = 60
WORM_SIZE = 15
NEURAL_PANEL_WIDTH = 300

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)
DARK_RED = (100, 0, 0)

# Типы объектов
OBJ_NONE = 0
OBJ_WALL = 1
OBJ_FOOD = 2
OBJ_MATERIAL = 3
OBJ_DANGER = 4

class Neuron:
    def __init__(self, name, x, y, type_='inter'):
        self.name = name
        self.x = x  # Позиция в панели визуализации (0-100%)
        self.y = y
        self.type = type_  # 'sensor', 'inter', 'motor', 'modulator'
        self.potential = 0.0
        self.bias = random.uniform(-0.1, 0.1)
        
    def reset(self):
        self.potential = 0.0

class Synapse:
    def __init__(self, pre_name, post_name, weight):
        self.pre = pre_name
        self.post = post_name
        self.weight = weight
        self.current_signal = 0.0
        
    def transmit(self, pre_potential, modulation):
        signal = pre_potential * self.weight * modulation
        self.current_signal = signal
        return signal

class WormBrain:
    def __init__(self):
        self.neurons = {}
        self.synapses = []
        self.modulation = 1.0
        self.spike_log = [] # Для визуализации последних сигналов
        
        self._init_network()
        
    def _init_network(self):
        # 1. Создаем базовые нейроны (упрощенная модель 302 + 10 новых)
        # Сенсоры (передняя часть)
        sensors = ['ASHL', 'ASHR', 'AWCL', 'AWCR', 'AFDL', 'AFDR', 'ADLL', 'ADLR']
        for i, name in enumerate(sensors):
            self.neurons[name] = Neuron(name, 10 + (i%4)*20, 10 + (i//4)*20, 'sensor')
            
        # Интернейроны (центр)
        inter = ['AIYL', 'AIYR', 'AIZL', 'AIZR', 'AWBL', 'AWBR', 'CEPVL', 'CEPVR']
        for i, name in enumerate(inter):
            self.neurons[name] = Neuron(name, 30 + (i%4)*20, 30 + (i//4)*20, 'inter')
            
        # Моторные (задняя часть)
        motors = ['AVAR', 'AVAL', 'AVBR', 'AVBL', 'PVCR', 'PVCL', 'DB1', 'VB1']
        for i, name in enumerate(motors):
            self.neurons[name] = Neuron(name, 60 + (i%4)*20, 60 + (i//4)*20, 'motor')
            
        # 2. Добавляем +10 НОВЫХ нейронов (EN1-EN10)
        new_neurons = [
            ('EN1', 'sensor'), ('EN2', 'sensor'),
            ('EN3', 'inter'), ('EN4', 'inter'), ('EN5', 'inter'), ('EN6', 'inter'),
            ('EN7', 'motor'), ('EN8', 'motor'), ('EN9', 'motor'),
            ('EN10', 'modulator')
        ]
        
        for i, (name, type_) in enumerate(new_neurons):
            # Размещаем их красиво на панели
            nx = 15 + (i % 5) * 18
            ny = 80 + (i // 5) * 15
            self.neurons[name] = Neuron(name, nx, ny, type_)

        # 3. Создаем связи (Оригинальные + 20+)
        connections = [
            # Сенсоры -> Интернейроны
            ('ASHL', 'AIYL', 0.8), ('ASHR', 'AIYR', 0.8),
            ('AWCL', 'AIZL', 0.6), ('AWCR', 'AIZR', 0.6),
            ('AFDL', 'AIYL', 0.5), ('AFDR', 'AIYR', 0.5),
            # Интернейроны -> Моторные
            ('AIYL', 'AVAR', 0.9), ('AIYR', 'AVAL', 0.9),
            ('AIZL', 'AVBR', 0.7), ('AIZR', 'AVBL', 0.7),
            # Моторные связи
            ('AVAR', 'DB1', 1.0), ('AVAL', 'VB1', 1.0),
            ('PVCR', 'AVAR', 0.5), ('PVCL', 'AVAL', 0.5),
        ]
        
        # Добавляем связи для новых нейронов (+20 связей)
        new_connections = [
            # EN1, EN2 (Сенсоры) подключаются к интернейронам
            ('EN1', 'AIYL', 0.7), ('EN1', 'AIZL', 0.6),
            ('EN2', 'AIYR', 0.7), ('EN2', 'AIZR', 0.6),
            # EN3-EN6 (Интернейроны) мостят связи
            ('EN3', 'AVAR', 0.8), ('EN3', 'PVCR', 0.5),
            ('EN4', 'AVAL', 0.8), ('EN4', 'PVCL', 0.5),
            ('EN5', 'EN3', 0.4), ('EN6', 'EN4', 0.4),
            ('EN5', 'DB1', 0.6), ('EN6', 'VB1', 0.6),
            # EN7-EN9 (Моторные) усиливают движение
            ('EN7', 'DB1', 1.2), ('EN8', 'VB1', 1.2),
            ('EN9', 'AVAR', 0.9),
            # EN10 (Модулятор) влияет на всех
            ('EN10', 'AIYL', 0.5), ('EN10', 'AIYR', 0.5),
            ('EN10', 'AVAR', 0.5), ('EN10', 'AVAL', 0.5),
            ('EN10', 'EN3', 0.6), ('EN10', 'EN4', 0.6),
            ('EN10', 'DB1', 0.4), ('EN10', 'VB1', 0.4),
            # Обратные связи
            ('AIYL', 'EN3', 0.3), ('AIYR', 'EN4', 0.3),
        ]
        
        all_conns = connections + new_connections
        
        for pre, post, w in all_conns:
            if pre in self.neurons and post in self.neurons:
                self.synapses.append(Synapse(pre, post, w))
                
    def set_modulation(self, val):
        self.modulation = max(0.1, min(5.0, val))
        
    def step(self, sensory_input):
        """
        sensory_input: dict {neuron_name: stimulus_value}
        Запускает один шаг симуляции мозга
        """
        # 1. Сброс и ввод сенсорных данных
        for n in self.neurons.values():
            n.potential = n.bias # Базовый шум
            
        for name, value in sensory_input.items():
            if name in self.neurons:
                self.neurons[name].potential += value
                
        # 2. Распространение сигнала (упрощенный прямой проход)
        # Сортируем синапсы чтобы идти от сенсоров к моторам (очень грубо)
        # В реальной модели нужно решать дифуры, тут имитация
        
        active_signals = []
        
        # Перемешиваем для динамики, если бы было много шагов
        for syn in self.synapses:
            pre_n = self.neurons.get(syn.pre)
            post_n = self.neurons.get(syn.post)
            
            if pre_n and post_n:
                # Сигнал идет только если пресинаптический нейрон активен
                if pre_n.potential > 0.1: 
                    signal = syn.transmit(pre_n.potential, self.modulation)
                    post_n.potential += signal
                    
                    # Запоминаем сильные сигналы для визуализации
                    if abs(signal) > 0.05:
                        active_signals.append((syn.pre, syn.post, abs(signal)))
        
        # 3. Генерация спайков (выход моторов)
        motor_output = {}
        for name, n in self.neurons.items():
            if n.type == 'motor':
                if n.potential > 0.5:
                    motor_output[name] = n.potential
                    n.potential -= 0.5 # Рефрактерность
                elif n.potential < -0.5:
                    motor_output[name] = n.potential
                    n.potential += 0.5
            
        return motor_output, active_signals

class GameObject:
    def __init__(self, x, y, type_):
        self.x = x
        self.y = y
        self.type = type_
        self.radius = 8 if type_ != OBJ_WALL else 10
        self.color = self._get_color()
        
    def _get_color(self):
        if self.type == OBJ_WALL: return GRAY
        if self.type == OBJ_FOOD: return GREEN
        if self.type == OBJ_MATERIAL: return YELLOW
        if self.type == OBJ_DANGER: return RED
        return WHITE

    def draw(self, surface):
        if self.type == OBJ_WALL:
            pygame.draw.rect(surface, self.color, (self.x-10, self.y-10, 20, 20))
        elif self.type == OBJ_FOOD:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 6)
            # Блик
            pygame.draw.circle(surface, WHITE, (int(self.x)-2, int(self.y)-2), 2)
        elif self.type == OBJ_MATERIAL:
            pygame.draw.polygon(surface, self.color, [
                (self.x, self.y-8), (self.x+8, self.y), (self.x, self.y+8), (self.x-8, self.y)
            ])
        elif self.type == OBJ_DANGER:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), 8, 2)
            pygame.draw.line(surface, RED, (self.x-5, self.y-5), (self.x+5, self.y+5), 2)
            pygame.draw.line(surface, RED, (self.x+5, self.y-5), (self.x-5, self.y+5), 2)

class Worm:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.angle = 0
        self.speed = 0
        self.turn_speed = 0
        self.segments = [(x, y)] * 10 # Для отрисовки хвоста
        self.color = CYAN
        
    def update(self, motor_signals, manual_control=False, manual_dx=0, manual_dy=0):
        # Интерпретация сигналов мозга в движение
        # AVAR/AVAL - движение вперед/назад
        # DB/VB - повороты
        
        force_fwd = 0
        force_turn = 0
        
        # Читаем моторные нейроны
        if 'AVAR' in motor_signals: force_fwd += motor_signals['AVAR']
        if 'AVAL' in motor_signals: force_fwd += motor_signals['AVAL']
        if 'DB1' in motor_signals: force_turn += motor_signals['DB1']
        if 'VB1' in motor_signals: force_turn -= motor_signals['VB1']
        
        # Если ручное управление - перехватываем
        if manual_control:
            self.x += manual_dx * 3
            self.y += manual_dy * 3
            # Вычисляем угол для отрисовки
            if manual_dx != 0 or manual_dy != 0:
                self.angle = math.atan2(manual_dy, manual_dx)
        else:
            # Автономное движение
            base_speed = 1.5
            turn_rate = 0.05
            
            # Дрейф (случайное блуждание)
            noise = random.uniform(-0.1, 0.1)
            
            speed = base_speed + (force_fwd * 0.5)
            if speed < 0: speed = 0
            
            turn = noise + (force_turn * turn_rate)
            
            self.angle += turn
            self.x += math.cos(self.angle) * speed
            self.y += math.sin(self.angle) * speed
            
        # Границы мира
        self.x = max(20, min(WIDTH - NEURAL_PANEL_WIDTH - 20, self.x))
        self.y = max(20, min(HEIGHT - 20, self.y))
        
        # Обновление сегментов тела
        self.segments.insert(0, (self.x, self.y))
        if len(self.segments) > 15:
            self.segments.pop()

    def draw(self, surface):
        # Рисуем тело
        for i, (sx, sy) in enumerate(self.segments):
            size = max(2, WORM_SIZE - i)
            alpha = 255 - (i * 15)
            col = (min(255, self.color[0]), min(255, self.color[1]), min(255, self.color[2]))
            pygame.draw.circle(surface, col, (int(sx), int(sy)), int(size))
            
        # Голова
        hx = self.x + math.cos(self.angle) * 10
        hy = self.y + math.sin(self.angle) * 10
        pygame.draw.circle(surface, WHITE, (int(hx), int(hy)), 4)

class Simulation:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("C. elegans Neuro-Robot Simulator (+10 Neurons)")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14)
        self.big_font = pygame.font.SysFont("Arial", 20, bold=True)
        
        self.brain = WormBrain()
        self.worm = Worm(WIDTH//2, HEIGHT//2)
        self.objects = []
        
        self.selected_obj = OBJ_FOOD
        self.last_active_signals = []
        self.total_spikes = 0
        self.sim_time = 0.0
        self.paused = False
        
        # Для создания объектов мышью
        self.mouse_held = False
        
    def handle_events(self):
        dx, dy = 0, 0
        manual_mode = False
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                if event.key == pygame.K_r:
                    self.worm = Worm(WIDTH//2, HEIGHT//2)
                    self.objects = []
                    self.brain.set_modulation(1.0)
                if event.key == pygame.K_m:
                    curr = self.brain.modulation
                    if curr < 1.0: self.brain.set_modulation(curr + 0.5)
                    else: self.brain.set_modulation(0.5)
                    
                # Выбор объекта
                if event.key == pygame.K_1: self.selected_obj = OBJ_WALL
                if event.key == pygame.K_2: self.selected_obj = OBJ_FOOD
                if event.key == pygame.K_3: self.selected_obj = OBJ_MATERIAL
                if event.key == pygame.K_4: self.selected_obj = OBJ_DANGER
                
            # Управление мышью (строительство)
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if mx > WIDTH - NEURAL_PANEL_WIDTH: continue # Не строить на панели
                
                if event.button == 1: # ЛКМ - создать
                    self.objects.append(GameObject(mx, my, self.selected_obj))
                if event.button == 3: # ПКМ - удалить (рядом с кликом)
                    self.objects = [o for o in self.objects if math.hypot(o.x-mx, o.y-my) > 20]
                    
            # Клавиатура для движения (перехват управления)
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                pass # Обработаем ниже через get_pressed для плавности

        # Плавное движение стрелками
        keys = pygame.key.get_pressed()
        if any([keys[pygame.K_LEFT], keys[pygame.K_RIGHT], keys[pygame.K_UP], keys[pygame.K_DOWN]]):
            manual_mode = True
            if keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_RIGHT]: dx += 1
            if keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_DOWN]: dy += 1
            
        return True, manual_mode, dx, dy

    def get_sensory_input(self):
        """Сканирует окружение и создает входные сигналы для сенсоров"""
        inputs = {}
        
        # Дистанция до ближайших объектов
        dist_food = 1000
        dist_danger = 1000
        dist_wall = 1000
        
        for obj in self.objects:
            d = math.hypot(obj.x - self.worm.x, obj.y - self.worm.y)
            if d < 150: # Радиус чувствительности
                if obj.type == OBJ_FOOD:
                    if d < dist_food: dist_food = d
                elif obj.type == OBJ_DANGER:
                    if d < dist_danger: dist_danger = d
                elif obj.type == OBJ_WALL:
                    if d < dist_wall: dist_wall = d
                    
        # Преобразуем дистанцию в силу сигнала (чем ближе, тем сильнее)
        # Сенсоры еды (AWC, AFD)
        if dist_food < 150:
            stim = (150 - dist_food) / 150.0
            inputs['AWCL'] = stim
            inputs['AWCR'] = stim
            inputs['AFDL'] = stim * 0.8
            
        # Сенсоры опасности (ASH)
        if dist_danger < 150:
            stim = (150 - dist_danger) / 150.0
            inputs['ASHL'] = stim
            inputs['ASHR'] = stim
            
        # Сенсоры касания/стен (ALM, touch - используем ADL как прокси)
        if dist_wall < 100:
            stim = (100 - dist_wall) / 100.0
            inputs['ADLL'] = stim
            inputs['ADLR'] = stim
            
        # Добавляем шум от новых сенсоров EN1, EN2 (доп. восприятие)
        inputs['EN1'] = random.uniform(0, 0.1) 
        inputs['EN2'] = random.uniform(0, 0.1)
        
        return inputs

    def draw_neural_panel(self, active_signals):
        panel_x = WIDTH - NEURAL_PANEL_WIDTH
        # Фон
        pygame.draw.rect(self.screen, (20, 20, 30), (panel_x, 0, NEURAL_PANEL_WIDTH, HEIGHT))
        pygame.draw.line(self.screen, WHITE, (panel_x, 0), (panel_x, HEIGHT), 2)
        
        # Заголовок
        title = self.big_font.render("NEURAL ACTIVITY", True, CYAN)
        self.screen.blit(title, (panel_x + 10, 10))
        
        info_mod = self.font.render(f"Modulation: {self.brain.modulation:.1f}x", True, WHITE)
        self.screen.blit(info_mod, (panel_x + 10, 40))
        
        info_spikes = self.font.render(f"Total Spikes: {self.total_spikes}", True, WHITE)
        self.screen.blit(info_spikes, (panel_x + 10, 60))
        
        # Визуализация сети
        # Рисуем узлы
        scale_x = NEURAL_PANEL_WIDTH - 40
        scale_y = HEIGHT - 100
        
        for name, neuron in self.brain.neurons.items():
            nx = panel_x + 20 + (neuron.x / 100.0) * scale_x
            ny = 100 + (neuron.y / 100.0) * scale_y
            
            # Цвет типа нейрона
            color = GRAY
            if neuron.type == 'sensor': color = GREEN
            elif neuron.type == 'motor': color = BLUE
            elif neuron.type == 'modulator': color = ORANGE
            
            # Пульсация от активности
            radius = 4
            if abs(neuron.potential) > 0.2:
                radius = 6 + abs(neuron.potential) * 5
                color = WHITE # Перегрузка белым
            
            pygame.draw.circle(self.screen, color, (int(nx), int(ny)), int(radius))
            
            # Имя (только для важных или новых)
            if name.startswith('EN') or neuron.type == 'modulator':
                txt = self.font.render(name, True, color)
                self.screen.blit(txt, (nx+10, ny-10))

        # Рисуем АКТИВНЫЕ связи (красные линии/точки)
        for pre, post, strength in active_signals:
            if pre in self.brain.neurons and post in self.brain.neurons:
                n1 = self.brain.neurons[pre]
                n2 = self.brain.neurons[post]
                
                x1 = panel_x + 20 + (n1.x / 100.0) * scale_x
                y1 = 100 + (n1.y / 100.0) * scale_y
                x2 = panel_x + 20 + (n2.x / 100.0) * scale_x
                y2 = 100 + (n2.y / 100.0) * scale_y
                
                # Яркость зависит от силы
                alpha_val = min(255, int(strength * 400))
                color_sig = (255, alpha_val, alpha_val) # Красный канал макс, зеленый/синий зависят от силы
                
                # Рисуем линию
                pygame.draw.line(self.screen, color_sig, (x1, y1), (x2, y2), int(1 + strength*3))
                
                # Рисуем "бегущую точку" посередине
                mx = (x1 + x2) / 2
                my = (y1 + y2) / 2
                pygame.draw.circle(self.screen, (255, 255, 255), (int(mx), int(my)), int(3 + strength*4))

        # Список последних активных сигналов (текстом)
        y_start = HEIGHT - 200
        lbl = self.font.render("Top Active Signals:", True, YELLOW)
        self.screen.blit(lbl, (panel_x + 10, y_start))
        
        # Сортируем по силе
        active_signals.sort(key=lambda x: x[2], reverse=True)
        for i, (pre, post, str_val) in enumerate(active_signals[:6]):
            txt = f"{pre}->{post}: {str_val:.2f}"
            color = (255, int(255 * (1-str_val)), int(255 * (1-str_val)))
            ren = self.font.render(txt, True, color)
            self.screen.blit(ren, (panel_x + 10, y_start + 20 + i*20))

    def run(self):
        running = True
        while running:
            try:
                res = self.handle_events()
                if isinstance(res, tuple):
                    running, manual_mode, dx, dy = res
                else:
                    running = res
                    manual_mode, dx, dy = False, 0, 0
                    
                if not running: break
                
                if not self.paused:
                    # 1. Получаем сенсорные данные
                    sensory = self.get_sensory_input()
                    
                    # 2. Шаг мозга
                    motor_out, active_sig = self.brain.step(sensory)
                    
                    # Подсчет спайков
                    spikes_count = sum(1 for v in motor_out.values() if abs(v) > 0.5)
                    self.total_spikes += spikes_count
                    
                    self.last_active_signals = active_sig
                    
                    # 3. Движение червя
                    self.worm.update(motor_out, manual_mode, dx, dy)
                    
                    # 4. Коллизии с объектами
                    for obj in self.objects:
                        dist = math.hypot(obj.x - self.worm.x, obj.y - self.worm.y)
                        if dist < 15:
                            if obj.type == OBJ_FOOD:
                                # Съел еду - бонус энергии (увеличиваем модуляцию временно)
                                self.brain.set_modulation(self.brain.modulation + 0.1)
                                self.objects.remove(obj)
                            elif obj.type == OBJ_WALL:
                                # Отталкивание
                                angle = math.atan2(self.worm.y - obj.y, self.worm.x - obj.x)
                                self.worm.x += math.cos(angle) * 5
                                self.worm.y += math.sin(angle) * 5
                                # Сигнал боли/касания
                                sensory['ASHL'] = 1.0
                                sensory['ASHR'] = 1.0

                    self.sim_time += 1/FPS

                # --- ОТРИСОВКА ---
                self.screen.fill(BLACK)
                
                # Сетка фона
                for x in range(0, WIDTH - NEURAL_PANEL_WIDTH, 50):
                    pygame.draw.line(self.screen, (30, 30, 30), (x, 0), (x, HEIGHT))
                for y in range(0, HEIGHT, 50):
                    pygame.draw.line(self.screen, (30, 30, 30), (0, y), (WIDTH - NEURAL_PANEL_WIDTH, y))
                
                # Объекты
                for obj in self.objects:
                    obj.draw(self.screen)
                    
                # Червь
                self.worm.draw(self.screen)
                
                # Панель мозга
                self.draw_neural_panel(self.last_active_signals)
                
                # UI подсказки
                ui_txt = [
                    f"FPS: {int(self.clock.get_fps())}",
                    f"Objects: {len(self.objects)}",
                    "Controls:",
                    "Arrows: Move Robot",
                    "1-4: Select Object",
                    "L-Click: Place, R-Click: Remove",
                    "M: Modulation, Space: Pause",
                    "R: Reset"
                ]
                for i, line in enumerate(ui_txt):
                    txt = self.font.render(line, True, WHITE)
                    self.screen.blit(txt, (10, 10 + i*20))
                    
                # Индикатор выбранного объекта
                sel_name = ["None", "Wall", "Food", "Material", "Danger"][self.selected_obj]
                sel_txt = self.big_font.render(f"Selected: {sel_name}", True, YELLOW)
                self.screen.blit(sel_txt, (10, HEIGHT - 40))
                
                pygame.display.flip()
                self.clock.tick(FPS)
                
            except Exception as e:
                print(f"Error in loop: {e}")
                # Не выходим, пробуем продолжить
                continue

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    print("Starting C. elegans Neuro-Robot Simulator...")
    print("Window should appear shortly.")
    try:
        sim = Simulation()
        sim.run()
    except Exception as e:
        print(f"Fatal Error: {e}")
        print("Make sure you have a display connected and pygame installed.")
        print("Install: pip install pygame numpy")
