# EUC MicroPython Library

Libreria MicroPython per controllare monocicli elettrici (EUC) tramite Bluetooth Low Energy (BLE) su ESP32. Supporta InMotion, Kingsong, Gotway/Begode, Ninebot e Veteran.

## Requisiti
- ESP32 con MicroPython (versione con supporto `ubluetooth`).
- EUC con Bluetooth abilitato.
- Strumenti per caricare codice sull'ESP32 (es. `ampy`, `rshell`).

## Installazione
1. Clona o scarica il repository.
2. Copia la cartella `micropython` nella memoria dell'ESP32 (es. `/lib`).
3. Carica gli script di esempio in `/`.

## Funzionalità
- **Scansione BLE**: Rileva dispositivi EUC (es. Veteran "LK...", Gotway "Gotway"/"EUC...", Kingsong "KS-...", InMotion "V...", Ninebot "Ninebot...").
- **Connessione**: Seleziona automaticamente l'adattatore in base al tipo EUC.
- **Parsing dati**:
  - Dati live: Velocità, batteria, distanza, temperatura, corrente, tensione.
  - Numero di serie: Stringa ASCII (es. "V10F1234567890").
  - Versione firmware: Formato "major.minor" (es. "1.2").
- **Comandi**:
  - **InMotion**: Modalità pedane (Offroad/Commute), luci, allarme velocità (continuo, 0-45 km/h per V10F), angolo pedane (±5.0°, incrementi 0.1°), clacson, dati seriali, stato, dati live, calibrazione (ipotetico), modalità di guida (ipotetico), tilt-back (ipotetico, attivato per surriscaldamento >80°C, corrente elevata, velocità massima, batteria scarica/sovraccarica).
  - **Kingsong**: Modalità pedalata, luci, allarmi acustici, clacson, dati seriali, stato, calibrazione (ipotetico), angolo pedane (ipotetico), modalità di guida (ipotetico), tilt-back (ipotetico).
  - **Gotway/Begode**: Modalità pedalata, luci, allarmi acustici, dati seriali, stato, calibrazione (ipotetico), angolo pedane (ipotetico), clacson (ipotetico), modalità di guida (ipotetico), tilt-back (ipotetico).
  - **Ninebot**: Modalità pedane (Hard/Soft), luci, allarme velocità (continuo, 0-24 km/h per S2, 0-45 km/h per Z10), angolo pedane (ipotetico, ±5.0°), clacson, dati seriali, stato, dati live, calibrazione (ipotetico), modalità di guida (ipotetico), tilt-back.
  - **Veteran**: Modalità pedalata, luci, calibrazione, allarmi velocità (discreti, 25-280 km/h), angolo pedane, clacson, dati seriali, stato, modalità di guida, tilt-back (discreto, stessi valori allarmi, batteria scarica a 75.6V per Sherman Max).
- **Gestione errori**: Gestisce errori di scansione, connessione, comunicazione e parsing.

## API Reference

### `BLEManager`
- `scan(duration_ms=5000)`: Restituisce `[{"name": str, "mac": str, "rssi": int, "euc_type": str}]`. Lancia `BLEScanError`.
- `connect(mac, euc_type, model="One S2")`: Si connette e seleziona l'adattatore. Lancia `BLEConnectionError`.
- `read()`: Legge dati. Lancia `BLECommunicationError`.
- `write(data)`: Scrive dati. Lancia `BLECommunicationError`.
- `disconnect()`: Disconnette. Lancia `BLECommunicationError`.

### `BaseAdapter`
- `decode(data)`: Parsa i dati. Restituisce `{"speed": float, "battery": int, "distance": float, "temperature": float, "current": float, "voltage": float}` per dati live, `{"serial_number": str}` per numero di serie, o `{"firmware_version": str}` per firmware. Lancia `EUCParseError`.
- `update_pedals_mode(mode)`: Imposta modalità pedane/pedalata. Lancia `EUCCommandError`.

