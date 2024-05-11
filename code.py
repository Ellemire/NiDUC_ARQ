import random
import zlib

# Funkcja generująca losowy ciąg bitów o określonej długośc
def generate_bit_string(length):
    return ''.join(str(random.randint(0, 1)) for _ in range(length))

# Funkcja dodająca sumę kontrolną CRC do danych
def add_crc(data):
    # Obliczenie sumy kontrolnej CRC dla danych
    crc = zlib.crc32(data.encode())
    # Konwersja sumy kontrolnej na ciąg bitów i dołączenie jej na końcu danych
    crc_bytes = crc.to_bytes(4, byteorder='big')
    return data + format(int.from_bytes(crc_bytes, byteorder='big'), '032b')

# Funkcja symulująca transmisję danych z zadanym współczynnikiem błędów
def transmit(data, error_rate):
    transmitted_data = ''
    for bit in data:
        # Symulacja zakłócenia bitów zgodnie z zadanym współczynnikiem błędów
        if random.random() < error_rate:
            bit = str(1 - int(bit))  # Zakłócenie bitu
        transmitted_data += bit
    return transmitted_data

# Funkcja weryfikująca sumę kontrolną CRC danych
def verify_crc(data):
    received_crc = data[-32:]  # Pobranie sumy kontrolnej CRC (32 bity) z danych
    received_data = data[:-32]  # Pobranie danych bez sumy kontrolnej
    calculated_crc = zlib.crc32(received_data.encode())  # Obliczenie sumy kontrolnej CRC dla otrzymanych danych
    # Porównanie obliczonej sumy kontrolnej z otrzymaną
    return calculated_crc == int(received_crc, 2)

# Funkcja symulująca transmisję danych i weryfikująca sumę kontrolną CRC
def simulate_transmission(original_data, error_rate):
    # Dodanie sumy kontrolnej CRC do oryginalnych danych
    data_with_crc = add_crc(original_data)
    # Symulacja transmisji danych z zadanym współczynnikiem błędów
    transmitted_data = transmit(data_with_crc, error_rate)
    # Weryfikacja sumy kontrolnej CRC otrzymanych danych
    if verify_crc(transmitted_data):
        return transmitted_data[:-32], 0, True  # Usunięcie sumy kontrolnej CRC i zwrócenie wyniku pozytywnego
    else:
        # W przypadku błędów transmisji zwrócenie danych wraz z sumą kontrolną CRC oraz wyniku negatywnego
        return transmitted_data, data_with_crc, False

def verify_parity_bit(data):
    # Pobranie bitu parzystości z danych
    parity_bit = data[-1]
    # Pobranie danych bez bitu parzystości
    data_without_parity = data[:-1]
    # Sprawdzenie liczby jedynek w danych
    ones_count = data_without_parity.count('1')
    # Porównanie liczby jedynek z bitowym parzystością
    return (ones_count % 2 == 0 and parity_bit == '0') or (ones_count % 2 != 0 and parity_bit == '1')

def add_parity_bit(data):
    # Sprawdzenie liczby jedynek w ciągu danych
    ones_count = data.count('1')
    # Dodanie bitu parzystości na końcu danych
    return data + str(ones_count % 2)

# Przykładowe użycie
length = 50  # Długość ciągu bitów
error_rate = 0.01  # Przykładowy współczynnik błędów

original_data = generate_bit_string(length)
print("Wygenerowany ciąg bitów do transmisji:\n", original_data)

# Symulacja transmisji danych
transmitted_data, data_with_crc, success = simulate_transmission(original_data, error_rate)
print("\n", transmitted_data)
if success:
    print("Transmisja udana!")
else:
    print("Błędy transmisji. Prośba o ponowne przesłanie danych.\n")
    print("Dane z CRC po transmisji:\n", data_with_crc)
    # Obliczenie różnicy między oryginalnymi danymi a otrzymanymi danymi
    y = int(data_with_crc, 2) ^ int(transmitted_data, 2)
    print("Różnica:\n", bin(y)[2:].zfill(len(transmitted_data)))  # Wypisanie różnicy w formacie binarnym
