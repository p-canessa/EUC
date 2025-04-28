# micropython/euc/gotway.py
from .base_adapter import BaseAdapter
from constants import GOTWAY_SERVICE_UUID, GOTWAY_CHAR_UUID, GOTWAY_COMMANDS, RESPONSE_TYPES
from errors import EUCParseError, EUCCommandError

class GotwayAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = GOTWAY_SERVICE_UUID
        self.char_uuid = GOTWAY_CHAR_UUID
        self.temperature = 0
        self.current = 0
        self.serial_number = None
        self.firmware_version = None

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC Gotway/Begode."""
        try:
            self._check_buffer_size()
            self.buffer.extend(data)
            if len(self.buffer) < 20:
                return None
            if self.buffer[0] != 0x55 or self.buffer[1] != 0xAA:
                self.buffer = bytearray()
                raise EUCParseError("Header pacchetto Gotway non valido.")
            
            response_type = self.buffer[16]
            result = {}

            if response_type == RESPONSE_TYPES["Gotway"]["live_data"]:  # Dati live
                voltage = (self.buffer[2] << 8 | self.buffer[3]) / 10.0
                speed = ((self.buffer[4] << 8 | self.buffer[5]) / 10.0)
                if speed > 3276.7:
                    speed -= 6553.6
                distance = (self.buffer[6] << 24 | self.buffer[7] << 16 |
                           self.buffer[8] << 8 | self.buffer[9]) / 1000.0
                current = ((self.buffer[10] << 8 | self.buffer[11]) / 10.0)
                if current > 3276.7:
                    current -= 6553.6
                temperature = (self.buffer[12] << 8 | self.buffer[13]) / 10.0
                battery = self._calculate_battery(voltage)
                
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

            elif response_type == RESPONSE_TYPES["Gotway"]["serial_data"]:  # Numero di serie
                serial = "".join(chr(b) for b in self.buffer[2:18] if b != 0)
                self.serial_number = serial
                result = {"serial_number": serial}

            elif response_type == RESPONSE_TYPES["Gotway"]["firmware"]:  # Firmware
                major = self.buffer[2]
                minor = self.buffer[3]
                firmware = f"{major}.{minor}"
                self.firmware_version = firmware
                result = {"firmware_version": firmware}

            else:
                raise EUCParseError(f"Tipo di risposta Gotway sconosciuto: {response_type}")

            self.buffer = bytearray()
            return result

        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Gotway incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Gotway: {e}")

    def _calculate_battery(self, voltage):
        """Calcola la percentuale della batteria per Gotway (ipotetico)."""
        for config in BEGODE_VOLTAGE_CONFIGS.values():
        if abs(voltage - config["max_voltage"]) < 10.0:  # Tolleranza aumentata per 176V
            max_voltage = config["max_voltage"]
            min_voltage = config["min_voltage"]
            return min(max(int((voltage - min_voltage) / (max_voltage - min_voltage) * 100), 0), 100)
    return 0

    def update_pedals_mode(self, mode):
        """Imposta modalità pedalata (0: hard, 1: medium, 2: soft)."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità pedali non valida: {mode}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["pedals_mode"], mode, 0x00, 0x00,
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
                                GOTWAY_COMMANDS["lights"], state, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando luci: {e}")

    def start_calibration(self):
        """Avvia la calibrazione del giroscopio (ipotetico, da verificare)."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["calibration"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando calibrazione: {e}")

    def set_speed_alert(self, level):
        """Imposta allarme acustico (0: disattivato, 1: primo livello, 2: secondo livello)."""
        try:
            if level not in GOTWAY_ALERT_LEVELS:
                valid_levels = ", ".join(map(str, GOTWAY_ALERT_LEVELS))
                raise EUCCommandError(f"Livello allarme non valido: {level}. Valori consentiti: {valid_levels}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["speed_alert"], level, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando allarme velocità: {e}")

    def set_speed_alert_with_speed(self, level, speed):
        """Imposta allarme velocità con soglia specifica (ipotetico, da verificare)."""
        try:
            if level not in [1, 2, 3]:
                raise EUCCommandError(f"Livello allarme non valido: {level}")
            if speed not in GOTWAY_SPEED_LIMITS:
                valid_speeds = ", ".join(map(str, GOTWAY_SPEED_LIMITS))
                raise EUCCommandError(f"Velocità non valida: {speed}. Valori consentiti: {valid_speeds}")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["speed_alert"], level, 
                                speed_value >> 8, speed_value & 0xFF,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando allarme velocità con soglia: {e}")

    def set_pedal_angle(self, angle):
        """Imposta l'angolo delle pedane (gradi, -5.0 a +5.0, ipotetico)."""
        try:
            if not (-5.0 <= angle <= 5.0):
                raise EUCCommandError(f"Angolo pedane non valido: {angle}")
            angle_value = int(angle * 100)  # Convertito in 0.01°
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["pedal_angle"], 
                                angle_value >> 8, angle_value & 0xFF, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando angolo pedane: {e}")

    def activate_horn(self):
        """Attiva il clacson (ipotetico, da verificare)."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["horn"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando clacson: {e}")

    def request_serial_data(self):
        """Richiede il numero di serie dell'EUC."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["serial_data"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando dati seriali: {e}")

    def set_ride_mode(self, mode):
        """Imposta modalità di guida (0: eco, 1: normale, 2: sport, ipotetico)."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità di guida non valida: {mode}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["ride_mode"], mode, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità di guida: {e}")

    def set_tiltback_alert(self, speed):
        """Imposta allarme tilt-back (ipotetico, da verificare)."""
        try:
            if speed not in GOTWAY_SPEED_LIMITS:
                valid_speeds = ", ".join(map(str, GOTWAY_SPEED_LIMITS))
                raise EUCCommandError(f"Velocità non valida: {speed}. Valori consentiti: {valid_speeds}")
            speed_value = int(speed * 100)  # Convertito in 0.01 km/h
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["tiltback_alert"], 
                                speed_value >> 8, speed_value & 0xFF, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando tilt-back: {e}")

    def request_status(self):
        """Richiede informazioni sullo stato (es. versione firmware)."""
        try:
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                GOTWAY_COMMANDS["status"], 0x01, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando stato: {e}")
