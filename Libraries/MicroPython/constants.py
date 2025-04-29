# micropython/constants.py

# UUID dei servizi e caratteristiche BLE
INMOTION_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
INMOTION_WRITE_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
INMOTION_NOTIFY_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
KINGSONG_SERVICE_UUID = "0000FFE0-0000-1000-8000-00805F9B34FB"
KINGSONG_CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"
GOTWAY_SERVICE_UUID = "0000FFF0-0000-1000-8000-00805F9B34FB"
GOTWAY_CHAR_UUID = "0000FFF1-0000-1000-8000-00805F9B34FB"
NINEBOT_SERVICE_UUID = "0000FFE0-0000-1000-8000-00805F9B34FB"
NINEBOT_CHAR_UUID = "0000FFE1-0000-1000-8000-00805F9B34FB"
VETERAN_SERVICE_UUID = "0000FFF0-0000-1000-8000-00805F9B34FB"
VETERAN_CHAR_UUID = "0000FFF1-0000-1000-8000-00805F9B34FB"

# Filtri per nomi dispositivi
EUC_NAME_FILTERS = {
    "InMotion": {
        "name": r"^V\d{1,2}[A-Z]*-[A-Z0-9]{8}$",
        "priority": 1,
        "description": "Inizia con V, 1-2 cifre, 0+ lettere, trattino, 8 caratteri alfanumerici (es. V10F-AE86027D)"
    },
    "Kingsong": {
        "name": r"^KS-",
        "priority": 2,
        "description": "Inizia con KS- (es. KS-18XL)"
    },
    "Veteran": {
        "name": r"^LK\d{1,8}$",
        "priority": 3,
        "description": "Inizia con LK, seguito da 1-8 cifre (es. LK5158, LK10657)"
    },
    "Ninebot": {
        "name": r"^(Ninebot|Segway-Ninebot)( .*)?$",
        "priority": 4,
        "description": "Inizia con Ninebot o Segway-Ninebot, opzionale modello (es. Ninebot E10, Segway-Ninebot)"
    },
    "Gotway": {
        "name": r".*",
        "priority": 5,
        "description": "Qualsiasi nome, ultima priorità (es. CustomName)"
    }
}

# Mappa delle marche agli UUID e adapter
EUC_BRANDS = [
    {
        "brand": "inmotion",
        "euc_type": "InMotion",
        "service_uuid": INMOTION_SERVICE_UUID,
        "adapter": "InMotionAdapter",
        "uuid_priority": 1
    },
    {
        "brand": "ninebot",
        "euc_type": "Ninebot",
        "service_uuid": NINEBOT_SERVICE_UUID,
        "adapter": "NinebotAdapter",
        "uuid_priority": 2
    },
    {
        "brand": "kingsong",
        "euc_type": "Kingsong",
        "service_uuid": KINGSONG_SERVICE_UUID,
        "adapter": "KingsongAdapter",
        "uuid_priority": 3
    },
    {
        "brand": "gotway",
        "euc_type": "Gotway",
        "service_uuid": GOTWAY_SERVICE_UUID,
        "adapter": "GotwayAdapter",
        "uuid_priority": 4
    },
    {
        "brand": "veteran",
        "euc_type": "Veteran",
        "service_uuid": VETERAN_SERVICE_UUID,
        "adapter": "VeteranAdapter",
        "uuid_priority": 5
    }
]

# Informazioni sulle tensioni InMotion
INMOTION_VOLTAGE_CONFIGS = {
    67.2: {  # 16S: V5, V5F
        "cells": 16,
        "max_voltage": 67.2,  # 4.2V * 16
        "min_voltage": 50.4,  # 3.15V * 16
        "low_battery_alarm": 52.0,  # 3.25V * 16
        "low_battery_tiltback": 50.4,  # 3.15V * 16
        "supports_low_battery_mode": False,
        "max_speed": 25.0
    },
    84.0: {  # 20S: V8, V8F, V8S, V10, V10F, V11, V12
        "cells": 20,
        "max_voltage": 84.0,  # 4.2V * 20
        "min_voltage": 63.0,  # 3.15V * 20
        "low_battery_alarm": 65.0,  # 3.25V * 20
        "low_battery_tiltback": 63.0,  # 3.15V * 20
        "supports_low_battery_mode": True,  # V11, V12 supportano modalità batteria scarica
        "max_speed": 45.0  # V10F, V11
    },
    100.8: {  # 24S: V13
        "cells": 24,
        "max_voltage": 100.8,  # 4.2V * 24
        "min_voltage": 75.6,  # 3.15V * 24
        "low_battery_alarm": 78.0,  # 3.25V * 24
        "low_battery_tiltback": 75.6,  # 3.15V * 24
        "supports_low_battery_mode": True,  # V13 supporta modalità batteria scarica
        "max_speed": 60.0
    },
    134.4: {  # 32S: V14 Adventure
        "cells": 32,
        "max_voltage": 134.4,  # 4.2V * 32
        "min_voltage": 100.8,  # 3.15V * 32
        "low_battery_alarm": 104.0,  # 3.25V * 32
        "low_battery_tiltback": 100.8,  # 3.15V * 32
        "supports_low_battery_mode": True,  # V14 supporta modalità batteria scarica
        "max_speed": 50.0  # Ipotetico
    }
}

