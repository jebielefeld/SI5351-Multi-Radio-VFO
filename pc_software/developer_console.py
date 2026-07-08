###########################################################################
# developer_console.py
#
# SI5351 Multi-Radio VFO Platform
#
# Purpose:
#   Provides the Developer Console window for the PC GUI application.
#
#   The Developer Console allows the operator, builder, or developer to send
#   manual CAT-style commands directly to the Arduino Nano firmware through
#   the existing SerialLink object.
#
# Description:
#   This window acts like a simple engineering terminal built into the GUI.
#   It replaces the need to open the Arduino Serial Monitor while the PC
#   application is running.
#
#   The console shares the same serial connection used by the main GUI.
#   This is important because only one program should control the Arduino
#   COM port at a time.
#
# Ham Radio Analogy:
#   Think of this window as a service port or test jack on a piece of radio
#   equipment. It gives the operator direct access to the controller for
#   testing, troubleshooting, and verification.
#
# Major Features:
#   - Manual command entry
#   - Automatic semicolon insertion
#   - TX/RX text log
#   - Shared serial connection with the main GUI
#   - Up/Down arrow command history
#   - Auto-scroll to newest response
#
# Important Design Rule:
#   This module does not open the serial port itself. It uses the existing
#   SerialLink object passed in from the main application.
#
# Revision History:
#   v6.1c Phase 3A
#       - Developer Console separated into its own module.
#       - Added manual command entry.
#       - Added TX/RX log display.
#       - Added command history using a custom QLineEdit subclass.
#       - Verified operation through shared SerialLink connection.
#
###########################################################################

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QLabel,
)

from PySide6.QtCore import Qt


###########################################################################
# class CommandLineEdit
#
# Purpose:
#   Custom command-entry text box used by the Developer Console.
#
# Description:
#   QLineEdit is the normal Qt single-line text entry widget. This subclass
#   adds terminal-style command history using the keyboard Up and Down arrows.
#
# Why This Class Exists:
#   Earlier versions used an event filter to catch key presses. This custom
#   widget is cleaner and more reliable because the command entry field owns
#   its own keyboard behavior.
#
# C/C++ Analogy:
#   This is similar to deriving a custom C++ class from a base widget class
#   and overriding a virtual keyboard handler.
#
# Inputs:
#   console:
#       Reference to the parent DeveloperConsole object. This lets the entry
#       field call recall_previous_command() and recall_next_command().
#
# Outputs:
#   None directly. It updates the text displayed in the command entry field.
#
###########################################################################
class CommandLineEdit(QLineEdit):
    def __init__(self, console, parent=None):
        super().__init__(parent)

        # Store a reference to the owning console window.
        # This is used to access the command-history methods.
        self.console = console

    #######################################################################
    # keyPressEvent()
    #
    # Purpose:
    #   Handle keyboard input for the command entry field.
    #
    # Operation:
    #   - Up Arrow recalls the previous command.
    #   - Down Arrow recalls the next command.
    #   - All other keys are handled by the normal QLineEdit behavior.
    #
    # Notes:
    #   Calling super().keyPressEvent(event) allows Qt to handle normal text
    #   entry, editing, cursor movement, Backspace, Delete, etc.
    #######################################################################
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Up:
            self.console.recall_previous_command()
            return

        if event.key() == Qt.Key_Down:
            self.console.recall_next_command()
            return

        # For all other keys, use the standard QLineEdit behavior.
        super().keyPressEvent(event)


