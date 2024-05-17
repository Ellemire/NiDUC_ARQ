from utils import generate_bit_string, show_bit_difference, transmit
from crc import simulate_transmission_crc
from parity_bit import simulate_transmission_parity, add_parity_bit
from md5 import simulate_transmission_md5

length = 50
error_rate = 0.01

original_data = generate_bit_string(length)
print("Generated bit string for transmission:\n", original_data)

# Simulating data transmission with CRC checksum
transmitted_data_crc, data_with_crc, success_crc = simulate_transmission_crc(original_data, error_rate)
while not success_crc:
    print("\nCRC transmission errors. Requesting data resend.\n")
    print("Data with CRC after transmission:\n", data_with_crc)
    print("CRC differences:\n", show_bit_difference(data_with_crc, transmitted_data_crc))
    transmitted_data_crc, data_with_crc, success_crc = simulate_transmission_crc(original_data, error_rate)
print("\nCRC transmission successful!")

# Simulating data transmission with parity bit
transmitted_data_parity, data_with_parity, success_parity = simulate_transmission_parity(original_data, error_rate)
while not success_parity:
    print("\nParity bit transmission errors. Requesting data resend.")
    print("Data after transmission with parity bit:\n", transmitted_data_parity)
    print("Parity bit differences:\n", show_bit_difference(data_with_parity, transmitted_data_parity))
    transmitted_data_parity, data_with_parity, success_parity = simulate_transmission_parity(original_data, error_rate)
print("\nParity bit transmission successful!")

# Simulating data transmission with MD5
transmitted_data_md5, data_with_md5, success_md5 = simulate_transmission_md5(original_data, error_rate)
while not success_md5:
    print("\nMD5 transmission errors. Requesting data resend.")
    print("MD5 value for data after transmission:", transmitted_data_md5)
    print("MD5 differences:\n", show_bit_difference(data_with_md5, transmitted_data_md5))
    transmitted_data_md5, data_with_md5, success_md5 = simulate_transmission_md5(original_data, error_rate)
print("\nMD5 transmission successful!")
