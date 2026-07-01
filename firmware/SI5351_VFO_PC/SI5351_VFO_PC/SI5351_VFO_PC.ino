// File: SI5351_VFO_PC.ino
// SI5351 Multi-Radio VFO Platform
// Nano + TCA9548A + two Adafruit SI5351 modules
// OUT0-OUT5 firmware with PTT polling, E output-enable commands,
// 60 MHz support, and GUI-compatible calibration mode commands.
// Version: v6.1c Calibration Save Fixed

#include <Arduino.h>
#include <Wire.h>
#include <EEPROM.h>
#include <Adafruit_SI5351.h>

// ------------------------------------------------------------
// Hardware configuration
// ------------------------------------------------------------

const byte TCA_ADDR = 0x70;
const byte SI5351_1_TCA_CH = 0;
const byte SI5351_2_TCA_CH = 1;

Adafruit_SI5351 si5351_1 = Adafruit_SI5351();
Adafruit_SI5351 si5351_2 = Adafruit_SI5351();

const byte OUT_COUNT = 6;
const byte CLK_PER_BOARD = 3;
const byte SI5351_COUNT = 2;

const uint32_t FREQ_MIN_HZ = 1800000UL;

// Maximum frequency the user is allowed to request
const uint32_t USER_MAX_HZ = 60000000UL;

// Maximum frequency the SI5351 is allowed to generate after calibration
const uint32_t HW_MAX_HZ   = 60100000UL;

const uint32_t PLL_HZ = 900000000UL;

// ------------------------------------------------------------
// EEPROM / state
// ------------------------------------------------------------

struct State {
  uint32_t freq_hz[OUT_COUNT];          // OUT0-OUT5 user/requested frequencies
  bool output_enabled[OUT_COUNT];       // runtime only
  int32_t cal_ppb[SI5351_COUNT];        // SI5351 #1 and SI5351 #2 calibration
};

struct PersistedSettingsV61 {
  uint32_t magic;
  uint32_t freq_hz[OUT_COUNT];
  int32_t cal_ppb[SI5351_COUNT];
};

struct PersistedSettingsV6 {
  uint32_t magic;
  uint32_t freq_hz[OUT_COUNT];
  int32_t cal_ppb;
};

const uint32_t EEPROM_MAGIC_V61 = 0x53515637UL;  // "SQV7" v6.1 two-cal settings
const uint32_t EEPROM_MAGIC_V6  = 0x53515636UL;  // "SQV6" old single-cal settings
const int EEPROM_ADDR = 0;

State radio = {
  {10000000UL, 11000000UL, 12000000UL, 7000000UL, 8000000UL, 9000000UL},
  {false, false, false, false, false, false},
  {19790, 19790}
};

// ------------------------------------------------------------
// GUI calibration mode state
// ------------------------------------------------------------

bool calModeActive = false;
byte calSiIndex = 0;                    // 0 = SI5351 #1, 1 = SI5351 #2
byte calOutput = 0;                     // OUT0 for SI5351 #1, OUT3 for SI5351 #2
uint32_t calSavedFreqHz = 10000000UL;
bool calSavedOutputEnabled = false;

// ------------------------------------------------------------
// Serial command buffer
// ------------------------------------------------------------

static char cmdBuffer[48];
static byte cmdLen = 0;

// ------------------------------------------------------------
// PTT INPUT SYSTEM
// ------------------------------------------------------------
// PTT active LOW
// PTT0 -> OUT0, PTT1 -> OUT1, etc.
// Use PS2501L-2 optocouplers.
// Nano pins use INPUT_PULLUP.

const byte PTT_COUNT = 6;

const byte PTT_PINS[PTT_COUNT] = {
  2, 3, 4, 5, 6, 7
};

const unsigned long PTT_SCAN_MS = 5;
const unsigned long PTT_DEBOUNCE_MS = 20;

bool pttStable[PTT_COUNT];
bool pttLastRaw[PTT_COUNT];
unsigned long pttLastChangeMs[PTT_COUNT];
unsigned long lastPttScanMs = 0;

// ------------------------------------------------------------
// Basic replies
// ------------------------------------------------------------

void reply(const char *s) {
  Serial.print(s);
  Serial.print(";");
  Serial.print("\r\n");
}

