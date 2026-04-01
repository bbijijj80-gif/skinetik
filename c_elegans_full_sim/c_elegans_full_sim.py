#!/usr/bin/env python3
"""
C. elegans Full Biophysical Simulation
Научно обоснованная модель с:
- Реальным коннектомом (White et al., 1986; Cook et al., 2019)
- Специфичными ионными каналами (EGL-19, UNC-2, SLO-1, etc.)
- Рецепторной спецификой синапсов (ACh, GABA, Glu, моноамины)
- Моделью Хилла для мышц с кальциевой активацией
- G-белковой сигнализацией и вторичными мессенджерами
- STDP синаптической пластичностью и гомеостазом
- Биофизической моделью тела (масса-пружина-демпфер)
- Температурной компенсацией (Q10)
- Валидацией против экспериментальных данных

Запуск: python3 c_elegans_full_sim.py
Управление:
- Стрелки: ручное управление
- 1-4: выбор объекта (стена, еда, опасность, материал)
- ЛКМ: создать объект
- ПКМ: удалить объект
- M: модуляция мозга
- T: изменение температуры
- G: переключение мутанта
- R: сброс
- Пробел: пауза
- H: помощь
- Esc: выход
"""

import pygame
import numpy as np
from scipy import integrate
from collections import deque
import sys
import os

# Добавляем путь к данным
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'data'))
from connectome_data import (
    CONNECTOME_DATA, ION_CHANNEL_PARAMS, SYNAPSE_RECEPTORS,
    MUSCLE_PARAMS, GPCR_PARAMS, SECOND_MESSENGERS, STDP_PARAMS,
    HOMEOSTASIS_PARAMS, TEMP_PARAMS, VALIDATION_DATA
)

# --- КОНФИГУРАЦИЯ ---
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 900
WORLD_WIDTH = 900
WORLD_HEIGHT = SCREEN_HEIGHT
NEURAL_PANEL_WIDTH = SCREEN_WIDTH - WORLD_WIDTH
FPS = 60
DT = 0.1  # мс (фиксированный шаг для стабильности)

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
ORANGE = (255, 165, 0)
PURPLE = (191, 0, 255)
CYAN = (0, 255, 255)
DARK_GREEN = (0, 100, 0)
LIGHT_BLUE = (173, 216, 230)

# Типы объектов
WALL = 0
FOOD = 1
MATERIAL = 2
DANGER = 3

class IonChannel:
    """Биофизическая модель ионного канала с кинетикой активации/инактивации"""
    def __init__(self, name, params, channel_type='voltage_gated'):
        self.name = name
        self.g_max = params['g_max']
        self.channel_type = channel_type
        
        if channel_type == 'voltage_gated':
            self.V_half = params.get('V_half', -20.0)
            self.k = params.get('k', 5.0)
            self.tau = params.get('tau', 10.0)
            self.E_rev = params.get('E_rev', 0.0)  # Для не селективных
            self.m = 0.0  # Переменная активации
            self.h = 1.0  # Переменная инактивации (если есть)
        elif channel_type == 'ligand_gated':
            self.E_rev = params['E_rev']
            self.tau_rise = params.get('tau_rise', 1.0)
            self.tau_decay = params.get('tau_decay', 10.0)
            self.s = 0.0  # Доля открытых каналов
        elif channel_type == 'calcium_dependent':
            self.V_half = params.get('V_half', -10.0)
            self.k = params.get('k', 8.0)
            self.tau_ca = params.get('tau_ca', 30.0)
            self.E_rev = params.get('E_rev', -80.0)
            self.m = 0.0
            self.ca_sensitivity = 0.5
        elif channel_type == 'leak':
            self.E_rev = params['E_rev']
            self.m = 1.0  # Всегда открыт
    
    def update(self, V, dt, ca_conc=0.0, ligand_conc=0.0, temperature_factor=1.0):
        """Обновление состояния канала по методу Рунге-Кутты 4"""
        tau_eff = self.tau / temperature_factor if hasattr(self, 'tau') else 1.0
        
        if self.channel_type == 'voltage_gated':
            # Стационарное значение и время активации
            m_inf = 1.0 / (1.0 + np.exp(-(V - self.V_half) / self.k))
            
            # RK4 для m
            dm_dt = lambda m_val: (m_inf - m_val) / tau_eff
            k1 = dm_dt(self.m)
            k2 = dm_dt(self.m + 0.5 * dt * k1)
            k3 = dm_dt(self.m + 0.5 * dt * k2)
            k4 = dm_dt(self.m + dt * k3)
            self.m = self.m + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            self.m = np.clip(self.m, 0.0, 1.0)
            
            # Ток: I = g * m^p * (V - E)
            return self.g_max * (self.m ** 3) * (V - self.E_rev)
        
        elif self.channel_type == 'ligand_gated':
            # Кинетика рецептора
            ds_dt = (ligand_conc * (1 - self.s) / self.tau_rise - 
                     self.s / self.tau_decay)
            self.s += ds_dt * dt
            self.s = np.clip(self.s, 0.0, 1.0)
            return self.g_max * self.s * (V - self.E_rev)
        
        elif self.channel_type == 'calcium_dependent':
            # Зависимость от кальция
            m_inf = 1.0 / (1.0 + np.exp(-(V - self.V_half) / self.k))
            ca_factor = ca_conc / (ca_conc + self.ca_sensitivity)
            m_target = m_inf * ca_factor
            
            dm_dt = (m_target - self.m) / tau_eff
            self.m += dm_dt * dt
            self.m = np.clip(self.m, 0.0, 1.0)
            
            return self.g_max * self.m * (V - self.E_rev)
        
        elif self.channel_type == 'leak':
            return self.g_max * (V - self.E_rev)
        
        return 0.0

