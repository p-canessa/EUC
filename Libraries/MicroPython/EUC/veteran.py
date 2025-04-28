# micropython/euc/veteran.py
from .base_adapter import BaseAdapter
from constants import VETERAN_SERVICE_UUID, VETERAN_CHAR_UUID, VETERAN_VOLTAGE_CONFIGS, VETERAN_COMMANDS, VETERAN_SPEED_LIMITS
from errors import EUCParseError, EUCCommandError

class VeteranAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = VETERAN_SERVICE_UUID
        self.char_uuid = VETERAN_CHAR_UUID
        self.temperature = 0
        self.current = 0
        self.serial_number = None
        self.firmware_version = None
        self.voltage_config = VETERAN_VOLTAGE_CONFIGS.get(100.8, VETERAN_VOLTAGE_CONFIGS[100.8])  # Default Sherman Max

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC Veteran."""
        try:
            self._check_buffer_size()
            self.buffer.extend(data)
            if len(self.buffer) < 20:
                return None
            if self.buffer[0] != 0x55 or self.buffer[1] != 0xAA:
                self.buffer = bytearray()
                raise EUCParseError("Header pacchetto Veteran non valido.")
            
            response_type = self.buffer[16]
            result = {}

            if response_type == RESPONSE_TYPES["Veteran"]["live_data"]:  # Dati live
                voltage = (self.buffer[2] << 8 | self.buffer[3]) / 100.0
                speed = ((self.buffer[4] << 8 | self.buffer[5]) / 100.0)
                if speed > 327.67:
                    speed -= 655.36
                distance = (self.buffer[6] << 24 | self.buffer[7] << 16 |
                           self.buffer[8] << 8 | self.buffer[9]) / 1000.0
                current = ((self.buffer[10] << 8 | self.buffer[11]) / 100.0)
                if current > 327.67:
                    current -= 655.36
                temperature = (self.buffer[12] << 8 | self.buffer[13]) / 100.0
                battery = min(max(int((voltage - self.voltage_config["min_voltage"]) /
                                     (self.voltage_config["max_voltage"] - self.voltage_config["min_voltage"]) * 100), 0), 100)
                
                self.speed = speed
                self.battery = battery
                self.distance = distance
                self.temperature = temperature
                self.current = current
                
                result = {
                    "speed": speed,
                    "battery": battery,
                    "distance": distance,
                    "temperature": temperature,
                    "current": current,
                    "voltage": voltage
                }

            elif response_type == RESPONSE_TYPES["Veteran"]["serial_data"]:  # Numero di serie
                serial = "".join(chr(b) for b in self.buffer[2:16] if b != 0)
                self.serial_number = serial
                result = {"serial_number": serial}

            elif response_type == RESPONSE_TYPES["Veteran"]["firmware"]:  # Firmware
                major = self.buffer[2]
                minor = self.buffer[3]
                firmware = f"{major}.{minor}"
                self.firmware_version = firmware
                result = {"firmware_version": firmware}

            else:
                raise EUCParseError(f"Tipo di risposta Veteran sconosciuto: {response_type}")

            self.buffer = bytearray()
            return result

        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Veteran incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Veteran: {e}")

    def update_pedals_mode(self, mode):
        """Imposta modalità pedalata (0: hard, 1: medium, 2: soft)."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità pedali non valida: {mode}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["pedals_mode"], mode, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedali: {e}")

    def set_lights(self, state):
        """Accende (1) o spegne (0) le luci."""
        try:
            if state not in [0, 1]:
                raise EUCCommandError(f"Stato luci non valido: {state}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["lights"], state, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando luci: {e}")

    def start_calibration(self):
        """Avvia la calibrazione del giroscopio."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["calibration"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando calibrazione: {e}")

    def set_speed_alert(self, level, speed):
        """Imposta allarme velocità (level: 1, 2, 3; speed: valori discreti in km/h)."""
        try:
            if level not in [1, 2, 3]:
                raise EUCCommandError(f"Livello allarme non valido: {level}")
            if speed not in VETERAN_SPEED_LIMITS:
                valid_speeds = ", ".join(map(str, VETERAN_SPEED_LIMITS[:-1])) + ", or 280 (no alert)"
                raise EUCCommandError(f"Velocità non valida: {speed}. Valori consentiti: {valid_speeds}")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["speed_alert"], level, 
                                speed_value >> 8, speed_value & 0xFF,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando allarme velocità: {e}")

    def set_pedal_angle(self, angle):
        """Imposta l'angolo delle pedane (gradi, es. -5.0 a +5.0)."""
        try:
            if not (-5.0 <= angle <= 5.0):
                raise EUCCommandError(f"Angolo pedane non valido: {angle}")
            angle_value = int(angle * 100)  # Convertito in 0.01°
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["pedal_angle"], 
                                angle_value >> 8, angle_value & 0xFF, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando angolo pedane: {e}")

    def activate_horn(self):
        """Attiva il clacson (se supportato)."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["horn"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando clacson: {e}")

    def request_serial_data(self):
        """Richiede il numero di serie dell'EUC."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["serial_data"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando dati seriali: {e}")

    def set_ride_mode(self, mode):
        """Imposta modalità di guida (0: eco, 1: normale, 2: sport)."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità di guida non valida: {mode}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                VETERAN_COMMANDS["ride_mode"], mode, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità di guida: {e}")
