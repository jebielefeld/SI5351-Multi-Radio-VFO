/*
  File: hardware_diag_v1b_low_level_si5351.ino
  SI5351 Multi-Radio VFO Hardware Diagnostic Sketch
  Version: v1b LOW-LEVEL SI5351

  Commands:
    ID;       firmware alive test
    SCAN;     main I2C + TCA channel scan
    RFTEST;   set BNC1..BNC6 to 10/20/30/40/50/60 MHz
    RFOFF;    disable all SI5351 outputs
    PTT;      print current PTT states
    HELP;     show command list

  Hardware:
    Nano A4 -> TCA9548A SDA
    Nano A5 -> TCA9548A SCL
    TCA9548A address 0x70
    SI5351 #1 on TCA channel 0
    SI5351 #2 on TCA channel 1

  PTT:
    LOW  = TX
    HIGH = RX

  Serial Monitor:
    115200 baud
*/

#include <Wire.h>

#define SERIAL_BAUD 115200
#define TCA_ADDR 0x70
#define SI5351_ADDR 0x60
#define LED_PIN 13

#define SI5351_OUTPUT_ENABLE   3
#define SI5351_CLK0_CONTROL    16
#define SI5351_CLK1_CONTROL    17
#define SI5351_CLK2_CONTROL    18
#define SI5351_PLLA_PARAMETERS 26
#define SI5351_MS0_PARAMETERS  42
#define SI5351_MS1_PARAMETERS  50
#define SI5351_MS2_PARAMETERS  58
#define SI5351_PLL_RESET       177
#define SI5351_XTAL_LOAD       183

const uint8_t PTT_COUNT = 6;
const uint8_t PTT_PINS[PTT_COUNT] = {2, 3, 4, 5, 6, 7};
const unsigned long PTT_DEBOUNCE_MS = 25;

char cmdBuf[16];
uint8_t cmdLen = 0;

bool pttStableState[PTT_COUNT];
bool pttLastRawState[PTT_COUNT];
unsigned long pttLastChangeMs[PTT_COUNT];

void blinkLed(uint8_t count) {
  for (uint8_t i = 0; i < count; i++) {
    digitalWrite(LED_PIN, HIGH);
    delay(80);
    digitalWrite(LED_PIN, LOW);
    delay(80);
  }
}

void printHexAddress(uint8_t addr) {
  Serial.print(F("0x"));
  if (addr < 16) Serial.print(F("0"));
  Serial.print(addr, HEX);
}

bool i2cDevicePresent(uint8_t address) {
  Wire.beginTransmission(address);
  return (Wire.endTransmission() == 0);
}

bool tcaSelect(uint8_t channel) {
  if (channel > 7) return false;
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << channel);
  uint8_t err = Wire.endTransmission();
  delay(5);
  return (err == 0);
}

void tcaDisableAll() {
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(0x00);
  Wire.endTransmission();
  delay(5);
}

bool si5351Write8(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(SI5351_ADDR);
  Wire.write(reg);
  Wire.write(value);
  return (Wire.endTransmission() == 0);
}

bool si5351WriteBulk(uint8_t startReg, const uint8_t *data, uint8_t len) {
  Wire.beginTransmission(SI5351_ADDR);
  Wire.write(startReg);
  for (uint8_t i = 0; i < len; i++) {
    Wire.write(data[i]);
  }
  return (Wire.endTransmission() == 0);
}

void makeSi5351Params(uint32_t a, uint8_t out[8]) {
  uint32_t p1 = 128UL * a - 512UL;
  uint32_t p2 = 0;
  uint32_t p3 = 1;

  out[0] = (p3 >> 8) & 0xFF;
  out[1] = p3 & 0xFF;
  out[2] = (p1 >> 16) & 0x03;
  out[3] = (p1 >> 8) & 0xFF;
  out[4] = p1 & 0xFF;
  out[5] = ((p3 >> 12) & 0xF0) | ((p2 >> 16) & 0x0F);
  out[6] = (p2 >> 8) & 0xFF;
  out[7] = p2 & 0xFF;
}

