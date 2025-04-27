# EUC MicroPython Library

Libreria MicroPython per controllare monocicli elettrici (EUC) tramite Bluetooth Low Energy (BLE) su ESP32. Supporta InMotion, Kingsong, Gotway, Ninebot e Veteran.

## Requisiti
- ESP32 con MicroPython (versione con supporto `ubluetooth`).
- EUC con Bluetooth abilitato.
- Strumenti per caricare codice sull'ESP32 (es. `ampy`, `rshell`).

## Installazione
1. Clona o scarica il repository.
2. Copia la cartella `micropython` nella memoria dell'ESP32 (es. `/lib`).
3. Carica gli script di esempio in `/`.

## Funzionalità
- **Scansione BLE**: Rileva dispositivi EUC vicini e restituisce nome, MAC e RSSI.
- **Connessione**: Si connette a un dispositivo specificato tramite MAC.
- **Parsing dati**: Estrae velocità, batteria, distanza, ecc. dai pacchetti BLE.
- **Comandi**: Supporta comandi come cambio modalità pedalata.

## API Reference

### `BLEManager`
- `scan(duration_ms=5000)`: Esegue la scansione BLE per `duration_ms` millisecondi. Restituisce una lista di dizionari con:
  - `name`: Nome del dispositivo.
  - `mac`: Indirizzo MAC.
  - `rssi`: Intensità del segnale.
  - `adv_data`: Dati pubblicitari grezzi.
- `connect(mac, service_uuid, char_uuid)`: Si connette al dispositivo con indirizzo MAC specificato.
- `read()`: Legge dati dalla caratteristica BLE.
- `write(data)`: Scrive dati sulla caratteristica BLE.
- `disconnect()`: Disconnette il dispositivo attuale.

### `BaseAdapter`
Classe base astratta per adattatori EUC.
- `decode(data)`: Parsa i dati ricevuti (implementato nelle sottoclassi).
- `update_pedals_mode(mode)`: Aggiorna la modalità dei pedali (implementato nelle sottoclassi).

### `InMotionAdapter`
Adattatore per EUC InMotion.
- `decode(data)`: Restituisce un dizionario con `speed`, `battery`, `distance`.
- `update_pedals_mode(mode)`: Invia comando per cambiare modalità (es. `mode=1` per modalità morbida).

## Esempio
```python
from micropython.ble import BLEManager
from micropython.euc.inmotion import InMotionAdapter
import time

ble = BLEManager()
devices = ble.scan(5000)
if devices:
    selected = devices[0]
    print(f"Connessione a {selected['name']} ({selected['mac']})")
    adapter = InMotionAdapter(ble)
    ble.connect(selected['mac'], adapter.service_uuid, adapter.char_uuid)
    while True:
        data = ble.read()
        if data:
            result = adapter.decode(data)
            if result:
                print(f"Velocità: {result['speed']} km/h, Batteria: {result['battery']}%")
        time.sleep_ms(100)
