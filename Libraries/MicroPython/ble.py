# micropython/ble.py
from ubluetooth import BLE, UUID
import time
from constants import EUC_NAME_FILTERS

class BLEManager:
    def __init__(self):
        self.ble = BLE()
        self.ble.active(True)
        self.connected = False
        self.devices = []
        self.current_device = None
        self.service_uuid = None
        self.char_uuid = None
        self._scan_callback = None
        self._data_buffer = bytearray()

    def scan(self, duration_ms=5000):
        """Scansiona dispositivi BLE e restituisce una lista di dispositivi rilevati."""
        self.devices = []
        self.ble.gap_scan(duration_ms, 30000, 30000)  # Scansione per 'duration_ms'
        self.ble.irq(self._irq_handler)
        time.sleep_ms(duration_ms + 100)  # Attendi fine scansione
        self.ble.gap_scan(None)  # Ferma scansione
        return self.devices

    def _irq_handler(self, event, data):
        """Gestisce eventi BLE, inclusi risultati della scansione."""
        if event == 5:  # Evento di scansione (nuovo dispositivo trovato)
            addr_type, addr, adv_type, rssi, adv_data = data
            addr = bytes(addr)  # Indirizzo MAC
            name = self._parse_adv_data(adv_data) or "Unknown"
            # Filtra dispositivi EUC in base al nome
            if any(filter_str in name for filter_str in EUC_NAME_FILTERS):
                device = {
                    "name": name,
                    "mac": ":".join(["%02X" % b for b in addr]),
                    "rssi": rssi,
                    "adv_data": adv_data
                }
                self.devices.append(device)

    def _parse_adv_data(self, adv_data):
        """Estrae il nome del dispositivo dai dati pubblicitari."""
        i = 0
        while i + 1 < len(adv_data):
            length = adv_data[i]
            if length == 0:
                break
            if adv_data[i + 1] == 0x09:  # Tipo: Nome completo
                return adv_data[i + 2:i + length + 1].decode('utf-8')
            i += length + 1
        return None

    def connect(self, mac, service_uuid, char_uuid):
        """Si connette a un dispositivo specificato dal MAC."""
        self.service_uuid = UUID(service_uuid)
        self.char_uuid = UUID(char_uuid)
        addr = bytes(int(x, 16) for x in mac.split(":"))
        self.ble.gap_connect(0, addr)
        self.current_device = mac
        time.sleep_ms(2000)  # Attendi connessione
        self.connected = True
        # Abilita notifiche sulla caratteristica
        self.ble.gattc_write(self.char_uuid, b'\x01\x00', 1)

    def read(self):
        """Legge dati dalla caratteristica BLE."""
        if self.connected:
            try:
                data = self.ble.gattc_read(self.char_uuid)
                self._data_buffer.extend(data)
                return data
            except:
                return None
        return None

    def write(self, data):
        """Scrive dati sulla caratteristica BLE."""
        if self.connected:
            self.ble.gattc_write(self.char_uuid, data)

    def disconnect(self):
        """Disconnette il dispositivo attuale."""
        if self.connected:
            self.ble.gap_disconnect()
            self.connected = False
            self.current_device = None
