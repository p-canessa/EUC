# micropython/euc/base_adapter.py
from errors import EUCParseError, EUCCommandError

class BaseAdapter:
    def __init__(self, ble):
        self.ble = ble
        self.buffer = bytearray()
        self.speed = 0
        self.battery = 0
        self.distance = 0
        self.max_buffer_size = 1024  # Limite per evitare overflow

    def decode(self, data):
        """Metodo astratto per parsare i dati ricevuti."""
        raise NotImplementedError

    def update_pedals_mode(self, mode):
        """Metodo astratto per aggiornare la modalità dei pedali."""
        raise NotImplementedError

    def _check_buffer_size(self):
        """Controlla se il buffer supera il limite massimo."""
        if len(self.buffer) > self.max_buffer_size:
            self.buffer = bytearray()
            raise EUCParseError("Buffer overflow: dati ricevuti troppo grandi.")
