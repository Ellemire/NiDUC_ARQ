from utils import transmit

# Funkcja dodająca bit parzystości do danych
def add_parity_bit(data):
    ones_count = data.count('1')
    return data + str(ones_count % 2)

# Funkcja weryfikująca bit parzystości danych
def verify_parity_bit(data):
    parity_bit = data[-1]
    data_without_parity = data[:-1]
    ones_count = data_without_parity.count('1')
    return (ones_count % 2 == 0 and parity_bit == '0') or (ones_count % 2 != 0 and parity_bit == '1')

# Funkcja symulująca transmisję danych i weryfikująca bit parzystości
def simulate_transmission_parity(original_data, error_rate):
    data_with_parity = add_parity_bit(original_data)
    transmitted_data = transmit(data_with_parity, error_rate)
    if verify_parity_bit(transmitted_data):
        return transmitted_data[:-1], data_with_parity, True
    else:
        return transmitted_data, data_with_parity, False
