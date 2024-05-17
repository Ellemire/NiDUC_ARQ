import hashlib
from utils import transmit

def calculate_md5(data):
    md5_hash = hashlib.md5(data.encode())
    return md5_hash.hexdigest()

# Function to add an MD5 hash to the data
# Function to add an MD5 hash to the data and return it in binary format
def add_md5(data):
    md5_hash = calculate_md5(data)
    md5_binary = ''.join(format(byte, '08b') for byte in bytes.fromhex(md5_hash))
    return data + md5_binary

# Function to verify the MD5 hash of the data
def verify_md5(data):
    received_md5 = data[-128:]  # MD5 hash in binary format is 128 bits
    received_data = data[:-128]
    calculated_md5 = calculate_md5(received_data)
    calculated_md5_binary = ''.join(format(byte, '08b') for byte in bytes.fromhex(calculated_md5))
    return calculated_md5_binary == received_md5

# Function to simulate data transmission and verify the MD5 hash
def simulate_transmission_md5(original_data, error_rate):
    data_with_md5 = add_md5(original_data)
    transmitted_data = transmit(data_with_md5, error_rate)
    if verify_md5(transmitted_data):
        return transmitted_data[:-128], data_with_md5, True
    else:
        return transmitted_data, data_with_md5, False