void replyOK() {
  reply("OK");
}

void replyERR() {
  reply("ERR");
}

void replyID() {
  reply("IDNANO-SI5351-TCA9548A-OUT0-OUT5");
}

// ------------------------------------------------------------
// TCA9548A selection
// ------------------------------------------------------------

void selectTcaChannel(byte ch) {
  if (ch > 7) return;

  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << ch);
  Wire.endTransmission();
}

void disableAllTcaChannels() {
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(0x00);
  Wire.endTransmission();
}

// ------------------------------------------------------------
// Helpers
// ------------------------------------------------------------

bool allDigits(const char *s) {
  if (*s == '\0') return false;

  while (*s) {
    if (!isdigit((unsigned char)*s)) return false;
    s++;
  }

  return true;
}

bool parseSignedLong(const char *s, int32_t *value) {
  bool neg = false;

  if (*s == '+') {
    s++;
  } else if (*s == '-') {
    neg = true;
    s++;
  }

  if (!allDigits(s)) return false;

  long v = strtol(s, nullptr, 10);
  *value = neg ? -v : v;

  return true;
}

byte outToTcaChannel(byte out) {
  return (out < 3) ? SI5351_1_TCA_CH : SI5351_2_TCA_CH;
}

byte outToClock(byte out) {
  return out % 3;
}

byte outToSiIndex(byte out) {
  return (out < 3) ? 0 : 1;
}

Adafruit_SI5351 *outToDevice(byte out) {
  return (out < 3) ? &si5351_1 : &si5351_2;
}

// ------------------------------------------------------------
// EEPROM
// ------------------------------------------------------------

void loadSettingsFromEEPROM() {
  uint32_t magic = 0;
  EEPROM.get(EEPROM_ADDR, magic);

  if (magic == EEPROM_MAGIC_V61) {
    PersistedSettingsV61 saved;
    EEPROM.get(EEPROM_ADDR, saved);

    for (byte i = 0; i < OUT_COUNT; i++) {
      if (saved.freq_hz[i] >= FREQ_MIN_HZ && saved.freq_hz[i] <= USER_MAX_HZ) {
        radio.freq_hz[i] = saved.freq_hz[i];
      }
    }

    for (byte i = 0; i < SI5351_COUNT; i++) {
      if (saved.cal_ppb[i] >= -1000000L && saved.cal_ppb[i] <= 1000000L) {
        radio.cal_ppb[i] = saved.cal_ppb[i];
      }
    }

    return;
  }

  // Backward compatibility with v6 EEPROM layout:
  // one calibration value was shared by both SI5351 modules.
  if (magic == EEPROM_MAGIC_V6) {
    PersistedSettingsV6 saved;
    EEPROM.get(EEPROM_ADDR, saved);

    for (byte i = 0; i < OUT_COUNT; i++) {
      if (saved.freq_hz[i] >= FREQ_MIN_HZ && saved.freq_hz[i] <= USER_MAX_HZ) {
        radio.freq_hz[i] = saved.freq_hz[i];
      }
    }

    if (saved.cal_ppb >= -1000000L && saved.cal_ppb <= 1000000L) {
      radio.cal_ppb[0] = saved.cal_ppb;
      radio.cal_ppb[1] = saved.cal_ppb;
    }
  }
}

void saveSettingsToEEPROM() {
  PersistedSettingsV61 saved;

  saved.magic = EEPROM_MAGIC_V61;

  for (byte i = 0; i < OUT_COUNT; i++) {
    saved.freq_hz[i] = radio.freq_hz[i];
  }

  for (byte i = 0; i < SI5351_COUNT; i++) {
    saved.cal_ppb[i] = radio.cal_ppb[i];
  }

  EEPROM.put(EEPROM_ADDR, saved);
}

// ------------------------------------------------------------
// SI5351 output control
// ------------------------------------------------------------

void setOutputEnabled(byte out, bool enabled) {
  if (out >= OUT_COUNT) return;

  byte tcaChannel = outToTcaChannel(out);
  Adafruit_SI5351 *dev = outToDevice(out);

  selectTcaChannel(tcaChannel);

  dev->enableOutputs(enabled);

  radio.output_enabled[out] = enabled;

  Serial.print("E");
  Serial.print(out);
  Serial.print(enabled ? "1" : "0");
  Serial.println(";");
}

