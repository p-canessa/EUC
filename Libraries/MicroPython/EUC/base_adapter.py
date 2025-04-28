# micropython/euc/base_adapter.py
from .inmotion import InmotionAdapter
from .kingsong import KingsongAdapter
from .gotway import GotwayAdapter
from .ninebot import NinebotAdapter
from .veteran import VeteranAdapter
from constants import EUC_NAME_FILTERS
from errors import EUCAdapterError

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

def select_adapter(ble, euc_type, model="One S2"):
    """Seleziona l'adattatore in base al tipo di EUC."""
    try:
        if euc_type == "InMotion":
            return InmotionAdapter(ble, model=model)
        elif euc_type == "Kingsong":
            return KingsongAdapter(ble)
        elif euc_type == "Gotway":
            return GotwayAdapter(ble)
        elif euc_type == "Ninebot":
            return NinebotAdapter(ble, model=model)
        elif euc_type == "Veteran":
            return VeteranAdapter(ble)
        else:
            raise EUCAdapterError(f"Tipo EUC non supportato: {euc_type}")
    except Exception as e:
        raise EUCAdapterError(f"Errore selezione adattatore: {e}")