###########################################################################
# class DeveloperConsole
#
# Purpose:
#   Main Developer Console dialog window.
#
# Description:
#   This dialog provides a built-in engineering terminal for the SI5351 VFO
#   controller. Commands typed into this window are sent to the Arduino Nano
#   firmware through the existing SerialLink object.
#
# Typical Commands:
#   ID;     Ask the Nano to identify itself.
#   XC0;    Read calibration value for SI5351 module #1.
#   XC1;    Read calibration value for SI5351 module #2.
#
# Design Notes:
#   The console intentionally uses the existing GUI serial connection. This
#   prevents COM-port conflicts and allows the operator to troubleshoot the
#   firmware without closing the main application.
#
###########################################################################
class DeveloperConsole(QDialog):
    def __init__(self, link, parent=None):
        super().__init__(parent)

        # Shared SerialLink object.
        # This is the same communication path used by the main GUI.
        self.link = link

        # Command history storage.
        # This behaves like a small terminal command buffer.
        self.command_history = []

        # Current position while browsing command history.
        # None means the user is not currently browsing history.
        self.history_index = None

        self.setWindowTitle("Developer Console")
        self.resize(700, 450)

        # Multi-line read-only text area used for the TX/RX log.
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        # Single-line command entry field with custom history support.
        self.command_entry = CommandLineEdit(self)
        self.command_entry.setPlaceholderText("Enter command, example: ID;")

        self.send_button = QPushButton("Send")
        self.clear_button = QPushButton("Clear")
        self.close_button = QPushButton("Close")

        # Horizontal row containing command label, entry field, and Send.
        command_layout = QHBoxLayout()
        command_layout.addWidget(QLabel("Command:"))
        command_layout.addWidget(self.command_entry)
        command_layout.addWidget(self.send_button)

        # Bottom button row.
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.close_button)

        # Main vertical window layout.
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.log_box)
        main_layout.addLayout(command_layout)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Qt signal/slot connections.
        # C/C++ analogy: these are callback connections between GUI events
        # and the functions that handle those events.
        self.send_button.clicked.connect(self.send_command)
        self.command_entry.returnPressed.connect(self.send_command)
        self.clear_button.clicked.connect(self.log_box.clear)
        self.close_button.clicked.connect(self.close)

        # Startup banner shown whenever the console opens.
        self.append_log("SI5351 Multi-Radio VFO Developer Console")
        self.append_log("Engineering Interface Ready")
        self.append_log("-" * 60)
        self.append_log("")

    #######################################################################
    # send_command()
    #
    # Purpose:
    #   Send the command currently typed into the command entry box.
    #
    # Operation:
    #   1. Read the text from the command entry field.
    #   2. Ignore empty commands.
    #   3. Add the required ';' terminator if the user omitted it.
    #   4. Store the command in history.
    #   5. Send the command through SerialLink.
    #   6. Display the firmware response in the log window.
    #
    # Inputs:
    #   None directly. Uses text from self.command_entry.
    #
    # Outputs:
    #   Sends a command string to the Arduino Nano.
    #   Displays TX/RX text in the console log.
    #
    # Returns:
    #   None.
    #
    # Notes:
    #   Firmware commands use a semicolon terminator, similar to many CAT
    #   command protocols used by amateur radio equipment.
    #######################################################################
    def send_command(self):
        command = self.command_entry.text().strip()

        if not command:
            return

        # Firmware commands end with ';'. Add it if the user forgets.
        if not command.endswith(";"):
            command += ";"

        # Store command in history unless it duplicates the last command.
        if not self.command_history or self.command_history[-1] != command:
            self.command_history.append(command)

        # Reset history browsing after a new command is sent.
        self.history_index = None

        self.append_log(f"TX> {command}")

        try:
            # Do not attempt communication if the COM port is not connected.
            if not self.link.is_connected():
                self.append_log("RX< ERROR: Serial port is not connected")
                self.append_log("")
                self.command_entry.clear()
                return

            # Send command and wait for the firmware response.
            response = self.link.query(command)

            if response:
                self.append_log(f"RX< {response}")
            else:
                self.append_log("RX< No response")

            self.append_log("")

        except Exception as e:
            # Keep the GUI alive even if a serial error occurs.
            self.append_log(f"RX< ERROR: {e}")
            self.append_log("")

        self.command_entry.clear()

    #######################################################################
    # recall_previous_command()
    #
    # Purpose:
    #   Recall older commands using the Up Arrow key.
    #
    # Operation:
    #   Each press of Up Arrow moves one step backward through the command
    #   history, similar to a terminal or command prompt.
    #
    # Inputs:
    #   None.
    #
    # Outputs:
    #   Updates the command entry field with a previous command.
    #
    # Returns:
    #   None.
    #######################################################################
    def recall_previous_command(self):
        if not self.command_history:
            return

        if self.history_index is None:
            self.history_index = len(self.command_history) - 1
        else:
            self.history_index = max(0, self.history_index - 1)

        self.command_entry.setText(self.command_history[self.history_index])
        self.command_entry.setCursorPosition(len(self.command_entry.text()))

    #######################################################################
    # recall_next_command()
    #
    # Purpose:
    #   Recall newer commands using the Down Arrow key.
    #
    # Operation:
    #   Each press of Down Arrow moves one step forward through the command
    #   history. When the newest command has been passed, the entry box is
    #   cleared so the user can type a new command.
    #
    # Inputs:
    #   None.
    #
    # Outputs:
    #   Updates or clears the command entry field.
    #
    # Returns:
    #   None.
    #######################################################################
    def recall_next_command(self):
        if not self.command_history:
            return

        if self.history_index is None:
            return

        self.history_index += 1

        if self.history_index >= len(self.command_history):
            self.history_index = None
            self.command_entry.clear()
            return

        self.command_entry.setText(self.command_history[self.history_index])
        self.command_entry.setCursorPosition(len(self.command_entry.text()))

    #######################################################################
    # append_log()
    #
    # Purpose:
    #   Add text to the console log and scroll to the newest line.
    #
    # Inputs:
    #   text:
    #       Text string to display in the console log.
    #
    # Outputs:
    #   Updates the QTextEdit log display.
    #
    # Returns:
    #   None.
    #
    # Notes:
    #   Auto-scroll keeps the newest TX/RX activity visible, which is helpful
    #   when repeatedly testing firmware commands.
    #######################################################################
    def append_log(self, text):
        self.log_box.append(text)

        # Scroll to the bottom so the newest message is visible.
        scrollbar = self.log_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
