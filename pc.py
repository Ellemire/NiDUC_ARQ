from utils import transmit, generate_bit_string, show_bit_difference
from parity_bit import add_parity_bit, verify_parity_bit
from crc import add_crc, verify_crc
from md5 import add_md5, verify_md5
import time, asyncio, random
import sys

sys.setrecursionlimit(100000)
ACK = '0000110'                                 # ASCII code for ACK
NACK = '0010101'                                # ASCII code for NACK (NAK)
#Nerror_rate = 0.01


# parametry zakłócenia, ARQ, error detection, różne sposoby zakłócenia, podział na paczki
# statystyki czy wykryto wszystkie błędy, liczba błędów,
class PC:
    def __init__(self, name):
        self.name = name                        # computer name
        self.buffered_data = []                 # buffered memory
        self.original_data = []                 # original data generated for transmission (for comparison)
        self.received_data = []                 # received data
         self.__packet_size = 1500              # Maximum packet size
        self.__error_rate = 0.05
        self.__data_size = 10
        self.__data_number = 10
        self.__data_segment_index = 0           # index of the currently sent segment (next segment to be sent)
        self.__ACK_event = asyncio.Event()      # Event for handling asynchronous events: ACK reception event
        self.__error_detection_code = 2         # 0 - none, 1 - parity bit, 2 - crc, 3 - md5
        self.__ARQ_protocol = 1                 # 0 - UDP, 1 - stop&wait, 2 - go back N, 3 - selective repeat

    # Function to generate data and store it in the original_data array - raw data to be sent
    def generate_data(self):
        for i in range(self.__data_number):
            generated_data = generate_bit_string(self.__data_size)
            self.original_data.append(generated_data)
        start_index = len(self.original_data) - self.__data_number
        end_index = len(self.original_data)
        return self.original_data[start_index: end_index]
        
    #Function to split a big amount of data into smaller packages
        def packetize_data(self, data):
            packets = []
            packet = ''
            for i in range(len(data)):
                packet += data[i]
                if len(packet) == self.__packet_size:
                    packets.append(packet)
                    packet = ''
            if packet:
                packets.append(packet)
            return packets

    # Function to select and add control sum bits for transmission from the original_data array
    async def send_data(self, receiver):
         start_index = len(self.original_data)
        data_to_send = self.generate_data()                    # Generating data to be sent
        end_index = len(self.original_data)
        gap = self.__data_segment_index - start_index
        while start_index < end_index:
            # Preparing data for transmission
            data_segment = self.original_data[start_index]
            if len(data_segment) > self.__packet_size:
                data_packets = self.packetize_data(data_segment)
            else:
                data_packets = [data_segment]                  # Treat as a single packet

            for packet in data_packets:
                if self.__error_detection_code == 1:
                    self.buffered_data.append(add_parity_bit(packet))
                elif self.__error_detection_code == 2:
                    self.buffered_data.append(add_crc(packet))
                elif self.__error_detection_code == 3:
                    self.buffered_data.append(add_md5(packet))
                else:
                    self.buffered_data.append(packet)

                # transmitting data segment
                await self.data_sending(receiver, self.buffered_data[self.__data_segment_index],
                                        self.__data_segment_index)
                self.__data_segment_index += 1                  # Incrementing the data segment index for transmission

                if self.__ARQ_protocol == 1:
                    await self.__ACK_event.wait()               # Waiting for ACK reception for ARQ: STOP & WAIT

            start_index = self.__data_segment_index - gap       # Incrementing start_index for data transmission by gap

    # Function to send a segment
    async def data_sending(self, receiver, data, index):
        # Simulating data transmission
        print(f"{self.name} sending data to {receiver.name}:    {data}")
        data = transmit(data, self.__error_rate)                # Simulating transmission with error probability
        # await asyncio.sleep(0)                                # Simulating transmission time
        await receiver.receive_data(self, data, index)          # Calling the receive_data method on the receiver object

    async def receive_data(self, sender, data, index):
        self.__data_segment_index = index
        print(f"{self.name} received data from {sender.name}: {data}")
        await asyncio.sleep(0)              # Simulating transmission time
        if self.__ARQ_protocol != 0:
            if self.__error_detection_code == 1:
                if verify_parity_bit(data):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.received_data.append(data[:-1])
                else:
                    await self.send_NACK(sender, index)
            elif self.__error_detection_code == 2:
                if verify_crc(data):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.received_data.append(data[:-32])
                else:
                    await self.send_NACK(sender, index)
            elif self.__error_detection_code == 3:
                if verify_md5(data):
                    await self.send_ACK(sender, index)
                    self.buffered_data.append(data)
                    self.received_data.append(data[:-128])
                else:
                    await self.send_NACK(sender, index)
            else:
                self.buffered_data.append(data)
                self.received_data.append(data)
        else:
            self.received_data.append(data)

    async def send_NACK(self, receiver, index):
        print(f"{self.name} is sending NACK. Data segment index: {index}")
        await receiver.receive_CK(self, index, transmit(NACK, self.__error_rate))

    # dodać do eksperymentu błędy ACK !!!!!
    async def send_ACK(self, receiver, index):
        print(f"{self.name} is sending ACK. Data segment index: {index}")
        print(self.__error_rate)
        await receiver.receive_CK(self, index, transmit(ACK, self.__error_rate))

    async def receive_CK(self, sender, index, transmitted):
        await asyncio.sleep(0)
        print(f"{self.name} received {transmitted}. Data segment index: {index}")

        if transmitted == ACK:
            print(f"{self.name} received ACK. Data segment index: {index}\n")
            if self.__ARQ_protocol == 1:
                self.__ACK_event.set()
        else:
            if transmitted == NACK:
                print(f"{self.name} received NACK. Data segment index: {index}")
            else:
                print("ACK/NACK has been corrupted!")

            if self.__ARQ_protocol == 3 or self.__ARQ_protocol == 1:
                print(f"Resending data. Data segment index: {index}\n")
                await self.data_sending(sender, self.buffered_data[index], index)
            elif self.__ARQ_protocol == 2:
                self.buffered_data.pop(index)
                print(f"Go back {index} and resending all data.")
                self.__data_segment_index = index - 1

    def reset(self):
        self.buffered_data = []
        self.original_data = []
        self.received_data = []
        self.__data_segment_index = 0

    def print_buffered_data(self):
        print(self.buffered_data)

    def set_error_rate(self, error_rate):
        try:
            self.__error_rate = error_rate
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    def set_data_size(self, data_size):
        try:
            self.__data_size = data_size
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    def set_data_number(self, data_number):
        try:
            self.__data_number = data_number
        except ValueError:
            print("Invalid input. Please enter a valid number.")

    def set_arq_protocol(self, protocol):
        try:
            if protocol in {0, 1, 2, 3}:
                self.__ARQ_protocol = protocol
            else:
                print("Invalid protocol. Default protocol set. (UDP)")
                self.__ARQ_protocol = 0
        except ValueError:
            print("Invalid input. Default protocol set. (UDP)")
            self.__ARQ_protocol = 0

    def set_error_detection_code(self, detection_code):
        try:
            if detection_code in {0, 1, 2, 3}:
                self.__error_detection_code = detection_code
            else:
                print("Invalid error detection code. Default error detection code set. (parity bit)")
                self.__error_detection_code = 1
        except ValueError:
            print("Invalid input. Default error detection code set. (parity bit)")
            self.__error_detection_code = 1

    def display_current_settings(self):
        print(f"\n--- Current Settings ---")
        print(f"Error Rate: {self.__error_rate}")
        print(f"Data Size: {self.__data_size}")
        print(f"Number of Data: {self.__data_number}")
        print(f"ARQ Protocol: {self.__ARQ_protocol}")
        print(f"Error Detection Code: {self.__error_detection_code}")