bool si5351SetupIntegerClock(uint8_t clk, uint32_t divider) {
  uint8_t params[8];
  uint8_t baseReg;
  uint8_t ctrlReg;

  if (clk == 0) {
    baseReg = SI5351_MS0_PARAMETERS;
    ctrlReg = SI5351_CLK0_CONTROL;
  } else if (clk == 1) {
    baseReg = SI5351_MS1_PARAMETERS;
    ctrlReg = SI5351_CLK1_CONTROL;
  } else if (clk == 2) {
    baseReg = SI5351_MS2_PARAMETERS;
    ctrlReg = SI5351_CLK2_CONTROL;
  } else {
    return false;
  }

  makeSi5351Params(divider, params);
  if (!si5351WriteBulk(baseReg, params, 8)) return false;

  // Enabled, integer mode, PLLA, multisynth source, 8 mA drive.
  if (!si5351Write8(ctrlReg, 0x4F)) return false;

  return true;
}

bool si5351LowLevelInitChannel(uint8_t channel) {
  if (!tcaSelect(channel)) {
    Serial.print(F("ERROR: Could not select TCA channel "));
    Serial.println(channel);
    return false;
  }

  if (!i2cDevicePresent(SI5351_ADDR)) {
    Serial.print(F("ERROR: No SI5351 found on TCA channel "));
    Serial.println(channel);
    return false;
  }

  // Disable all outputs while programming.
  if (!si5351Write8(SI5351_OUTPUT_ENABLE, 0xFF)) return false;

  // Disable CLK0/1/2 while programming.
  si5351Write8(SI5351_CLK0_CONTROL, 0x80);
  si5351Write8(SI5351_CLK1_CONTROL, 0x80);
  si5351Write8(SI5351_CLK2_CONTROL, 0x80);

  // Crystal load capacitance. 0xD2 is commonly used for 10 pF on Si5351A.
  si5351Write8(SI5351_XTAL_LOAD, 0xD2);

  // PLLA = 600 MHz assuming 25 MHz crystal, multiplier = 24.
  uint8_t pllParams[8];
  makeSi5351Params(24, pllParams);
  if (!si5351WriteBulk(SI5351_PLLA_PARAMETERS, pllParams, 8)) return false;

  // Reset PLLA and PLLB.
  si5351Write8(SI5351_PLL_RESET, 0xA0);
  delay(10);

  return true;
}

void scanMainBus() {
  Serial.println();
  Serial.println(F("=== I2C MAIN BUS SCAN ==="));
  bool foundAny = false;

  for (uint8_t addr = 1; addr < 127; addr++) {
    Wire.beginTransmission(addr);
    uint8_t error = Wire.endTransmission();
    if (error == 0) {
      Serial.print(F("Found device at "));
      printHexAddress(addr);
      Serial.println();
      foundAny = true;
    }
  }

  if (!foundAny) Serial.println(F("No I2C devices found on main bus."));
  Serial.println(F("=== END MAIN BUS SCAN ==="));
  Serial.println();
}

void scanTcaChannels() {
  Serial.println();
  Serial.println(F("=== TCA9548A CHANNEL SCAN ==="));

  if (!i2cDevicePresent(TCA_ADDR)) {
    Serial.print(F("ERROR: TCA9548A not found at "));
    printHexAddress(TCA_ADDR);
    Serial.println();
    Serial.println(F("Check Nano A4/A5, VCC, GND, SDA, SCL, A0/A1/A2."));
    Serial.println(F("=== END TCA SCAN ==="));
    Serial.println();
    return;
  }

  Serial.print(F("TCA9548A found at "));
  printHexAddress(TCA_ADDR);
  Serial.println();

  for (uint8_t ch = 0; ch < 8; ch++) {
    tcaSelect(ch);
    Serial.print(F("Channel "));
    Serial.print(ch);
    Serial.println(F(":"));
    bool foundAny = false;

    for (uint8_t addr = 1; addr < 127; addr++) {
      if (addr == TCA_ADDR) continue;
      Wire.beginTransmission(addr);
      uint8_t error = Wire.endTransmission();
      if (error == 0) {
        Serial.print(F("  Found device at "));
        printHexAddress(addr);
        Serial.println();
        foundAny = true;
      }
    }

    if (!foundAny) Serial.println(F("  No devices found."));
  }

  tcaDisableAll();
  Serial.println(F("=== END TCA SCAN ==="));
  Serial.println();
}

