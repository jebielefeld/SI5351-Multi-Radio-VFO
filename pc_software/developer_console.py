from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)


class DeveloperConsole(QDialog):
    def __init__(self, link, parent=None):
        super().__init__(parent)

        self.link = link

        self.setWindowTitle("Developer Console")
        self.resize(700, 450)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.command_entry = QLineEdit()
        self.command_entry.setPlaceholderText("Enter command, example: ID;")

        self.send_button = QPushButton("Send")
        self.clear_button = QPushButton("Clear")
        self.close_button = QPushButton("Close")

        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Command:"))
        command_layout.addWidget(self.command_entry)
        command_layout.addWidget(self.send_button)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.close_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.log_box)
        main_layout.addLayout(command_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        self.send_button.clicked.connect(self.send_command)
        self.command_entry.returnPressed.connect(self.send_command)
        self.clear_button.clicked.connect(self.log_box.clear)
        self.close_button.clicked.connect(self.close)

        self.append_log("SI5351 Multi-Radio VFO Developer Console")
        self.append_log("Engineering Interface Ready")
        self.append_log("-" * 60)
        self.append_log("")

    def send_command(self):
        command = self.command_entry.text().strip()

        if not command:
            return

        if not command.endswith(";"):
            command += ";"

        self.append_log(f"TX> {command}")

        try:
            if not self.link.is_connected():
                self.append_log("< ERROR: Serial port is not connected\n")
                self.command_entry.clear()
                return

            response = self.link.query(command)

            if response:
                self.append_log(f"RX< {response}")
                self.append_log("")
            else:
                self.append_log("RX< No response")
                self.append_log("")

        except Exception as e:
            self.append_log(f"RX< ERROR: {e}")
            self.append_log("")

        self.command_entry.clear()

    def append_log(self, text):
        self.log_box.append(text)

        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
