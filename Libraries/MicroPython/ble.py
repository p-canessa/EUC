# micropython/ble.py
from ubluetooth import BLE, UUID
import time
from constants import EUC_NAME_FILTERS
from errors import BLEScanError, BLEConnectionError, BLECommunicationError

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
        self._connection_timeout = 5  # Timeout connessione in secondi

    def scan(self, duration_ms=5000):
        """Scansiona dispositivi BLE e restituisce una lista di dispositivi rilevati."""
        self.devices = []
        try:
            self.ble.gap_scan(duration_ms, 30000, 30000)
            self.ble.irq(self._irq_handler)
            time.sleep_ms(duration_ms + 100)
            self.ble.gap_scan(None)  # Ferma scansione
        except Exception as e:
            raise BLEScanError(f"Errore durante la scansione BLE: {e}")
        
        if not self.devices:
            raise BLEScanError("Nessun dispositivo EUC trovato durante la scansione.")
        return self.devices

    def _irq_handler(self, event, data):
        """Gestisce eventi BLE."""
        try:
            if event == 5:  # Evento di scansione
                addr_type, addr, adv_type, rssi, adv_data = data
                addr = bytes(addr)
                name = self._parse_adv_data(adv_data) or "Unknown"
                if any(filter_str in name for filter_str in EUC_NAME_FILTERS):
                    device = {
                        "name": name,
                        "mac": ":".join(["%02X" % b for b in addr]),
                        "rssi": rssi,
                        "adv_data": adv_data
                    }
                    if device not in self.devices:  # Evita duplicati
                        self.devices.append(device)
            elif event == 6:  # Errore scansione
                raise BLEScanError("Errore evento scansione BLE.")
        except Exception as e:
            raise BLEScanError(f"Errore gestione evento BLE: {e}")

    def _parse_adv_data(self, adv_data):
        """Estrae il nome del dispositivo dai dati pubblicitari."""
        try:
            i = 0
            while i + 1 < len(adv_data):
                length = adv_data[i]
                if length == 0:
                    break
                if adv_data[i + 1] == 0x09:  # Tipo: Nome completo
                    return adv_data[i + 2:i + length + 1].decode('utf-8')
                i += length + 1
            return None
        except Exception as e:
            raise BLEScanError(f"Errore parsing dati pubblicitari: {e}")

    def connect(self, mac, service_uuid, char_uuid):
        """Si connette a un dispositivo specificato dal MAC."""
        if self.connected:
            raise BLEConnectionError("Già connesso a un dispositivo. Disconnetti prima.")
        
        try:
            self.service_uuid = UUID(service_uuid)
            self.char_uuid = UUID(char_uuid)
            addr = bytes(int(x, 16) for x in mac.split(":"))
            self.ble.gap_connect(0, addr)
            
            # Attendi connessione con timeout
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < self._connection_timeout:
                time.sleep_ms(100)
            
            if not self.connected:
                raise BLEConnectionError(f"Timeout connessione a {mac}")
            
            self.current_device = mac
            # Abilita notifiche sulla caratteristica
            self.ble.gattc_write(self.char_uuid, b'\x01\x00', 1)
        except ValueError as e:
            raise BLEConnectionError(f"Formato MAC non valido: {e}")
        except Exception as e:
            raise BLEConnectionError(f"Errore connessione a {mac}: {e}")

    def read(self):
        """Legge dati dalla caratteristica BLE."""
        if not self.connected:
            raise BLECommunicationError("Non connesso a nessun dispositivo.")
        
        try:
            data = self.ble.gattc_read(self.char_uuid)
            if data:
                self._data_buffer.extend(data)
                return data
            return None
        except Exception as e:
            self.disconnect()  # Disconnetti in caso di errore critico
            raise BLECommunicationError(f"Errore lettura dati BLE: {e}")

    def write(self, data):
        """Scrive dati sulla caratteristica BLE."""
        if not self.connected:
            raise BLECommunicationError("Non connesso a nessun dispositivo.")
        
        try:
            self.ble.gattc_write(self.char_uuid, data)
        except Exception as e:
            self.disconnect()
            raise BLECommunicationError(f"Errore scrittura dati BLE: {e}")

    def disconnect(self):
        """Disconnette il dispositivo attuale."""
        try:
            if self.connected:
                self.ble.gap_disconnect()
                self.connected = False
                self.current_device = None
                self._data_buffer = bytearray()
        except Exception as e:
            raise BLECommunicationError(f"Errore disconnessione: {e}")