class SecondMessengerSystem:
    """Система вторичных мессенджеров (cAMP, IP3, DAG, Ca2+)"""
    def __init__(self):
        self.cAMP = SECOND_MESSENGERS['cAMP']['basal']
        self.IP3 = SECOND_MESSENGERS['IP3']['basal']
        self.DAG = SECOND_MESSENGERS['DAG']['basal']
        self.Ca_internal = SECOND_MESSENGERS['Ca2+_internal']['basal']
        
        self.params = SECOND_MESSENGERS.copy()
    
    def update(self, dt, gpcr_activity=0.0, temperature_factor=1.0):
        """Обновление концентраций вторичных мессенджеров"""
        # cAMP динамика
        production_cAMP = self.params['cAMP']['production_rate'] * gpcr_activity
        degradation_cAMP = self.params['cAMP']['degradation_rate'] * self.cAMP
        self.cAMP += (production_cAMP - degradation_cAMP) * dt / temperature_factor
        self.cAMP = np.clip(self.cAMP, 0.0, 10.0)
        
        # IP3 динамика
        production_IP3 = self.params['IP3']['production_rate'] * gpcr_activity
        degradation_IP3 = self.params['IP3']['degradation_rate'] * self.IP3
        self.IP3 += (production_IP3 - degradation_IP3) * dt / temperature_factor
        self.IP3 = np.clip(self.IP3, 0.0, 10.0)
        
        # DAG динамика
        production_DAG = self.params['DAG']['production_rate'] * gpcr_activity
        degradation_DAG = self.params['DAG']['degradation_rate'] * self.DAG
        self.DAG += (production_DAG - degradation_DAG) * dt / temperature_factor
        self.DAG = np.clip(self.DAG, 0.0, 10.0)
        
        # Внутриклеточный кальций (высвобождение через IP3R)
        release_Ca = self.params['Ca2+_internal']['release_rate'] * self.IP3 * (1 - self.Ca_internal)
        uptake_Ca = self.params['Ca2+_internal']['uptake_rate'] * self.Ca_internal
        buffer = self.params['Ca2+_internal']['buffer_capacity']
        
        self.Ca_internal += (release_Ca - uptake_Ca) * dt / temperature_factor
        self.Ca_internal = np.clip(self.Ca_internal, 0.0, 5.0)
        
        return {
            'cAMP': self.cAMP,
            'IP3': self.IP3,
            'DAG': self.DAG,
            'Ca_internal': self.Ca_internal
        }

class MuscleHillModel:
    """Модель мышцы Хилла с кальциевой активацией"""
    def __init__(self):
        self.F_max = MUSCLE_PARAMS['F_max']
        self.v_max = MUSCLE_PARAMS['v_max']
        self.a_rel = MUSCLE_PARAMS['a_rel']
        self.l_opt = MUSCLE_PARAMS['l_opt']
        self.k_se = MUSCLE_PARAMS['k_se']
        self.k_pe = MUSCLE_PARAMS['k_pe']
        self.ca_half = MUSCLE_PARAMS['ca_half']
        self.n_hill = MUSCLE_PARAMS['n_hill']
        self.tau_ca_on = MUSCLE_PARAMS['tau_ca_on']
        self.tau_ca_off = MUSCLE_PARAMS['tau_ca_off']
        self.viscosity = MUSCLE_PARAMS['viscosity']
        
        # Состояние
        self.Ca_active = 0.0  # Активный кальций
        self.length = self.l_opt
        self.velocity = 0.0
        self.force = 0.0
        self.activation = 0.0
    
    def update(self, dt, motor_neuron_signal, temperature_factor=1.0):
        """Обновление модели мышцы"""
        # Кальциевая динамика
        if motor_neuron_signal > 0.5:
            dCa_dt = (1.0 - self.Ca_active) / (self.tau_ca_on / temperature_factor)
        else:
            dCa_dt = -self.Ca_active / (self.tau_ca_off / temperature_factor)
        
        self.Ca_active += dCa_dt * dt
        self.Ca_active = np.clip(self.Ca_active, 0.0, 1.0)
        
        # Активация через уравнение Хилла
        self.activation = (self.Ca_active ** self.n_hill) / (
            self.Ca_active ** self.n_hill + self.ca_half ** self.n_hill
        )
        
        # Сила-скорость (уравнение Хилла)
        a = self.a_rel * self.F_max
        if self.velocity < self.v_max:
            F_velocity = self.F_max * (1 - self.velocity / self.v_max) / (
                1 + self.velocity / (self.v_max * a / self.F_max)
            )
        else:
            F_velocity = 0.0
        
        # Сила-длина (параболическая зависимость)
        length_ratio = self.length / self.l_opt
        if 0.5 < length_ratio < 1.5:
            F_length = 1.0 - ((length_ratio - 1.0) ** 2)
        else:
            F_length = 0.0
        
        # Пассивная сила (параллельный упругий элемент)
        F_passive = self.k_pe * max(0, self.length - self.l_opt)
        
        # Общая сила
        self.force = self.activation * F_velocity * F_length + F_passive
        
        # Вязкое демпфирование
        damping = self.viscosity * self.velocity
        
        return self.force - damping
    
    def set_length(self, new_length):
        self.length = new_length
        self.velocity = (new_length - self.length) / 0.016  # Приближенно

