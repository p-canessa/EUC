# wheellog_euc_micropython/euc/base_adapter.py
class BaseAdapter:
    def __init__(self, ble):
        self.ble = ble
        self.buffer = bytearray()
        self.speed = 0
        self.battery = 0
        self.distance = 0

    def decode(self, data):
        """Metodo astratto per parsare i dati ricevuti."""
        raise NotImplementedError

    def update_pedals_mode(self, mode):
        """Metodo astratto per aggiornare la modalità dei pedali."""
        raise NotImplementedError
