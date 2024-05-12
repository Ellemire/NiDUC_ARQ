import random

# Funkcja symulująca transmisję danych z zadanym współczynnikiem błędów
def transmit(data, error_rate):
    transmitted_data = ''
    for bit in data:
        if random.random() < error_rate:
            bit = str(1 - int(bit))
        transmitted_data += bit
    return transmitted_data
