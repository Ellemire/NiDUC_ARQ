import zlib

# Funkcja dodająca sumę kontrolną CRC do danych
def add_crc(data):
    crc = zlib.crc32(data.encode())
    crc_bytes = crc.to_bytes(4, byteorder='big')
    return data + format(int.from_bytes(crc_bytes, byteorder='big'), '032b')

# Funkcja weryfikująca sumę kontrolną CRC danych
def verify_crc(data):
    received_crc = data[-32:]
    received_data = data[:-32]
    calculated_crc = zlib.crc32(received_data.encode())
    return calculated_crc == int(received_crc, 2)

# Funkcja symulująca transmisję danych i weryfikująca sumę kontrolną CRC
def simulate_transmission_crc(original_data, error_rate):
    data_with_crc = add_crc(original_data)
    transmitted_data = transmit(data_with_crc, error_rate)
    if verify_crc(transmitted_data):
        return transmitted_data[:-32], 0, True
    else:
        return transmitted_data, data_with_crc, False