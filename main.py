from utils import generate_bit_string, show_bit_difference
from crc import simulate_transmission_crc
from parity_bit import simulate_transmission_parity, add_parity_bit

length = 50
error_rate = 0.01

original_data = generate_bit_string(length)
print("Wygenerowany ciąg bitów do transmisji:\n", original_data)

transmitted_data_crc, data_with_crc, success_crc = simulate_transmission_crc(original_data, error_rate)
transmitted_data_parity, success_parity = simulate_transmission_parity(original_data, error_rate)

if success_crc:
    print("\nTransmisja CRC udana!")
else:
    print("\nBłędy transmisji CRC. Prośba o ponowne przesłanie danych.\n")
    print("Dane z CRC po transmisji:\n", data_with_crc)
    y = int(data_with_crc, 2) ^ int(transmitted_data_crc, 2)
    print("Różnica CRC:\n", bin(y)[2:].zfill(len(transmitted_data_crc)))

print("\nDane z bitem parzystości przed transmisją:\n", add_parity_bit(original_data))
if success_parity:
    print("\nTransmisja z bitem parzystości udana!")
else:
    print("Błędy transmisji z bitem parzystości. Prośba o ponowne przesłanie danych.\n")
    print("Dane po transmisji z bitem parzystości:\n", transmitted_data_parity)

if not success_parity:
    print("Różnice w bitach parzystości:\n", show_bit_difference(original_data, transmitted_data_parity))
