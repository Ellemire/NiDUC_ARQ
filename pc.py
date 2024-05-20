from utils import transmit, generate_bit_string
from parity_bit import add_parity_bit, verify_parity_bit
from crc import add_crc, verify_crc
from md5 import add_md5, verify_md5
import time, asyncio, random
import sys

sys.setrecursionlimit(50000)

#parametry zakłócenia, ARQ, error detection, różne sposoby zakłócenia, podział na paczki
#statystyki czy wykryto wszystkie błędy, liczba błędów,
class PC:
    def __init__(self, name):
        self.name = name                    # computer name
        self.buffered_data = []             # buffered memory
        self.original_data = []             # original data generated for transmission (for comparison)
        self.recived_data = []              # received data
        self.__data_segment_index = 0       # index of the currently sent segment (next segment to be sent)
        self.__ACK_event = asyncio.Event()  # for handling asynchronous events: ACK reception event
        self.__error_detection_code = 3     # 0 - none, 1 - parity bit, 2 - crc, 3 - md5
        self.__ARQ_protocol = 2             # 0 - UDP, 1 - stop&wait, 2 - go back N, 3 - selective repeat

# Function to generate data and store it in the original_data array - raw data to be sent
    def generate_data(self, length, number_of_data):
        for i in range(number_of_data):
            generated_data = generate_bit_string(length)
            self.original_data.append(generated_data)
        start_index = len(self.original_data) - number_of_data
        end_index = len(self.original_data)
        return self.original_data[start_index : end_index]

# Function to select and add control sum bits for transmission from the original_data array
    async def send_data(self, receiver, start_index, end_index):
        gap = self.__data_segment_index - start_index                # difference between indices for index synchronization
        while start_index < end_index:
            # preparing data for transmission
            if self.__error_detection_code == 1:
                self.buffered_data.append(add_parity_bit(self.original_data[start_index]))
            elif self.__error_detection_code == 2:
                self.buffered_data.append(add_crc(self.original_data[start_index]))
            elif self.__error_detection_code == 3:
                self.buffered_data.append(add_md5(self.original_data[start_index]))
            else:
                self.buffered_data.append(self.original_data[start_index])

            # transmitting data segment
            await self.data_sending(receiver, self.buffered_data[self.__data_segment_index], self.__data_segment_index)
            self.__data_segment_index += 1                    # incrementing the data segment index for transmission

            if self.__ARQ_protocol == 1:
                await self.__ACK_event.wait()                 # waiting for ACK reception for ARQ: STOP & WAIT

            start_index = self.__data_segment_index - gap     # incrementing start_index for data transmission by gap

# Function to send a segment
    async def data_sending(self, receiver, data, index):
        # Simulating data transmission
        error_rate = 0.05
        print(f"{self.name} sending data to {receiver.name}:    {data}")
        data = transmit(data, error_rate)                   # Simulating transmission with error probability
        await asyncio.sleep(0)                              # Simulating transmission time
        await receiver.receive_data(self, data, index)      # Calling the receive_data method on the receiver object

    async def receive_data(self, sender, data, index):
        self.__data_segment_index = index
        print(f"{self.name} received data from {sender.name}: {data}")
        await asyncio.sleep(0)                   # Simulating transmission time
        if self.__ARQ_protocol != 0:
            if self.__error_detection_code == 1:
                if verify_parity_bit(data):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.recived_data.append(data[:-1])
                else:
                    await self.send_NACK(sender, index)
            elif self.__error_detection_code == 2:
                if verify_crc(data):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.recived_data.append(data[:-32])
                else:
                    await self.send_NACK(sender, index)
                    #WSTAW MD5
            elif self.__error_detection_code == 3:
                if verify_md5(data):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.recived_data.append(data[:-128])
                else:
                    await self.send_NACK(sender, index)
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
        try:
            protocol = int(
                input("Choose ARQ protocol: \n0 - UDP, 1 - stop&wait, 2 - go-back-N, 3 - selective repeat: "))
            if protocol in {0, 1, 2, 3}:
                self.__ARQ_protocol = protocol
            else:
                print("Invalid protocol. Default protocol set. (UDP)")
                self.__ARQ_protocol = 0
        except ValueError:
            print("Invalid input. Default protocol set. (UDP)")
            self.__ARQ_protocol = 0

    def set_error_detection_code(self):
        try:
            detection_code = int(input("Choose error_detection_code:\n0 - none, 1 - parity bit, 2 - crc, 3 - md5: "))
            if detection_code in {0, 1, 2, 3}:
                self.__error_detection_code = detection_code
            else:
                print("Invalid error detection code. Default error detection code set. (parity bit)")
                self.__error_detection_code = 1
        except ValueError:
            print("Invalid input. Default error detection code set. (parity bit)")
            self.__error_detection_code = 1


# drukowanie wysłanych i odebranych danych do porównania
async def print_transmition_data(sender, reciver):
    print(f"\nOriginal data by {sender.name}: {sender.original_data}")  # Displaying data sent by PC1
    print(f"Recived  data by {reciver.name}: {reciver.recived_data}")   # Displaying data received by PC2

# przykład użycia
async def main():
    pc1 = PC("PC1")
    pc2 = PC("PC2")

    data_to_send = pc1.generate_data(length=10, number_of_data=10)      # Generating data to be sent

    await pc1.send_data(pc2, start_index=0, end_index=10)               # Sending data from PC1 to PC2

    await print_transmition_data(pc1, pc2)

asyncio.run(main())