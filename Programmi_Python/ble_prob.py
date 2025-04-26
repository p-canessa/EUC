import os
import re
import struct
import csv
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np

def extract_ble_timestamps(ble_file, manual_date=None, timezone_offset_hours=2):
    """
    Estrae il primo e ultimo timestamp dal log BLE, applicando un offset di fuso orario.
    
    Args:
        ble_file (str): Percorso del file BLE.
        manual_date (str): Data manuale (es. '2025-04-26') se il parsing del nome file fallisce.
        timezone_offset_hours (int): Offset del fuso orario in ore (es. 2 per CEST).
    
    Returns:
        tuple: (primo_timestamp, ultimo_timestamp) come oggetti datetime in UTC, o (None, None) se fallisce.
    """
    first_ts = None
    last_ts = None
    line_count = 0
    i_line_count = 0
    date_str = manual_date

    # Estrai la data dal nome file
    if not date_str:
        try:
            filename = os.path.basename(ble_file)
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
            if date_match:
                date_str = date_match.group(1)
            else:
                print(f"Errore: Impossibile estrarre la data dal nome file {ble_file}. Specifica manual_date (es. '2025-04-26').")
                return None, None
        except Exception as e:
            print(f"Errore nel parsing del nome file {ble_file}: {str(e)}")
            return None, None

    try:
        with open(ble_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                print(f"Errore: Il file {ble_file} è vuoto")
                return None, None
            if "null" in content.lower() and len(content.strip()) < 100:
                print(f"Errore: Il file {ble_file} contiene solo 'null' o dati non validi")
                return None, None
            
            f.seek(0)
            for line in f:
                line_count += 1
                if line.startswith('I'):
                    i_line_count += 1
                    ts_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})', line)
                    if ts_match:
                        ts_str = ts_match.group(1)
                        try:
                            # Assumi che il timestamp BLE sia in CEST (+0200) e converti in UTC
                            ts = datetime.strptime(f"{date_str} {ts_str}", '%Y-%m-%d %H:%M:%S.%f')
                            ts = ts - timedelta(hours=timezone_offset_hours)  # Converti in UTC
                            if first_ts is None:
                                first_ts = ts
                            last_ts = ts
                        except ValueError as e:
                            print(f"Errore nel parsing del timestamp alla riga {line_count}: {line.strip()} ({str(e)})")
                            continue
                    else:
                        print(f"Riga 'I' senza timestamp valido alla riga {line_count}: {line.strip()}")
        if first_ts and last_ts:
            print(f"Trovati timestamp BLE (UTC): {first_ts} a {last_ts}")
            print(f"Analizzate {line_count} righe, {i_line_count} righe 'I'")
            return first_ts, last_ts
        else:
            print(f"Errore: Nessun timestamp valido trovato in {ble_file}")
            print(f"Analizzate {line_count} righe, {i_line_count} righe 'I'")
            if i_line_count == 0:
                print("Nessuna riga inizia con 'I'. Verifica il formato del file BLE.")
            return None, None
    except UnicodeDecodeError:
        print(f"Errore: Problema di codifica nel file {ble_file}. Prova a convertirlo in UTF-8.")
        return None, None
    except FileNotFoundError:
        print(f"Errore: File BLE {ble_file} non trovato")
        return None, None
    except Exception as e:
        print(f"Errore lettura BLE: {str(e)}")
        return None, None

