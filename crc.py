import zlib
from utils import transmit

# Function to add a CRC checksum to data
def add_crc(data):
    crc = zlib.crc32(data.encode())
    crc_bytes = crc.to_bytes(4, byteorder='big')
    return data + format(int.from_bytes(crc_bytes, byteorder='big'), '032b')

# Function to verify the CRC checksum of data
def verify_crc(data):
    received_crc = data[-32:]
    received_data = data[:-32]
    calculated_crc = zlib.crc32(received_data.encode())
    return calculated_crc == int(received_crc, 2)

