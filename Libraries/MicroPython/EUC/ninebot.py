# micropython/euc/ninebot.py
from .base_adapter import BaseAdapter
from constants import NINEBOT_SERVICE_UUID, NINEBOT_CHAR_UUID
from errors import EUCParseError, EUCCommandError

class NinebotAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = NINEBOT_SERVICE_UUID
        self.char_uuid = NINEBOT_CHAR_UUID

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
            
            # Velocità (km/h)
            speed = (self.buffer[6] << 8 | self.buffer[7]) / 100.0
            # Batteria (%)
            battery = self.buffer[8]
            # Distanza (km)
            distance = (self.buffer[12] << 24 | self.buffer[13] << 16 |
                        self.buffer[14] << 8 | self.buffer[15]) / 1000.0
            
            self.buffer = bytearray()
            self.speed = speed
            self.battery = battery
            self.distance = distance
            return {"speed": speed, "battery": battery, "distance": distance}
        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Ninebot incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Ninebot: {e}")

    def update_pedals_mode(self, mode):
        """Invia comando per cambiare modalità pedalata."""
        try:
            if mode not in [0, 1, 2]:
                raise EUCCommandError(f"Modalità pedali non valida: {mode}")
            command = bytearray([0x5A, 0xA5, 0x00, 0x00, 0x00, mode, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x00, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedali: {e}")
