# wheellog_euc_micropython/euc/gotway.py
from .base_adapter import BaseAdapter
from constants import GOTWAY_SERVICE_UUID, GOTWAY_CHAR_UUID
from errors import EUCParseError, EUCCommandError

class GotwayAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = GOTWAY_SERVICE_UUID
        self.char_uuid = GOTWAY_CHAR_UUID

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC Gotway."""
        try:
            self._check_buffer_size()
            self.buffer.extend(data)
            if len(self.buffer) < 20:
                return None
            if self.buffer[0] != 0x55 or self.buffer[1] != 0xAA:
                self.buffer = bytearray()
                raise EUCParseError("Header pacchetto Gotway non valido.")
            
            # Velocità (km/h)
            speed = (self.buffer[4] << 8 | self.buffer[5]) / 100.0
            # Batteria (%)
            voltage = (self.buffer[2] << 8 | self.buffer[3]) / 100.0
            battery = min(max(int((voltage - 50.0) / (67.2 - 50.0) * 100), 0), 100)
            # Distanza (km)
            distance = (self.buffer[10] << 24 | self.buffer[11] << 16 |
                        self.buffer[12] << 8 | self.buffer[13]) / 1000.0
            
            self.buffer = bytearray()
            self.speed = speed
            self.battery = battery
            self.distance = distance
            return {"speed": speed, "battery": battery, "distance": distance}
        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Gotway incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Gotway: {e}")

    def update_pedals_mode(self, mode):
        """Invia comando per cambiare modalità pedalata."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità pedali non valida: {mode}")
            command = bytearray([0x55, 0xAA, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0xF1, mode, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedali: {e}")