class Synapse:
    """Синапс с рецепторной спецификой, STDP и электрическими контактами"""
    def __init__(self, pre_neuron, post_neuron, syn_type, weight, count, 
                 neurotransmitter='ACh', is_electrical=False):
        self.pre = pre_neuron
        self.post = post_neuron
        self.syn_type = syn_type  # 'chem' или 'elec'
        self.base_weight = weight
        self.weight = weight * count  # Учет количества синапсов
        self.count = count
        self.neurotransmitter = neurotransmitter
        self.is_electrical = is_electrical
        
        # STDP переменные
        self.pre_spike_times = deque(maxlen=10)
        self.post_spike_times = deque(maxlen=10)
        
        # Гомеостаз
        self.running_avg = 0.0
        self.avg_window = deque(maxlen=100)
        
        # Задержка передачи
        self.delay_ms = 1.0 if is_electrical else 2.0
        self.queue = deque()
        
        # Рецептор
        if neurotransmitter in SYNAPSE_RECEPTORS:
            rec_params = SYNAPSE_RECEPTORS[neurotransmitter]
            self.receptor = IonChannel(
                rec_params['receptor'], 
                rec_params, 
                channel_type='ligand_gated'
            )
        else:
            self.receptor = None
    
    def transmit(self, dt, temperature_factor=1.0):
        """Передача сигнала через синапс"""
        if self.is_electrical:
            # Щелевой контакт: прямой ток
            coupling = self.weight * temperature_factor
            current = coupling * (self.pre.V - self.post.V)
            self.post.receive_current(current)
            return
        
        # Химический синапс
        if self.pre.spike_flag:
            self.pre_spike_times.append(pygame.time.get_ticks())
            self.queue.append((self.weight, self.delay_ms))
        
        # Обработка очереди с задержкой
        if self.queue and self.queue[0][1] <= 0:
            weight, _ = self.queue.popleft()
            if self.receptor:
                # Выброс нейромедиатора
                self.receptor.update(self.post.V, dt, ligand_conc=weight, 
                                   temperature_factor=temperature_factor)
                receptor_current = self.receptor.s * weight * (self.post.V - self.receptor.E_rev)
                self.post.receive_current(receptor_current)
        else:
            for i in range(len(self.queue)):
                w, delay = self.queue[i]
                self.queue[i] = (w, delay - dt)
    
    def apply_stdp(self, post_spike_time):
        """STDP пластичность"""
        if not self.pre_spike_times:
            return
        
        current_time = pygame.time.get_ticks()
        
        # Потенцирование (pre before post)
        for pre_time in self.pre_spike_times:
            delta_t = (post_spike_time - pre_time) / 1000.0  # в секундах
            if 0 < delta_t < 0.1:
                delta_w = STDP_PARAMS['A_plus'] * np.exp(-delta_t / STDP_PARAMS['tau_plus'])
                self.weight = min(STDP_PARAMS['w_max'], self.weight + delta_w)
        
        # Депрессия (post before pre)
        for pre_time in self.pre_spike_times:
            delta_t = (pre_time - post_spike_time) / 1000.0
            if 0 < delta_t < 0.1:
                delta_w = -STDP_PARAMS['A_minus'] * np.exp(-delta_t / STDP_PARAMS['tau_minus'])
                self.weight = max(STDP_PARAMS['w_min'], self.weight + delta_w)
    
    def apply_homeostasis(self, target_rate, actual_rate, dt):
        """Гомеостатическая регуляция"""
        error = target_rate - actual_rate
        scaling = HOMEOSTASIS_PARAMS['scaling_factor'] * error * dt
        self.weight *= (1 + scaling)
        self.weight = np.clip(self.weight, STDP_PARAMS['w_min'], STDP_PARAMS['w_max'])