void forceAllOutputsOff() {
  for (byte out = 0; out < OUT_COUNT; out++) {
    byte tcaChannel = outToTcaChannel(out);
    byte clk = outToClock(out);
    Adafruit_SI5351 *dev = outToDevice(out);

    selectTcaChannel(tcaChannel);
    dev->enableOutputs(false);
    radio.output_enabled[out] = false;
  }
}

bool setOutputFrequency(byte out, uint32_t freq_hz) {
  if (out >= OUT_COUNT) return false;

  if (freq_hz < FREQ_MIN_HZ || freq_hz > USER_MAX_HZ) {
    return false;
  }

  int64_t corrected =
    (int64_t)freq_hz +
    ((int64_t)freq_hz * (int64_t)radio.cal_ppb[outToSiIndex(out)]) / 1000000000LL;

  if (corrected < FREQ_MIN_HZ || corrected > HW_MAX_HZ) {
    return false;
  }

  uint32_t actual_hz = (uint32_t)corrected;

  uint32_t div = PLL_HZ / actual_hz;
  uint32_t rem = PLL_HZ % actual_hz;

  if (div < 8 || div > 900) {
    return false;
  }

  const uint32_t denom = 1000000UL;
  uint32_t num = (uint32_t)(((uint64_t)rem * denom) / actual_hz);

  if (num >= denom) {
    num = denom - 1;
  }

  byte tcaChannel = outToTcaChannel(out);
  byte clk = outToClock(out);
  Adafruit_SI5351 *dev = outToDevice(out);

  selectTcaChannel(tcaChannel);

  err_t e = dev->setupMultisynth(
    clk,
    SI5351_PLL_A,
    div,
    num,
    denom
); 

  if (e != ERROR_NONE) return false;

  radio.freq_hz[out] = freq_hz;

  // Preserve current ON/OFF state after frequency change.
  dev->enableOutputs(true);
  dev->enableOutputs(radio.output_enabled[out]);

  return true;
}

// ------------------------------------------------------------
// Reply helpers
// ------------------------------------------------------------

void replyFA() {
  char out[24];
  snprintf(out, sizeof(out), "FA%011lu", (unsigned long)radio.freq_hz[0]);
  reply(out);
}

void replyXC(byte siIndex) {
  char out[24];

  if (siIndex >= SI5351_COUNT) {
    replyERR();
    return;
  }

  if (radio.cal_ppb[siIndex] >= 0) {
    snprintf(out, sizeof(out), "XC+%09ld", (long)radio.cal_ppb[siIndex]);
  } else {
    snprintf(out, sizeof(out), "XC-%09ld", (long)(-radio.cal_ppb[siIndex]));
  }

  reply(out);
}

void replyIF() {
  char out[160];

  snprintf(
    out,
    sizeof(out),
    "IFO0=%011lu,O1=%011lu,O2=%011lu,O3=%011lu,O4=%011lu,O5=%011lu,XC0=%ld,XC1=%ld",
    (unsigned long)radio.freq_hz[0],
    (unsigned long)radio.freq_hz[1],
    (unsigned long)radio.freq_hz[2],
    (unsigned long)radio.freq_hz[3],
    (unsigned long)radio.freq_hz[4],
    (unsigned long)radio.freq_hz[5],
    (long)radio.cal_ppb[0],
    (long)radio.cal_ppb[1]
  );

  reply(out);
}

// ------------------------------------------------------------
// Command handlers
// ------------------------------------------------------------

void handleFmulti(const char *cmd) {
  // F0xxxxxxxxxxx; through F5xxxxxxxxxxx;

  char outChar = cmd[1];

  if (outChar < '0' || outChar > '5') {
    replyERR();
    return;
  }

  byte out = outChar - '0';
  const char *args = cmd + 2;

  if (!allDigits(args)) {
    replyERR();
    return;
  }

  uint32_t f = strtoul(args, nullptr, 10);

  if (!setOutputFrequency(out, f)) {
    replyERR();
    return;
  }

  replyOK();
}

