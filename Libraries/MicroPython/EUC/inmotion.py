# wheellog_euc_micropython/euc/inmotion.py
from .base_adapter import BaseAdapter
from constants import INMOTION_SERVICE_UUID, INMOTION_CHAR_UUID

class InMotionAdapter(BaseAdapter):
    def __init__(self, ble):
        super().__init__(ble)
        self.service_uuid = INMOTION_SERVICE_UUID
        self.char_uuid = INMOTION_CHAR_UUID

    def decode(self, data):
        """Parsa i dati ricevuti da un EUC InMotion."""
        self.buffer.extend(data)
        if len(self.buffer) >= 20:  # Lunghezza minima del pacchetto
            if self.buffer[0] == 0xAA and self.buffer[1] == 0x55:  # Header InMotion
                speed = (self.buffer[2] << 8 | self.buffer[3]) / 100.0
                battery = self.buffer[4]
                distance = (self.buffer[10] << 24 | self.buffer[11] << 16 |
                            self.buffer[12] << 8 | self.buffer[13]) / 1000.0
                self.buffer = bytearray()  # Reset buffer
                self.speed = speed
                self.battery = battery
                self.distance = distance
                return {"speed": speed, "battery": battery, "distance": distance}
        return None

    def update_pedals_mode(self, mode):
        """Invia comando per cambiare modalità pedalata."""
        command = bytearray([0xAA, 0x55, mode, 0x00] + [0x00] * 16)
        self.ble.write(command)
