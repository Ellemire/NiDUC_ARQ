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
        self.name = name                    # Name of the PC
        self.packet_size = packet_size      # Maxiumum size of packet that can be sent
        self.sent_data = []
        self.sent_data_no_retr = []         # Data that was sent by sender without retransmissions of packets
        self.retransmissions = 0            # Number of retranssmsions
        self.received_data = []             # Data that receiver received
        self.ack_data = []                  # Data for which Receiver sent ACK
        self.nack_data = []                 # Data for which Receiver sent NACK
        self.acknowledged_packets = []      # Data for which Receiver sent ACK and Sender received that ACK correctly


    def send_data(self, data, packet_number, protocol, error_rate, first_attempt=True):
        # Add a checksum or error-detection code based on the specified protocol
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

        # Append the data with checksum to the sent data list
        self.sent_data.append(data_with_check)

        # If it's the first attempt of transmitting this data, also append to the no-retransmission list
        if first_attempt:
            self.sent_data_no_retr.append(data_with_check)

        # If it's not the first attempt, increment the retransmission counter
        if not first_attempt:
            self.retransmissions += 1

        # Prepare the packet data by adding the packet number and simulating transmission errors
        packet_data = data_with_check  # Only data and checksum are transmitted with errors
        transmitted_data = f"{packet_number:08d}" + transmit(packet_data, error_rate)
        print(f"{self.name}: send data {packet_number}: {data_with_check}")
        return transmitted_data

    def receive_data(self, packet, protocol, error_rate):
        # Extract the packet number and data from the received packet
        packet_number = packet[:8]
        data = packet[8:]

        self.received_data.append(data)  # Save all received packets

        # Verify the data integrity based on the specified protocol
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
            # If data is valid, send an acknowledgment (ACK)
            ack = ACK
            self.ack_data.append(data)      # Append the valid data to the ack_data list
            print(f"{self.name}: received data {packet_number}: {data}")
            # Simulate ACK transmission error and return the ACK with the data and packet number
            return transmit(ack, error_rate) + data, int(packet_number)
        else:
            # If data is corrupted, send a negative acknowledgment (NACK)
            ack = NACK
            self.nack_data.append(data)     # Append the corrupted data to the nack_data list
            print(f"{self.name}: received corrupted data {data}")
            # Simulate NACK transmission error and return the NACK and packet number
            return transmit(ack, error_rate), int(packet_number)

    def packetize_data(self, data_list):
        packets = []
        packet_number = 1
        for data in data_list:
            packet = ''
            for i in range(len(data)):
                packet += data[i]
                # If the packet reaches the specified packet size, add it to the packets list
                if len(packet) == self.packet_size:
                    packets.append((packet, packet_number))  # Add the packet and its number
                    packet = ''  # Reset the packet to an empty string
                    packet_number += 1  # Increment the packet number
            # If there is any remaining data in the packet after the loop, add it as a packet
            if packet:
                packets.append((packet, packet_number)) # Add the remaining packet and its number
                packet_number += 1   # Increment the packet number
        return packets


def stop_and_wait(sender, receiver, data_list, protocol, error_rate):
    packets = sender.packetize_data(data_list)      # Packetize the data into smaller packets
    for data, packet_number in packets:
        first_attempt = True
        while True:
            # Sender transmits data
            transmitted_data = sender.send_data(data, packet_number, protocol, error_rate, first_attempt)
            # Receiver receives data and sends acknowledgment (ACK) or negative acknowledgment (NACK)
            ack, received_packet_number = receiver.receive_data(transmitted_data, protocol, error_rate)

            print(f"{receiver.name}: sending {ack}")
            # Check if the acknowledgment is an ACK (first bits are ACK, next one are packet )
            if ack[:len(ACK)] == ACK:
                print(f"{sender.name}: received ACK. Transmission successful.")
                sender.acknowledged_packets.append(ack[len(ACK):])  # Append the original data (without ACK) from receiver to the acknowledged packets list
                break
            else:
                print(f"{sender.name}: received NACK. Resending data..")
                first_attempt = False  # Mark as a retransmission

    print_final(sender, receiver)


def go_back_n(sender, receiver, data_list, protocol, error_rate, window_size):
    packets = sender.packetize_data(data_list)
    base = 1  # The base of the window
    next_seq_num = base  # The next sequence number to be sent
    packet_count = len(packets)  # Total number of packets
    sent_packets = {}  # Dictionary to store sent packets

    # Continue while the base is within the number of packets
    while base <= packet_count:
        # Send packets within the window
        while next_seq_num < base + window_size and next_seq_num <= packet_count:
            data, packet_number = packets[next_seq_num - 1]
            # Send data and store the transmitted packet
            sent_packets[next_seq_num] = sender.send_data(data, packet_number, protocol, error_rate, first_attempt=(next_seq_num not in sent_packets))
            next_seq_num += 1

        # Receive acknowledgment for the base packet
        ack, received_packet_number = receiver.receive_data(sent_packets[base], protocol, error_rate)

        print(f"{receiver.name}: sending {ack}")
        # Check if the acknowledgment is an ACK
        if ack[:len(ACK)] == ACK:
            print(f"{sender.name}: received ACK for packet {base}.")
            sender.acknowledged_packets.append(ack[len(ACK):])
            base += 1
        else:
            print(f"{sender.name}: received NACK for packet {base}. Resending window starting from packet {base}.")
            next_seq_num = base  # Reset the next sequence number to the base to resend the window

    print_final(sender, receiver)


