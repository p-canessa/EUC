# micropython/euc/kingsong.py
from .base_adapter import BaseAdapter
from constants import KINGSONG_SERVICE_UUID, KINGSONG_CHAR_UUID
from errors import EUCParseError, EUCCommandError

class KingsongAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = KINGSONG_SERVICE_UUID
        self.char_uuid = KINGSONG_CHAR_UUID

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC Kingsong."""
        try:
            self._check_buffer_size()
            self.buffer.extend(data)
            if len(self.buffer) < 20:
                return None
            if self.buffer[0] != 0xAA or self.buffer[1] != 0x55:
                self.buffer = bytearray()
                raise EUCParseError("Header pacchetto Kingsong non valido.")
            
            # Velocità (km/h), codificata in 0.1 km/h
            speed = (self.buffer[2] << 8 | self.buffer[3]) / 10.0
            # Batteria (%), calcolata da tensione
            voltage = (self.buffer[4] << 8 | self.buffer[5]) / 100.0
            battery = min(max(int((voltage - 50.0) / (67.2 - 50.0) * 100), 0), 100)
            # Distanza (km)
            distance = (self.buffer[6] << 24 | self.buffer[7] << 16 |
                        self.buffer[8] << 8 |)";
            return {
                "speed": speed,
                "battery": battery,
                "distance": distance
            }
        except IndexError:
            self.buffer = bytearray()
            raise EUCParseError("Pacchetto Kingsong incompleto o corrotto.")
        except Exception as e:
            self.buffer = bytearray()
            raise EUCParseError(f"Errore parsing dati Kingsong: {e}")

    def update_pedals_mode(self, mode):
        """Invia comando per cambiare modalità pedalata."""
        try:
            if mode not in [0, 1, 2]:  # 0: hard, 1: medium, 2: soft
                raise EUCCommandError(f"Modalità pedali non valida: {mode}")
            command = bytearray([0xAA, 0x55, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0x87, mode, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                0xE0, 0x00, 0x00, 0x00])
            self.ble.write(command)
        except Exception as e:
            raise EUCCommandError(f"Errore invio comando modalità pedali: {e}")