def parse_ble_packets(ble_file, timezone_offset_hours=2):
    """
    Estrae pacchetti BLE con timestamp, solo righe 'I', applicando un offset di fuso orario.
    
    Args:
        ble_file (str): Percorso del file BLE.
        timezone_offset_hours (int): Offset del fuso orario in ore (es. 2 per CEST).
    
    Returns:
        list: Lista di (timestamp, hex_packet, header) con timestamp in UTC.
    """
    packets = []
    date_str = None
    try:
        filename = os.path.basename(ble_file)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            date_str = date_match.group(1)
        else:
            print(f"Errore: Impossibile estrarre la data dal nome file {ble_file}.")
            return []

        with open(ble_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('I'):
                    ts_match = re.search(r'(\d{2}:\d{2}:\d{2}\.\d{3})', line)
                    hex_match = re.search(r'\(0x\)\s*([0-9A-Fa-f\s\-]+)', line)
                    if ts_match and hex_match:
                        ts_str = ts_match.group(1)
                        try:
                            ts = datetime.strptime(f"{date_str} {ts_str}", '%Y-%m-%d %H:%M:%S.%f')
                            ts = ts - timedelta(hours=timezone_offset_hours)  # Converti in UTC
                            hex_str = hex_match.group(1).replace('-', '').replace(' ', '')
                            header = hex_str[:4]  # Es. 'AAAA' o 'C07D'
                            packets.append((ts, hex_str, header))
                        except ValueError:
                            continue
        print(f"Caricati {len(packets)} pacchetti BLE")
        return packets
    except UnicodeDecodeError:
        print(f"Errore: Problema di codifica nel file {ble_file}. Prova a convertirlo in UTF-8.")
        return []
    except FileNotFoundError:
        print(f"Errore: File BLE {ble_file} non trovato")
        return []
    except Exception as e:
        print(f"Errore lettura BLE: {str(e)}")
        return []

def parse_euc_world_csv(csv_file, first_ts, last_ts):
    """
    Estrae dati dal log CSV di EUC World, filtrando per intervallo BLE (in UTC).
    
    Args:
        csv_file (str): Percorso del file CSV.
        first_ts (datetime): Primo timestamp BLE (UTC).
        last_ts (datetime): Ultimo timestamp BLE (UTC).
    
    Returns:
        list: Lista di dizionari con timestamp, chilometraggio, velocità, corrente, potenza.
    """
    data = []
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                try:
                    ts_str = row[0].split('+')[0]  # Rimuove +0200
                    ts = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S.%f')
                    print(f"Timestamp CSV (UTC): {ts}")  # Debug
                    if first_ts <= ts <= last_ts:
                        entry = {
                            'timestamp': ts,
                            'mileage': float(row[4]),  # Colonna 4: distance_total
                            'speed': float(row[5]),    # Colonna 5: speed
                            'current': float(row[13]), # Colonna 13: current
                            'power': float(row[15]),   # Colonna 15: power
                            'voltage': float(row[12]), # Colonna 12: voltage
                        }
                        data.append(entry)
                except (IndexError, ValueError) as e:
                    print(f"Errore parsing riga CSV: {row[0]} ({str(e)})")
                    continue
        print(f"Caricato CSV: {len(data)} righe filtrate")
        return data
    except FileNotFoundError:
        print(f"Errore: File CSV {csv_file} non trovato")
        return []
    except Exception as e:
        print(f"Errore CSV: {str(e)}")
        return []

def extract_values_from_packet(hex_packet):
    """
    Estrae byte, word (16-bit), e dword (32-bit) in little e big endian.
    
    Args:
        hex_packet (str): Pacchetto esadecimale.
    
    Returns:
        dict: Valori estratti con chiavi (tipo, indice, endian).
    """
    try:
        packet = bytes.fromhex(hex_packet)
    except ValueError:
        return {}
    
    values = {}
    for i in range(len(packet)):
        values[('byte', i, 'none')] = packet[i]
    for i in range(len(packet) - 1):
        value_le = struct.unpack('<h', packet[i:i+2])[0]
        value_be = struct.unpack('>h', packet[i:i+2])[0]
        values[('word', i, 'le')] = value_le
        values[('word', i, 'be')] = value_be
    for i in range(len(packet) - 3):
        value_le = struct.unpack('<i', packet[i:i+4])[0]
        value_be = struct.unpack('>i', packet[i:i+4])[0]
        values[('dword', i, 'le')] = value_le
        values[('dword', i, 'be')] = value_be
    return values

def calculate_probability(csv_value, ble_value, value_range):
    """
    Calcola la probabilità che ble_value rappresenti csv_value.
    
    Args:
        csv_value (float): Valore dal CSV.
        ble_value (float): Valore dal BLE.
        value_range (float): Range atteso del valore.
    
    Returns:
        float: Probabilità (0-1).
    """
    if value_range == 0:
        return 0.0
    distance = abs(csv_value - ble_value)
    normalized_distance = distance / value_range
    probability = max(0, 1 - normalized_distance)
    return probability

def group_packets_by_interval(packets, interval_ms=200):
    """
    Raggruppa pacchetti BLE in intervalli di 200 ms.
    
    Args:
        packets (list): Lista di (timestamp, hex_packet, header).
        interval_ms (int): Intervallo in millisecondi.
    
    Returns:
        list: Lista di (start_ts, [(ts, hex_packet, header)]).
    """
    if not packets:
        return []
    
    grouped = []
    current_group = []
    current_start = packets[0][0]
    
    for packet in packets:
        ts, hex_packet, header = packet
        if (ts - current_start).total_seconds() * 1000 <= interval_ms:
            current_group.append(packet)
        else:
            grouped.append((current_start, current_group))
            current_group = [packet]
            current_start = ts
    if current_group:
        grouped.append((current_start, current_group))
    
    return grouped

def correlate_ble_csv(ble_packets, csv_data, output_file="ble_correlation_output.txt"):
    """
    Correla pacchetti BLE raggruppati con righe CSV e assegna probabilità.
    
    Args:
        ble_packets (list): Lista di (timestamp, hex_packet, header).
        csv_data (list): Lista di dizionari CSV.
        output_file (str): File di output.
    """
    ranges = {
        'mileage': 10000.0,
        'speed': 100.0,
        'current': 400.0,
        'power': 30000.0,
    }
    
    probabilities = defaultdict(list)
    grouped_packets = group_packets_by_interval(ble_packets)
    
    for csv_entry in csv_data:
        csv_ts = csv_entry['timestamp']
        window_start = csv_ts - timedelta(milliseconds=100)
        window_end = csv_ts + timedelta(milliseconds=100)
        
        for group_start, group in grouped_packets:
            if window_start <= group_start <= window_end:
                for _, hex_packet, header in group:
                    ble_values = extract_values_from_packet(hex_packet)
                    for (value_type, index, endian), ble_value in ble_values.items():
                        for csv_field in ['mileage', 'speed', 'current', 'power']:
                            csv_value = csv_entry[csv_field]
                            for scale in [1, 10, 100, 1000, 0.1, 0.01]:
                                scaled_ble_value = ble_value / scale
                                prob = calculate_probability(csv_value, scaled_ble_value, ranges[csv_field])
                                if prob > 0:
                                    probabilities[(value_type, index, endian, csv_field, scale, header)].append(prob)
    
    aggregated_probs = {}
    for key, probs in probabilities.items():
        mean_prob = np.mean(probs)
        aggregated_probs[key] = mean_prob
    
    sorted_probs = sorted(aggregated_probs.items(), key=lambda x: x[1], reverse=True)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("Correlazione BLE-CSV\n")
            f.write(f"File BLE: {ble_file}, CSV: {csv_file}\n\n")
            f.write("Probabilità per campo (top 5 per campo):\n")
            for csv_field in ['mileage', 'speed', 'current', 'power']:
                f.write(f"\n{csv_field.upper()}:\n")
                field_probs = [(k, p) for k, p in sorted_probs if k[3] == csv_field][:5]
                for (value_type, index, endian, _, scale, header), prob in field_probs:
                    f.write(f"Tipo: {value_type}, Indice: {index}, Endian: {endian}, Scala: {scale}, Header: {header}, Probabilità: {prob:.4f}\n")
            f.write("\nEventi di frenata (current < 0, deltaV < -1 km/h):\n")
            prev_speed = None
            for entry in csv_data:
                delta_v = 0.0
                if prev_speed is not None:
                    delta_v = entry['speed'] - prev_speed
                if entry['current'] < 0 and delta_v < -1.0:
                    f.write(f"{entry['timestamp']}, Current: {entry['current']:.2f} A, DeltaV: {delta_v:.2f} km/h, Power: {entry['power']:.2f} W\n")
                prev_speed = entry['speed']
        print(f"Risultati salvati in {output_file}")
    except Exception as e:
        print(f"Errore salvataggio: {str(e)}")
    
    return sorted_probs

def main():
    global ble_file, csv_file
    ble_file = input("Inserisci il percorso del file BLE (es. EUC/Log_2025-04-26_15_17_37.txt): ")
    csv_file = input("Inserisci il percorso del file CSV completo (es. EUC/V10F-AE86027D-2025-04-26_125038.csv): ")
    output_file = input("Inserisci il percorso del file di output (es. v10f_2025_correlation.txt, premere Invio per default): ") or "v10f_2025_correlation.txt"
    
    # Estrai timestamp BLE (assumendo CEST, +0200)
    first_ts, last_ts = extract_ble_timestamps(ble_file, timezone_offset_hours=2)
    if not first_ts or not last_ts:
        print("Impossibile procedere senza timestamp BLE")
        manual_date = input("Inserisci la data manuale (es. 2025-04-26) o premi Invio per uscire: ")
        if manual_date:
            first_ts, last_ts = extract_ble_timestamps(ble_file, manual_date, timezone_offset_hours=2)
            if not first_ts or not last_ts:
                print("Fallito anche con data manuale. Verifica il file BLE.")
                return
        else:
            return
    
    # Carica pacchetti BLE
    ble_packets = parse_ble_packets(ble_file, timezone_offset_hours=2)
    if not ble_packets:
        print("Nessun pacchetto BLE trovato")
        return
    
    # Carica e filtra CSV
    csv_data = parse_euc_world_csv(csv_file, first_ts, last_ts)
    if not csv_data:
        print("Nessun dato CSV trovato")
        return
    
    # Correla BLE e CSV
    sorted_probs = correlate_ble_csv(ble_packets, csv_data, output_file)
    
    # Stampa i migliori risultati
    print("\nMigliori corrispondenze (top 5 per campo):")
    for csv_field in ['mileage', 'speed', 'current', 'power']:
        print(f"\n{csv_field.upper()}:")
        field_probs = [(k, p) for k, p in sorted_probs if k[3] == csv_field][:5]
        for (value_type, index, endian, _, scale, header), prob in field_probs:
            print(f"Tipo: {value_type}, Indice: {index}, Endian: {endian}, Scala: {scale}, Header: {header}, Probabilità: {prob:.4f}")

if __name__ == "__main__":
    main()
