# micropython/examples/scan_and_connect.py
from wheellog_euc_micropython.ble import BLEManager
from wheellog_euc_micropython.euc.inmotion import InMotionAdapter
from wheellog_euc_micropython.errors import (
    BLEScanError, BLEConnectionError, BLECommunicationError,
    EUCParseError, EUCCommandError
)
import time

def main():
    # Inizializza BLE
    try:
        ble = BLEManager()
    except Exception as e:
        print(f"Errore inizializzazione BLE: {e}")
        return
    
    # Esegui scansione
    try:
        print("Scansione dispositivi BLE...")
        devices = ble.scan(5000)
        
        # Mostra dispositivi trovati
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
        
        # Cambia modalità pedali (esempio)
        try:
            adapter.update_pedals_mode(1)  # Modalità morbida
            print("Modalità pedali aggiornata.")
        except EUCCommandError as e:
            print(f"Errore comando modalità pedali: {e}")
        
        # Leggi dati in loop
        while True:
            try:
                data = ble.read()
                if data:
                    result = adapter.decode(data)
                    if result:
                        print(f"Velocità: {result['speed']} km/h, "
                              f"Batteria: {result['battery']}%, "
                              f"Distanza: {result['distance']} km")
            except (BLECommunicationError, EUCParseError) as e:
                print(f"Errore comunicazione/parsing: {e}")
                break
            except KeyboardInterrupt:
                print("Interruzione manuale.")
                break
            time.sleep_ms(100)
    
    except BLEScanError as e:
        print(f"Errore scansione: {e}")
    except BLEConnectionError as e:
        print(f"Errore connessione: {e}")
    finally:
        try:
            ble.disconnect()
            print("Disconnesso.")
        except Exception as e:
            print(f"Errore disconnessione: {e}")

if __name__ == "__main__":
    main()
