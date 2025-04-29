from ubluetooth import BLE, UUID
import time
from constants import EUC_NAME_FILTERS, INMOTION_SERVICE_UUID, KINGSONG_SERVICE_UUID, GOTWAY_SERVICE_UUID, NINEBOT_SERVICE_UUID, VETERAN_SERVICE_UUID
from errors import BLEScanError, BLEConnectionError, BLECommunicationError
from euc.inmotion import InMotionAdapter
from euc.kingsong import KingsongAdapter
from euc.gotway import GotwayAdapter
from euc.ninebot import NinebotAdapter
from euc.veteran import VeteranAdapter

class BLEManager:
    def __init__(self):
        try:
            self.ble = BLE()
            self.ble.active(True)
        except Exception as e:
            raise BLECommunicationError(f"Errore inizializzazione BLE: {e}")
        self.connected = False
        self.devices = []
        self.current_device = None
        self.service_uuid = None
        self.char_uuid = None
        self._scan_callback = None
        self._data_buffer = bytearray()
        self._connection_timeout = 5
        self.adapter = None

    def scan(self, duration_ms=5000):
        """Scansiona dispositivi BLE e restituisce una lista di dispositivi rilevati."""
        self.devices = []
        try:
            self.ble.gap_scan(duration_ms, 30000, 30000)
            self.ble.irq(self._irq_handler)
            time.sleep_ms(duration_ms + 100)
            self.ble.gap_scan(None)
        except Exception as e:
            raise BLEScanError(f"Errore durante la scansione BLE: {e}")
        
        if not self.devices:
            raise BLEScanError("Nessun dispositivo EUC trovato durante la scansione.")
        return self.devices

    def _irq_handler(self, event, data):
        try:
            if event == 5:  # Evento di scansione
                addr_type, addr, adv_type, rssi, adv_data = data
                addr = bytes(addr)
                name = self._parse_adv_data(adv_data, 0x09) or "Unknown"
                uuids = self._parse_adv_uuids(adv_data)
                euc_type = None
                for euc_type_key, info in EUC_NAME_FILTERS.items():
                    if info["name"] in name:
                        euc_type = euc_type_key
                        break
                
                device = {
                    "name": name,
                    "mac": ":".join(["%02X" % b for b in addr]),
                    "rssi": rssi,
                    "adv_data": adv_data,
                    "euc_type": euc_type,
                    "uuids": uuids
                }
                if device not in self.devices:
                    self.devices.append(device)
            elif event == 6:
                raise BLEScanError("Errore evento scansione BLE.")
        except Exception as e:
            raise BLEScanError(f"Errore gestione evento BLE: {e}")

    def _parse_adv_data(self, adv_data, ad_type):
        """Parsa dati di advertising per il tipo specificato (es. 0x09 per nome)."""
        try:
            i = 0
            while i + 1 < len(adv_data):
                length = adv_data[i]
                if length == 0:
                    break
                if adv_data[i + 1] == ad_type:
                    return adv_data[i + 2:i + length + 1].decode('utf-8')
                i += length + 1
            return None
        except Exception as e:
            raise BLEScanError(f"Errore parsing dati pubblicitari: {e}")

    def _parse_adv_uuids(self, adv_data):
        """Parsa UUID dei servizi dai dati di advertising."""
        uuids = []
        try:
            i = 0
            while i + 1 < len(adv_data):
                length = adv_data[i]
                if length == 0:
                    break
                ad_type = adv_data[i + 1]
                if ad_type in (0x02, 0x03, 0x06, 0x07):  # UUID a 16-bit o 128-bit
                    data = adv_data[i + 2:i + length + 1]
                    if ad_type in (0x02, 0x03):  # UUID a 16-bit
                        for j in range(0, len(data), 2):
                            uuid = data[j:j+2][::-1].hex().upper()
                            uuid = f"0000{uuid}-0000-1000-8000-00805F9B34FB"
                            uuids.append(uuid)
                    elif ad_type in (0x06, 0x07):  # UUID a 128-bit
                        uuid = ""
                        for j in range(len(data) - 1, -1, -1):
                            uuid += f"{data[j]:02X}"
                        uuid = f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}".upper()
                        uuids.append(uuid)
                i += length + 1
            return uuids
        except Exception as e:
            raise BLEScanError(f"Errore parsing UUID pubblicitari: {e}")

    def select_adapter(self, euc_type):
        adapters = {
            "InMotion": InMotionAdapter,
            "Kingsong": KingsongAdapter,
            "Gotway": GotwayAdapter,
            "Ninebot": NinebotAdapter,
            "Veteran": VeteranAdapter
        }
        adapter_class = adapters.get(euc_type)
        if not adapter_class:
            raise BLEConnectionError(f"Tipo EUC non supportato: {euc_type}")
        return adapter_class(self)

    def connect(self, mac, euc_type):
        if self.connected:
            raise BLEConnectionError("Già connesso a un dispositivo. Disconnetti prima.")
        
        try:
            self.adapter = self.select_adapter(euc_type)
            self.service_uuid = UUID(self.adapter.service_uuid)
            self.char_uuid = UUID(self.adapter.char_uuid)
            addr = bytes(int(x, 16) for x in mac.split(":"))
            self.ble.gap_connect(0, addr)
            
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < self._connection_timeout:
                time.sleep_ms(100)
            
            if not self.connected:
                raise BLEConnectionError(f"Timeout connessione a {mac}")
            
            self.current_device = mac
            self.ble.gattc_write(self.char_uuid, b'\x01\x00', 1)
        except ValueError as e:
            raise BLEConnectionError(f"Formato MAC non valido: {e}")
        except Exception as e:
            raise BLEConnectionError(f"Errore connessione a {mac}: {e}")

    def read(self):
        if not self.connected:
            raise BLECommunicationError("Non connesso a nessun dispositivo.")
        
        try:
            data = self.ble.gattc_read(self.char_uuid)
            if data:
                self._data_buffer.extend(data)
                return data
            return None
        except Exception as e:
            self.disconnect()
            raise BLECommunicationError(f"Errore lettura dati BLE: {e}")

    def write(self, data):
        if not self.connected:
            raise BLECommunicationError("Non connesso a nessun dispositivo.")
        
        try:
            self.ble.gattc_write(self.char_uuid, data)
        except Exception as e:
            self.disconnect()
            raise BLECommunicationError(f"Errore scrittura dati BLE: {e}")

    def disconnect(self):
        try:
            if self.connected:
                self.ble.gap_disconnect()
                self.connected = False
                self.current_device = None
                self._data_buffer = bytearray()
                self.adapter = None
        except Exception as e:
            raise BLECommunicationError(f"Errore disconnessione: {e}")
