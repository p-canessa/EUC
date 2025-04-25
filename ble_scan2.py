import os
import re
import struct

def find_value_in_log(file_path, target_value, tolerance=50, max_results=5, output_file="ble_search_output.txt", filter_prefix=True):
    """
    Cerca il chilometraggio nei log BLE di nRF Connect, con deduplicazione e limite risultati.
    
    Args:
        file_path (str): Percorso del file di log.
        target_value (float): Valore da cercare (es. 2975.3 per km).
        tolerance (int): Tolleranza in unità (es. 50 = ±0.05 km in scala /1000).
        max_results (int): Numero massimo di pacchetti unici.
        output_file (str): File di output.
        filter_prefix (bool): Filtra pacchetti 00-00-00 o 00-00-00-00 (per InMotion).
    
    Returns:
        list: Risultati trovati.
    """
    scale = 1000  # Scala fissa per chilometraggio EUC
    target = int(target_value * scale)  # Es. 2975.3 → 2975300
    results = []
    seen_packets = set()  # Deduplicazione
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                # Ignora righe "A"
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
                
                # Filtro opzionale per InMotion
                if filter_prefix and len(packet) >= 7:
                    if packet[:3] != b'\x00\x00\x00' and (len(packet) < 8 or packet[:4] != b'\x00\x00\x00\x00'):
                        continue
                
                # Cerca in 32-bit LE
                for offset in [3, 4]:
                    if offset + 3 < len(packet):
                        value_le = struct.unpack('<I', packet[offset:offset+4])[0]
                        if abs(value_le - target) <= tolerance:
                            if hex_str not in seen_packets:
                                results.append(f"Riga {line_num}, Byte {offset}-{offset+3}, 32-bit LE: {value_le} (target {target}, scala {scale}, diff {value_le - target})")
                                results.append(f"Pacchetto: {hex_str}")
                                results.append(f"Linea completa: {line.strip()}")
                                seen_packets.add(hex_str)
                
                # Ferma dopo max_results
                if len(seen_packets) >= max_results:
                    break
    
    except FileNotFoundError:
        print(f"Errore: File {file_path} non trovato")
        return []
    except Exception as e:
        print(f"Errore: {str(e)}")
        return []
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Ricerca per valore: {target_value}, tolleranza: ±{tolerance/1000} km\n")
            f.write(f"File: {file_path}\n\n")
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
    file_path = input("Inserisci il percorso del file di log (es. C:/Users/Nome/ble_log.txt): ")
    target_value = float(input("Inserisci il valore da cercare (es. 2975.3 per km): "))
    tolerance = float(input("Inserisci la tolleranza in km (es. 0.05 per ±0.05 km, default 0.05): ") or 0.05)
    max_results = int(input("Inserisci il numero massimo di risultati (es. 5, default 5): ") or 5)
    filter_prefix = input("Filtrare pacchetti InMotion (00-00-00)? (sì/no, default sì): ").lower() in ['s', 'sì', 'si', 'yes', '']
    output_file = input("Inserisci il percorso del file di output (es. ble_search_output.txt, premere Invio per default): ") or "ble_search_output.txt"
    
    results = find_value_in_log(file_path, target_value, int(tolerance * 1000), max_results, output_file, filter_prefix)
    
    if results:
        print("\nRisultati trovati:")
        for result in results:
            print(result)
    else:
        print("Nessun valore trovato.")

if __name__ == "__main__":
    main()
