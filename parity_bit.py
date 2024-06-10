from utils import transmit

# Function to add a parity bit to data
def add_parity_bit(data):
    ones_count = data.count('1')
    return data + str(ones_count % 2)

# Function to verify the parity bit of data
def verify_parity_bit(data):
    parity_bit = data[-1]
    data_without_parity = data[:-1]
    ones_count = data_without_parity.count('1')
    return (ones_count % 2 == 0 and parity_bit == '0') or (ones_count % 2 != 0 and parity_bit == '1')


