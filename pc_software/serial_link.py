# File: serial_link.py

import threading
import serial
import serial.tools.list_ports

from config import DEFAULT_BAUD, SERIAL_TIMEOUT


class SerialLink:
    def __init__(self):
        self.ser = None
        self.listener_thread = None
        self.running = False
        self.callbacks = []

    def list_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def connect(self, port_name):
        self.disconnect()

        self.ser = serial.Serial(
            port=port_name,
            baudrate=DEFAULT_BAUD,
            timeout=SERIAL_TIMEOUT,
        )

        self.running = True
        self.listener_thread = threading.Thread(
            target=self._read_loop,
            daemon=True,
        )
        self.listener_thread.start()

    def disconnect(self):
        self.running = False

        if self.ser and self.ser.is_open:
            self.ser.close()

        self.ser = None

    def is_connected(self):
        return self.ser is not None and self.ser.is_open

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
                pass

    def query(self, command):
        if not self.is_connected():
            raise RuntimeError("Serial port is not connected")

        self.ser.reset_input_buffer()
        self.ser.write(command.encode("ascii"))

        response = self.ser.readline().decode("ascii", errors="replace").strip()
        return response

    def send_frequency(self, freq_hz, output):
        if not self.is_connected():
            raise RuntimeError("Serial port is not connected")

        output = str(output).upper().strip()
        output = output.replace("CLK", "OUT")  # legacy safety

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

    def send_output_enable(self, output_name, enabled):
        """
        Send RF output enable command.

        output_name: "OUT0" through "OUT5"
        enabled: True = RF ON, False = RF OFF

        Command format:
            E01; = OUT0 ON
            E00; = OUT0 OFF
            E31; = OUT3 ON
            E30; = OUT3 OFF
        """
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