# drukowanie wysłanych i odebranych danych do porównania
async def print_transmition_data(sender, receiver):
    print(f"\nOriginal data by {sender.name}: {sender.original_data}")      # Displaying data sent by PC1
    print(f"Received  data by {receiver.name}: {receiver.received_data}")    # Displaying data received by PC2


async def compare_data(sender, receiver):
    original_data = sender.original_data
    received_data = receiver.received_data

    if len(original_data) != len(received_data):
        print("The data arrays have different lengths.")
        return

    total_elements = len(original_data)
    same_elements = sum(1 for o, r in zip(original_data, received_data) if o == r)
    different_elements = total_elements - same_elements

    print(f"Total transmitted data: {total_elements}")
    print(f"Number of successfully transmitted data: {same_elements}")
    print(f"Number of incorrectly transmitted data: {different_elements}")


async def main():
    pc1 = PC("PC1")
    pc2 = PC("PC2")

    while True:
        print("\n--- Menu ---")
        print("1. Set Error Rate")
        print("2. Set Error Detection Code")
        print("3. Set ARQ Protocol")
        print("4. Set Data Size")
        print("5. Set Number Of Data")
        print("6. Run Data Transmission")
        print("7. Display Current Settings")
        print("8. Exit")
        choice = input("Enter your choice (1-8): ")

        if choice == '1':
            error_rate = float(input("Enter error rate (as a number between 0 and 1): "))
            pc1.set_error_rate(error_rate)
            pc2.set_error_rate(error_rate)
        elif choice == '2':
            detection_code = int(input("Choose error_detection_code:\n0 - none, 1 - parity bit, 2 - crc, 3 - md5: "))
            pc1.set_error_detection_code(detection_code)
            pc2.set_error_detection_code(detection_code)
        elif choice == '3':
            protocol = int(
                input("Choose ARQ protocol: \n0 - UDP, 1 - stop&wait, 2 - go-back-N, 3 - selective repeat: "))
            pc1.set_arq_protocol(protocol)
            pc2.set_arq_protocol(protocol)
        elif choice == '4':
            data_size = int(input("Enter data size (as a positive integer): "))
            pc1.set_data_size(data_size)
            pc2.set_data_size(data_size)
        elif choice == '5':
            data_number = int(input("Enter number of data (as a positive integer): "))
            pc1.set_data_number(data_number)
            pc2.set_data_number(data_number)
        elif choice == '6':
            pc1.reset()
            pc2.reset()
            await pc1.send_data(pc2)  # Sending data from PC1 to PC2
            await print_transmition_data(pc1, pc2)
            await compare_data(pc1, pc2)
        elif choice == '7':
            pc1.display_current_settings()
        elif choice == '8':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please select a valid option.")


asyncio.run(main())
