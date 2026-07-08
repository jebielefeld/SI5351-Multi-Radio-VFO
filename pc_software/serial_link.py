###########################################################################
# serial_link.py
#
# SI5351 Multi-Radio VFO Platform
#
# Purpose:
#   Provides the serial communication interface between the PC GUI and the
#   Arduino Nano firmware.
#
# Description:
#   SerialLink is the single communication path used by the entire GUI.
#   The main window, calibration window, Developer Console, and other tools
#   all share this object instead of opening the COM port separately.
#
# Ham Radio Analogy:
#   Think of this module as the control cable between a computer and a modern
#   transceiver. Every command from the PC to the VFO controller passes
#   through this one path.
#
# Major Responsibilities:
#   - List available COM ports.
#   - Open and close the selected serial port.
#   - Send firmware commands.
#   - Read firmware responses.
#   - Format frequency commands.
#   - Format RF output enable/disable commands.
#
# Important Design Rule:
#   Only one SerialLink object should own the Arduino COM port at a time.
#   Opening the same COM port from multiple places can cause connection
#   failures or unpredictable behavior.
#
# Firmware Command Examples:
#   ID;                 Identify firmware.
#   XC0;                Read SI5351 #1 calibration.
#   F0003882000;        Set OUT0 to 3.882000 MHz.
#   E01;                Enable OUT0 RF.
#   E00;                Disable OUT0 RF.
#
# Revision History:
#   v6.1c
#       - Stable serial communication interface.
#       - Supports shared use by main GUI, calibration window, and Developer
#         Console.
#       - Supports OUT0 through OUT5 frequency and RF enable commands.
#
###########################################################################

import threading
import serial
import serial.tools.list_ports

from config import DEFAULT_BAUD, SERIAL_TIMEOUT