# Informazioni sulle tensioni Ninebot
NINEBOT_VOLTAGE_CONFIGS = {
    "One S2": {"cells": 15, "max_voltage": 63.0, "min_voltage": 50.4, "max_speed": 24.0, "pedal_angle_range": (-5.0, 5.0)},
    "Z10": {"cells": 20, "max_voltage": 72.0, "min_voltage": 57.6, "max_speed": 45.0, "pedal_angle_range": (-5.0, 5.0)},
    "default": {"cells": 15, "max_voltage": 63.0, "min_voltage": 50.4, "max_speed": 24.0, "pedal_angle_range": (-5.0, 5.0)}
}

# Informazioni sulle tensioni Veteran
VETERAN_VOLTAGE_CONFIGS = {
    100.8: {
        "cells": 24,
        "max_voltage": 100.8,
        "min_voltage": 75.6,  # 3.15V/cella
        "low_battery_alarm": 78.0,  # 3.25V/cella (Sherman Max)
        "low_battery_tiltback": 75.6,  # 3.15V/cella (Sherman Max)
        "supports_low_battery_mode": False  # Non supportato su Sherman Max
    },
    126.0: {
        "cells": 30,
        "max_voltage": 126.0,
        "min_voltage": 94.5,  # 3.15V/cella
        "low_battery_alarm": 97.5,  # 3.25V/cella (Patton)
        "low_battery_tiltback": 94.5,  # 3.15V/cella (Patton)
        "supports_low_battery_mode": True  # Supportato su Patton (solo display)
    },
    151.2: {
        "cells": 36,
        "max_voltage": 151.2,
        "min_voltage": 113.4,  # 3.15V/cella
        "low_battery_alarm": 117.0,  # 3.25V/cella (Lynx/Sherman L)
        "low_battery_tiltback": 113.4,  # 3.15V/cella (Lynx/Sherman L)
        "supports_low_battery_mode": True  # Supportato su Lynx/Sherman L (solo display)
    }
}

BEGODE_VOLTAGE_CONFIGS = {
    67.2: {  # 16S: MTen3, MCM5
        "cells": 16,
        "max_voltage": 67.2,  # 4.2V * 16
        "min_voltage": 50.4,  # 3.15V * 16
        "low_battery_alarm": 52.0,  # 3.25V * 16
        "low_battery_tiltback": 50.4,  # 3.15V * 16
        "supports_low_battery_mode": False
    },
    84.0: {  # 20S: Tesla, MSuper V3, RS
        "cells": 20,
        "max_voltage": 84.0,  # 4.2V * 20
        "min_voltage": 63.0,  # 3.15V * 20
        "low_battery_alarm": 65.0,  # 3.25V * 20
        "low_battery_tiltback": 63.0,  # 3.15V * 20
        "supports_low_battery_mode": True  # RS supporta modalità batteria scarica
    },
    100.8: {  # 24S: Nikola, EX, Monster, T4
        "cells": 24,
        "max_voltage": 100.8,  # 4.2V * 24
        "min_voltage": 75.6,  # 3.15V * 24
        "low_battery_alarm": 78.0,  # 3.25V * 24
        "low_battery_tiltback": 75.6,  # 3.15V * 24
        "supports_low_battery_mode": True  # Nikola, T4 supportano modalità batteria scarica
    },
    134.4: {  # 32S: Master, EX.N, Extreme
        "cells": 32,
        "max_voltage": 134.4,  # 4.2V * 32
        "min_voltage": 100.8,  # 3.15V * 32
        "low_battery_alarm": 104.0,  # 3.25V * 32
        "low_battery_tiltback": 100.8,  # 3.15V * 32
        "supports_low_battery_mode": True  # Master supporta modalità batteria scarica
    },
    168.0: {  # 40S: X-Way
        "cells": 40,
        "max_voltage": 168.0,  # 4.2V * 40
        "min_voltage": 126.0,  # 3.15V * 40
        "low_battery_alarm": 130.0,  # 3.25V * 40
        "low_battery_tiltback": 126.0,  # 3.15V * 40
        "supports_low_battery_mode": True  # X-Way supporta modalità batteria scarica
    }
}

