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
- **Scansione BLE**: Rileva dispositivi EUC vicini e restituisce nome, MAC e RSSI.
- **Connessione**: Si connette a un dispositivo specificato tramite MAC.
- **Parsing dati**: Estrae velocità, batteria, distanza, ecc. dai pacchetti BLE.
- **Comandi**: Supporta comandi come cambio modalità pedalata.
- **Gestione errori**: Gestisce errori di scansione, connessione, comunicazione e parsing.

## API Reference

### `BLEManager`
- `scan(duration_ms=5000)`: Esegue la scansione BLE. Lancia `BLEScanError` se fallisce.
  - Restituisce lista di dizionari: `{"name": str, "mac": str, "rssi": int, "adv_data": bytes}`.
- `connect(mac, service_uuid, char_uuid)`: Si connette al dispositivo. Lancia `BLEConnectionError` se fallisce.
- `read()`: Legge dati. Lancia `BLECommunicationError` se fallisce.
- `write(data)`: Scrive dati. Lancia `BLECommunicationError` se fallisce.
- `disconnect()`: Disconnette. Lancia `BLECommunicationError` se fallisce.

### `BaseAdapter`
Classe base astratta per adattatori EUC.
- `decode(data)`: Parsa i dati ricevuti (implementato nelle sottoclassi). Lancia `EUCParseError`.
- `update_pedals_mode(mode)`: Aggiorna la modalità dei pedali. Lancia `EUCCommandError`.

### `InMotionAdapter`
Adattatore per EUC InMotion.
- `decode(data)`: Restituisce dizionario con `speed`, `battery`, `distance`. Lancia `EUCParseError` se fallisce.
- `update_pedals_mode(mode)`: Invia comando modalità (es. `0`, `1`, `2`). Lancia `EUCCommandError` se fallisce.

## Gestione Errori
La libreria definisce eccezioni personalizzate:
- `WheelLogError`: Base per tutti gli errori.
- `BLEScanError`: Errori di scansione.
- `BLEConnectionError`: Errori di connessione.
- `BLECommunicationError`: Errori di lettura/scrittura.
- `EUCParseError`: Errori di parsing dati.
- `EUCCommandError`: Errori di comandi EUC.

## Esempio
```python
from wheellog_euc_micropython.ble import BLEManager
from wheellog_euc_micropython.euc.inmotion import InMotionAdapter
from wheellog_euc_micropython.errors import (
    BLEScanError, BLEConnectionError, BLECommunicationError, EUCParseError
)
import time

ble = BLEManager()
try:
    devices = ble.scan(5000)
    print("Dispositivi trovati:")
    for i, device in enumerate(devices):
        print(f"{i}: {device['name']} ({device['mac']})")
    selected = devices[0]
    adapter = InMotionAdapter(ble)
    ble.connect(selected['mac'], adapter.service_uuid, adapter.char_uuid)
    while True:
        data = ble.read()
        if data:
            result = adapter.decode(data)
            if result:
                print(f"Velocità: {result['speed']} km/h, Batteria: {result['battery']}%")
        time.sleep_ms(100)
except (BLEScanError, BLEConnectionError, BLECommunicationError, EUCParseError) as e:
    print(f"Errore: {e}")
finally:
    ble.disconnect()
