# micropython/euc/ninebot.py
from .base_adapter import BaseAdapter
from constants import NINEBOT_SERVICE_UUID, NINEBOT_CHAR_UUID, NINEBOT_COMMANDS, NINEBOT_VOLTAGE_CONFIGS
from errors import EUCParseError, EUCCommandError

class NinebotAdapter(BaseAdapter):
    def __init__(self, ble, model="One S2"):
        super().__init__(ble)
        self.service_uuid = NINEBOT_SERVICE_UUID
        self.char_uuid = NINEBOT_CHAR_UUID
        self.temperature = 0
        self.current = 0
        self.serial_number = None
        self.firmware_version = None
        self.model = model
        self.voltage_config = NINEBOT_VOLTAGE_CONFIGS.get(model, NINEBOT_VOLTAGE_CONFIGS["default"])
        self.max_speed = self.voltage_config["max_speed"]

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC Ninebot."""
        try:
            self._check_buffer_size()
            self.buffer.extend(data)
            if len(self.buffer) < 20:
                return None
            if self.buffer[0] != 0x5A or self.buffer[1] != 0xA5:
                self.buffer = bytearray()
                raise EUCParseError("Header pacchetto Ninebot non valido.")
            
            checksum = sum(self.buffer[:-1]) & 0xFF
            if checksum != self.buffer[-1]:
                self.buffer = bytearray()
                raise EUCParseError("Checksum pacchetto Ninebot non valido.")
            
            response_type = self.buffer[2]
            result = {}

            if response_type == RESPONSE_TYPES["Ninebot"]["live_data"]:  # Dati live
                speed = ((self.buffer[4] << 8 | self.buffer[5]) / 100.0)
                if speed > 327.67:
                    speed -= 655.36
                voltage = (self.buffer[6] << 8 | self.buffer[7]) / 100.0
                distance = (self.buffer[12] << 24 | self.buffer[13] << 16 |
                           self.buffer[14] << 8 | self.buffer[15]) / 1000.0
                temperature = (self.buffer[10] << 8 | self.buffer[11]) / 100.0
                current = ((self.buffer[8] << 8 | self.buffer[9]) / 100.0)
                if current > 327.67:
                    current -= 655.36
                
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

            elif response_type == RESPONSE_TYPES["Ninebot"]["serial_data"]:  # Numero di serie
                serial = "".join(chr(b) for b in self.buffer[3:17] if b != 0)
                self.serial_number = serial
                result = {"serial_number": serial}

            elif response_type == RESPONSE_TYPES["Ninebot"]["firmware"]:  # Firmware
                major = self.buffer[3]
                minor = self.buffer[4]
                firmware = f"{major}.{minor}"
                self.firmware_version = firmware
                result = {"firmware_version": firmware}

            else:
                raise EUCParseError(f"Tipo di risposta Ninebot sconosciuto: {response_type}")

            self.buffer = bytearray()
            return result

        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Ninebot incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Ninebot: {e}")

    def update_pedals_mode(self, mode):
        """Imposta modalità pedane (0: Soft, 1: Hard)."""
        try:
            if mode not in [0, 1]:
                raise EUCCommandError(f"Modalità pedane non valida: {mode}. Usa 0 (Soft) o 1 (Hard).")
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["pedals_mode"], mode] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedane: {e}")

    def set_lights(self, state):
        """Accende (1) o spegne (0) le luci."""
        try:
            if state not in [0, 1]:
                raise EUCCommandError(f"Stato luci non valido: {state}")
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["lights"], state] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando luci: {e}")

    def start_calibration(self):
        """Avvia la calibrazione del giroscopio (ipotetico, da verificare)."""
        try:
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["calibration"], 0x01] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando calibrazione: {e}")

    def set_speed_alert(self, speed):
        """Imposta allarme velocità (continuo, fino a velocità massima)."""
        try:
            if not (0 <= speed <= self.max_speed):
                raise EUCCommandError(f"Velocità non valida: {speed}. Deve essere tra 0 e {self.max_speed} km/h.")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["speed_alert"],
                                speed_value >> 8, speed_value & 0xFF] + [0x00] * 14 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando allarme velocità: {e}")

    def set_pedal_angle(self, angle):
        """Imposta l'angolo delle pedane (gradi, -5.0 a +5.0, incrementi di 0.1, ipotetico)."""
        try:
            min_angle, max_angle = self.voltage_config["pedal_angle_range"]
            if not (min_angle <= angle <= max_angle) or round(angle * 10) % 1 != 0:
                raise EUCCommandError(f"Angolo pedane non valido: {angle}. Deve essere tra {min_angle} e {max_angle} gradi, con incrementi di 0.1.")
            angle_value = int(angle * 100)  # Convertito in 0.01°
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["pedal_angle"],
                                angle_value >> 8, angle_value & 0xFF] + [0x00] * 14 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando angolo pedane: {e}")

    def activate_horn(self):
        """Attiva il clacson."""
        try:
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["horn"], 0x01] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando clacson: {e}")

    def request_serial_data(self):
        """Richiede il numero di serie dell'EUC."""
        try:
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["serial_data"], 0x00] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando dati seriali: {e}")

    def set_ride_mode(self, mode):
        """Imposta modalità di guida (0: eco, 1: normale, 2: sport, ipotetico)."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità di guida non valida: {mode}")
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["ride_mode"], mode] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità di guida: {e}")

    def set_tiltback_alert(self, speed):
        """Imposta allarme tilt-back."""
        try:
            if not (0 <= speed <= self.max_speed):
                raise EUCCommandError(f"Velocità non valida: {speed}. Deve essere tra 0 e {self.max_speed} km/h.")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["tiltback_alert"],
                                speed_value >> 8, speed_value & 0xFF] + [0x00] * 14 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando tilt-back: {e}")

    def request_status(self):
        """Richiede informazioni sullo stato (es. versione firmware)."""
        try:
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["status"], 0x00] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando stato: {e}")

    def request_live_data(self):
        """Richiede dati live (velocità, tensione, ecc.)."""
        try:
            command = bytearray([0x5A, 0xA5, NINEBOT_COMMANDS["live_data"], 0x01] + [0x00] * 15 + [0x00])
            command[-1] = sum(command[:-1]) & 0xFF  # Checksum
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando dati live: {e}")
