import csv
from itertools import product
from utils import generate_bit_string
from pc import PC, stop_and_wait, go_back_n, selective_repeat, udp_transmission
from collections import Counter

class Tests:
    def __init__(self):
        self.error_rates = [0.0005, 0.001, 0.005, 0.01, 0.05]  #0.05%, 0.1%, 0.5%, 1%, 5%
        self.packet_sizes = [10, 50, 100, 200, 300, 400]
        self.error_detection_codes = ['parity', 'crc', 'md5', 'none']
        self.arq_protocols = ['Stop-and-Wait', 'Go-Back-N', 'Selective Repeat', 'UDP']
        self.window_sizes = [10, 20, 50, 100]

    def run_tests(self):
        with open('test_results1.csv', 'w', newline='') as csvfile:
            fieldnames = ['ARQ Protocol', 'Error Detection Code', 'Window Size', 'Error Rate', 'Packet Size',
                          'Success Rate', 'Correct ACK', 'Retransmition rate', 'Total packet send']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()

            for error_detection_code in self.error_detection_codes:
                for arq_protocol in self.arq_protocols:
                    for error_rate in self.error_rates:
                        for packet_size in self.packet_sizes:
                            if arq_protocol in ['Go-Back-N', 'Selective Repeat']:
                                for window_size in self.window_sizes:
                                    self.run_single_test(writer, error_rate, packet_size, error_detection_code, arq_protocol, window_size)
                            else:
                                self.run_single_test(writer, error_rate, packet_size, error_detection_code, arq_protocol, 'N/A')

    def run_single_test(self, writer, error_rate, packet_size, error_detection_code, arq_protocol, window_size):
        data_list = [generate_bit_string(packet_size) for _ in range(50000)]  # generate 50000 packets
        sender = PC("Sender", packet_size=packet_size)
        receiver = PC("Receiver", packet_size=packet_size)

        if arq_protocol == 'Stop-and-Wait':
            stop_and_wait(sender, receiver, data_list, protocol=error_detection_code, error_rate=error_rate)
        elif arq_protocol == 'Go-Back-N':
            go_back_n(sender, receiver, data_list, protocol=error_detection_code, error_rate=error_rate, window_size=window_size)
        elif arq_protocol == 'Selective Repeat':
            selective_repeat(sender, receiver, data_list, protocol=error_detection_code, error_rate=error_rate, window_size=window_size)
        elif arq_protocol == 'UDP':
            udp_transmission(sender, receiver, data_list, protocol=error_detection_code, error_rate=error_rate)
        else:
            raise ValueError("Unsupported ARQ Protocol")

        #Analize transmition
        packets_to_sent = len(sender.sent_data_no_retr)
        number_of_packet_send = len(sender.sent_data)
        success_rate = len(sender.acknowledged_packets) / number_of_packet_send if number_of_packet_send else 0

        sent_counter = Counter(sender.sent_data_no_retr)
        ack_counter = Counter(sender.acknowledged_packets)

        # Find common elements and their counts
        common_elements = sent_counter & ack_counter
        same_elements_count = sum(common_elements.values())  # Count of packets that match between sent and acknowledged
        rate = same_elements_count / packets_to_sent if packets_to_sent else 0  # Rate of successfully acknowledged packets
        total_retransmissions = sender.retransmissions
        retranssmision_rate = total_retransmissions / number_of_packet_send

        writer.writerow({
                        'ARQ Protocol': arq_protocol,
                        'Error Detection Code': error_detection_code,
                        'Window Size': window_size,
                        'Error Rate': error_rate,
                        'Packet Size': packet_size,
                        'Success Rate': success_rate,
                        'Correct ACK': rate,
                        'Retransmition rate': retranssmision_rate,
                        'Total packet send': number_of_packet_send})

if __name__ == "__main__":
    tests = Tests()
    tests.run_tests()