bool setupRfTestFrequencies() {
  Serial.println();
  Serial.println(F("=== RF OUTPUT FREQUENCY TEST SETUP ==="));

  bool ok = true;

  Serial.println(F("Configuring SI5351 #1 on TCA channel 0..."));
  if (si5351LowLevelInitChannel(0)) {
    bool ok0 = true;
    ok0 &= si5351SetupIntegerClock(0, 60); // 10 MHz
    ok0 &= si5351SetupIntegerClock(1, 30); // 20 MHz
    ok0 &= si5351SetupIntegerClock(2, 20); // 30 MHz
    ok0 &= si5351Write8(SI5351_OUTPUT_ENABLE, 0xF8);
    if (ok0) {
      Serial.println(F("  OUT0/BNC1 = 10 MHz"));
      Serial.println(F("  OUT1/BNC2 = 20 MHz"));
      Serial.println(F("  OUT2/BNC3 = 30 MHz"));
    } else {
      Serial.println(F("  FAILED: register write error on SI5351 #1."));
      ok = false;
    }
  } else {
    Serial.println(F("  FAILED: SI5351 #1 not configured."));
    ok = false;
  }

  Serial.println(F("Configuring SI5351 #2 on TCA channel 1..."));
  if (si5351LowLevelInitChannel(1)) {
    bool ok1 = true;
    ok1 &= si5351SetupIntegerClock(0, 15); // 40 MHz
    ok1 &= si5351SetupIntegerClock(1, 12); // 50 MHz
    ok1 &= si5351SetupIntegerClock(2, 10); // 60 MHz
    ok1 &= si5351Write8(SI5351_OUTPUT_ENABLE, 0xF8);
    if (ok1) {
      Serial.println(F("  OUT3/BNC4 = 40 MHz"));
      Serial.println(F("  OUT4/BNC5 = 50 MHz"));
      Serial.println(F("  OUT5/BNC6 = 60 MHz"));
    } else {
      Serial.println(F("  FAILED: register write error on SI5351 #2."));
      ok = false;
    }
  } else {
    Serial.println(F("  FAILED: SI5351 #2 not configured."));
    ok = false;
  }

  tcaDisableAll();

  if (ok) {
    Serial.println(F("RFTEST,OK;"));
    Serial.println(F("Measure BNC1..BNC6 with counter or oscilloscope."));
  } else {
    Serial.println(F("RFTEST,FAILED;"));
  }

  Serial.println(F("=== END RF OUTPUT FREQUENCY TEST SETUP ==="));
  Serial.println();
  return ok;
}

void disableAllRfOutputs() {
  Serial.println();
  Serial.println(F("Disabling SI5351 outputs..."));

  for (uint8_t ch = 0; ch < 2; ch++) {
    if (tcaSelect(ch) && i2cDevicePresent(SI5351_ADDR)) {
      si5351Write8(SI5351_OUTPUT_ENABLE, 0xFF);
    }
  }

  tcaDisableAll();
  Serial.println(F("RFOFF,OK;"));
  Serial.println();
}

void initPttInputs() {
  for (uint8_t i = 0; i < PTT_COUNT; i++) {
    pinMode(PTT_PINS[i], INPUT_PULLUP);
    bool raw = digitalRead(PTT_PINS[i]);
    pttStableState[i] = raw;
    pttLastRawState[i] = raw;
    pttLastChangeMs[i] = millis();
  }
}

void printPttState(uint8_t index, bool stateHigh) {
  Serial.print(stateHigh ? F("RX") : F("TX"));
  Serial.print(index);
  Serial.println(F(";"));
}

