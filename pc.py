from utils import transmit, generate_bit_string, show_bit_difference
from parity_bit import add_parity_bit, verify_parity_bit
from crc import add_crc, verify_crc
from md5 import add_md5, verify_md5
import sys
import csv

sys.setrecursionlimit(100000)
ACK = '0000110'  # ASCII code for ACK
NACK = '0010101'  # ASCII code for NACK (NAK)


class PC:
    def __init__(self, name, packet_size=128):
        self.name = name
        self.packet_size = packet_size
        self.sent_data = []
        self.sent_data_no_retr = []
        self.received_data = []
        self.ack_data = []
        self.nack_data = []
        self.acknowledged_packets = []  # List to store acknowledged packets
        self.retransmissions = 0

    def send_data(self, data, packet_number, protocol, error_rate, first_attempt=True):
        if protocol == 'parity':
            data_with_check = add_parity_bit(data)
        elif protocol == 'crc':
            data_with_check = add_crc(data)
        elif protocol == 'md5':
            data_with_check = add_md5(data)
        elif protocol == 'none':
            data_with_check = data
        else:
            raise ValueError("Unsupported protocol")

        self.sent_data.append(data_with_check)

        if first_attempt:
            self.sent_data_no_retr.append(data_with_check)

        if not first_attempt:
            self.retransmissions += 1

        packet_data = data_with_check  # Only data and checksum are transmitted with errors
        transmitted_data = f"{packet_number:08d}" + transmit(packet_data, error_rate)
        print(f"{self.name}: send data {packet_number}: {data_with_check}")
        return transmitted_data

    def receive_data(self, packet, protocol, error_rate):
        packet_number = packet[:8]
        data = packet[8:]

        self.received_data.append(data)  # Save all received packets

        if protocol == 'parity':
            is_valid = verify_parity_bit(data)
        elif protocol == 'crc':
            is_valid = verify_crc(data)
        elif protocol == 'md5':
            is_valid = verify_md5(data)
        elif protocol == 'none':
            is_valid = True
        else:
            raise ValueError("Unsupported protocol")

        if is_valid:
            ack = ACK
            self.ack_data.append(data)
            print(f"{self.name}: received data {packet_number}: {data}")
            return transmit(ack, error_rate) + data, int(packet_number)  # Simulate ACK transmission error
        else:
            ack = NACK
            self.nack_data.append(data)
            print(f"{self.name}: received corrupted data {data}")
            return transmit(ack, error_rate), int(packet_number)

    def packetize_data(self, data_list):
        packets = []
        packet_number = 1
        for data in data_list:
            packet = ''
            for i in range(len(data)):
                packet += data[i]
                if len(packet) == self.packet_size:
                    packets.append((packet, packet_number))
                    packet = ''
                    packet_number += 1
            if packet:
                packets.append((packet, packet_number))
                packet_number += 1
        return packets


def stop_and_wait(sender, receiver, data_list, protocol, error_rate):
    packets = sender.packetize_data(data_list)
    for data, packet_number in packets:
        first_attempt = True
        while True:
            transmitted_data = sender.send_data(data, packet_number, protocol, error_rate, first_attempt)
            ack, received_packet_number = receiver.receive_data(transmitted_data, protocol, error_rate)

            print(f"{receiver.name}: sending {ack}")
            if ack[:len(ACK)] == ACK:
                print(f"{sender.name}: received ACK. Transmission successful.")
                sender.acknowledged_packets.append(ack[len(ACK):])  # Append the original data from receiver
                break
            else:
                print(f"{sender.name}: received NACK. Resending data..")
                first_attempt = False  # Mark as a retransmission

    print_final(sender, receiver)


