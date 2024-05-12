import hashlib
from utils import transmit


def calculate_md5(data):
    md5_hash = hashlib.md5(data.encode())
    return md5_hash.hexdigest()

# Funkcja symulująca transmisję danych z obliczeniem wartości MD5 przed i po transmisji
def simulate_transmission_md5(original_data, error_rate):
    # Obliczenie skrótu MD5 dla danych przed transmisją
    md5_before_transmission = calculate_md5(original_data)

    # Symulacja transmisji danych
    transmitted_data = transmit(original_data, error_rate)

    # Obliczenie skrótu MD5 dla danych po transmisji
    md5_after_transmission = calculate_md5(transmitted_data)

    # Porównanie skrótu MD5 przed i po transmisji
    success = md5_before_transmission == md5_after_transmission

    return md5_before_transmission, md5_after_transmission, success

