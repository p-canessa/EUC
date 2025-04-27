# micropython/constants.py

# UUID dei servizi e caratteristiche BLE
INMOTION_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
INMOTION_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"
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
    "InMotion": {"name": "InMotion", "adapter": "inmotion"},
    "Kingsong": {"name": "KS-", "adapter": "kingsong"},
    "Gotway": {"name": "Gotway", "adapter": "gotway"},
    "Ninebot": {"name": "Ninebot", "adapter": "ninebot"},
    "Veteran": {"name": "LK", "adapter": "veteran"}  # Aggiornato per "LK"
}

# Informazioni sulle tensioni Veteran
VETERAN_VOLTAGE_CONFIGS = {
    100.8: {"cells": 24, "max_voltage": 100.8, "min_voltage": 76.8},  # Sherman, Sherman Max, Sherman S, Abrams
    126.0: {"cells": 30, "max_voltage": 126.0, "min_voltage": 96.0},  # Patton
    151.2: {"cells": 36, "max_voltage": 151.2, "min_voltage": 115.2}  # Lynx, Sherman L
}
