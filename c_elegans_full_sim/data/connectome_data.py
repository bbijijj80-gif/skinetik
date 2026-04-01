# Полный коннектом C. elegans (фрагмент для демонстрации)
# Источник: White et al. (1986), Cook et al. (2019), OpenWorm
# Формат: pre_neuron, post_neuron, synapse_type, weight, count

CONNECTOME_DATA = """
# Сенсорные -> Интернейроны (AWC путь)
AWCL,AIYL,chem,0.85,3
AWCR,AIYR,chem,0.85,3
AWCL,AIZL,chem,0.45,1
AWCR,AIZR,chem,0.45,1
AWCL,RIA L,chem,0.35,1
AWCR,RIA R,chem,0.35,1

# ASE путь (соленость/химия)
ASEL,AIYL,chem,0.75,2
ASER,AIYR,chem,0.75,2
ASEL,AIZL,chem,0.55,1
ASER,AIZR,chem,0.55,1

# Тактильные (ALM, AVM, PVM)
ALML,AVBL,chem,0.9,4
ALML,AVBR,chem,0.8,3
ALMR,AVBR,chem,0.9,4
ALMR,AVBL,chem,0.8,3
AVML,AVBL,chem,0.85,3
AVMR,AVBR,chem,0.85,3
PVML,AVDL,chem,0.7,2
PVMR,AVDR,chem,0.7,2

# Интернейронные связи (передние)
AIYL,AIBR,chem,0.65,2
AIYR,AIBL,chem,0.65,2
AIYL,RIBL,chem,0.55,2
AIYR,RIBR,chem,0.55,2
AIBL,RIML,chem,0.7,3
AIBR,RIMR,chem,0.7,3
AIBL,AVBL,chem,0.6,2
AIBR,AVBR,chem,0.6,2

# Интернейронные связи (задние)
AIZL,RIML,chem,0.75,2
AIZR,RIMR,chem,0.75,2
AIZL,AVJL,chem,0.5,1
AIZR,AVJR,chem,0.5,1

# Моторные команды
RIML,SMDDL,chem,0.8,2
RIMR,SMDDR,chem,0.8,2
RIBL,SMBVL,chem,0.7,2
RIBR,SMBVR,chem,0.7,2
AVBL,VD,chem,0.65,3
AVBR,DD,chem,0.65,3
AVDL,VA,chem,0.7,3
AVDR,VB,chem,0.7,3

# Электрические синапсы (щелевые контакты)
AIYL,AIYR,elec,0.9,1
AIBL,AIBR,elec,0.85,1
AIZL,AIZR,elec,0.8,1
RIML,RIMR,elec,0.75,1
AVBL,AVBR,elec,0.9,1
AVDL,AVDR,elec,0.9,1

# Обратные связи
RIML,AIBL,chem,0.5,1
RIMR,AIBR,chem,0.5,1
SMBDL,RIVL,chem,0.4,1
SMBDR,RIVR,chem,0.4,1

# Модуляторные пути (серотонин, дофамин)
NSML,AVKL,chem,0.6,2,modulator:serotonin
NSMR,AVKR,chem,0.6,2,modulator:serotonin
CEPDL,AVKL,chem,0.55,2,modulator:dopamine
CEPDR,AVKR,chem,0.55,2,modulator:dopamine

# Новые нейроны EN1-EN10 (экспериментальные)
EN1,AWCL,chem,0.3,1,modulator:octopamine
EN2,AIYL,chem,0.4,1
EN3,AIBL,chem,0.5,1
EN4,RIML,chem,0.45,1
EN5,AVBL,chem,0.6,2
EN6,VD,chem,0.55,1
EN7,DD,chem,0.55,1
EN8,SMDDL,chem,0.5,1
EN9,SMBVL,chem,0.5,1
EN10,RIVL,chem,0.45,1
"""