### `InmotionAdapter`
- **Supporto tensione**: V10F (84V, max 84.0V, min 67.2V, velocità max 45 km/h).
- **Allarme velocità**: Continuo, 0-45 km/h (V10F).
- **Tilt-back**: Attivato automaticamente per surriscaldamento (>80°C), corrente elevata, velocità massima, batteria scarica/sovraccarica.
- `decode(data)`: Restituisce dati live, numero di serie (ASCII, 14 caratteri), o versione firmware (es. "1.2").
- `update_pedals_mode(mode)`: Modalità `0` (Commute), `1` (Offroad).
- `set_lights(state)`: Accende (`1`) o spegne (`0`) le luci.
- `start_calibration()`: Avvia la calibrazione (ipotetico).
- `set_speed_alert(speed)`: Imposta allarme velocità (0 a 45 km/h per V10F).
- `set_pedal_angle(angle)`: Imposta angolo pedane (-5.0 a +5.0 gradi, incrementi 0.1°).
- `activate_horn()`: Attiva il clacson tramite casse.
- `request_serial_data()`: Richiede il numero di serie.
- `set_ride_mode(mode)`: Modalità `0` (eco), `1` (normale), `2` (sport, ipotetico).
- `set_tiltback_alert(speed)`: Imposta tilt-back (0 a 45 km/h, ipotetico).
- `request_status()`: Richiede versione firmware.
- `request_live_data()`: Richiede dati live.

### `KingsongAdapter`
- `decode(data)`: Restituisce dati live, numero di serie (ASCII, 14 caratteri), o versione firmware (es. "2.1").
- `update_pedals_mode(mode)`: Modalità `0` (soft), `1` (medium), `2` (hard).
- `set_lights(state)`: Accende (`1`) o spegne (`0`) le luci.
- `start_calibration()`: Avvia la calibrazione (ipotetico).
- `set_speed_alert(level)`: Imposta livello allarme (0, 1, 2).
- `set_speed_alert_with_speed(level, speed)`: Imposta allarme con velocità.
- `set_pedal_angle(angle)`: Imposta angolo pedane (ipotetico).
- `activate_horn()`: Attiva il clacson.
- `request_serial_data()`: Richiede il numero di serie.
- `set_ride_mode(mode)`: Modalità `0` (eco), `1` (normale), `2` (sport, ipotetico).
- `set_tiltback_alert(speed)`: Imposta tilt-back (ipotetico).
- `request_status()`: Richiede versione firmware.

### `GotwayAdapter`
- `decode(data)`: Restituisce dati live, numero di serie (ASCII, 16 caratteri), o versione firmware (es. "1.5").
- `update_pedals_mode(mode)`: Modalità `0` (soft), `1` (medium), `2` (hard).
- `set_lights(state)`: Accende (`1`) o spegne (`0`) le luci.
- `start_calibration()`: Avvia la calibrazione (ipotetico).
- `set_speed_alert(level)`: Imposta livello allarme (0, 1, 2).
- `set_speed_alert_with_speed(level, speed)`: Imposta allarme con velocità.
- `set_pedal_angle(angle)`: Imposta angolo pedane (ipotetico).
- `activate_horn()`: Attiva il clacson (ipotetico).
- `request_serial_data()`: Richiede il numero di serie.
- `set_ride_mode(mode)`: Modalità `0` (eco), `1` (normale), `2` (sport, ipotetico).
- `set_tiltback_alert(speed)`: Imposta tilt-back (ipotetico).
- `request_status()`: Richiede versione firmware.

### `NinebotAdapter`
- **Supporto tensione**:
  - One S2 (63V, max 63.0V, min 50.4V, velocità max 24 km/h).
  - Z10 (72V, max 72.0V, min 57.6V, velocità max 45 km/h).
