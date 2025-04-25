import os
import re
import struct
from datetime import datetime

def find_value_in_log(file_path, target_value=12954.238, tolerance=50, max_results=10, output_file="ble_search_output.txt", search_device_info=True, search_battery=True, search_proprietary=True):
    """
    Cerca chilometraggio, Device Information, Battery Level o dati proprietari nei log BLE.
    Salva risultati in un file, evitando duplicati.
    
    Args:
        file_path (str): Percorso del file di log.
        target_value (float): Valore chilometraggio (es. 12954.238).
        tolerance (int): Tolleranza in unità (es. 50 = ±0.05 km).
        max_results (int): Numero massimo di pacchetti unici per tipo.
        output_file (str): File di output.
        search_device_info (bool): Cerca Device Information.
        search_battery (bool): Cerca Battery Level.
        search_proprietary (bool): Cerca dati proprietari (es. Sherman Max).
    
    Returns:
        list: Risultati trovati.
    """
    scale = 1000
    target = int(target_value * scale) if target_value else None
    results = []
    seen_packets = set()  # Per deduplicazione
    packet_counts = {
        'total': 0,
        'long': 0,  # DC-5A-5C-20
        'short': 0,  # 0D-8F/90/91/92/87/88/FA/FB
        'device_info': 0,
        'battery': 0
    }

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if line.startswith('A'):
                    continue
                if '(0x)' not in line:
                    continue
                hex_match = re.search(r'\(0x\)\s*([0-9A-Fa-f\s\-]+)', line)
                if not hex_match:
                    continue
                
                hex_str = hex_match.group(1).replace('-', '').replace(' ', '')
                try:
                    packet = bytes.fromhex(hex_str)
                except ValueError:
                    continue

                packet_counts['total'] += 1
                packet_key = hex_str.lower()  # Chiave per deduplicazione

                # Chilometraggio (Sherman Max)
                if target_value and search_proprietary and len(packet) >= 16 and packet[0] == 0x0D and packet[1] in [0x8F, 0x90, 0x91, 0x92, 0x87, 0x88, 0xFA, 0xFB]:
                    packet_counts['short'] += 1
                    if packet_key in seen_packets:
                        continue
                    seen_packets.add(packet_key)
                    # Prova byte 5-8
                    value_le = struct.unpack('<I', packet[5:9])[0]
                    value_be = struct.unpack('>I', packet[5:9])[0]
                    for value in [value_le, value_be]:
                        if abs(value - target) <= tolerance:
                            results.append(f"Riga {line_num}, Byte 5-8, 32-bit: {value} (target {target}, scala {scale}, diff {value - target})")
                            results.append(f"Pacchetto: {hex_str}")
                            results.append(f"Linea completa: {line.strip()}")
                    # Prova byte 9-12
                    value_le = struct.unpack('<I', packet[9:13])[0]
                    value_be = struct.unpack('>I', packet[9:13])[0]
                    for value in [value_le, value_be]:
                        if abs(value - target) <= tolerance:
                            results.append(f"Riga {line_num}, Byte 9-12, 32-bit: {value} (target {target}, scala {scale}, diff {value - target})")
                            results.append(f"Pacchetto: {hex_str}")
                            results.append(f"Linea completa: {line.strip()}")

                # Device Information
                if search_device_info:
                    for uuid in ['00002a23', '00002a24', '00002a25', '00002a26', '00002a29']:
                        if uuid in line:
                            packet_counts['device_info'] += 1
                            if packet_key in seen_packets:
                                continue
                            seen_packets.add(packet_key)
                            try:
                                decoded = bytes.fromhex(hex_str).decode('ascii').strip('\x00')
                                results.append(f"Riga {line_num}, {uuid}: {decoded}")
                            except:
                                results.append(f"Riga {line_num}, {uuid} (non-ASCII): {hex_str}")
                            results.append(f"Linea completa: {line.strip()}")

                # Battery Level
                if search_battery and '00002a19' in line:
                    packet_counts['battery'] += 1
                    if packet_key in seen_packets:
                        continue
                    seen_packets.add(packet_key)
                    if len(packet) >= 1:
                        battery_level = packet[0]
                        results.append(f"Riga {line_num}, Battery Level: {battery_level}%")
                        results.append(f"Pacchetto: {hex_str}")
                        results.append(f"Linea completa: {line.strip()}")

                # Proprietario (Sherman Max)
                if search_proprietary and '0000ffe1' in line.lower():
                    if len(packet) >= 20 and packet[0] == 0xDC and packet[1] == 0x5A:
                        packet_counts['long'] += 1
                        if packet_key in seen_packets:
                            continue
                        seen_packets.add(packet_key)
                        voltage = (packet[13] | (packet[14] << 8)) / 0.3309
                        battery = (packet[17] | (packet[18] << 8)) / 27.6
                        temp = (packet[15] | (packet[16] << 8)) / 7.3
                        results.append(f"Riga {line_num}, Tensione: {voltage:.2f} V, Batteria: {battery:.0f}%, Temperatura: {temp:.0f}°C")
                        results.append(f"Pacchetto: {hex_str}")
                        results.append(f"Linea completa: {line.strip()}")

                if len(seen_packets) >= max_results and not (search_device_info or search_battery or search_proprietary):
                    break
    
    except FileNotFoundError:
        print(f"Errore: File {file_path} non trovato")
        return []
    except Exception as e:
        print(f"Errore: {str(e)}")
        return []
    
    # Salva risultati nel file
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Analisi log BLE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"File: {file_path}\n")
            f.write(f"Ricerca per chilometraggio: {target_value} km, tolleranza: ±{tolerance/1000} km\n")
            f.write(f"Pacchetti analizzati: {packet_counts['total']}\n")
            f.write(f" - Pacchetti lunghi (DC-5A-5C-20): {packet_counts['long']}\n")
            f.write(f" - Pacchetti corti (0D-8F/90/91/92/87/88/FA/FB): {packet_counts['short']}\n")
            f.write(f" - Device Information: {packet_counts['device_info']}\n")
            f.write(f" - Battery Level: {packet_counts['battery']}\n")
            f.write(f"Pacchetti unici trovati: {len(seen_packets)}\n\n")
            if results:
                for result in results:
                    f.write(result + "\n")
            else:
                f.write("Nessun risultato rilevante trovato\n")
    except Exception as e:
        print(f"Errore scrittura file: {str(e)}")
    
    return results

# Esempio di utilizzo
if __name__ == "__main__":
    log_file = "sherman_log.txt"  # Sostituisci con il percorso del tuo log
    results = find_value_in_log(
        file_path=log_file,
        target_value=12954.238,
        tolerance=50,
        max_results=10,
        search_device_info=True,
        search_battery=True,
        search_proprietary=True
    )
    print(f"Risultati salvati in ble_search_output.txt")
    for result in results[:10]:  # Mostra solo i primi 10 risultati
        print(result)
