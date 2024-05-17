import random

# Funkcja generująca losowy ciąg bitów o określonej długości
def generate_bit_string(length):
    return ''.join(str(random.randint(0, 1)) for _ in range(length))

# Funkcja pokazująca różnice bitów
def show_bit_difference(original_data, transmitted_data):
    differences = ''
    for original_bit, transmitted_bit in zip(original_data, transmitted_data):
        if original_bit != transmitted_bit:
            differences += '1'
        else:
            differences += '0'
    return differences

# Funkcja symulująca transmisję danych z zadanym współczynnikiem błędów
def transmit(data, error_rate):
    transmitted_data = ''
    for bit in data:
        if random.random() < error_rate:
            bit = str(1 - int(bit))             # Symulacja błędu transmisji
        transmitted_data += bit
    return transmitted_data