# wheellog_euc_micropython/examples/scan_and_connect.py
from wheellog_euc_micropython.ble import BLEManager
from wheellog_euc_micropython.euc.inmotion import InMotionAdapter
import time

def main():
    # Inizializza BLE
    ble = BLEManager()
    
    # Esegui scansione per 5 secondi
    print("Scansione dispositivi BLE...")
    devices = ble.scan(5000)
    
    # Mostra dispositivi trovati
    if not devices:
        print("Nessun dispositivo trovato.")
        return
    
    print("Dispositivi trovati:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} ({device['mac']}), RSSI: {device['rssi']}")
    
    # Seleziona un dispositivo (es. primo dispositivo)
    selected = devices[0]
    print(f"Connessione a {selected['name']} ({selected['mac']})...")
    
    # Inizializza adattatore InMotion
    adapter = InMotionAdapter(ble)
    
    # Connettiti al dispositivo
    ble.connect(selected['mac'], adapter.service_uuid, adapter.char_uuid)
    
    # Leggi dati in loop
    while True:
        data = ble.read()
        if data:
            result = adapter.decode(data)
            if result:
                print(f"Velocità: {result['speed']} km/h, "
                      f"Batteria: {result['battery']}%, "
                      f"Distanza: {result['distance']} km")
        time.sleep_ms(100)

if __name__ == "__main__":
    main()