void printAllPttStates() {
  Serial.println();
  Serial.println(F("=== PTT INPUT STATES ==="));
  for (uint8_t i = 0; i < PTT_COUNT; i++) {
    Serial.print(F("PTT"));
    Serial.print(i);
    Serial.print(F(" pin D"));
    Serial.print(PTT_PINS[i]);
    Serial.print(F(" = "));
    Serial.println(digitalRead(PTT_PINS[i]) == LOW ? F("TX / LOW") : F("RX / HIGH"));
  }
  Serial.println(F("=== END PTT INPUT STATES ==="));
  Serial.println();
}

void servicePttInputs() {
  unsigned long now = millis();

  for (uint8_t i = 0; i < PTT_COUNT; i++) {
    bool raw = digitalRead(PTT_PINS[i]);

    if (raw != pttLastRawState[i]) {
      pttLastRawState[i] = raw;
      pttLastChangeMs[i] = now;
    }

    if ((now - pttLastChangeMs[i]) >= PTT_DEBOUNCE_MS) {
      if (raw != pttStableState[i]) {
        pttStableState[i] = raw;
        printPttState(i, raw);
      }
    }
  }
}

void printHelp() {
  Serial.println();
  Serial.println(F("Commands:"));
  Serial.println(F("  ID;       - firmware alive test"));
  Serial.println(F("  HELP;     - show help"));
  Serial.println(F("  MAIN;     - scan main I2C bus"));
  Serial.println(F("  TCA;      - scan TCA channels"));
  Serial.println(F("  SCAN;     - scan main bus and TCA channels"));
  Serial.println(F("  RFTEST;   - set BNC1..BNC6 to 10/20/30/40/50/60 MHz"));
  Serial.println(F("  RFOFF;    - disable SI5351 RF outputs"));
  Serial.println(F("  PTT;      - print current PTT input states"));
  Serial.println();
}

bool commandEquals(const char *cmd, const char *target) {
  return strcmp(cmd, target) == 0;
}

void uppercaseCommand(char *s) {
  while (*s) {
    if (*s >= 'a' && *s <= 'z') *s = *s - 32;
    s++;
  }
}

void processCommand(char *cmd) {
  uppercaseCommand(cmd);

  if (commandEquals(cmd, "ID;")) Serial.println(F("ID,NANO_HARDWARE_DIAG_V1B_OK;"));
  else if (commandEquals(cmd, "HELP;")) printHelp();
  else if (commandEquals(cmd, "MAIN;")) scanMainBus();
  else if (commandEquals(cmd, "TCA;")) scanTcaChannels();
  else if (commandEquals(cmd, "SCAN;")) { scanMainBus(); scanTcaChannels(); }
  else if (commandEquals(cmd, "RFTEST;")) setupRfTestFrequencies();
  else if (commandEquals(cmd, "RFOFF;")) disableAllRfOutputs();
  else if (commandEquals(cmd, "PTT;")) printAllPttStates();
  else {
    Serial.print(F("ERR,UNKNOWN_COMMAND,"));
    Serial.println(cmd);
  }
}

void serviceSerialCommands() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n' || c == '\r') {
      if (cmdLen > 0) {
        cmdBuf[cmdLen] = '\0';
        processCommand(cmdBuf);
        cmdLen = 0;
      }
      continue;
    }

    if (cmdLen < sizeof(cmdBuf) - 1) cmdBuf[cmdLen++] = c;

    if (c == ';') {
      cmdBuf[cmdLen] = '\0';
      processCommand(cmdBuf);
      cmdLen = 0;
    }
  }
}

void setup() {
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  Serial.begin(SERIAL_BAUD);
  delay(1000);

  Wire.begin();
  Wire.setClock(100000);

  initPttInputs();
  blinkLed(2);

  Serial.println();
  Serial.println(F("==============================================="));
  Serial.println(F(" SI5351 MULTI-RADIO VFO HARDWARE DIAGNOSTIC"));
  Serial.println(F(" v1b LOW-LEVEL SI5351"));
  Serial.println(F("==============================================="));
  Serial.println(F("Serial alive at 115200 baud. Use HELP;"));
  Serial.println();

  printHelp();
}

void loop() {
  servicePttInputs();
  serviceSerialCommands();
}