void handleFA(const char *args) {
  // Legacy OUT0 command:
  // FAxxxxxxxxxxx; = set OUT0
  // FA;            = read OUT0

  if (*args == '\0') {
    replyFA();
    return;
  }

  if (!allDigits(args)) {
    replyERR();
    return;
  }

  uint32_t f = strtoul(args, nullptr, 10);

  if (!setOutputFrequency(0, f)) {
    replyERR();
    return;
  }

  replyOK();
}

void handleE(const char *cmd) {
  // E01; = OUT0 ON
  // E00; = OUT0 OFF
  // E31; = OUT3 ON
  // E30; = OUT3 OFF

  if (strlen(cmd) != 3) {
    replyERR();
    return;
  }

  char outChar = cmd[1];
  char stateChar = cmd[2];

  if (outChar < '0' || outChar > '5') {
    replyERR();
    return;
  }

  if (stateChar != '0' && stateChar != '1') {
    replyERR();
    return;
  }

  byte out = outChar - '0';
  bool enabled = (stateChar == '1');

  setOutputEnabled(out, enabled);
}

void handleOE(const char *args) {
  // Legacy global enable command.
  // OE1; enables all outputs.
  // OE0; disables all outputs.

  if (*args == '\0') {
    reply("OE0");
    return;
  }

  if (strcmp(args, "1") == 0) {
    for (byte i = 0; i < OUT_COUNT; i++) {
      setOutputEnabled(i, true);
    }
    replyOK();
    return;
  }

  if (strcmp(args, "0") == 0) {
    for (byte i = 0; i < OUT_COUNT; i++) {
      setOutputEnabled(i, false);
    }
    replyOK();
    return;
  }

  replyERR();
}

void handleXC(const char *args) {
  // XC;          read SI5351 #1 calibration, legacy command
  // XC0;         read SI5351 #1 calibration for GUI
  // XC1;         read SI5351 #2 calibration for GUI
  // XC+19790;    set both SI5351 calibration values, legacy/manual command

  if (*args == '\0') {
    replyXC(0);
    return;
  }

  if (strlen(args) == 1 && (args[0] == '0' || args[0] == '1')) {
    replyXC(args[0] - '0');
    return;
  }

  int32_t newCal = 0;

  if (!parseSignedLong(args, &newCal)) {
    replyERR();
    return;
  }

  if (newCal < -1000000L || newCal > 1000000L) {
    replyERR();
    return;
  }

  // Legacy/manual set command updates both SI5351 modules.
  radio.cal_ppb[0] = newCal;
  radio.cal_ppb[1] = newCal;

  for (byte i = 0; i < OUT_COUNT; i++) {
    if (!setOutputFrequency(i, radio.freq_hz[i])) {
      replyERR();
      return;
    }
  }

  replyOK();
}


bool reprogramOutputsForSi(byte siIndex) {
  if (siIndex >= SI5351_COUNT) return false;

  byte firstOut = (siIndex == 0) ? 0 : 3;
  byte lastOut = firstOut + 3;

  for (byte out = firstOut; out < lastOut; out++) {
    if (!setOutputFrequency(out, radio.freq_hz[out])) {
      return false;
    }
  }

  return true;
}

bool parseCalNudgeArgs(const char *args, byte *siIndex, int32_t *step) {
  // Expected GUI format: CU0,+10; or CD1,+100;
  if (strlen(args) < 3) return false;

  if (args[0] != '0' && args[0] != '1') return false;
  if (args[1] != ',') return false;

  int32_t parsedStep = 0;
  if (!parseSignedLong(args + 2, &parsedStep)) return false;

  *siIndex = args[0] - '0';
  *step = parsedStep;
  return true;
}

void handleC(const char *args) {
  // C0; = enter calibration mode for SI5351 #1 using OUT0
  // C1; = enter calibration mode for SI5351 #2 using OUT3
  if (strlen(args) != 1 || (args[0] != '0' && args[0] != '1')) {
    replyERR();
    return;
  }

  byte siIndex = args[0] - '0';
  byte out = (siIndex == 0) ? 0 : 3;

  if (!calModeActive) {
    calSavedFreqHz = radio.freq_hz[out];
    calSavedOutputEnabled = radio.output_enabled[out];
  }

  calModeActive = true;
  calSiIndex = siIndex;
  calOutput = out;

  if (!setOutputFrequency(calOutput, 10000000UL)) {
    replyERR();
    return;
  }

  setOutputEnabled(calOutput, true);
  replyOK();
}

