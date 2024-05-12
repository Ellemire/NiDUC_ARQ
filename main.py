from utils import generate_bit_string, show_bit_difference, transmit
from crc import simulate_transmission_crc
from parity_bit import simulate_transmission_parity, add_parity_bit
from md5 import simulate_transmission_md5

length = 50
error_rate = 0.01

original_data = generate_bit_string(length)
print("Wygenerowany ciąg bitów do transmisji:\n", original_data)

# Symulacja transmisji danych z sumą kontrolną CRC
transmitted_data_crc, data_with_crc, success_crc = simulate_transmission_crc(original_data, error_rate)
while not success_crc:
    print("\nBłędy transmisji CRC. Prośba o ponowne przesłanie danych.\n")
    print("Dane z CRC po transmisji:\n", data_with_crc)
    y = int(data_with_crc, 2) ^ int(transmitted_data_crc, 2)
    print("Różnica CRC:\n", bin(y)[2:].zfill(len(transmitted_data_crc)))
    transmitted_data_crc, data_with_crc, success_crc = simulate_transmission_crc(original_data, error_rate)
print("\nTransmisja CRC udana!")


# Symulacja transmisji danych z bitem parzystości
transmitted_data_parity, data_with_parity, success_parity = simulate_transmission_parity(original_data, error_rate)
while not success_parity:
    print("\nBłędy transmisji z bitem parzystości. Prośba o ponowne przesłanie danych.")
    print("Dane po transmisji z bitem parzystości:\n", transmitted_data_parity)
    print("Różnice w bitach parzystości:\n", show_bit_difference(original_data, transmitted_data_parity))
    transmitted_data_parity, data_with_parity ,success_parity = simulate_transmission_parity(original_data, error_rate)
print("\nTransmisja z bitem parzystości udana!")

# Symulacja transmisji danych z MD5
md5_before, md5_after, success_md5 = simulate_transmission_md5(original_data, error_rate)
while not success_md5:
    print("\nBłędy transmisji MD5. Prośba o ponowne przesłanie danych.")
    print("Wartość MD5 dla danych przed transmisją:", md5_before)
    print("Wartość MD5 dla danych po transmisji:", md5_after)
    md5_before, md5_after, success_md5 = simulate_transmission_md5(original_data, error_rate)
print("\nTransmisja MD5 udana!")