import os
import re
import struct
import csv
from datetime import datetime

def extract_ble_timestamps(ble_file):
    """
    Estrae il primo e ultimo timestamp dal log BLE.
    
    Args:
        ble_file (str): Percorso del file BLE.
    
    Returns:
        tuple: (primo_timestamp, ultimo_timestamp) come oggetti datetime, o (None, None) se fallisce.
    """
    first_ts = None
    last_ts = None
    try:
        with open(ble_file, 'r', encoding='utf-8') as f:
            for line in f:
                ts_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})', line)
                if ts_match:
                    ts_str = ts_match.group(1)
                    # Assumi la data dal nome del file (es. 2025-04-25)
                    date_str = os.path.basename(ble_file).split('_-_')[-1].split('.')[0]
                    date_str = date_str.replace('_', ':')[:10]  # Prendi solo la data (2025-04-25)
                    try:
                        ts = datetime.strptime(f"{date_str} {ts_str}", '%Y-%m-%d %H:%M:%S.%f')
                        if first_ts is None:
                            first_ts = ts
                        last_ts = ts
                    except ValueError:
                        continue
        if first_ts and last_ts:
            print(f"Trovati timestamp BLE: {first_ts} a {last_ts}")
            return first_ts, last_ts
        else:
            print(f"Errore: Nessun timestamp trovato in {ble_file}")
            return None, None
    except FileNotFoundError:
        print(f"Errore: File BLE {ble_file} non trovato")
        return None, None
    except Exception as e:
        print(f"Errore lettura BLE: {str(e)}")
        return None, None

def extract_mileage_from_csv(csv_file):
    """
    Estrae il chilometraggio dalla prima riga valida del CSV (colonna 4).
    
    Args:
        csv_file (str): Percorso del file CSV.
    
    Returns:
        float: Chilometraggio (es. 2975.3), o None se fallisce.
    """
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Salta l'intestazione
            for row in reader:
                try:
                    mileage = float(row[4])  # Colonna 4: Total distance
                    print(f"Chilometraggio estratto dal CSV: {mileage} km")
                    return mileage
                except (IndexError, ValueError):
                    continue
        print(f"Errore: Nessun chilometraggio trovato in {csv_file}")
        return None
    except FileNotFoundError:
        print(f"Errore: File CSV {csv_file} non trovato")
        return None
    except Exception as e:
        print(f"Errore lettura CSV: {str(e)}")
        return None

def parse_euc_world_csv(csv_file):
    """
    Estrae dati dal log CSV di EUC World.
    
    Args:
        csv_file (str): Percorso del file CSV.
    
    Returns:
        list: Lista di dizionari con timestamp, chilometraggio, inclinazione, ecc.
    """
    data = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)  # Salta l'intestazione
            for row in reader:
                try:
                    ts_str = row[0].split('+')[0]
                    ts = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S.%f')
                    entry = {
                        'timestamp': ts,
                        'mileage': float(row[4]),
                        'tilt': float(row[13]),
                        'speed': float(row[5]),
                        'voltage': float(row[11]),
                        'current': float(row[12]),
                        'temperature': float(row[15])
                    }
                    data.append(entry)
                except (IndexError, ValueError):
                    continue
        print(f"Caricato CSV: {len(data)} righe")
        return data
    except FileNotFoundError:
        print(f"Errore: File CSV {csv_file} non trovato")
        return []
    except Exception as e:
        print(f"Errore CSV: {str(e)}")
        return []

