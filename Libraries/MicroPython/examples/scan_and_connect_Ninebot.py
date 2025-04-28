# micropython/examples/scan_and_connect_Ninebot.py
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
        
        model = "V10F" if "V10" in selected['name'] else "Z10" if "Z" in selected['name'] else "One S2" if "S2" in selected['name'] else "default"
        ble.connect(selected['mac'], selected['euc_type'], model=model)
        
        if selected['euc_type'] == "InMotion":
            try:
                ble.adapter.update_pedals_mode(1)  # Offroad
                ble.adapter.set_lights(1)
                ble.adapter.set_speed_alert(30.0)
                ble.adapter.set_tiltback_alert(40.0)
                ble.adapter.set_pedal_angle(2.3)  # Aggiornato per incrementi 0.1°
                ble.adapter.activate_horn()
                ble.adapter.request_serial_data()
                ble.adapter.set_ride_mode(1)
                ble.adapter.request_status()
                ble.adapter.request_live_data()
                print("Comandi InMotion eseguiti.")
            except EUCCommandError as e:
                print(f"Errore comando InMotion: {e}")
        elif selected['euc_type'] == "Kingsong":
            try:
                ble.adapter.update_pedals_mode(1)
                ble.adapter.set_lights(1)
                ble.adapter.set_speed_alert(1)
                ble.adapter.set_speed_alert_with_speed(1, 30)
                ble.adapter.set_tiltback_alert(40)
                ble.adapter.set_pedal_angle(2.0)
                ble.adapter.activate_horn()
                ble.adapter.request_serial_data()
                ble.adapter.set_ride_mode(1)
                ble.adapter.request_status()
                print("Comandi Kingsong eseguiti.")
            except EUCCommandError as e:
                print(f"Errore comando Kingsong: {e}")
        elif selected['euc_type'] == "Gotway":
            try:
                ble.adapter.update_pedals_mode(1)
                ble.adapter.set_lights(1)
                ble.adapter.set_speed_alert(1)
                ble.adapter.set_speed_alert_with_speed(1, 40)
                ble.adapter.set_tiltback_alert(50)
                ble.adapter.set_pedal_angle(2.0)
                ble.adapter.activate_horn()
                ble.adapter.request_serial_data()
                ble.adapter.set_ride_mode(1)
                ble.adapter.request_status()
                print("Comandi Gotway eseguiti.")
            except EUCCommandError as e:
                print(f"Errore comando Gotway: {e}")
        elif selected['euc_type'] == "Ninebot":
            try:
                ble.adapter.update_pedals_mode(1)  # Hard
                ble.adapter.set_lights(1)
                ble.adapter.set_speed_alert(20.0)  # 20 km/h per S2
                ble.adapter.set_tiltback_alert(22.0)  # 22 km/h per S2
                ble.adapter.set_pedal_angle(2.0)  # Ipotetico
                ble.adapter.activate_horn()
                ble.adapter.request_serial_data()
                ble.adapter.set_ride_mode(1)  # Normale, ipotetico
                ble.adapter.request_status()
                ble.adapter.request_live_data()
                print("Comandi Ninebot eseguiti.")
            except EUCCommandError as e:
                print(f"Errore comando Ninebot: {e}")
        elif selected['euc_type'] == "Veteran":
            try:
                ble.adapter.update_pedals_mode(1)
                ble.adapter.set_lights(1)
                ble.adapter.set_speed_alert(1, 40)
                ble.adapter.set_speed_alert(2, 50)
                ble.adapter.set_speed_alert(3, 280)
                ble.adapter.set_pedal_angle(2.0)
                ble.adapter.activate_horn()
                ble.adapter.request_serial_data()
                ble.adapter.set_ride_mode(1)
                print("Comandi Veteran eseguiti.")
            except EUCCommandError as e:
                print(f"Errore comando Veteran: {e}")
        
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
