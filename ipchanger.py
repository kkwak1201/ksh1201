import sys
import psutil
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QComboBox, QRadioButton, QLineEdit, 
                             QPushButton, QButtonGroup, QMessageBox, QFormLayout)
from PyQt5.QtCore import Qt
import subprocess
import ctypes

class IPChanger(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('IP Changer')

        layout = QVBoxLayout()

        # Network Adapter Selection
        adapter_layout = QHBoxLayout()
        adapter_label = QLabel('Network Adapter:')
        self.adapter_combo = QComboBox()
        self.load_adapters()
        adapter_layout.addWidget(adapter_label)
        adapter_layout.addWidget(self.adapter_combo)
        layout.addLayout(adapter_layout)

        # IP Configuration
        ip_config_group = QVBoxLayout()
        
        self.dhcp_radio = QRadioButton('DHCP')
        self.static_radio = QRadioButton('Static IP')
        self.ip_group = QButtonGroup()
        self.ip_group.addButton(self.dhcp_radio)
        self.ip_group.addButton(self.static_radio)
        
        ip_config_group.addWidget(self.dhcp_radio)
        ip_config_group.addWidget(self.static_radio)
        
        form_layout = QFormLayout()
        
        self.ip_address_input = QLineEdit()
        self.subnet_input = QLineEdit()
        self.gateway_input = QLineEdit()
        
        form_layout.addRow('IP Address:', self.ip_address_input)
        form_layout.addRow('Subnet Mask:', self.subnet_input)
        form_layout.addRow('Default Gateway:', self.gateway_input)
        
        ip_config_group.addLayout(form_layout)
        layout.addLayout(ip_config_group)

        # DNS Configuration
        dns_group = QVBoxLayout()
        
        self.auto_dns_radio = QRadioButton('자동으로 DNS 서버 주소 받기')
        self.manual_dns_radio = QRadioButton('다음 DNS 서버 주소 사용:')
        self.dns_group = QButtonGroup()
        self.dns_group.addButton(self.auto_dns_radio)
        self.dns_group.addButton(self.manual_dns_radio)
        
        dns_group.addWidget(self.auto_dns_radio)
        dns_group.addWidget(self.manual_dns_radio)
        
        dns_form_layout = QFormLayout()
        
        self.preferred_dns_input = QLineEdit()
        self.alternate_dns_input = QLineEdit()
        
        dns_form_layout.addRow('기본 설정 DNS 서버:', self.preferred_dns_input)
        dns_form_layout.addRow('보조 DNS 서버:', self.alternate_dns_input)
        
        dns_group.addLayout(dns_form_layout)
        layout.addLayout(dns_group)

        # Apply Button
        apply_button = QPushButton('Apply')
        apply_button.clicked.connect(self.apply_settings)
        layout.addWidget(apply_button)

        self.setLayout(layout)

        # Signal Connections for Enabling/Disabling Fields
        self.dhcp_radio.toggled.connect(self.toggle_ip_fields)
        self.auto_dns_radio.toggled.connect(self.toggle_dns_fields)

        # Set Initial States
        self.dhcp_radio.setChecked(True)
        self.auto_dns_radio.setChecked(True)
        self.toggle_ip_fields()
        self.toggle_dns_fields()

    def load_adapters(self):
        adapters = self.get_network_adapters()
        self.adapter_combo.addItems(adapters)

    def get_network_adapters(self):
        adapters = []
        for name, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == psutil.AF_LINK:
                    adapters.append(name)
        return adapters

    def apply_settings(self):
        adapter = self.adapter_combo.currentText()
        
        if self.dhcp_radio.isChecked():
            self.set_dhcp(adapter)
        elif self.static_radio.isChecked():
            ip = self.ip_address_input.text()
            subnet = self.subnet_input.text()
            gateway = self.gateway_input.text()
            self.set_static_ip(adapter, ip, subnet, gateway)

        if self.auto_dns_radio.isChecked():
            self.set_auto_dns(adapter)
        elif self.manual_dns_radio.isChecked():
            preferred_dns = self.preferred_dns_input.text()
            alternate_dns = self.alternate_dns_input.text()
            self.set_manual_dns(adapter, preferred_dns, alternate_dns)

        QMessageBox.information(self, 'Settings Applied', 'Network settings have been updated.')

    def toggle_ip_fields(self):
        is_dhcp = self.dhcp_radio.isChecked()
        self.ip_address_input.setDisabled(is_dhcp)
        self.subnet_input.setDisabled(is_dhcp)
        self.gateway_input.setDisabled(is_dhcp)

    def toggle_dns_fields(self):
        is_auto_dns = self.auto_dns_radio.isChecked()
        self.preferred_dns_input.setDisabled(is_auto_dns)
        self.alternate_dns_input.setDisabled(is_auto_dns)

    def set_dhcp(self, adapter):
        command = f'netsh interface ip set address "{adapter}" dhcp'
        subprocess.run(command, shell=True)
        command = f'netsh interface ip set dns "{adapter}" dhcp'
        subprocess.run(command, shell=True)

    def set_static_ip(self, adapter, ip, subnet, gateway):
        command = f'netsh interface ip set address "{adapter}" static {ip} {subnet} {gateway}'
        subprocess.run(command, shell=True)

    def set_auto_dns(self, adapter):
        command = f'netsh interface ip set dns "{adapter}" dhcp'
        subprocess.run(command, shell=True)

    def set_manual_dns(self, adapter, preferred_dns, alternate_dns):
        command = f'netsh interface ip set dns "{adapter}" static {preferred_dns}'
        subprocess.run(command, shell=True)
        if alternate_dns:
            command = f'netsh interface ip add dns "{adapter}" {alternate_dns} index=2'
            subprocess.run(command, shell=True)

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if __name__ == '__main__':
    if is_admin():
        app = QApplication(sys.argv)
        window = IPChanger()
        window.show()
        sys.exit(app.exec_())
    else:
        # 재실행하여 관리자 권한 요청
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
