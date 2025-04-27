# micropython/euc/veteran.py
from .base_adapter import BaseAdapter
from constants import VETERAN_SERVICE_UUID, VETERAN_CHAR_UUID, VETERAN_VOLTAGE_CONFIGS
from errors import EUCParseError, EUCCommandError

class VeteranAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = VETERAN_SERVICE_UUID
        self.char_uuid = VETERAN_CHAR_UUID
        self.voltage_config = None  # Determinato dinamicamente
        self.temperature = 0
        self.current = 0

    def _determine_voltage_config(self, voltage):
        """Determina la configurazione della batteria in base alla tensione."""
        for max_voltage, config in VETERAN_VOLTAGE_CONFIGS.items():
            if abs(voltage - max_voltage) < 10 or (config["min_voltage"] <= voltage <= max_voltage):
                return config
        raise EUCParseError(f"Tensione non supportata: {voltage}V")

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
            
            # Velocità (km/h)
            speed = (self.buffer[4] << 8 | self.buffer[5]) / 100.0
            # Tensione (V)
            voltage = (self.buffer[2] << 8 | self.buffer[3]) / 100.0
            # Distanza (km)
            distance = (self.buffer[10] << 24 | self.buffer[11] << 16 |
                        self.buffer[12] << 8 | self.buffer[13]) / 1000.0
            # Temperatura (°C)
            temperature = (self.buffer[14] << 8 | self.buffer[15]) / 100.0
            # Corrente (A)
            current = (self.buffer[6] << 8 | self.buffer[7]) / 100.0
            
            # Determina configurazione batteria
            if not self.voltage_config:
                self.voltage_config = self._determine_voltage_config(voltage)
            
            # Calcola percentuale batteria
            min_voltage = self.voltage_config["min_voltage"]
            max_voltage = self.voltage_config["max_voltage"]
            battery = min(max(int((voltage - min_voltage) / (max_voltage - min_voltage) * 100), 0), 100)
            
            self.buffer = bytearray()
            self.speed = speed
            self.battery = battery
            self.distance = distance
            self.temperature = temperature
            self.current = current
            
            return {
                "speed": speed,
                "battery": battery,
                "distance": distance,
                "temperature": temperature,
                "current": current,
                "voltage": voltage
            }
        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Veteran incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Veteran: {e}")

    def update_pedals_mode(self, mode):
        """Invia comando per cambiare modalità pedalata."""
        try:
            if mode not in [0, 1, 2]:  # 0: hard, 1: medium, 2: soft
                raise EUCCommandError(f"Modalità pedali non valida: {mode}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0xF1, mode, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedali: {e}")

    def set_lights(self, state):
        """Accende o spegne le luci (0: spente, 1: accese)."""
        try:
            if state not in [0, 1]:
                raise EUCCommandError(f"Stato luci non valido: {state}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0xE7, state, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando luci: {e}")