def go_back_n(sender, receiver, data_list, protocol, error_rate, window_size):
    packets = sender.packetize_data(data_list)
    base = 1
    next_seq_num = base
    packet_count = len(packets)
    sent_packets = {}

    while base <= packet_count:
        while next_seq_num < base + window_size and next_seq_num <= packet_count:
            data, packet_number = packets[next_seq_num - 1]
            sent_packets[next_seq_num] = sender.send_data(data, packet_number, protocol, error_rate, first_attempt=(next_seq_num not in sent_packets))
            next_seq_num += 1

        ack, received_packet_number = receiver.receive_data(sent_packets[base], protocol, error_rate)

        print(f"{receiver.name}: sending {ack}")
        if ack[:len(ACK)] == ACK:
            print(f"{sender.name}: received ACK for packet {base}.")
            sender.acknowledged_packets.append(ack[len(ACK):])  # Append the original data from receiver
            base += 1
        else:
            print(f"{sender.name}: received NACK for packet {base}. Resending window starting from packet {base}.")
            next_seq_num = base  # Reset the next sequence number to the base

    print_final(sender, receiver)


def selective_repeat(sender, receiver, data_list, protocol, error_rate, window_size):
    packets = sender.packetize_data(data_list)
    base = 1
    next_seq_num = base
    packet_count = len(packets)
    sent_packets = {}
    acked_packets = set()

    while base <= packet_count:
        while next_seq_num < base + window_size and next_seq_num <= packet_count:
            data, packet_number = packets[next_seq_num - 1]
            sent_packets[next_seq_num] = sender.send_data(data, packet_number, protocol, error_rate, first_attempt=(next_seq_num not in sent_packets))
            next_seq_num += 1

        ack, received_packet_number = receiver.receive_data(sent_packets[base], protocol, error_rate)

        print(f"{receiver.name}: sending {ack}")
        if ack[:len(ACK)] == ACK:
            print(f"{sender.name}: received ACK for packet {received_packet_number}.")
            acked_packets.add(received_packet_number)
            sender.acknowledged_packets.append(ack[len(ACK):])  # Append the original data from receiver
            while base in acked_packets:
                base += 1
        else:
            print(f"{sender.name}: received NACK for packet {received_packet_number}. Resending packet {received_packet_number}.")
            data, packet_number = packets[received_packet_number - 1]
            sent_packets[received_packet_number] = sender.send_data(data, packet_number, protocol, error_rate, first_attempt=False)

    print_final(sender, receiver)


def udp_transmission(sender, receiver, data_list, protocol, error_rate):
    packets = sender.packetize_data(data_list)
    for data, packet_number in packets:
        transmitted_data = sender.send_data(data, packet_number, protocol, error_rate)
        receiver.receive_data(transmitted_data, protocol, error_rate)
    sender.acknowledged_packets = receiver.ack_data
    print_final(sender, receiver)


def print_final(sender, receiver):
    print("\nFinal State:")
    print(f"{sender.name} sent data: {sender.sent_data}")
    print(f"{sender.name} sent data without retransmissions: {sender.sent_data_no_retr}")
    print(f"{sender.name} acknowledged packets: {sender.acknowledged_packets}")
    print(f"{receiver.name} received data: {receiver.received_data}")
    print(f"{receiver.name} ACK data: {receiver.ack_data}")
    print(f"{receiver.name} NACK data: {receiver.nack_data}")
    analyze_transmission(sender, receiver)