def selective_repeat(sender, receiver, data_list, protocol, error_rate, window_size):
    packets = sender.packetize_data(data_list)
    base = 1  # The base of the window
    next_seq_num = base  # The next sequence number to be sent
    packet_count = len(packets)  # Total number of packets
    sent_packets = {}  # Dictionary to store sent packets
    acked_packets = set()  # Set to store acknowledged packets

    while base <= packet_count:
        while next_seq_num < base + window_size and next_seq_num <= packet_count:
            data, packet_number = packets[next_seq_num - 1]
            # Send data and store the transmitted packet
            sent_packets[next_seq_num] = sender.send_data(data, packet_number, protocol, error_rate, first_attempt=(next_seq_num not in sent_packets))
            next_seq_num += 1
        # Receive acknowledgment for the base packet
        ack, received_packet_number = receiver.receive_data(sent_packets[base], protocol, error_rate)

        # Check if the acknowledgment is an ACK
        if ack[:len(ACK)] == ACK:
            print(f"{sender.name}: received ACK for packet {received_packet_number}.")
            # Add the received packet number to the list of acknowledged packets
            acked_packets.add(received_packet_number)
            # Append the original data (without ACK) from receiver to the acknowledged packets list
            sender.acknowledged_packets.append(ack[len(ACK):])
            # Move the base forward while packets are acknowledged
            while base in acked_packets:
                base += 1
        else:
            print(f"{sender.name}: received NACK for packet {received_packet_number}. Resending packet {received_packet_number}.")
            # Resend the packet for which NACK was received
            data, packet_number = packets[received_packet_number - 1]
            sent_packets[received_packet_number] = sender.send_data(data, packet_number, protocol, error_rate, first_attempt=False)

    print_final(sender, receiver)


def udp_transmission(sender, receiver, data_list, protocol, error_rate):
    packets = sender.packetize_data(data_list)
    # Iterate over each packet and its number
    for data, packet_number in packets:
        # Send data without waiting for acknowledgment
        transmitted_data = sender.send_data(data, packet_number, protocol, error_rate)
        # Receiver receives data without sending acknowledgment
        receiver.receive_data(transmitted_data, protocol, error_rate)
        # Update sender's acknowledged packets with receiver's acknowledged data
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
    packets_to_sent = len(sender.sent_data_no_retr)     # Number of packets that the sender wanted to send
    total_packets_sent = len(sender.sent_data)          # Total number of packets that the sender sent (including retransmissions)
    total_retransmissions = sender.retransmissions      # Total number of retransmissions
    retransmission_rate = total_retransmissions / total_packets_sent    # Retransmission rate

    total_packets_received = len(receiver.received_data)  # Total packets received by the receiver
    correctly_received_packets = len(receiver.ack_data)  # Number of correctly received packets
    corrupted_packets = len(receiver.nack_data)  # Number of corrupted packets

    # Calculate success and corruption rates
    success_rate = correctly_received_packets / total_packets_sent if total_packets_sent else 0  # Success rate of received packets
    corruption_rate = corrupted_packets / total_packets_received if total_packets_received else 0  # Corruption rate of received packets

    # Calculate sender's metrics based on acknowledgments received
    correctly_received_packets_correct_ACK_to_sender = len(sender.acknowledged_packets)  # Number of correctly received packets based on sender's ACKs
    success_rate_based_on_sender_ACK = correctly_received_packets_correct_ACK_to_sender / total_packets_sent if total_packets_sent else 0  # Success rate based on sender's ACKs

    # Compare sent packets and acknowledged packets
    same_elements_count = sum(1 for sent, ack in zip(sender.sent_data_no_retr, sender.acknowledged_packets) if sent == ack)  # Count of packets that match between sent and acknowledged
    different_elements_count = len(sender.sent_data_no_retr) - same_elements_count  # Count of packets that do not match
    rate = same_elements_count / packets_to_sent if packets_to_sent else 0  # Rate of successfully acknowledged packets

    print("\nTransmission Analysis:")
    print(f"The number of packets the sender wanted to send: {packets_to_sent}")
    print(f"Total packets sent by sender: {total_packets_sent}")
    print(f"Total retransmissions sent by sender: {total_retransmissions}")
    print(f"Retransmission rate: {retransmission_rate * 100:.2f}%")
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
    arq_protocol = 'UDP'
    packet_length = 10
    num_packets = 10
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