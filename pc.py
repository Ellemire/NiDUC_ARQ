from utils import transmit
import time, asyncio
# ARQ_protocol, error_detection_code

class PC:
    def __init__(self, name):
        self.name = name
        self.buffered_data = []
        self.original_data = []

    def generate_data(self, lenght):
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