void handleCX(const char *args) {
  // CX; = exit calibration mode and restore previous frequency/state
  if (*args != '\0') {
    replyERR();
    return;
  }

  if (calModeActive) {
    setOutputFrequency(calOutput, calSavedFreqHz);
    setOutputEnabled(calOutput, calSavedOutputEnabled);
    calModeActive = false;
  }

  replyOK();
}

void handleCU(const char *args) {
  // CU0,+10; = GUI UP button: raise measured output frequency.
  // Increasing cal_ppb increases the generated frequency.
  byte siIndex = 0;
  int32_t step = 0;

  if (!parseCalNudgeArgs(args, &siIndex, &step)) {
    replyERR();
    return;
  }

  int32_t newCal = radio.cal_ppb[siIndex] + step;

  if (newCal < -1000000L || newCal > 1000000L) {
    replyERR();
    return;
  }

  radio.cal_ppb[siIndex] = newCal;

  if (!reprogramOutputsForSi(siIndex)) {
    replyERR();
    return;
  }

  if (calModeActive && calSiIndex == siIndex) {
    setOutputFrequency(calOutput, 10000000UL);
    setOutputEnabled(calOutput, true);
  }

  replyOK();
}

void handleCD(const char *args) {
  // CD0,+10; = GUI DOWN button: lower measured output frequency.
  // Decreasing cal_ppb decreases the generated frequency.
  byte siIndex = 0;
  int32_t step = 0;

  if (!parseCalNudgeArgs(args, &siIndex, &step)) {
    replyERR();
    return;
  }

  int32_t newCal = radio.cal_ppb[siIndex] - step;

  if (newCal < -1000000L || newCal > 1000000L) {
    replyERR();
    return;
  }

  radio.cal_ppb[siIndex] = newCal;

  if (!reprogramOutputsForSi(siIndex)) {
    replyERR();
    return;
  }

  if (calModeActive && calSiIndex == siIndex) {
    setOutputFrequency(calOutput, 10000000UL);
    setOutputEnabled(calOutput, true);
  }

  replyOK();
}



void handleCS(const char *args) {
  // CS0; / CS1; = GUI Save Calibration button.
  // The firmware currently stores both SI5351 calibration values
  // and all saved output frequencies together in EEPROM.
  if (strlen(args) != 1 || (args[0] != '0' && args[0] != '1')) {
    replyERR();
    return;
  }

  saveSettingsToEEPROM();
  replyOK();
}

void handleSV(const char *args) {
  if (*args != '\0') {
    replyERR();
    return;
  }

  saveSettingsToEEPROM();
  replyOK();
}

// ------------------------------------------------------------
// CAT parser
// ------------------------------------------------------------

void dispatchCommand(char *cmd) {
  size_t len = strlen(cmd);

  while (len > 0 && isspace((unsigned char)cmd[len - 1])) {
    cmd[--len] = '\0';
  }

  while (*cmd && isspace((unsigned char)*cmd)) {
    cmd++;
  }

  if (strlen(cmd) < 2) {
    replyERR();
    return;
  }

  // F0-F5
  if (toupper((unsigned char)cmd[0]) == 'F' &&
      cmd[1] >= '0' && cmd[1] <= '5') {
    handleFmulti(cmd);
    return;
  }

  // E00-E51
  if (toupper((unsigned char)cmd[0]) == 'E') {
    handleE(cmd);
    return;
  }

  // C0/C1 enter calibration mode
  if (toupper((unsigned char)cmd[0]) == 'C' &&
      (cmd[1] == '0' || cmd[1] == '1')) {
    handleC(cmd + 1);
    return;
  }

  char op[3];
  op[0] = toupper((unsigned char)cmd[0]);
  op[1] = toupper((unsigned char)cmd[1]);
  op[2] = '\0';

  const char *args = cmd + 2;

  if (strcmp(op, "FA") == 0) {
    handleFA(args);
  } else if (strcmp(op, "OE") == 0) {
    handleOE(args);
  } else if (strcmp(op, "XC") == 0) {
    handleXC(args);
  } else if (strcmp(op, "CU") == 0) {
    handleCU(args);
  } else if (strcmp(op, "CD") == 0) {
    handleCD(args);
  } else if (strcmp(op, "CX") == 0) {
    handleCX(args);
  } else if (strcmp(op, "CS") == 0) {
    handleCS(args);
  } else if (strcmp(op, "SV") == 0) {
    handleSV(args);
  } else if (strcmp(op, "IF") == 0) {
    replyIF();
  } else if (strcmp(op, "ID") == 0) {
    replyID();
  } else {
    replyERR();
  }
}

void serviceSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();

    if (c == ';') {
      cmdBuffer[cmdLen] = '\0';
      dispatchCommand(cmdBuffer);
      cmdLen = 0;
    } else if (c == '\r' || c == '\n') {
      // Ignore CR/LF
    } else {
      if (cmdLen < sizeof(cmdBuffer) - 1) {
        cmdBuffer[cmdLen++] = c;
      } else {
        cmdLen = 0;
        replyERR();
      }
    }
  }
}

// ------------------------------------------------------------
// PTT functions
// ------------------------------------------------------------

void initPttInputs() {
  for (byte i = 0; i < PTT_COUNT; i++) {
    pinMode(PTT_PINS[i], INPUT_PULLUP);

    bool raw = digitalRead(PTT_PINS[i]);

    pttStable[i] = raw;
    pttLastRaw[i] = raw;
    pttLastChangeMs[i] = millis();
  }

  Serial.println("PTT inputs ready");
}

void servicePttInputs() {
  unsigned long now = millis();

  if (now - lastPttScanMs < PTT_SCAN_MS) {
    return;
  }

  lastPttScanMs = now;

  for (byte i = 0; i < PTT_COUNT; i++) {
    bool raw = digitalRead(PTT_PINS[i]);

    if (raw != pttLastRaw[i]) {
      pttLastRaw[i] = raw;
      pttLastChangeMs[i] = now;
    }

    if ((now - pttLastChangeMs[i]) >= PTT_DEBOUNCE_MS) {
      if (raw != pttStable[i]) {
        pttStable[i] = raw;

        if (pttStable[i] == LOW) {
          Serial.print("TX");
          Serial.print(i);
          Serial.println(";");
        } else {
          Serial.print("RX");
          Serial.print(i);
          Serial.println(";");
        }
      }
    }
  }
}

// ------------------------------------------------------------
// Setup / loop
// ------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(200);

  Serial.println("Nano SI5351 TCA9548A OUT0-OUT5 Firmware v6.1c CAL");

  Wire.begin();

  initPttInputs();
  loadSettingsFromEEPROM();

  Serial.println("Initializing SI5351 #1 on TCA CH0...");
  selectTcaChannel(SI5351_1_TCA_CH);

  if (si5351_1.begin() != ERROR_NONE) {
    Serial.println("SI5351 #1 FAIL");
    reply("ERRSI5351A");
    while (1) {
      delay(1000);
    }
  }

  si5351_1.enableSpreadSpectrum(false);

  if (si5351_1.setupPLLInt(SI5351_PLL_A, 36) != ERROR_NONE) {
    reply("ERRPLL1");
    while (1) {
      delay(1000);
    }
  }

  Serial.println("SI5351 #1 OK");

  Serial.println("Initializing SI5351 #2 on TCA CH1...");
  selectTcaChannel(SI5351_2_TCA_CH);

  if (si5351_2.begin() != ERROR_NONE) {
    Serial.println("SI5351 #2 FAIL");
    reply("ERRSI5351B");
    while (1) {
      delay(1000);
    }
  }

  si5351_2.enableSpreadSpectrum(false);

  if (si5351_2.setupPLLInt(SI5351_PLL_A, 36) != ERROR_NONE) {
    reply("ERRPLL2");
    while (1) {
      delay(1000);
    }
  }

  Serial.println("SI5351 #2 OK");

  // Program all six outputs to saved/default frequencies.
  for (byte i = 0; i < OUT_COUNT; i++) {
    if (!setOutputFrequency(i, radio.freq_hz[i])) {
      reply("ERRFREQ");
      while (1) {
        delay(1000);
      }
    }
  }

  // Safe startup: all outputs OFF.
  forceAllOutputsOff();

  reply("READY");
}

void loop() {
  serviceSerial();
  servicePttInputs();
}