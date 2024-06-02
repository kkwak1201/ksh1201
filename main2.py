import sys
import random
import time
import os
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton, QMessageBox
from PyQt5.QtGui import QIntValidator, QIcon
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from scapy.all import *

class PacketSenderThread(QThread):
    update_status = pyqtSignal(str)

    def __init__(self, dst_ip, packet_count, interval, local, echo_request):
        super().__init__()
        self.dst_ip = dst_ip
        self.packet_count = packet_count
        self.interval = interval
        self.local = local
        self.echo_request = echo_request
        self.running = True

    def run(self):
        success_count = 0
        for _ in range(self.packet_count):
            if not self.running:
                break
            if self.local:
                src_ip = get_if_addr(conf.iface)
            else:
                src_ip = f"{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

            if self.echo_request:
                packet = IP(src=src_ip, dst=self.dst_ip) / ICMP(type=8)
            else:
                packet = IP(src=src_ip, dst=self.dst_ip) / ICMP(type=0)

            try:
                send(packet, verbose=False)
                success_count += 1
            except Exception as e:
                print(f"Failed to send packet: {e}")

            self.update_status.emit(f"Sent {success_count} out of {self.packet_count} packets successfully.")

            if self.interval > 0:
                time.sleep(self.interval)

        self.update_status.emit(f"Completed sending packets. Sent {success_count} out of {self.packet_count} packets successfully.")

    def stop(self):
        self.running = False

class ICMPGenerator(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.packet_sender_thread = None

    def initUI(self):
        # Layouts
        vbox = QVBoxLayout()
        hbox_ip_selection = QHBoxLayout()
        hbox_packet_selection = QHBoxLayout()

        # IP Selection
        self.local_checkbox = QCheckBox('Local')
        self.local_checkbox.setChecked(True)
        self.random_checkbox = QCheckBox('Random')
        self.local_checkbox.stateChanged.connect(self.update_ip_selection)
        self.random_checkbox.stateChanged.connect(self.update_ip_selection)

        hbox_ip_selection.addWidget(self.local_checkbox)
        hbox_ip_selection.addWidget(self.random_checkbox)

        # Destination IP
        self.destination_ip_label = QLabel('Destination IP:')
        self.destination_ip_input = QLineEdit()

        # Packet Count
        self.packet_count_label = QLabel('Number of Packets:')
        self.packet_count_input = QLineEdit()

        # Packet Type
        self.echo_request_checkbox = QCheckBox('Echo Request')
        self.echo_request_checkbox.setChecked(True)
        self.echo_reply_checkbox = QCheckBox('Echo Reply')
        self.echo_request_checkbox.stateChanged.connect(self.update_packet_type_selection)
        self.echo_reply_checkbox.stateChanged.connect(self.update_packet_type_selection)

        hbox_packet_selection.addWidget(self.echo_request_checkbox)
        hbox_packet_selection.addWidget(self.echo_reply_checkbox)

        # Send Interval
        self.interval_label = QLabel('Send Interval (seconds):')
        self.interval_input = QLineEdit()
        self.interval_input.setValidator(QIntValidator(0, 3600))  # Accept only integer values between 0 and 3600 seconds

        # Buttons
        self.generate_button = QPushButton('Generate')
        self.generate_button.clicked.connect(self.generate_packets)
        self.stop_button = QPushButton('Stop')
        self.stop_button.clicked.connect(self.stop_packets)
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close)

        # Response Label
        self.response_label = QLabel()

        # Add widgets to layout
        vbox.addLayout(hbox_ip_selection)
        vbox.addWidget(self.destination_ip_label)
        vbox.addWidget(self.destination_ip_input)
        vbox.addWidget(self.packet_count_label)
        vbox.addWidget(self.packet_count_input)
        vbox.addLayout(hbox_packet_selection)
        vbox.addWidget(self.interval_label)
        vbox.addWidget(self.interval_input)
        vbox.addWidget(self.generate_button)
        vbox.addWidget(self.stop_button)
        vbox.addWidget(self.close_button)
        vbox.addWidget(self.response_label)

        self.setLayout(vbox)

        self.setWindowTitle('ICMP Traffic Generator')
        
        # Get absolute path of the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(current_dir, 'ping.ico')
        
        self.setWindowIcon(QIcon(icon_path))  # Set the window icon
        
        self.resize(400, 300)  # Set initial size
        self.setFixedSize(self.size())  # Fix the window size
        self.center()  # Center the window
        self.show()

    def center(self):
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def update_ip_selection(self):
        if self.sender() == self.local_checkbox:
            self.random_checkbox.setChecked(not self.local_checkbox.isChecked())
        elif self.sender() == self.random_checkbox:
            self.local_checkbox.setChecked(not self.random_checkbox.isChecked())

    def update_packet_type_selection(self):
        if self.sender() == self.echo_request_checkbox:
            self.echo_reply_checkbox.setChecked(not self.echo_request_checkbox.isChecked())
        elif self.sender() == self.echo_reply_checkbox:
            self.echo_request_checkbox.setChecked(not self.echo_reply_checkbox.isChecked())

    def generate_packets(self):
        try:
            packet_count = int(self.packet_count_input.text())
            if packet_count <= 0:
                raise ValueError("Packet count must be a positive integer.")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", str(e))
            return

        try:
            interval = int(self.interval_input.text())
        except ValueError:
            interval = 0  # Default interval to 0 if not provided

        dst_ip = self.destination_ip_input.text()
        if not dst_ip:
            QMessageBox.warning(self, "Invalid Input", "Destination IP is required.")
            return

        local = self.local_checkbox.isChecked()
        echo_request = self.echo_request_checkbox.isChecked()

        self.packet_sender_thread = PacketSenderThread(dst_ip, packet_count, interval, local, echo_request)
        self.packet_sender_thread.update_status.connect(self.update_response_label)
        self.packet_sender_thread.start()

    def stop_packets(self):
        if self.packet_sender_thread is not None:
            self.packet_sender_thread.stop()

    def update_response_label(self, message):
        self.response_label.setText(message)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Get absolute path of the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(current_dir, 'ping.ico')
    
    app.setWindowIcon(QIcon(icon_path))  # Set the application icon
    ex = ICMPGenerator()
    sys.exit(app.exec_())