def analyze_transmission(sender, receiver):
    packets_to_sent = len(sender.sent_data_no_retr)
    total_packets_sent = len(sender.sent_data)
    total_retransmissions = sender.retransmissions
    total_packets_received = len(receiver.received_data)
    correctly_received_packets = len(receiver.ack_data)
    corrupted_packets = len(receiver.nack_data)
    success_rate = correctly_received_packets / total_packets_sent if total_packets_sent else 0
    corruption_rate = corrupted_packets / total_packets_received if total_packets_received else 0
    correctly_received_packets_correct_ACK_to_sender = len(sender.acknowledged_packets)
    success_rate_based_on_sender_ACK = correctly_received_packets_correct_ACK_to_sender / total_packets_sent if total_packets_sent else 0

    same_elements_count = sum(1 for sent, ack in zip(sender.sent_data_no_retr, sender.acknowledged_packets) if sent == ack)
    different_elements_count = len(sender.sent_data_no_retr) - same_elements_count
    rate = same_elements_count / packets_to_sent if packets_to_sent else 0

    print("\nTransmission Analysis:")
    print(f"The number of packets the sender wanted to send: {packets_to_sent}")
    print(f"Total packets sent by sender: {total_packets_sent}")
    print(f"Total retransmissions sent by sender: {total_retransmissions}")
    print(f"Total packets received by receiver: {total_packets_received}")  # for go-back-n the number is less than the sent packets because when nack appears, receiver waits for retransmission, does not analyze subsequent sent packets

    print(f"Correctly received packets by receiver: {correctly_received_packets}")
    print(f"Corrupted packets received by receiver: {corrupted_packets}")

    print(f"Number of packets that sender received ACK for: {correctly_received_packets_correct_ACK_to_sender}")
    print(f"Success rate based on ACK sent by receiver: {success_rate * 100:.2f}%")
    print(f"Corruption rate based on NACK sent by receiver: {corruption_rate * 100:.2f}%")
    print(f"Success rate based on ACK received by sender: {success_rate_based_on_sender_ACK * 100:.2f}%")

    print(f"Number of error-free transsmited data: {same_elements_count}")
    print(f"Number of transsmited data with error: {different_elements_count}")
    print(f"Rate of error-free transsmited data / all data: {rate* 100:.2f}%")


def display_settings(transmission_error_rate, error_detection_code, arq_protocol, packet_length, num_packets, window_size):
    print("\nCurrent Settings:")
    print(f"Transmission error rate: {transmission_error_rate}")
    print(f"Error Detection Code: {error_detection_code}")
    print(f"ARQ Protocol: {arq_protocol}")
    print(f"Length of each packet: {packet_length}")
    print(f"Number of packets to generate: {num_packets}")
    print(f"Window size: {window_size}")


def main():
    transmission_error_rate = 0.05
    error_detection_code = 'parity'
    arq_protocol = 'Stop-and-Wait'
    packet_length = 10
    num_packets = 50000
    window_size = 3

    while True:
        print("\nARQ Protocol Simulation")
        print("1. Set transmission error rate")
        print("2. Set Error Detection Code (parity, crc, md5, none)")
        print("3. Set ARQ Protocol (Stop-and-Wait, Go-Back-N, Selective Repeat, UDP)")
        print("4. Set length of each packet")
        print("5. Set number of packets to generate")
        print("6. Set window size")
        print("7. Run Data Transmission")
        print("8. Display current settings")
        print("9. Exit")
        choice = input("Choose an option (1-9): ")

        if choice == '1':
            transmission_error_rate = float(input("Enter the transmission error rate (0.0 to 1.0): "))
        elif choice == '2':
            error_detection_code = input("Enter Error Detection Code (parity, crc, md5): ")
        elif choice == '3':
            arq_protocol = input("Enter ARQ Protocol (Stop-and-Wait, Go-Back-N, Selective Repeat, UDP): ")
        elif choice == '4':
            packet_length = int(input("Enter the length of each packet: "))
        elif choice == '5':
            num_packets = int(input("Enter the number of packets to generate: "))
        elif choice == '6':
            window_size = int(input("Enter the window size: "))
        elif choice == '7':
            data_list = [generate_bit_string(packet_length) for _ in range(num_packets)]
            sender = PC("Sender")
            receiver = PC("Receiver")
            if arq_protocol == 'Stop-and-Wait':
                stop_and_wait(sender, receiver, data_list, protocol=error_detection_code, error_rate=transmission_error_rate)
            elif arq_protocol == 'Go-Back-N':
                go_back_n(sender, receiver, data_list, protocol=error_detection_code, error_rate=transmission_error_rate, window_size=window_size)
            elif arq_protocol == 'Selective Repeat':
                selective_repeat(sender, receiver, data_list, protocol=error_detection_code, error_rate=transmission_error_rate, window_size=window_size)
            elif arq_protocol == 'UDP':
                udp_transmission(sender, receiver, data_list, protocol=error_detection_code, error_rate=transmission_error_rate)
            else:
                print("Invalid ARQ Protocol. Please try again.")
        elif choice == '8':
            display_settings(transmission_error_rate, error_detection_code, arq_protocol, packet_length, num_packets, window_size)
        elif choice == '9':
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()