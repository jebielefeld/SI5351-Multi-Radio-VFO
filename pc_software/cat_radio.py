class CatRadio:
    def __init__(self, serial_link):
        self.link = serial_link

    def get_id(self):
        return self.link.query("ID;")

    def get_frequency(self):
        return self.link.query("FA;")

    def set_frequency(self, hz):
        command = f"FA{hz:011d};"
        return self.link.query(command)

    def rf_on(self):
        return self.link.query("OE1;")

    def rf_off(self):
        return self.link.query("OE0;")

    def get_output_enable(self):
        return self.link.query("OE;")

    def get_calibration(self):
        return self.link.query("XC;")