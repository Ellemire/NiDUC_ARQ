import random
import zlib

# Funkcja generująca losowy ciąg bitów o określonej długości
def generate_bit_string(length):
    return ''.join(str(random.randint(0, 1)) for _ in range(length))

# Funkcja dodająca sumę kontrolną CRC do danych
def add_crc(data):
    crc = zlib.crc32(data.encode())     # Obliczenie sumy kontrolnej CRC dla danych
    crc_bytes = crc.to_bytes(4, byteorder='big')    ## Konwersja sumy kontrolnej na ciąg bitów i dołączenie jej na końcu danych
    return data + format(int.from_bytes(crc_bytes, byteorder='big'), '032b')  # Konwersja na ciąg bitów

# Funkcja symulująca transmisję danych z zadanym współczynnikiem błędów

# Funkcja dodająca bit parzystości do danych
def add_parity_bit(data):
    # Sprawdzenie liczby jedynek w ciągu danych
    ones_count = data.count('1')
    # Dodanie bitu parzystości na końcu danych
    return data + str(ones_count % 2)
def transmit(data, error_rate):
    transmitted_data = ''
    for bit in data:
        if random.random() < error_rate:    # Symulacja zakłócenia bitów zgodnie z zadanym współczynnikiem błędów
            bit = str(1 - int(bit))  # Zakłócenie bitu
        transmitted_data += bit
    return transmitted_data

# Funkcja weryfikująca bit parzystości danych
def verify_parity_bit(data):
    # Pobranie bitu parzystości z danych
    parity_bit = data[-1]
    # Pobranie danych bez bitu parzystości
    data_without_parity = data[:-1]
    # Sprawdzenie liczby jedynek w danych
    ones_count = data_without_parity.count('1')
    # Porównanie liczby jedynek z bitowym parzystością
    return (ones_count % 2 == 0 and parity_bit == '0') or (ones_count % 2 != 0 and parity_bit == '1')


# Funkcja weryfikująca sumę kontrolną CRC danych
def verify_crc(data):
    received_crc = data[-32:]   # Pobranie sumy kontrolnej CRC (32 bity) z danych
    received_data = data[:-32] # Pobranie danych bez sumy kontrolnej
    #print("", data, "\n", received_crc, "\n", received_data)
    calculated_crc = zlib.crc32(received_data.encode())
    return calculated_crc == int(received_crc, 2)

# Funkcja symulująca transmisję danych i weryfikująca sumę kontrolną CRC
def simulate_transmission_crc(original_data, error_rate):
    # Dodanie sumy kontrolnej CRC do oryginalnych danych
    data_with_crc = add_crc(original_data) # Dodanie sumy kontrolnej CRC do oryginalnych danych
    # Symulacja transmisji danych z zadanym współczynnikiem błędów
    transmitted_data = transmit(data_with_crc, error_rate)
    # Weryfikacja sumy kontrolnej CRC otrzymanych danych
    if verify_crc(transmitted_data):
        return transmitted_data[:-32], 0, True  # Usunięcie sumy kontrolnej CRC
    else:
        # W przypadku błędów transmisji zwrócenie danych wraz z sumą kontrolną CRC oraz wyniku negatywnego
        return transmitted_data, data_with_crc, False

def simulate_transmission_parity(original_data, error_rate):
    # Dodanie bitu parzystości do oryginalnych danych
    data_with_parity = add_parity_bit(original_data)
    # Symulacja transmisji danych z zadanym współczynnikiem błędów
    transmitted_data = transmit(data_with_parity, error_rate)
    # Weryfikacja bitu parzystości otrzymanych danych
    if verify_parity_bit(transmitted_data):
        return transmitted_data[:-1], True  # Usunięcie bitu parzystości i zwrócenie wyniku pozytywnego
    else:
        # W przypadku błędów transmisji zwrócenie danych oraz wyniku negatywnego
        return transmitted_data, False

# Przykładowe użycie
length = 50  # Długość ciągu bitów
error_rate = 0.01  # Przykładowy współczynnik błędów

original_data = generate_bit_string(length)
print("Wygenerowany ciąg bitów do transmisji:\n", original_data)

# Symulacja transmisji danych z sumą kontrolną CRC
transmitted_data_crc, data_with_crc, success_crc = simulate_transmission_crc(original_data, error_rate)

# Symulacja transmisji danych z bitem parzystości
transmitted_data_parity, success_parity = simulate_transmission_parity(original_data, error_rate)

if success_crc:
    print("Transmisja CRC udana!")
else:
    print("Błędy transmisji CRC. Prośba o ponowne przesłanie danych.\n")
    print("Dane z CRC po transmisji:\n", data_with_crc)
    y = int(data_with_crc, 2) ^ int(transmitted_data_crc, 2)
    print("Różnica CRC:\n", bin(y)[2:].zfill(len(transmitted_data_crc)))

if success_parity:
    print("Transmisja z bitem parzystości udana!")
else:
    print("Błędy transmisji z bitem parzystości. Prośba o ponowne przesłanie danych.\n")
    print("Dane po transmisji z bitem parzystości:\n", transmitted_data_parity)