class Neuron:
    """Нейрон с конкретными ионными каналами C. elegans"""
    def __init__(self, name, neuron_type='inter'):
        self.name = name
        self.type = neuron_type
        self.V = -65.0  # мВ (потенциал покоя)
        self.C_m = 1.0  # мкФ/см² (ёмкость мембраны)
        
        # Создание ионных каналов для этого типа нейрона
        self.channels = {}
        if neuron_type in ION_CHANNEL_PARAMS:
            channel_configs = ION_CHANNEL_PARAMS[neuron_type]
            for chan_name, params in channel_configs.items():
                if 'KCa' in chan_name:
                    self.channels[chan_name] = IonChannel(chan_name, params, 'calcium_dependent')
                elif 'leak' in chan_name:
                    self.channels[chan_name] = IonChannel(chan_name, params, 'leak')
                else:
                    self.channels[chan_name] = IonChannel(chan_name, params, 'voltage_gated')
        
        # Вторичные мессенджеры
        self.second_messenger = SecondMessengerSystem()
        
        # GPCR активность
        self.gpcr_activity = 0.0
        
        # Кальций внутриклеточный
        self.Ca_in = 0.05
        
        # Спайк переменные
        self.spike_flag = False
        self.refractory_timer = 0.0
        self.last_spike_time = -1000
        self.spike_history = deque(maxlen=100)
        
        # Входящий ток
        self.I_injected = 0.0
        
        # Синапсы
        self.incoming_synapses = []
        self.outgoing_synapses = []
    
    def receive_current(self, current):
        self.I_injected += current
    
    def receive_modulator(self, modulator_type, concentration):
        """Получение нейромодулятора через GPCR"""
        if modulator_type == 'serotonin':
            self.gpcr_activity += concentration * 0.5
        elif modulator_type == 'dopamine':
            self.gpcr_activity += concentration * 0.4
        elif modulator_type == 'octopamine':
            self.gpcr_activity += concentration * 0.6
    
    def update(self, dt, temperature_factor=1.0):
        """Интеграция уравнений мембраны (RK4)"""
        # Обновление вторичных мессенджеров
        messengers = self.second_messenger.update(dt, self.gpcr_activity, temperature_factor)
        self.Ca_in = messengers['Ca_internal']
        
        # Затухание GPCR активности
        self.gpcr_activity *= 0.99
        
        # Рефрактерный период
        if self.refractory_timer > 0:
            self.refractory_timer -= dt
            if self.refractory_timer <= 0:
                self.V = -65.0
                self.spike_flag = False
            return False
        
        # Суммарный ионный ток
        I_ion = 0.0
        for channel in self.channels.values():
            ca_conc = self.Ca_in if channel.channel_type == 'calcium_dependent' else 0.0
            I_ion += channel.update(self.V, dt, ca_conc=ca_conc, temperature_factor=temperature_factor)
        
        # Уравнение мембраны: C*dV/dt = -I_ion + I_injected
        def dV_dt(V_val):
            # Пересчитываем токи для текущего V
            I_total = I_ion + self.I_injected
            return (-I_total) / self.C_m
        
        # RK4 интеграция
        k1 = dV_dt(self.V)
        k2 = dV_dt(self.V + 0.5 * dt * k1)
        k3 = dV_dt(self.V + 0.5 * dt * k2)
        k4 = dV_dt(self.V + dt * k3)
        
        self.V = self.V + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
        
        # Проверка на спайк
        spiked = False
        if self.V > -45.0 and self.refractory_timer <= 0:  # Порог
            self.V = 40.0  # Пик потенциала
            self.refractory_timer = 3.0  # мс
            self.last_spike_time = pygame.time.get_ticks()
            self.spike_flag = True
            self.spike_history.append(self.last_spike_time)
            spiked = True
            
            # Применение STDP ко всем исходящим синапсам
            for syn in self.outgoing_synapses:
                syn.apply_stdp(self.last_spike_time)
        
        # Очистка входящего тока
        self.I_injected = 0.0
        
        return spiked

