import csv
from itertools import product
from utils import generate_bit_string
from pc import PC, stop_and_wait, go_back_n, selective_repeat, udp_transmission


class Tests:
    def __init__(self):
        self.error_rates = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 5]
        self.packet_sizes = [10, 20, 40, 80, 160, 320, 640, 1280]
        self.error_detection_codes = ['parity', 'crc', 'md5', 'none']
        self.arq_protocols = ['Stop-and-Wait', 'Go-Back-N', 'Selective Repeat', 'UDP']
        self.window_sizes = [16, 32, 64, 128]

    def run_tests(self):
        with open('test_results.csv', 'w', newline='') as csvfile:
            fieldnames = ['Error Rate', 'Packet Size', 'Error Detection Code', 'ARQ Protocol', 'Window Size', 'Success Rate', 'Overhead', 'Errors']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=';')
            writer.writeheader()

            for error_rate, packet_size, error_detection_code, arq_protocol in product(
                    self.error_rates, self.packet_sizes, self.error_detection_codes, self.arq_protocols):

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

        success_rate = len(receiver.ack_data) / len(sender.sent_data) if len(sender.sent_data) else 0
        number_of_incorect_ack_data = 0
        same_elements_count = sum(1 for sent, ack in zip(sender.sent_data_no_retr, sender.acknowledged_packets) if sent == ack)
        number_of_incorect_ack_data = len(sender.sent_data_no_retr) - same_elements_count
        overhead = len(sender.sent_data)

        writer.writerow({'Error Rate': error_rate, 'Packet Size': packet_size, 'Error Detection Code': error_detection_code, 'ARQ Protocol': arq_protocol,
                         'Window Size': window_size, 'Success Rate': success_rate, 'Overhead': overhead, 'Errors': number_of_incorect_ack_data})

if __name__ == "__main__":
    tests = Tests()
    tests.run_tests()