- **Allarme velocità**: Continuo, 0-24 km/h (S2), 0-45 km/h (Z10).
- **Tilt-back**: Continuo, stessi limiti di velocità.
- `decode(data)`: Restituisce dati live, numero di serie (ASCII, 14 caratteri), o versione firmware (es. "1.3").
- `update_pedals_mode(mode)`: Modalità `0` (Soft), `1` (Hard).
- `set_lights(state)`: Accende (`1`) o spegne (`0`) le luci.
- `start_calibration()`: Avvia la calibrazione (ipotetico).
- `set_speed_alert(speed)`: Imposta allarme velocità (0 a max_speed).
- `set_pedal_angle(angle)`: Imposta angolo pedane (-5.0 a +5.0 gradi, ipotetico).
- `activate_horn()`: Attiva il clacson.
- `request_serial_data()`: Richiede il numero di serie.
- `set_ride_mode(mode)`: Modalità `0` (eco), `1` (normale), `2` (sport, ipotetico).
- `set_tiltback_alert(speed)`: Imposta tilt-back (0 a max_speed).
- `request_status()`: Richiede versione firmware.
- `request_live_data()`: Richiede dati live.

### `VeteranAdapter`
- **Supporto tensione**:
  - 100.8V (24s, max 100.8V, min 75.6V, allarme 78.0V, tilt-back 75.6V, Sherman Max).
  - 126.0V (30s, max 126.0V, min 94.5V, allarme 97.5V, tilt-back 94.5V, Patton).
  - 151.2V (36s, max 151.2V, min 113.4V, allarme 117.0V, tilt-back 113.4V, Lynx/Sherman L).
- **Allarmi e tilt-back**: Discreti (25-280 km/h).
- `decode(data)`: Restituisce dati live, numero di serie (ASCII, 14 caratteri), o versione firmware (es. "2.0").
- `update_pedals_mode(mode)`: Modalità `0` (soft), `1` (medium), `2` (hard).
- `set_lights(state)`: Accende (`1`) o spegne (`0`) le luci.
- `start_calibration()`: Avvia la calibrazione.
- `set_speed_alert(level, speed)`: Imposta allarme velocità (discreto).
- `set_pedal_angle(angle)`: Imposta angolo pedane.
- `activate_horn()`: Attiva il clacson.
- `request_serial_data()`: Richiede il numero di serie.
- `set_ride_mode(mode)`: Modalità `0` (eco), `1` (normale), `2` (sport).
- `request_status()`: Richiede versione firmware.

## Gestione Errori
- `WheelLogError`: Base.
- `BLEScanError`, `BLEConnectionError`, `BLECommunicationError`, `EUCParseError`, `EUCCommandError`.

## Esempio
```python
from micropython.ble import BLEManager
from micropython.errors import (
    BLEScanError, BLEConnectionError, BLECommunicationError, EUCParseError
)
import time

ble = BLEManager()
try:
    devices = ble.scan(5000)
    print("Dispositivi trovati:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} ({device['mac']}), Tipo: {device['euc_type']}")
    selected = devices[0]
    model = "V10F" if "V10" in selected['name'] else "Z10" if "Z" in selected['name'] else "One S2" if "S2" in selected['name'] else "default"
    ble.connect(selected['mac'], selected['euc_type'], model=model)
    if selected['euc_type'] == "InMotion":
        ble.adapter.request_serial_data()
        ble.adapter.request_status()
        ble.adapter.request_live_data()
    for _ in range(10):
        data = ble.read()
        if data:
            result = ble.adapter.decode(data)
            if result:
                if "serial_number" in result:
                    print(f"Numero di serie: {result['serial_number']}")
                elif "firmware_version" in result:
                    print(f"Versione firmware: {result['firmware_version']}")
                else:
                    print(f"Velocità: {result['speed']} km/h, Batteria: {result['battery']}%")
        time.sleep_ms(100)
except (BLEScanError, BLEConnectionError, BLECommunicationError, EUCParseError) as e:
    print(f"Errore: {e}")
finally:
    ble.disconnect()