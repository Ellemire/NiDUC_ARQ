from utils import transmit, generate_bit_string
from parity_bit import add_parity_bit, verify_parity_bit
from crc import add_crc, verify_crc
from md5 import calculate_md5
import time, asyncio, random

#parametry zakłócenia, ARQ, error detection, różne sposoby zakłócenia, podział na paczki
#statystyki czy wykryto wszystkie błędy, liczba błędów,
class PC:
    def __init__(self, name):
        self.name = name                # nazwa komputera
        self.buffered_data = []         # pamięć buforowana
        self.original_data = []         # oryginalne dane wygenerowane do przesyłania (do porówanania)
        self.recived_data = []         # dane otrzymane
        self.__data_segment_index = 0     # numer aktualnie wysyłanego segmentu (następnego segmentu do przesłania)
        self.__ACK_event = asyncio.Event()    # do obsługu zdarzeń asynchronicznych: wydarzenie otrzymania ACK
        self.__error_detection_code = 1    # 0 - none, 1 - bit parzystości, 2 - crc, 3 - mr5
        self.__ARQ_protocol = 3            # 0 - UDP, 1 - stop&wait, 2 - go back N, 3 - selective repet

# funkcja generująca dane i wpisujące je do tablicy original_data - nieobrobione dane do wysłania
    def generate_data(self, length, number_of_data):
        for i in range(number_of_data):
            generated_data = generate_bit_string(length)
            self.original_data.append(generated_data)
        start_index = len(self.original_data) - number_of_data
        end_index = len(self.original_data)
        return self.original_data[start_index : end_index]

#funkcja wybierające i przygotywująca segmenty do wysłania z tablicy original_data
    async def send_data(self, receiver, start_index, end_index):
        gap = self.__data_segment_index - start_index                 # różnica między indeksami w celu synchronizacji indeksów
        while start_index < end_index:
            # przygotowanie danych do wysłania
            if self.__error_detection_code == 1:
                self.buffered_data.append(add_parity_bit(self.original_data[start_index]))
            elif self.__error_detection_code == 2:
                self.buffered_data.append(add_crc(self.original_data[start_index]))
            elif self.__error_detection_code == 3:
                self.buffered_data.append(calculate_md5(self.original_data[start_index]))
            else:
                self.buffered_data.append(self.original_data[start_index])

            #przesłanie segmentu danych
            await self.data_sending(receiver, self.buffered_data[self.__data_segment_index], self.__data_segment_index)
            self.__data_segment_index += 1            # przesunięcie indeksu danych do przesłania

            if self.__ARQ_protocol == 1:
                await self.__ACK_event.wait()         # oczekiwanie na otrzymanie ACK dla ARQ: STOP & WAIT

            start_index = self.__data_segment_index - gap     # inkrementacja indeksu start_indeks do wysłania danych o gap

#funkcja wysyłająca segment
    async def data_sending(self, receiver, data, index):
        # Symulacja przesyłania danych
        error_rate = 0.1
        print(f"{self.name} sending data to {receiver.name}:    {data}")
        data = transmit(data, error_rate)                   # Symulacja transmisji z prawdopodobieństwem błędu
        await asyncio.sleep(0)                              # Symulacja czasu potrzebnego na transmisję
        await receiver.receive_data(self, data, index)      # Wywołanie metody receive_data na obiekcie odbiorcy

    async def receive_data(self, sender, data, index):
        self.__data_segment_index = index
        print(f"{self.name} received data from {sender.name}: {data}")
        await asyncio.sleep(0)                  # Symulacja czasu potrzebnego na transmisję
        if self.__ARQ_protocol != 0:
            if self.__error_detection_code == 1:
                if(verify_parity_bit(data)):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.recived_data.append(data[:-1])
                else:
                    await self.send_NACK(sender, index)
            elif self.__error_detection_code == 2:
                if (verify_crc(data)):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.recived_data.append(data[:-32])
                else:
                    await self.send_NACK(sender, index)
                    #WSTAW MD5
            elif self.__error_detection_code == 3:
                calculate_md5(data)
                self.buffered_data.append(data)
            else:
                self.buffered_data.append(data)
                self.recived_data.append(data)
        else:
            self.recived_data.append(data)

    async def send_NACK(self, reciver, index):
        print(f"{self.name} is sending NACK. Data segment index: {index}")
        await reciver.recive_NACK(self, index)

    #dodać do eksperymentu błędy ACK
    async def send_ACK(self, reciver, index):
        print(f"{self.name} is sending ACK. Data segment index: {index}")
        await reciver.recive_ACK(self, index)
    async def recive_ACK(self, sender, index):
        print(f"{self.name} recived ACK. Data segment index: {index}")
        if self.__ARQ_protocol == 1:
            self.__ACK_event.set();
    async def recive_NACK(self, sender, index):
        print(f"{self.name} recived NACK. Data segment index: {index}")
        self.NACK = True
        if self.__ARQ_protocol == 3 or self.__ARQ_protocol == 1:
            print(f"Resending data. Data segment index: {index}")
            await self.data_sending(sender, self.buffered_data[index], index)
        if self.__ARQ_protocol == 2:
            print(f"Go back {index} and resending all data.")
            self.__data_segment_index = index - 1                 # -1 bo indeks zaraz będzie inkrementowany

    def print_buffered_data(self):
        print(self.buffered_data)

    def set_ARQ_protocol(self):
        protocol = input("Choose ARQ protocol: \n0 - UDP, 1 - stop&wait, 2 - go-back-N, 3 - selective repet: ")
        if protocol in {0, 1, 2, 3}:
            self.__ARQ_protocol = protocol
        else:
            print("Unvalid protocol. Default protocol set. (UTP)")
            self.__ARQ_protocol = 0

    def set_error_detection_code(self):
        detection_code = input("Choose error_detection_code:\n0 - none, 1 - parity bit, 2 - crc, 3 - mr5")
        if detection_code in {0, 1, 2, 3}:
            self.__error_detection_code = detection_code
        else:
            print("Unvalid error detection code. Default error detection code set. (parity bit)")
            self.__ARQ_protocol = 1

# drukowanie wysłanych i odebranych danych do porównania
async def print_transmition_data(sender, reciver):
    print(f"\nOriginal data by {sender.name}: {sender.original_data}")  # Wyświetlenie przesyłanych danych przez PC1
    print(f"Recived  data by {reciver.name}: {reciver.recived_data}")  # Wyświetlenie przesyłanych danych przez PC2

# przykład użycia
async def main():
    pc1 = PC("PC1")
    pc2 = PC("PC2")

    data_to_send = pc1.generate_data(length=10, number_of_data=10)  # Generowanie danych do przesłania

    # asyncio.create_task(pc1.send_data(pc2, start_index=0, end_index=10))
    await pc1.send_data(pc2, start_index=0, end_index=10)  # Wysłanie danych z PC1 do PC2

    await print_transmition_data(pc1, pc2)

asyncio.run(main())