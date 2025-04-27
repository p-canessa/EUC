# EUC MicroPython Library

Libreria MicroPython per controllare monocicli elettrici (EUC) tramite Bluetooth Low Energy (BLE) su ESP32. Supporta InMotion, Kingsong, Gotway, Ninebot e Veteran.

## Requisiti
- ESP32 con MicroPython (versione con supporto `ubluetooth`).
- EUC con Bluetooth abilitato.
- Strumenti per caricare codice sull'ESP32 (es. `ampy`, `rshell`).

## Installazione
1. Clona o scarica il repository.
2. Copia la cartella `wheellog_euc_micropython` nella memoria dell'ESP32 (es. `/lib`).
3. Carica gli script di esempio in `/`.

## Funzionalità
- **Scansione BLE**: Rileva dispositivi EUC (es. Veteran con nomi "LK...").
- **Connessione**: Seleziona automaticamente l'adattatore in base al tipo EUC.
- **Parsing dati**: Estrae velocità, batteria, distanza, temperatura, corrente, tensione.
- **Comandi**: Supporta modalità pedalata, accensione luci (per Veteran), ecc.
- **Gestione errori**: Gestisce errori di scansione, connessione, comunicazione e parsing.

## API Reference

### `BLEManager`
- `scan(duration_ms=5000)`: Restituisce `[{"name": str, "mac": str, "rssi": int, "euc_type": str}]`. Lancia `BLEScanError`.
- `connect(mac, euc_type)`: Si connette e seleziona l'adattatore. Lancia `BLEConnectionError`.
- `read()`: Legge dati. Lanca `BLECommunicationError`.
- `write(data)`: Scrive dati. Lancia `BLECommunicationError`.
- `disconnect()`: Disconnette. Lancia `BLECommunicationError`.

### `BaseAdapter`
- `decode(data)`: Parsa i dati. Lancia `EUCParseError`.
- `update_pedals_mode(mode)`: Modalità `0` (hard), `1` (medium), `2` (soft). Lancia `EUCCommandError`.

### `VeteranAdapter`
- **Supporto tensione**: Gestisce 100.8V (Sherman, Sherman Max, Sherman S, Abrams), 126V (Patton), 151.2V (Lynx, Sherman L).
- `decode(data)`: Restituisce `{"speed": float, "battery": int, "distance": float, "temperature": float, "current": float, "voltage": float}`.
- `update_pedals_mode(mode)`: Imposta modalità pedalata.
- `set_lights(state)`: Accende (`1`) o spegne (`0`) le luci.

## Gestione Errori
- `WheelLogError`: Base.
- `BLEScanError`, `BLEConnectionError`, `BLECommunicationError`, `EUCParseError`, `EUCCommandError`.

## Esempio
```python
from wheellog_euc_micropython.ble import BLEManager
from wheellog_euc_micropython.errors import (
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
    ble.connect(selected['mac'], selected['euc_type'])
    ble.adapter.set_lights(1)  # Accendi luci (Veteran)
    while True:
        data = ble.read()
        if data:
            result = ble.adapter.decode(data)
            if result:
                print(f"Velocità: {result['speed']} km/h, Batteria: {result['battery']}%")
        time.sleep_ms(100)
except (BLEScanError, BLEConnectionError, BLECommunicationError, EUCParseError) as e:
    print(f"Errore: {e}")
finally:
    ble.disconnect()