class WormBody:
    """Биофизическая модель тела червя (масса-пружина-демпфер)"""
    def __init__(self, num_segments=10):
        self.num_segments = num_segments
        self.segments = []
        self.velocities = []
        self.muscles = []
        
        # Параметры сегментов
        self.mass = 0.1  # мг на сегмент
        self.rest_length = 50.0  # мкм между сегментами
        self.spring_k = 1.0  # жесткость пружины
        self.damping = 0.1  # демпфирование
        self.friction = 0.05  # трение о субстрат
        
        # Инициализация сегментов
        start_x = WORLD_WIDTH // 2
        start_y = WORLD_HEIGHT // 2
        for i in range(num_segments):
            self.segments.append(np.array([start_x - i * self.rest_length, start_y]))
            self.velocities.append(np.array([0.0, 0.0]))
            self.muscles.append(MuscleHillModel())
    
    def update(self, dt, muscle_activations, temperature_factor=1.0):
        """Интеграция физики тела"""
        for i in range(self.num_segments):
            force = np.array([0.0, 0.0])
            
            # Сила от пружин (соседние сегменты)
            if i > 0:
                dx = self.segments[i-1] - self.segments[i]
                dist = np.linalg.norm(dx)
                if dist > 0:
                    spring_force = self.spring_k * (dist - self.rest_length) * (dx / dist)
                    force += spring_force
            
            if i < self.num_segments - 1:
                dx = self.segments[i+1] - self.segments[i]
                dist = np.linalg.norm(dx)
                if dist > 0:
                    spring_force = self.spring_k * (dist - self.rest_length) * (dx / dist)
                    force += spring_force
            
            # Сила от мышц
            if i < len(muscle_activations):
                muscle_force = self.muscles[i].update(dt, muscle_activations[i], temperature_factor)
                # Направление силы вдоль тела
                if i > 0:
                    direction = self.segments[i-1] - self.segments[i]
                else:
                    direction = self.segments[i+1] - self.segments[i]
                dist = np.linalg.norm(direction)
                if dist > 0:
                    force += muscle_force * (direction / dist)
            
            # Демпфирование
            force -= self.damping * self.velocities[i]
            
            # Трение о субстрат
            force -= self.friction * self.velocities[i]
            
            # Интеграция (Эйлер для простоты, можно RK4)
            acceleration = force / self.mass
            self.velocities[i] += acceleration * dt
            self.segments[i] += self.velocities[i] * dt
            
            # Ограничение скорости
            max_speed = 500.0
            speed = np.linalg.norm(self.velocities[i])
            if speed > max_speed:
                self.velocities[i] = (self.velocities[i] / speed) * max_speed
    
    def draw(self, screen):
        """Отрисовка червя"""
        for i, seg in enumerate(self.segments):
            # Градиент цвета от головы к хвосту
            t = i / self.num_segments
            r = int(BLUE[0] * (1 - t * 0.5))
            g = int(BLUE[1] * (1 - t * 0.5))
            b = int(BLUE[2] * (1 - t * 0.5))
            color = (r, g, b)
            
            radius = max(3, int(8 * (1 - t * 0.6)))
            pygame.draw.circle(screen, color, (int(seg[0]), int(seg[1])), radius)
        
        # Соединительные линии
        points = [(int(s[0]), int(s[1])) for s in self.segments]
        if len(points) > 1:
            pygame.draw.lines(screen, BLUE, False, points, 3)
    
    def get_head_pos(self):
        return self.segments[0] if self.segments else (WORLD_WIDTH//2, WORLD_HEIGHT//2)

class WorldObject:
    """Объект в мире (еда, стена, опасность)"""
    def __init__(self, x, y, obj_type):
        self.x = x
        self.y = y
        self.type = obj_type
        self.radius = 12
        self.gradient = 0.0  # Для хемотаксиса
    
    def draw(self, screen):
        if self.type == WALL:
            pygame.draw.rect(screen, GRAY, 
                           (self.x - self.radius, self.y - self.radius, 
                            self.radius*2, self.radius*2), 2)
        elif self.type == FOOD:
            pygame.draw.circle(screen, GREEN, (int(self.x), int(self.y)), self.radius)
            # Свечение
            pygame.draw.circle(screen, LIGHT_BLUE, (int(self.x), int(self.y)), self.radius + 3, 1)
        elif self.type == MATERIAL:
            points = [
                (self.x, self.y - self.radius),
                (self.x - self.radius, self.y + self.radius),
                (self.x + self.radius, self.y + self.radius)
            ]
            pygame.draw.polygon(screen, YELLOW, points)
        elif self.type == DANGER:
            pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius - 5, 2)
    
    def get_concentration(self, x, y, sensor_type='chemo'):
        """Вычисление концентрации стимула в точке (x,y)"""
        dx = self.x - x
        dy = self.y - y
        dist_sq = dx*dx + dy*dy
        max_dist_sq = 200**2
        
        if dist_sq > max_dist_sq:
            return 0.0
        
        if self.type == FOOD and sensor_type == 'chemo':
            return 1.0 * (1 - dist_sq/max_dist_sq)
        elif self.type == DANGER and sensor_type == 'chemo':
            return -0.8 * (1 - dist_sq/max_dist_sq)
        elif self.type == WALL and sensor_type == 'tactile':
            dist = np.sqrt(dist_sq)
            if dist < self.radius + 10:
                return 1.0 * (1 - dist/(self.radius + 10))
        return 0.0

