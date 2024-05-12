from utils import transmit
import time, asyncio, random
# ARQ_protocol, error_detection_code

class PC:
    def __init__(self, name):
        self.name = name                # nazwa komputera
        self.buffered_data = []         # pamięć buforowana
        self.original_data = []         # oryginalne dane wygenerowane do przesyłania (do porówanania)

    def generate_data(self, length):
        return ''.join(str(random.randint(0, 1)) for _ in range(length))

    async def send_data(self, receiver, data):
        # Symulacja przesyłania danych
        error_rate = 0.1
        print(f"{self.name} sending data to {receiver.name}: {data}")
        data = transmit(data, error_rate)
        await asyncio.sleep(0.1)  # Symulacja czasu potrzebnego na transmisję
        await receiver.receive_data(data)  # Wywołanie asynchronicznej metody receive_data na obiekcie odbiorcy
        self.original_data.append(data)  # Zapisanie przesyłanych danych

    async def receive_data(self, data):
        print(f"{self.name} received data: {data}")
        self.buffered_data.append(data)

    def print_buffered_data(self):
        print(self.buffered_data)

async def main():
    pc1 = PC("PC1")
    pc2 = PC("PC2")

    data_to_send = pc1.generate_data(10)  # Generowanie danych do przesłania
    await pc1.send_data(pc2, data_to_send)  # Wysłanie danych z PC1 do PC2

    print(f"Original data by {pc1.name}: {pc1.original_data}")  # Wyświetlenie przesyłanych danych przez PC1
    print(f"Transmitted data by {pc2.name}: {pc2.buffered_data}")  # Wyświetlenie przesyłanych danych przez PC2

asyncio.run(main())