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
    def __init__(self, parent=None):
        super().__init__(parent)

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

        self.append_log("Developer Console Phase 1")
        self.append_log("Serial connection not active yet.")
        self.append_log("This window is currently a GUI framework test.\n")

    def send_command(self):
        command = self.command_entry.text().strip()

        if not command:
            return

        self.append_log(f"> {command}")
        self.append_log("Placeholder only — serial send not connected yet.\n")

        self.command_entry.clear()

    def append_log(self, text):
        self.log_box.append(text)

        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
