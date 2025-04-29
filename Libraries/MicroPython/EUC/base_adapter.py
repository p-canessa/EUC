# micropython/euc/base_adapter.py
class BaseAdapter:
    def __init__(self, ble):
        self.ble = ble
        self.speed = 0
        self.battery = 0
        self.distance = 0
        self.buffer = bytearray()
    
    def _check_buffer_size(self):
        if len(self.buffer) > 100:
            self.buffer = bytearray()
    
    def decode(self, data):
        raise NotImplementedError("Il metodo decode deve essere implementato.")

    def get_serial_number(self):
        raise NotImplementedError("Il metodo get_serial_number deve essere implementato.")

    def get_firmware_version(self):
        raise NotImplementedError("Il metodo get_firmware_version deve essere implementato.")

    def get_live_data(self):
        raise NotImplementedError("Il metodo get_live_data deve essere implementato.")