# Параметры ионных каналов для разных типов нейронов
# Основано на данных: Goodman & Lockery (2000), Boyle et al. (2012)
ION_CHANNEL_PARAMS = {
    'sensory': {
        'EGL-19_CaV1': {'g_max': 0.8, 'V_half': -25.0, 'k': 6.0, 'tau': 15.0},
        'UNC-2_CaV2': {'g_max': 0.6, 'V_half': -20.0, 'k': 5.5, 'tau': 10.0},
        'UNC-8_DEG': {'g_max': 0.4, 'V_half': -30.0, 'k': 8.0, 'tau': 20.0},
        'TAX-2_TAX-4': {'g_max': 0.5, 'V_half': -35.0, 'k': 7.0, 'tau': 25.0},
        'SLO-1_KCa': {'g_max': 0.7, 'V_half': -10.0, 'k': 10.0, 'tau_ca': 50.0},
        'K2P_leak': {'g_max': 0.3, 'E_rev': -70.0}
    },
    'inter': {
        'EGL-19_CaV1': {'g_max': 0.7, 'V_half': -22.0, 'k': 5.5, 'tau': 12.0},
        'UNC-2_CaV2': {'g_max': 0.75, 'V_half': -18.0, 'k': 5.0, 'tau': 8.0},
        'SLO-1_KCa': {'g_max': 0.8, 'V_half': -8.0, 'k': 9.0, 'tau_ca': 40.0},
        'Kv1_Kdr': {'g_max': 0.6, 'V_half': -15.0, 'k': 7.0, 'tau': 5.0},
        'K2P_leak': {'g_max': 0.25, 'E_rev': -72.0}
    },
    'motor': {
        'EGL-19_CaV1': {'g_max': 0.9, 'V_half': -20.0, 'k': 5.0, 'tau': 10.0},
        'UNC-2_CaV2': {'g_max': 0.8, 'V_half': -15.0, 'k': 4.5, 'tau': 6.0},
        'ACR-16_nAChR': {'g_max': 0.85, 'V_half': -10.0, 'k': 6.0, 'tau': 3.0},
        'UNC-49_GABAR': {'g_max': 0.7, 'E_rev': -65.0, 'tau': 8.0},
        'SLO-1_KCa': {'g_max': 0.9, 'V_half': -5.0, 'k': 8.0, 'tau_ca': 30.0},
        'K2P_leak': {'g_max': 0.2, 'E_rev': -68.0}
    },
    'muscle': {
        'EGL-19_CaV1': {'g_max': 1.2, 'V_half': -18.0, 'k': 4.5, 'tau': 8.0},
        'UNC-2_CaV2': {'g_max': 0.5, 'V_half': -12.0, 'k': 5.0, 'tau': 5.0},
        'LEV-1_nAChR': {'g_max': 1.0, 'V_half': -8.0, 'k': 5.5, 'tau': 2.0},
        'UNC-49_GABAR': {'g_max': 0.8, 'E_rev': -60.0, 'tau': 10.0},
        'SLO-1_KCa': {'g_max': 1.1, 'V_half': -2.0, 'k': 7.0, 'tau_ca': 25.0},
        'K2P_leak': {'g_max': 0.15, 'E_rev': -65.0}
    }
}

# Рецепторная специфика синапсов
SYNAPSE_RECEPTORS = {
    'ACh': {'receptor': 'ACR-16', 'E_rev': 0.0, 'tau_rise': 0.5, 'tau_decay': 5.0, 'type': 'excitatory'},
    'Glu': {'receptor': 'GLC-1', 'E_rev': -40.0, 'tau_rise': 0.8, 'tau_decay': 8.0, 'type': 'excitatory'},
    'GABA': {'receptor': 'UNC-49', 'E_rev': -65.0, 'tau_rise': 1.0, 'tau_decay': 10.0, 'type': 'inhibitory'},
    'Serotonin': {'receptor': 'MOD-1', 'E_rev': -20.0, 'tau_rise': 2.0, 'tau_decay': 50.0, 'type': 'modulatory'},
    'Dopamine': {'receptor': 'DOP-1', 'E_rev': -15.0, 'tau_rise': 2.5, 'tau_decay': 60.0, 'type': 'modulatory'},
    'Octopamine': {'receptor': 'SER-3', 'E_rev': -10.0, 'tau_rise': 3.0, 'tau_decay': 80.0, 'type': 'modulatory'},
    'Neuropeptide': {'receptor': 'NPR-1', 'E_rev': -5.0, 'tau_rise': 5.0, 'tau_decay': 300.0, 'type': 'modulatory'}
}