def filter_csv_by_ble_timestamps(csv_file, output_csv, ble_file):
    """
    Filtra il CSV usando i timestamp estratti dal log BLE.
    
    Args:
        csv_file (str): File CSV di input.
        output_csv (str): File CSV di output.
        ble_file (str): File BLE per i timestamp.
    """
    first_ts, last_ts = extract_ble_timestamps(ble_file)
    if not first_ts or not last_ts:
        print("Impossibile filtrare CSV senza timestamp BLE")
        return
    
    filtered_rows = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                try:
                    ts_str = row[0].split('+')[0]
                    ts = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S.%f')
                    if first_ts <= ts <= last_ts:
                        filtered_rows.append(row)
                except (IndexError, ValueError):
                    continue
        
        with open(output_csv, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(header)
            writer.writerows(filtered_rows)
        print(f"Salvato estratto: {output_csv}, {len(filtered_rows)} righe")
    except Exception as e:
        print(f"Errore filtro CSV: {str(e)}")

def find_value_in_log(ble_file, csv_file, mileage, tolerance=0.5, output_file="ble_search_output.txt", max_matches=10):
    """
    Cerca chilometraggio, inclinazione e handshake nei log BLE, correlati con il CSV di EUC World.
    
    Args:
        ble_file (str): Percorso del file BLE.
        csv_file (str): Percorso del file CSV.
        mileage (float): Chilometraggio dal CSV (es. 2975.3 km).
        tolerance (float): Tolleranza in km (es. 0.5 km).
        output_file (str): File di output.
        max_matches (int): Numero massimo di corrispondenze da mostrare.
    
    Returns:
        list: Risultati trovati.
    """
    scales = [1000, 100]  # Priorità a /1000
    tolerance_units = int(tolerance * 1000)  # Es. 0.5 km = 500 unità
    target_values = [int(mileage * scale) for scale in scales]
    
    csv_data = parse_euc_world_csv(csv_file)
    results = []
    match_count = 0
    
    try:
        with open(ble_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if "null" in content.lower() and len(content.strip()) < 100:
                results.append("Errore: Log BLE vuoto o contiene solo 'null'. Riprova a registrare.")
                return results
            
            f.seek(0)
            for line_num, line in enumerate(f, 1):
                hex_match = re.search(r'\(0x\)\s*([0-9A-Fa-f\s\-]+)', line)
                if hex_match:
                    hex_str = hex_match.group(1).replace('-', '').replace(' ', '')
                    try:
                        packet = bytes.fromhex(hex_str)
                    except ValueError:
                        continue
                    
                    if len(packet) < 4 or (packet[0:3] != b'\x00\x00\x00' and packet[0:2] != b'\x55\xAA'):
                        continue
                    
                    for i in range(len(packet) - 3):
                        if i + 3 < len(packet):
                            value_le = struct.unpack('<I', packet[i:i+4])[0]
                            for scale, target in zip(scales, target_values):
                                if abs(value_le - target) <= tolerance_units and match_count < max_matches:
                                    results.append(f"Riga {line_num}, Byte {i}-{i+3}, 32-bit LE: {value_le} (target {target}, scala {scale}, diff {value_le - target})")
                                    results.append(f"Pacchetto: {hex_str}")
                                    results.append(f"Linea completa: {line.strip()}")
                                    match_count += 1
                    
                    for i in range(len(packet) - 1):
                        if i + 1 < len(packet):
                            value_be = struct.unpack('>H', packet[i:i+2])[0]
                            if -1000 <= value_be <= 1000:  # -10.0° a +10.0°
                                results.append(f"Riga {line_num}, Byte {i}-{i+1}, 16-bit BE: {value_be} (possibile inclinazione: {value_be/100.0}°)")
                                results.append(f"Pacchetto: {hex_str}")
                                results.append(f"Linea completa: {line.strip()}")
                
                if 'Write command' in line or 'Write request' in line:
                    results.append(f"Riga {line_num}, Possibile comando di scrittura (handshake): {line.strip()}")

    except FileNotFoundError:
        print(f"Errore: File BLE {ble_file} non trovato")
        return []
    except Exception as e:
        print(f"Errore BLE: {str(e)}")
        return []
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Ricerca per chilometraggio: {mileage} km, tolleranza: ±{tolerance} km, max {max_matches} corrispondenze\n")
            f.write(f"File BLE: {ble_file}, CSV: {csv_file}\n\n")
            if csv_data:
                f.write("Dati CSV (prime 5 righe):\n")
                for entry in csv_data[:5]:
                    f.write(str(entry) + "\n")
                f.write("\n")
            if results:
                for result in results:
                    f.write(result + "\n")
            else:
                f.write("Nessun valore trovato.\n")
        print(f"Risultati salvati in {output_file}")
    except Exception as e:
        print(f"Errore salvataggio: {str(e)}")
    
    return results

def main():
    # Input file
    ble_file = input("Inserisci il percorso del file BLE (es. EUC/Registro_dati_BLE_...txt): ")
    csv_file = input("Inserisci il percorso del file CSV completo (es. EUC/Registro_dati_EUC_...csv): ")
    output_csv = input("Inserisci il percorso del file CSV filtrato (es. EUC/v10f_2025_1424.csv): ")
    tolerance = float(input("Inserisci la tolleranza in km (es. 0.5 per ±0.5 km, default 0.5): ") or 0.5)
    output_file = input("Inserisci il percorso del file di output (es. v10f_2025_1424_output.txt, premere Invio per default): ") or "v10f_2025_1424_output.txt"
    
    # Estrai il chilometraggio dal CSV
    mileage = extract_mileage_from_csv(csv_file)
    if mileage is None:
        print("Impossibile procedere senza chilometraggio dal CSV")
        return
    
    # Filtra il CSV usando i timestamp del BLE
    filter_csv_by_ble_timestamps(csv_file, output_csv, ble_file)
    
    # Analizza il log BLE
    results = find_value_in_log(ble_file, output_csv, mileage, tolerance, output_file, max_matches=10)
    
    if results:
        print("\nRisultati trovati (prime 10 corrispondenze):")
        for result in results:
            print(result)
    else:
        print("Nessun valore trovato.")

if __name__ == "__main__":
    main()
