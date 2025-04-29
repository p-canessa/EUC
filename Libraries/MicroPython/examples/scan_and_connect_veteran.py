# micropython/examples/scan_and_connect_veteran.py
from micropython.ble import BLEManager
from micropython.errors import (
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
        
        if selected['euc_type'] == "Veteran":
            try:
                # Configura modalità pedalata
                ble.adapter.update_pedals_mode(1)  # Media
                print("Modalità pedali impostata su media.")
                
                # Accendi luci
                ble.adapter.set_lights(1)
                print("Luci accese.")
                
                # Imposta allarmi velocità
                ble.adapter.set_speed_alert(1, 40)  # Allarme 1 a 40 km/h
                ble.adapter.set_speed_alert(2, 50)  # Allarme 2 a 50 km/h
                ble.adapter.set_speed_alert(3, 280)  # Allarme 3 disattivato
                print("Allarmi velocità impostati: 40 km/h, 50 km/h, disattivato.")
                
                # Regola angolo pedane
                ble.adapter.set_pedal_angle(2.0)  # +2°
                print("Angolo pedane impostato a +2°.")
                
                # Attiva clacson
                ble.adapter.activate_horn()
                print("Clacson attivato.")
                
                # Richiedi dati seriali
                ble.adapter.request_serial_data()
                print("Richiesti dati seriali.")
                
                # Imposta modalità di guida
                ble.adapter.set_ride_mode(1)  # Normale
                print("Modalità di guida impostata su normale.")
                
                # Nota: Non eseguo la calibrazione automaticamente per sicurezza
                # ble.adapter.start_calibration()
                # print("Calibrazione avviata.")
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