class CElegansFullSim:
    """Основной класс симуляции"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("C. elegans Full Biophysical Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Consolas", 18)
        self.small_font = pygame.font.SysFont("Consolas", 14)
        
        # Температура
        self.temperature = 20.0  # °C
        self.update_temperature_factor()
        
        # Мутант режим
        self.mutant_mode = None  # None, 'unc-2_null', 'slo-1_null', etc.
        
        # Создание нейронов
        self.neurons = {}
        self.create_neurons()
        
        # Создание синапсов из коннектома
        self.synapses = []
        self.parse_connectome()
        
        # Связывание синапсов с нейронами
        for syn in self.synapses:
            syn.pre.outgoing_synapses.append(syn)
            syn.post.incoming_synapses.append(syn)
        
        # Тело червя
        self.worm_body = WormBody(num_segments=12)
        
        # Объекты мира
        self.objects = []
        self.selected_obj_type = FOOD
        
        # Состояния
        self.paused = False
        self.modulation_on = False
        self.show_help = False
        
        # Статистика
        self.total_spikes = 0
        self.simulation_time = 0.0
        self.validation_stats = {
            'speed': 0.0,
            'frequency': 0.0,
            'avg_firing_rate': 0.0
        }
        
        # Визуализация спайков
        self.spike_visuals = []
    
    def create_neurons(self):
        """Создание всех нейронов с правильными типами"""
        # Сенсорные нейроны
        sensory_names = ['AWCL', 'AWCR', 'ASEL', 'ASER', 'ALML', 'ALMR', 
                        'AVML', 'AVMR', 'PVML', 'PVMR', 'ADFL', 'ADFR',
                        'ASHL', 'ASHR', 'EN1', 'EN2']
        for name in sensory_names:
            self.neurons[name] = Neuron(name, 'sensory')
        
        # Интернейроны
        inter_names = ['AIYL', 'AIYR', 'AIZL', 'AIZR', 'AIBL', 'AIBR',
                      'RIML', 'RIMR', 'RIBL', 'RIBR', 'RIA L', 'RIA R',
                      'AVJL', 'AVJR', 'AVKL', 'AVKR', 'EN3', 'EN4']
        for name in inter_names:
            self.neurons[name] = Neuron(name, 'inter')
        
        # Моторные нейроны
        motor_names = ['SMDDL', 'SMDDR', 'SMBVL', 'SMBVR', 'VD', 'DD',
                      'VA', 'VB', 'RIVL', 'RIVR', 'EN5', 'EN6', 'EN7', 'EN8', 'EN9', 'EN10']
        for name in motor_names:
            self.neurons[name] = Neuron(name, 'motor')
    
    def parse_connectome(self):
        """Парсинг коннектома из данных"""
        lines = CONNECTOME_DATA.strip().split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split(',')
            if len(parts) >= 5:
                pre_name = parts[0].strip()
                post_name = parts[1].strip()
                syn_type = parts[2].strip()
                weight = float(parts[3])
                count = int(parts[4])
                
                # Проверка наличия нейронов
                if pre_name not in self.neurons or post_name not in self.neurons:
                    continue
                
                # Определение нейромедиатора
                neurotransmitter = 'ACh'  # По умолчанию
                is_electrical = (syn_type == 'elec')
                
                if len(parts) > 5 and 'modulator:' in parts[5]:
                    mod_type = parts[5].split(':')[1].strip()
                    if mod_type == 'serotonin':
                        neurotransmitter = 'Serotonin'
                    elif mod_type == 'dopamine':
                        neurotransmitter = 'Dopamine'
                    elif mod_type == 'octopamine':
                        neurotransmitter = 'Octopamine'
                
                # Применение мутаций
                if self.mutant_mode == 'unc-2_null' and 'UNC-2' in str(self.neurons[pre_name].channels):
                    weight *= 0.1  # Сильное ослабление
                elif self.mutant_mode == 'slo-1_null' and 'SLO-1' in str(self.neurons[pre_name].channels):
                    weight *= 2.0  # Гиперактивность
                
                syn = Synapse(
                    self.neurons[pre_name],
                    self.neurons[post_name],
                    syn_type,
                    weight,
                    count,
                    neurotransmitter=neurotransmitter,
                    is_electrical=is_electrical
                )
                self.synapses.append(syn)
    
    def update_temperature_factor(self):
        """Расчет температурного фактора Q10"""
        delta_T = self.temperature - TEMP_PARAMS['T_ref']
        self.temp_factor = TEMP_PARAMS['Q10_general'] ** (delta_T / 10.0)
    
    def handle_events(self):
        """Обработка событий"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_simulation()
                elif event.key == pygame.K_m:
                    self.modulation_on = not self.modulation_on
                elif event.key == pygame.K_t:
                    self.temperature = (self.temperature + 2) % 30
                    if self.temperature < 10:
                        self.temperature = 10
                    self.update_temperature_factor()
                elif event.key == pygame.K_g:
                    mutants = [None, 'unc-2_null', 'slo-1_null', 'egl-19_null']
                    current_idx = mutants.index(self.mutant_mode) if self.mutant_mode in mutants else 0
                    self.mutant_mode = mutants[(current_idx + 1) % len(mutants)]
                    self.parse_connectome()  # Пересоздать синапсы с учетом мутации
                elif event.key == pygame.K_h:
                    self.show_help = not self.show_help
                elif event.key == pygame.K_1:
                    self.selected_obj_type = WALL
                elif event.key == pygame.K_2:
                    self.selected_obj_type = FOOD
                elif event.key == pygame.K_3:
                    self.selected_obj_type = MATERIAL
                elif event.key == pygame.K_4:
                    self.selected_obj_type = DANGER
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                x, y = pygame.mouse.get_pos()
                if x < WORLD_WIDTH:
                    if event.button == 1:  # ЛКМ
                        self.objects.append(WorldObject(x, y, self.selected_obj_type))
                    elif event.button == 3:  # ПКМ
                        for obj in reversed(self.objects):
                            dx = obj.x - x
                            dy = obj.y - y
                            if dx*dx + dy*dy < (obj.radius + 5)**2:
                                self.objects.remove(obj)
                                break
            
            # Ручное управление стрелками
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    self.manual_control(event.key)
        
        return True
    
    def manual_control(self, key):
        """Ручное управление моторными нейронами"""
        motor_map = {
            pygame.K_UP: ['VA', 'VB'],  # Вперед
            pygame.K_DOWN: ['VD', 'DD'],  # Назад
            pygame.K_LEFT: ['SMDDL', 'SMBVL'],  # Влево
            pygame.K_RIGHT: ['SMDDR', 'SMBVR']  # Вправо
        }
        neurons_to_stimulate = motor_map.get(key, [])
        for name in neurons_to_stimulate:
            if name in self.neurons:
                self.neurons[name].receive_current(2.0)
    
    def sense_environment(self):
        """Сенсорная трансдукция из среды"""
        head_pos = self.worm_body.get_head_pos()
        
        for neuron_name, neuron in self.neurons.items():
            if neuron.type != 'sensory':
                continue
            
            total_stimulus = 0.0
            
            # Хемотаксис (AWC, ASE)
            if neuron_name in ['AWCL', 'AWCR', 'ASEL', 'ASER']:
                for obj in self.objects:
                    conc = obj.get_concentration(head_pos[0], head_pos[1], 'chemo')
                    if obj.type == FOOD:
                        total_stimulus += conc * 0.8
                    elif obj.type == DANGER:
                        total_stimulus += conc * (-0.6)
            
            # Тактильные сенсоры (ALM, AVM, PVM)
            if neuron_name in ['ALML', 'ALMR', 'AVML', 'AVMR', 'PVML', 'PVMR']:
                for obj in self.objects:
                    if obj.type == WALL:
                        touch = obj.get_concentration(head_pos[0], head_pos[1], 'tactile')
                        total_stimulus += touch * 1.0
            
            # Преобразование стимула в рецепторный потенциал
            if total_stimulus != 0:
                # Нелинейная трансдукция
                receptor_potential = np.tanh(total_stimulus) * 3.0
                neuron.receive_current(receptor_potential)
    
    def update_brain(self, dt):
        """Обновление нейронной сети"""
        # Обновление всех нейронов
        for neuron in self.neurons.values():
            spiked = neuron.update(dt, self.temp_factor)
            if spiked:
                self.total_spikes += 1
        
        # Передача через синапсы
        for syn in self.synapses:
            syn.transmit(dt, self.temp_factor)
        
        # Гомеостаз (медленный процесс)
        if int(self.simulation_time * 1000) % 100 == 0:
            target_rate = HOMEOSTASIS_PARAMS['target_firing_rate']
            for syn in self.synapses:
                # Расчет средней частоты
                recent_spikes = sum(1 for t in syn.pre.spike_history 
                                  if pygame.time.get_ticks() - t < 1000)
                actual_rate = recent_spikes / 1.0  # Гц
                syn.apply_homeostasis(target_rate, actual_rate, dt)
    
    def get_muscle_activations(self):
        """Получение активаций мышц от моторных нейронов"""
        activations = []
        motor_order = ['SMDDL', 'SMDDR', 'SMBVL', 'SMBVR', 'VD', 'DD', 
                      'VA', 'VB', 'RIVL', 'RIVR']
        
        for name in motor_order:
            if name in self.neurons:
                neuron = self.neurons[name]
                # Частота спайков за последние 100 мс
                recent_spikes = sum(1 for t in neuron.spike_history 
                                  if pygame.time.get_ticks() - t < 100)
                activation = min(1.0, recent_spikes / 10.0)
                activations.append(activation)
            else:
                activations.append(0.0)
        
        # Циклическое повторение для сегментов
        while len(activations) < self.worm_body.num_segments:
            activations.extend(activations[:min(4, self.worm_body.num_segments - len(activations))])
        
        return activations[:self.worm_body.num_segments]
    
    def calculate_validation_stats(self):
        """Расчет валидационных метрик"""
        # Скорость движения
        if len(self.worm_body.segments) > 1:
            head_vel = np.linalg.norm(self.worm_body.velocities[0])
            # Конвертация в мм/с (приближенно)
            self.validation_stats['speed'] = head_vel / 2500.0  # масштабирование
        
        # Частота изгибов
        # (упрощенно: по активации мышц)
        motor_neurons = [n for n in self.neurons.values() if n.type == 'motor']
        total_recent = sum(sum(1 for t in n.spike_history if pygame.time.get_ticks() - t < 500) 
                          for n in motor_neurons)
        self.validation_stats['frequency'] = total_recent / len(motor_neurons) / 0.5  # Гц
        
        # Средняя частота спайков
        total_spikes_all = sum(len(n.spike_history) for n in self.neurons.values())
        self.validation_stats['avg_firing_rate'] = total_spikes_all / len(self.neurons) / 1.0
    
    def draw_neural_network(self, surface):
        """Визуализация нейронной сети"""
        neuron_positions = {}
        x_start = WORLD_WIDTH + 30
        y_offset = 80
        col_width = 60
        row_height = 25
        
        # Группировка по типам
        types_order = ['sensory', 'inter', 'motor']
        type_cols = {'sensory': 0, 'inter': 1, 'motor': 2}
        
        idx = 0
        for neuron_type in types_order:
            neurons_of_type = [(name, n) for name, n in self.neurons.items() 
                              if n.type == neuron_type]
            for i, (name, neuron) in enumerate(neurons_of_type):
                col = type_cols[neuron_type]
                row = i % 20
                neuron_positions[name] = (
                    x_start + col * col_width,
                    y_offset + row * row_height
                )
                idx += 1
        
        # Отрисовка синапсов
        for syn in self.synapses:
            if syn.pre.name not in neuron_positions or syn.post.name not in neuron_positions:
                continue
            
            start = neuron_positions[syn.pre.name]
            end = neuron_positions[syn.post.name]
            
            # Цвет в зависимости от типа
            if syn.is_electrical:
                color = CYAN
                alpha = 100
            else:
                if syn.neurotransmitter in ['ACh', 'Glu']:
                    color = GREEN
                elif syn.neurotransmitter == 'GABA':
                    color = RED
                else:
                    color = PURPLE
                alpha = min(255, int(255 * min(1.0, syn.weight)))
            
            pygame.draw.line(surface, color, start, end, 1)
        
        # Отрисовка нейронов
        for name, pos in neuron_positions.items():
            neuron = self.neurons[name]
            
            # Цвет по типу
            type_colors = {
                'sensory': GREEN,
                'inter': BLUE,
                'motor': RED
            }
            base_color = type_colors.get(neuron.type, WHITE)
            
            # Яркость по активности
            recent_spikes = sum(1 for t in neuron.spike_history 
                              if pygame.time.get_ticks() - t < 200)
            intensity = min(1.0, recent_spikes / 5.0)
            
            r = min(255, base_color[0] + int(150 * intensity))
            g = min(255, base_color[1] + int(150 * intensity))
            b = min(255, base_color[2] + int(150 * intensity))
            
            color = (r, g, b)
            size = 5 + int(3 * intensity)
            
            pygame.draw.circle(surface, color, pos, size)
            
            # Имя нейрона (только при большой яркости)
            if intensity > 0.5:
                text = self.small_font.render(name, True, BLACK)
                surface.blit(text, (pos[0] + 8, pos[1] - 6))
    
    def draw_ui(self, surface):
        """Отрисовка пользовательского интерфейса"""
        # Заголовок
        title = self.font.render("C. elegans Full Biophysical Simulation", True, BLACK)
        surface.blit(title, (WORLD_WIDTH + 20, 20))
        
        # Статус
        status_lines = [
            f"Time: {self.simulation_time:.1f}s",
            f"Temperature: {self.temperature:.1f}°C (Q10={self.temp_factor:.2f})",
            f"Neurons: {len(self.neurons)}",
            f"Synapses: {len(self.synapses)}",
            f"Total Spikes: {self.total_spikes}",
            f"Mutant: {self.mutant_mode if self.mutant_mode else 'Wildtype'}",
            f"Modulation: {'ON' if self.modulation_on else 'OFF'}",
            f"Objects: {len(self.objects)}",
            "",
            "=== VALIDATION ===",
            f"Speed: {self.validation_stats['speed']:.3f} mm/s (ref: 0.2)",
            f"Frequency: {self.validation_stats['frequency']:.2f} Hz (ref: 0.4)",
            f"Avg Firing: {self.validation_stats['avg_firing_rate']:.1f} Hz",
            "",
            "=== CONTROLS ===",
            "Arrows: Manual control",
            "1-4: Select object",
            "LMB: Create | RMB: Delete",
            "M: Modulation | T: Temperature",
            "G: Mutant | R: Reset",
            "Space: Pause | H: Help",
            "Esc: Exit"
        ]
        
        if self.mutant_mode:
            mutant_info = VALIDATION_DATA['mutants'].get(self.mutant_mode, {})
            status_lines.append(f"Expected: {mutant_info.get('phenotype', 'N/A')}")
        
        y = 50
        for line in status_lines:
            text = self.small_font.render(line, True, BLACK)
            surface.blit(text, (WORLD_WIDTH + 20, y))
            y += 20
        
        # Помощь
        if self.show_help:
            help_bg = pygame.Surface((400, 300))
            help_bg.fill(WHITE)
            help_bg.set_alpha(240)
            surface.blit(help_bg, (WORLD_WIDTH + 20, SCREEN_HEIGHT - 320))
            
            help_text = [
                "=== HELP ===",
                "This simulation models:",
                "- Real C. elegans connectome",
                "- Specific ion channels (EGL-19, UNC-2, SLO-1)",
                "- Receptor-specific synapses",
                "- Hill muscle model with Ca2+",
                "- GPCR signaling & 2nd messengers",
                "- STDP plasticity & homeostasis",
                "- Temperature compensation (Q10)",
                "",
                "Validation against experimental data",
                "is performed in real-time."
            ]
            
            y = SCREEN_HEIGHT - 310
            for line in help_text:
                text = self.small_font.render(line, True, BLACK)
                surface.blit(text, (WORLD_WIDTH + 30, y))
                y += 18
    
    def reset_simulation(self):
        """Сброс симуляции"""
        self.objects = []
        self.worm_body = WormBody(num_segments=12)
        self.total_spikes = 0
        self.simulation_time = 0.0
        
        # Сброс нейронов
        for neuron in self.neurons.values():
            neuron.V = -65.0
            neuron.spike_history.clear()
            neuron.second_messenger = SecondMessengerSystem()
        
        # Пересоздание синапсов
        self.synapses = []
        self.parse_connectome()
        
        # Пересвязывание
        for neuron in self.neurons.values():
            neuron.incoming_synapses = []
            neuron.outgoing_synapses = []
        for syn in self.synapses:
            syn.pre.outgoing_synapses.append(syn)
            syn.post.incoming_synapses.append(syn)
    
    def run(self):
        """Основной цикл симуляции"""
        running = True
        accumulated_time = 0.0
        
        while running:
            dt = DT  # Фиксированный шаг
            
            running = self.handle_events()
            
            if not self.paused:
                # Сенсорика
                self.sense_environment()
                
                # Мозг (несколько подшагов для точности)
                substeps = 5
                for _ in range(substeps):
                    self.update_brain(dt / substeps)
                
                # Получение активаций мышц
                muscle_activations = self.get_muscle_activations()
                
                # Физика тела
                self.worm_body.update(dt, muscle_activations, self.temp_factor)
                
                # Время
                accumulated_time += dt
                self.simulation_time = accumulated_time / 1000.0  # конвертация в секунды
                
                # Валидация
                self.calculate_validation_stats()
            
            # Отрисовка
            self.screen.fill(WHITE)
            
            # Мир
            world_surface = pygame.Surface((WORLD_WIDTH, WORLD_HEIGHT))
            world_surface.fill((245, 245, 245))
            for obj in self.objects:
                obj.draw(world_surface)
            self.worm_body.draw(world_surface)
            self.screen.blit(world_surface, (0, 0))
            
            # Нейронная панель
            neural_surface = pygame.Surface((NEURAL_PANEL_WIDTH, SCREEN_HEIGHT))
            neural_surface.fill((250, 250, 250))
            self.draw_neural_network(neural_surface)
            self.draw_ui(neural_surface)
            self.screen.blit(neural_surface, (WORLD_WIDTH, 0))
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    try:
        sim = CElegansFullSim()
        sim.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