# Параметры мышц (модель Хилла с кальциевой активацией)
MUSCLE_PARAMS = {
    'F_max': 1.5,  # Максимальная сила (нН)
    'v_max': 0.5,  # Максимальная скорость сокращения (мкм/с)
    'a_rel': 0.25, # Отношение a/F_max
    'l_opt': 1.0,  # Оптимальная длина
    'k_se': 2.0,   # Жесткость последовательного упругого элемента
    'k_pe': 0.5,   # Жесткость параллельного упругого элемента
    'ca_half': 0.5,# Полунасыщение кальция
    'n_hill': 3.0, # Коэффициент Хилла для Ca2+
    'tau_ca_on': 10.0,  # Время активации кальция (мс)
    'tau_ca_off': 50.0, # Время деактивации кальция (мс)
    'viscosity': 0.1    # Вязкость
}

# Параметры G-белковой сигнализации
GPCR_PARAMS = {
    'ODR-3': {'G_alpha': 'GPA-3', 'effector': 'PLC-beta', 'k_on': 0.01, 'k_off': 0.001},
    'GPA-3': {'effector': 'adenylyl_cyclase', 'k_on': 0.008, 'k_off': 0.0008},
    'EAT-16': {'G_alpha': 'GOA-1', 'effector': 'PLC-beta', 'k_on': 0.012, 'k_off': 0.0012}
}

# Вторичные мессенджеры
SECOND_MESSENGERS = {
    'cAMP': {'basal': 0.1, 'production_rate': 0.5, 'degradation_rate': 0.2, 'target': 'PKA'},
    'IP3': {'basal': 0.05, 'production_rate': 0.8, 'degradation_rate': 0.3, 'target': 'IP3R'},
    'DAG': {'basal': 0.08, 'production_rate': 0.6, 'degradation_rate': 0.25, 'target': 'PKC'},
    'Ca2+_internal': {'basal': 0.05, 'release_rate': 1.0, 'uptake_rate': 0.4, 'buffer_capacity': 50.0}
}

# STDP параметры
STDP_PARAMS = {
    'A_plus': 0.005,   # Амплитуда потенцирования
    'A_minus': 0.004,  # Амплитуда депрессии
    'tau_plus': 20.0,  # Время затухания потенцирования (мс)
    'tau_minus': 20.0, # Время затухания депрессии (мс)
    'w_max': 1.5,      # Максимальный вес
    'w_min': 0.0       # Минимальный вес
}

# Гомеостаз параметры
HOMEOSTASIS_PARAMS = {
    'target_firing_rate': 5.0,  # Целевая частота спайков (Гц)
    'homeo_tau': 1000.0,        # Время адаптации (с)
    'scaling_factor': 0.01      # Фактор масштабирования синапсов
}

# Температурные параметры
TEMP_PARAMS = {
    'Q10_general': 2.0,     # Общий Q10
    'Q10_channels': 2.3,    # Q10 для ионных каналов
    'Q10_synapses': 1.8,    # Q10 для синапсов
    'Q10_metabolism': 2.5,  # Q10 для метаболизма
    'T_ref': 20.0           # Референсная температура (°C)
}

# Валидационные данные (экспериментальные)
VALIDATION_DATA = {
    'locomotion': {
        'speed_wildtype': 0.2,      # мм/с
        'frequency_wildtype': 0.4,  # Гц (изгибы)
        'wavelength': 0.8,          # мм
        'amplitude': 0.15           # мм
    },
    'electrophysiology': {
        'resting_potential': -65.0, # мВ
        'threshold': -45.0,         # мВ
        'spike_amplitude': 80.0,    # мВ
        'spike_duration': 2.0,      # мс
        'refractory_period': 3.0    # мс
    },
    'calcium_imaging': {
        'baseline_F0': 1.0,
        'delta_F_max': 0.5,
        'rise_time': 100.0,         # мс
        'decay_time': 500.0         # мс
    },
    'mutants': {
        'unc-2_null': {'phenotype': 'paralysis', 'speed': 0.02},
        'egl-19_null': {'phenotype': 'lethal', 'speed': 0.0},
        'slo-1_null': {'phenotype': 'hyperactive', 'speed': 0.35},
        'unc-8_null': {'phenotype': 'uncoordinated', 'speed': 0.1}
    }
}
