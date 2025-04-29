# /lib/ble.py
import ubluetooth
import time
import ure
from constants import EUC_NAME_FILTERS, EUC_BRANDS, GOTWAY_SERVICE_UUID, INMOTION_SERVICE_UUID
from errors import BLEScanError, BLEConnectionError, BLECommunicationError

# Costanti BLE
_IRQ_SCAN_RESULT = 5
V10F_MAC = "f8:33:31:dd:5c:32"
# ALTERNATIVE_INMOTION_UUID = "0000FFF0-0000-1000-8000-00805F9B34FB"

class BLEManager:
    def __init__(self):
        try:
            self.ble = ubluetooth.BLE()
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
        self._seen_macs = {}

    def scan(self, duration_ms=10000):
        self.devices = []
        self._seen_macs = {}
        try:
            self.ble.gap_scan(duration_ms, 30000, 30000, True)
            self.ble.irq(self._irq_handler)
            time.sleep_ms(duration_ms + 100)
            self.ble.gap_scan(None)
        except Exception as e:
            raise BLEScanError(f"Errore durante la scansione BLE: {e}")
        return self.devices

    def _irq_handler(self, event, data):
        if event == _IRQ_SCAN_RESULT:
            addr_type, addr, adv_type, rssi, adv_data = data
            mac = ':'.join(['%02x' % b for b in addr]).lower()
            name = ''
            uuids = []
            
            # Estrai nome e UUID
            i = 0
            while i < len(adv_data):
                if i + 1 >= len(adv_data):
                    break
                length = adv_data[i]
                if length == 0 or i + length >= len(adv_data):
                    break
                ad_type = adv_data[i + 1]
                
                if ad_type in (0x08, 0x09):
                    try:
                        name_bytes = bytes(adv_data[i + 2:i + length + 1])
                        name = name_bytes.decode('utf-8', 'ignore')
                    except Exception:
                        pass  # Ignora errori di decodifica silenziosamente
                
                elif ad_type in (0x02, 0x03, 0x06, 0x07):
                    try:
                        uuid = self._parse_uuid(adv_data[i + 2:i + length + 1], ad_type)
                        if uuid:
                            uuids.append(uuid)
                    except Exception:
                        pass  # Ignora errori di parsing UUID silenziosamente
                
                i += length + 1
            
            # Scarta dispositivi senza nome e senza UUID Gotway
            gotway_uuids = [GOTWAY_SERVICE_UUID]
            if not name and not any(uuid in gotway_uuids for uuid in uuids):
                return
            
            # Deduplicazione
            update_device = False
            existing_euc_type = None
            if mac in self._seen_macs:
                existing_device = self._seen_macs[mac]
                existing_euc_type = existing_device.get('euc_type')
                if name and not existing_device['name']:
                    self._seen_macs[mac] = {'name': name, 'rssi': rssi, 'adv_data': adv_data, 'uuids': uuids, 'euc_type': existing_euc_type}
                    update_device = True
                elif rssi > existing_device['rssi'] and bool(name) == bool(existing_device['name']):
                    self._seen_macs[mac] = {'name': name, 'rssi': rssi, 'adv_data': adv_data, 'uuids': uuids, 'euc_type': existing_euc_type}
                    update_device = False
            else:
                self._seen_macs[mac] = {'name': name, 'rssi': rssi, 'adv_data': adv_data, 'uuids': uuids, 'euc_type': None}
                update_device = True
            
            if name:
                print(f"Found device: Name={name}, MAC={mac}, RSSI={rssi}")
            
            # Identifica il tipo EUC
            euc_type = existing_euc_type
            possible_brands = []
            matched_by_regex = False
            if name and not euc_type:
                for brand, filter_info in sorted(EUC_NAME_FILTERS.items(), key=lambda x: x[1].get('priority', 99)):
                    pattern = filter_info.get('name')
                    if not pattern or brand == 'Gotway':
                        continue
                    try:
                        match = ure.match(pattern, name)
                        if match:
                            euc_type = brand
                            matched_by_regex = True
                            break
                        if ure.search(pattern, name):
                            possible_brands.append(brand)
                    except Exception:
                        pass  # Ignora errori regex silenziosamente
            
            # Verifica UUID per Gotway solo se non identificato tramite regex
            if not matched_by_regex:
                if any(uuid in gotway_uuids for uuid in uuids):
                    euc_type = 'Gotway'
                elif not euc_type:
                    euc_type = 'PossibleBegode'
            
            # Aggiorna euc_type in _seen_macs
            self._seen_macs[mac]['euc_type'] = euc_type
            
            # Aggiungi o aggiorna dispositivo
            device = {
                'name': name,
                'euc_type': euc_type,
                'adv_data': adv_data,
                'uuids': uuids,
                'mac': mac,
                'rssi': rssi,
                'possible_brands': possible_brands
            }
            
            if update_device:
                self.devices = [d for d in self.devices if d['mac'] != mac]
                self.devices.append(device)


    def _parse_uuid(self, data, ad_type):
        try:
            if ad_type in (0x02, 0x03):
                uuid_bytes = data[0:2]
                uuid = ''.join(['%02x' % b for b in uuid_bytes]).upper()
                return f"0000{uuid}-0000-1000-8000-00805F9B34FB"
            elif ad_type in (0x06, 0x07):
                uuid = ''.join(['%02X' % b for b in data[::-1]]).upper()
                return f"{uuid[0:8]}-{uuid[8:12]}-{uuid[12:16]}-{uuid[16:20]}-{uuid[20:32]}"
            return None
        except Exception:
            return None

    def select_adapter(self, euc_type, model="V10F"):
        if euc_type == 'PossibleBegode':
            euc_type = 'Gotway'
        try:
            adapters = {
                "InMotion": {
                    "module": "EUC.inmotion",
                    "class": "InmotionAdapter",
                    "args": {"model": model}
                },
                "Kingsong": {
                    "module": "EUC.kingsong",
                    "class": "KingsongAdapter",
                    "args": {}
                },
                "Gotway": {
                    "module": "EUC.gotway",
                    "class": "GotwayAdapter",
                    "args": {}
                },
                "Ninebot": {
                    "module": "EUC.ninebot",
                    "class": "NinebotAdapter",
                    "args": {"model": model}
                },
                "Veteran": {
                    "module": "EUC.veteran",
                    "class": "VeteranAdapter",
                    "args": {}
                }
            }
            adapter_info = adapters.get(euc_type)
            if not adapter_info:
                raise BLEConnectionError(f"Tipo EUC non supportato: {euc_type}")
            
            module = __import__(adapter_info["module"], fromlist=[adapter_info["class"]])
            adapter_class = getattr(module, adapter_info["class"])
            
            return adapter_class(self.ble, **adapter_info["args"])
        except Exception as e:
            raise BLEConnectionError(f"Errore selezione adattatore: {e}")

    def connect(self, mac, euc_type, model="V10F"):
        if self.connected:
            raise BLEConnectionError("Già connesso a un dispositivo.")
        
        try:
            if euc_type == 'PossibleBegode':
                for device in self.devices:
                    if device['mac'] == mac:
                        uuids = self._parse_adv_uuids(device['adv_data'])
                        if GOTWAY_SERVICE_UUID not in uuids:
                            raise BLEConnectionError(f"Dispositivo {mac} non è un Begode valido")
                        euc_type = 'Gotway'
                        break
            
            self.adapter = self.select_adapter(euc_type, model)
            self.service_uuid = ubluetooth.UUID(self.adapter.service_uuid)
            self.char_uuid = ubluetooth.UUID(self.adapter.write_uuid)
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
                return self.adapter.decode(data)
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