KINGSONG_VOLTAGE_CONFIGS = {
    67.2: {  # 16S: 14S, 16S, N8, N10
        "cells": 16,
        "max_voltage": 67.2,  # 4.2V * 16
        "min_voltage": 50.4,  # 3.15V * 16
        "low_battery_alarm": 52.0,  # 3.25V * 16
        "low_battery_tiltback": 50.4,  # 3.15V * 16
        "supports_low_battery_mode": False
    },
    84.0: {  # 20S: 16X, 18L, 18XL, S18
        "cells": 20,
        "max_voltage": 84.0,  # 4.2V * 20
        "min_voltage": 63.0,  # 3.15V * 20
        "low_battery_alarm": 65.0,  # 3.25V * 20
        "low_battery_tiltback": 63.0,  # 3.15V * 20
        "supports_low_battery_mode": True  # S18 supporta modalità batteria scarica (display)
    },
    126.0: {  # 30S: S19 Pro, F-series (ipotetico)
        "cells": 30,
        "max_voltage": 126.0,  # 4.2V * 30
        "min_voltage": 94.5,  # 3.15V * 30
        "low_battery_alarm": 97.5,  # 3.25V * 30
        "low_battery_tiltback": 94.5,  # 3.15V * 30
        "supports_low_battery_mode": True  # S19 supporta modalità batteria scarica
    },
    134.4: {  # 32S: S22, S22 Pro
        "cells": 32,
        "max_voltage": 134.4,  # 4.2V * 32
        "min_voltage": 100.8,  # 3.15V * 32
        "low_battery_alarm": 104.0,  # 3.25V * 32
        "low_battery_tiltback": 100.8,  # 3.15V * 32
        "supports_low_battery_mode": True  # S22 supporta modalità batteria scarica (display)
    },
    176.4: {  # 42S: F22 Pro
        "cells": 42,
        "max_voltage": 176.4,  # 4.2V * 42
        "min_voltage": 132.3,  # 3.15V * 42
        "low_battery_alarm": 136.5,  # 3.25V * 42
        "low_battery_tiltback": 132.3,  # 3.15V * 42
        "supports_low_battery_mode": True  # F22 Pro ipoteticamente supporta modalità batteria scarica
    }
}

# Codici comandi InMotion
INMOTION_COMMANDS = {
    "pedals_mode": 0x17,
    "lights": 0x14,
    "calibration": 0xF7,
    "speed_alert": 0x12,
    "pedal_angle": 0x13,
    "horn": 0x16,
    "serial_data": 0x1B,
    "ride_mode": 0xF3,
    "tiltback_alert": 0xF8,
    "status": 0x1A,
    "live_data": 0x01
}

# Codici comandi Kingsong
KINGSONG_COMMANDS = {
    "pedals_mode": 0xF1,
    "lights": 0x73,
    "calibration": 0xF7,
    "speed_alert": 0xF5,
    "pedal_angle": 0xF6,
    "horn": 0x88,
    "serial_data": 0x63,
    "ride_mode": 0xF3,
    "tiltback_alert": 0xF8,
    "status": 0x1A
}

# Codici comandi Gotway/Begode
GOTWAY_COMMANDS = {
    "pedals_mode": 0xF1,
    "lights": 0x73,
    "calibration": 0xF7,
    "speed_alert": 0xF5,
    "pedal_angle": 0xF6,
    "horn": 0x88,
    "serial_data": 0x1B,
    "ride_mode": 0xF3,
    "tiltback_alert": 0xF8,
    "status": 0x1A
}

# Codici comandi Ninebot
NINEBOT_COMMANDS = {
    "pedals_mode": 0x09,
    "lights": 0x07,
    "calibration": 0x0A,
    "speed_alert": 0x05,
    "pedal_angle": 0x0B,
    "horn": 0x08,
    "serial_data": 0x03,
    "ride_mode": 0x0C,
    "tiltback_alert": 0x06,
    "status": 0x04,
    "live_data": 0x01
}

# Codici comandi Veteran
VETERAN_COMMANDS = {
    "pedals_mode": 0xF1,
    "lights": 0xE7,
    "calibration": 0xF7,
    "speed_alert": 0xF5,
    "pedal_angle": 0xF6,
    "horn": 0x88,
    "serial_data": 0x1B,
    "ride_mode": 0xF3,
    "status": 0x1A
}

# Codici dei pacchetti di risposta
RESPONSE_TYPES = {
    "InMotion": {
        "live_data": 0x04,
        "serial_data": 0x1B,
        "firmware": 0x1A
    },
    "Kingsong": {
        "live_data": 0x9B,
        "serial_data": 0x63,
        "firmware": 0x1A
    },
    "Gotway": {
        "live_data": 0x04,
        "serial_data": 0x1B,
        "firmware": 0x1A
    },
    "Ninebot": {
        "live_data": 0x01,
        "serial_data": 0x03,
        "firmware": 0x04
    },
    "Veteran": {
        "live_data": 0x04,
        "serial_data": 0x1B,
        "firmware": 0x1A
    }
}
