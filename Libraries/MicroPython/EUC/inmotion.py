# micropython/euc/inmotion.py
from .base_adapter import BaseAdapter
from constants import INMOTION_SERVICE_UUID, INMOTION_WRITE_UUID, INMOTION_NOTIFY_UUID, INMOTION_COMMANDS, INMOTION_VOLTAGE_CONFIGS, RESPONSE_TYPES
from errors import EUCParseError, EUCCommandError

class InmotionAdapter(BaseAdapter):
    def __init__(self, ble, model="V10F"):
        super().__init__(ble)
        self.service_uuid = INMOTION_SERVICE_UUID
        self.write_uuid = INMOTION_WRITE_UUID
        self.notify_uuid = INMOTION_NOTIFY_UUID
        self.temperature = 0
        self.current = 0
        self.serial_number = None
        self.firmware_version = None
        self.model = model
        self.voltage_config = INMOTION_VOLTAGE_CONFIGS.get(model, INMOTION_VOLTAGE_CONFIGS["default"])
        self.max_speed = self.voltage_config["max_speed"]

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC InMotion."""
        try:
            self._check_buffer_size()
            self.buffer.extend(data)
            if len(self.buffer) < 20:
                return None
            if self.buffer[0] != 0xAA or self.buffer[1] != 0x55:
                self.buffer = bytearray()
                raise EUCParseError("Header pacchetto InMotion non valido.")
            
            response_type = self.buffer[16]
            result = {}

            if response_type == RESPONSE_TYPES["InMotion"]["live_data"]:  # Dati live
                speed = ((self.buffer[4] << 8 | self.buffer[5]) / 100.0)
                if speed > 327.67:
                    speed -= 655.36
                voltage = (self.buffer[2] << 8 | self.buffer[3]) / 100.0
                distance = (self.buffer[12] << 24 | self.buffer[13] << 16 |
                           self.buffer[14] << 8 | self.buffer[15]) / 1000.0
                temperature = (self.buffer[8] << 8 | self.buffer[9]) / 100.0
                current = ((self.buffer[6] << 8 | self.buffer[7]) / 100.0)
                if current > 327.67:
                    current -= 655.36
                
                battery battery = self._calculate_battery(voltage)
                
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

            elif response_type == RESPONSE_TYPES["InMotion"]["serial_data"]:  # Numero di serie
                serial = "".join(chr(b) for b in self.buffer[2:16] if b != 0)
                self.serial_number = serial
                result = {"serial_number": serial}

            elif response_type == RESPONSE_TYPES["InMotion"]["firmware"]:  # Firmware
                major = self.buffer[2]
                minor = self.buffer[3]
                firmware = f"{major}.{minor}"
                self.firmware_version = firmware
                result = {"firmware_version": firmware}

            else:
                raise EUCParseError(f"Tipo di risposta InMotion sconosciuto: {response_type}")

            self.buffer = bytearray()
            return result

        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto InMotion incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati InMotion: {e}")

def _calculate_battery(self, voltage):
        """Calcola la percentuale della batteria per InMotion."""
        for config in INMOTION_VOLTAGE_CONFIGS.values():
        if abs(voltage - config["max_voltage"]) < 10.0:  # Tolleranza aumentata per 176V
            max_voltage = config["max_voltage"]
            min_voltage = config["min_voltage"]
            return min(max(int((voltage - min_voltage) / (max_voltage - min_voltage) * 100), 0), 100)
    return 0
def update_pedals_mode(self, mode):
        """Imposta modalità pedane (0: Commute, 1: Offroad)."""
        try:
            if mode not in [0, 1]:
                raise EUCCommandError(f"Modalità pedane non valida: {mode}. Usa 0 (Commute) o 1 (Offroad).")
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["pedals_mode"], mode, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedane: {e}")

    def set_lights(self, state):
        """Accende (1) o spegne (0) le luci."""
        try:
            if state not in [0, 1]:
                raise EUCCommandError(f"Stato luci non valido: {state}")
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["lights"], state, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando luci: {e}")

    def start_calibration(self):
        """Avvia la calibrazione del giroscopio (ipotetico, da verificare)."""
        try:
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["calibration"], 0x01, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando calibrazione: {e}")

    def set_speed_alert(self, speed):
        """Imposta allarme velocità (continuo, fino a velocità massima)."""
        try:
            if not (0 <= speed <= self.max_speed):
                raise EUCCommandError(f"Velocità non valida: {speed}. Deve essere tra 0 e {self.max_speed} km/h.")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["speed_alert"],
                                speed_value >> 8, speed_value & 0xFF, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando allarme velocità: {e}")

    def set_pedal_angle(self, angle):
        """Imposta l'angolo delle pedane (gradi, -5.0 a +5.0)."""
        try:
            if not (-5.0 <= angle <= 5.0):
                raise EUCCommandError(f"Angolo pedane non valido: {angle}. Deve essere tra -5.0 e +5.0 gradi.")
            angle_value = int(angle * 100)  # Convertito in 0.01°
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["pedal_angle"],
                                angle_value >> 8, angle_value & 0xFF, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando angolo pedane: {e}")

    def activate_horn(self):
        """Attiva il clacson tramite casse audio."""
        try:
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["horn"], 0x01, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando clacson: {e}")

    def request_serial_data(self):
        """Richiede il numero di serie dell'EUC."""
        try:
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["serial_data"], 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando dati seriali: {e}")

    def set_ride_mode(self, mode):
        """Imposta modalità di guida (0: eco, 1: normale, 2: sport, ipotetico)."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità di guida non valida: {mode}")
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["ride_mode"], mode, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità di guida: {e}")

    def set_tiltback_alert(self, speed):
        """Imposta allarme tilt-back (ipotetico)."""
        try:
            if not (0 <= speed <= self.max_speed):
                raise EUCCommandError(f"Velocità non valida: {speed}. Deve essere tra 0 e {self.max_speed} km/h.")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["tiltback_alert"],
                                speed_value >> 8, speed_value & 0xFF, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando tilt-back: {e}")

    def request_status(self):
        """Richiede informazioni sullo stato (es. versione firmware)."""
        try:
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["status"], 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando stato: {e}")

    def request_live_data(self):
        """Richiede dati live (velocità, tensione, ecc.)."""
        try:
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                INMOTION_COMMANDS["live_data"], 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando dati live: {e}")