###########################################################################
# class SerialLink
#
# Purpose:
#   Encapsulates all low-level serial communication with the Arduino Nano.
#
# Description:
#   This class hides the details of PySerial from the rest of the GUI.
#   Other modules do not need to know how the serial port is opened, written,
#   read, or closed. They call methods such as query(), send_frequency(), or
#   send_output_enable().
#
# C/C++ Analogy:
#   This is similar to a serial-driver module or hardware-abstraction layer.
#   The GUI code uses a clean API instead of directly manipulating the UART.
#
###########################################################################
class SerialLink:
    def __init__(self):
        ###################################################################
        # ser:
        #   PySerial Serial object. None means no port is currently open.
        ###################################################################
        self.ser = None

        ###################################################################
        # listener_thread / running / callbacks:
        #   Reserved support for asynchronous serial monitoring.
        #
        #   The current application primarily uses query/response commands.
        #   These members remain available for future live-monitor features.
        ###################################################################
        self.listener_thread = None
        self.running = False
        self.callbacks = []

    #######################################################################
    # list_ports()
    #
    # Purpose:
    #   Return a list of available serial COM ports.
    #
    # Returns:
    #   List of port device names, for example:
    #       ["COM3", "COM6"]
    #
    # Notes:
    #   On Windows, Arduino Nano boards usually appear as COMx devices.
    #######################################################################
    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    #######################################################################
    # add_callback()
    #
    # Purpose:
    #   Register a callback function for future asynchronous serial receive.
    #
    # Inputs:
    #   callback:
    #       Function to call when a complete line of serial text is received.
    #
    # Notes:
    #   This is not heavily used by the present query/response design, but it
    #   provides a path for future live monitor features.
    #######################################################################
    def add_callback(self, callback):
        self.callbacks.append(callback)

    #######################################################################
    # connect()
    #
    # Purpose:
    #   Open the selected serial port.
    #
    # Inputs:
    #   port_name:
    #       COM port name, such as "COM6".
    #
    # Operation:
    #   1. Disconnect any currently open port.
    #   2. Open the requested port using the project baud rate and timeout.
    #   3. Store the PySerial object in self.ser.
    #
    # Raises:
    #   Re-raises any PySerial exception if the port cannot be opened.
    #
    # Notes:
    #   The print statements are intentional diagnostic messages. They are
    #   useful when running the Python program from a terminal or VS Code.
    #######################################################################
    def connect(self, port_name):

        print("CONNECT CALLED")
        print(f"OPEN SERIAL: {port_name}")

        # Close any previous connection before opening a new one.
        self.disconnect()

        try:
            self.ser = serial.Serial(
                port=port_name,
                baudrate=DEFAULT_BAUD,
                timeout=SERIAL_TIMEOUT,
            )

            print("SERIAL OPEN SUCCESS")

        except Exception as e:
            print("SERIAL OPEN FAILED")
            print(repr(e))
            raise

    #######################################################################
    # disconnect()
    #
    # Purpose:
    #   Close the active serial port.
    #
    # Operation:
    #   Stops any receive loop and closes the PySerial object if it is open.
    #
    # Returns:
    #   None.
    #######################################################################
    def disconnect(self):
        self.running = False

        if self.ser and self.ser.is_open:
            self.ser.close()

        self.ser = None

    #######################################################################
    # is_connected()
    #
    # Purpose:
    #   Report whether the serial port is currently open.
    #
    # Returns:
    #   True if a serial port object exists and is open.
    #   False otherwise.
    #######################################################################
    def is_connected(self):
        return self.ser is not None and self.ser.is_open

    #######################################################################
    # _read_loop()
    #
    # Purpose:
    #   Background receive loop for asynchronous serial messages.
    #
    # Operation:
    #   While running is True:
    #       - Read one line from the serial port.
    #       - Decode it as ASCII.
    #       - Strip newline characters.
    #       - Send the line to each registered callback.
    #
    # Notes:
    #   The present GUI mostly uses query(), which sends a command and waits
    #   for one response. This loop is reserved for future features such as a
    #   live monitor, continuous status stream, or diagnostic log.
    #######################################################################
    def _read_loop(self):
        while self.running:
            try:
                if not self.is_connected():
                    continue

                line = self.ser.readline().decode("ascii", errors="replace").strip()

                if not line:
                    continue

                for callback in self.callbacks:
                    callback(line)

            except Exception:
                # Do not allow a serial read error to crash the GUI.
                pass

    #######################################################################
    # query()
    #
    # Purpose:
    #   Send one command to the firmware and return one response line.
    #
    # Inputs:
    #   command:
    #       ASCII command string to send to the Arduino firmware.
    #       Most commands end with a semicolon.
    #
    # Outputs:
    #   Writes the command to the serial port.
    #
    # Returns:
    #   Response string received from the firmware.
    #
    # Raises:
    #   RuntimeError if the serial port is not connected.
    #
    # Notes:
    #   reset_input_buffer() clears stale serial data before sending the new
    #   command. This helps keep command/response pairs synchronized.
    #######################################################################
    def query(self, command):
        if not self.is_connected():
            raise RuntimeError("Serial port is not connected")

        self.ser.reset_input_buffer()
        self.ser.write(command.encode("ascii"))

        response = self.ser.readline().decode("ascii", errors="replace").strip()
        return response

    #######################################################################
    # send_frequency()
    #
    # Purpose:
    #   Send a frequency command to one RF output.
    #
    # Inputs:
    #   freq_hz:
    #       Desired RF output frequency in Hertz.
    #
    #   output:
    #       Output name. Expected format is "OUT0" through "OUT5".
    #       "CLK0" through "CLK5" are accepted for legacy compatibility.
    #
    # Returns:
    #   Firmware response string returned by query().
    #
    # Raises:
    #   RuntimeError if the serial port is not connected.
    #   ValueError if the output name is invalid.
    #
    # Firmware Command Format:
    #   F<output><frequency>;
    #
    # Example:
    #   OUT0 at 3.882 MHz becomes:
    #       F0003882000;
    #
    # Notes:
    #   Frequency is formatted as an 11-digit integer field. This matches the
    #   Arduino firmware command parser.
    #######################################################################
    def send_frequency(self, freq_hz, output):
        if not self.is_connected():
            raise RuntimeError("Serial port is not connected")

        output = str(output).upper().strip()

        # Accept older CLK naming but convert it to the current OUT naming.
        output = output.replace("CLK", "OUT")

        if not output.startswith("OUT"):
            raise ValueError(f"Invalid output name: {output}")

        try:
            output_num = int(output[3:])
        except ValueError:
            raise ValueError(f"Invalid output name: {output}")

        if output_num < 0 or output_num > 5:
            raise ValueError("Output must be OUT0 through OUT5")

        command = f"F{output_num}{int(freq_hz):011d};"
        return self.query(command)

    #######################################################################
    # send_output_enable()
    #
    # Purpose:
    #   Send RF output enable or disable command.
    #
    # Inputs:
    #   output_name:
    #       Output name, "OUT0" through "OUT5".
    #       "CLK0" through "CLK5" are accepted for legacy compatibility.
    #
    #   enabled:
    #       True  = RF output ON.
    #       False = RF output OFF.
    #
    # Outputs:
    #   Writes the enable/disable command to the serial port.
    #
    # Returns:
    #   The command string that was sent.
    #
    # Raises:
    #   RuntimeError if the serial port is not connected.
    #   ValueError if the output name is invalid or out of range.
    #
    # Firmware Command Format:
    #   E<output><state>;
    #
    # Examples:
    #   E01; = OUT0 ON
    #   E00; = OUT0 OFF
    #   E31; = OUT3 ON
    #   E30; = OUT3 OFF
    #
    # Notes:
    #   Unlike send_frequency(), this method writes directly to the serial
    #   port and does not wait for a firmware response. This preserves the
    #   existing behavior of the working release.
    #######################################################################
    def send_output_enable(self, output_name, enabled):
        if not self.is_connected():
            raise RuntimeError("Serial port is not connected")

        out = output_name.upper().replace("CLK", "OUT")

        if not out.startswith("OUT"):
            raise ValueError(f"Invalid output name: {output_name}")

        out_num = int(out[3:])

        if out_num < 0 or out_num > 5:
            raise ValueError(f"Output out of range: {output_name}")

        state = "1" if enabled else "0"
        command = f"E{out_num}{state};"

        self.ser.write(command.encode("ascii"))
        return command
