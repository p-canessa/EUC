# micropython/examples/scan_and_connect_veteran.py
from wheellog_euc_micropython.ble import BLEManager
from wheellog_euc_micropython.errors import (
    BLEScanError, BLEConnectionError, BLECommunicationError,
    EUCParseError, EUCCommandError
)
import time

def main():
    try:
        ble = BLEManager()
    except Exception as e:
        print(f"Errore inizializzazione BLE: {e}")
        return
    
    try:
        print("Scansione dispositivi BLE...")
        devices = ble.scan(5000)
        
        print("Dispositivi trovati:")
        for i, device in enumerate(devices):
            print(f"{i}: {device['name']} ({device['mac']}), Tipo: {device['euc_type']}")
        
        selected = devices[0]
        print(f"Connessione a {selected['name']} ({selected['mac']})...")
        
        ble.connect(selected['mac'], selected['euc_type'])
        
        try:
            ble.adapter.update_pedals_mode(1)  # Modalità media
            print("Modalità pedali aggiornata.")
            if selected['euc_type'] == "Veteran":
                ble.adapter.set_lights(1)  # Accendi luci
                print("Luci accese.")
        except EUCCommandError as e:
            print(f"Errore comando: {e}")
        
        while True:
            try:
                data = ble.read()
                if data:
                    result = ble.adapter.decode(data)
                    if result:
                        print(f"Velocità: {result['speed']} km/h, "
                              f"Batteria: {result['battery']}%, "
                              f"Distanza: {result['distance']} km, "
                              f"Temperatura: {result['temperature']}°C, "
                              f"Corrente: {result['current']}A, "
                              f"Tensione: {result['voltage']}V")
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
