###########################################################################
# help_window.py
#
# SI5351 Multi-Radio VFO Platform
#
# Searchable Built-In User Guide
#
# Purpose:
#   Provides an offline, searchable Help/User Guide window for the SI5351
#   Multi-Radio VFO Platform.
#
# Description:
#   This file is intentionally self-contained so the installed application can
#   display operating help without internet access or external documentation
#   files. The Help window is written primarily for amateur radio operators,
#   builders, and experimenters who may not be software developers.
#
# Design Notes:
#   - Help content is stored in HELP_TOPICS as simple dictionaries.
#   - Each topic contains a title, search keywords, and HTML body text.
#   - The GUI provides a topic list, text search, and read-only display pane.
#   - No external web resources are required.
#
# Revision History:
#   Help v1.1
#       - Searchable Help window implemented.
#       - Added calibration, profile editor, output manager, and session help.
#
#   Help v1.2 / Version 6.1d Release
#       - Updated Help into a built-in user guide.
#       - Added Developer Console section.
#       - Updated calibration button names and workflow.
#       - Added automatic session restore details.
#       - Added Version 1.0 release information.
#       - Added MIT License and author/callsign information.
#
###########################################################################

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_VERSION = "SI5351 Multi-Radio VFO Platform - User Guide v1.2"


HELP_TOPICS = [
    {
        "title": "Welcome / About This Project",
        "keywords": "welcome about project vfo si5351 john bielefeld k1jeb license mit openai chatgpt",
        "body": """
<h2>SI5351 Multi-Radio VFO Platform</h2>
<p><b>Version 6.1d Release </b></p>
<p><b>Firmware Version:</b> 6.1c</p>
<p><b>Documentation Version:</b> 1.0</p>

<p>The SI5351 Multi-Radio VFO Platform is a software-controlled external VFO
system for vintage Amateur Radio equipment. It uses a Windows PC application,
an Arduino Nano controller, a TCA9548A I2C multiplexer, and two SI5351A
frequency synthesizer modules to provide six assignable RF outputs.</p>

<p>The platform is designed to emulate or replace the VFO functions used by
classic transmitters, receivers, and transceivers while keeping the firmware
simple and moving radio-specific frequency math into the PC application.</p>

<h3>Designed and Developed by</h3>
<p><b>John Bielefeld, K1JEB</b><br>
Amateur Radio Operator</p>

<h3>Engineering Assistance</h3>
<p>ChatGPT<br>
OpenAI</p>

<h3>License</h3>
<p>Copyright &copy; 2026 John Bielefeld, K1JEB</p>
<p>Licensed under the MIT License.</p>

<h3>Intended Use</h3>
<p>This software is intended for educational, experimental, and Amateur Radio
use. Always verify generated frequencies with appropriate test equipment before
on-air use.</p>
""",
    },
    {
        "title": "Quick Start",
        "keywords": "start quick connect com port radio band output frequency spot rf set tune",
        "body": """
<h2>Quick Start</h2>
<ol>
<li>Connect the SI5351 VFO hardware to the PC USB port.</li>
<li>Select the USB COM port for the Arduino Nano controller.</li>
<li>Click <b>Connect</b>.</li>
<li>Select the desired <b>Radio</b> profile.</li>
<li>Select the desired <b>Band</b>.</li>
<li>Select the RF output connector.</li>
<li>Enter the desired RF operating frequency or tune with the arrow keys or mouse wheel.</li>
<li>Use <b>RF ON</b> only when you are ready to enable the selected RF output.</li>
<li>Use <b>SPOT</b> for receive-only carrier checking and zero-beat setup.</li>
</ol>

<p>The large frequency display shows the desired <b>RF operating frequency</b>.
The <b>VFO</b> field shows the calculated SI5351 output frequency being sent to
the hardware.</p>

<h3>Important Safety Reminder</h3>
<p>RF, SPOT, and TX states are never automatically restored at startup. The
program intentionally starts with RF outputs off.</p>
""",
    },
    {
        "title": "Version / Release Status",
        "keywords": "version release freeze stable firmware documentation 6.1d 6.1c",
        "body": """
<h2>Version / Release Status</h2>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Item</th><th>Status</th></tr>
<tr><td>PC Application</td><td>Version 6.1d Release </td></tr>
<tr><td>Nano Firmware</td><td>Version 6.1c Release</td></tr>
<tr><td>Documentation</td><td>Version 1.0</td></tr>
<tr><td>License</td><td>MIT License</td></tr>
</table>

<h3>Current Release Features</h3>
<ul>
<li>Six assignable RF outputs.</li>
<li>Two SI5351A synthesizer modules behind a TCA9548A I2C multiplexer.</li>
<li>EEPROM-based per-SI5351 calibration.</li>
<li>Profile-based frequency translation.</li>
<li>Output Manager with conflict prevention.</li>
<li>Session save and automatic startup restore.</li>
<li>Developer Console with command history.</li>
<li>Profile Editor with validation and automatic JSON backup.</li>
<li>Integrated Help/User Guide.</li>
</ul>
""",
    },
    {
        "title": "Architecture Overview",
        "keywords": "architecture gui brain nano executor profiles json radio math si5351 seriallink outputmanager",
        "body": """
<h2>Architecture Overview</h2>
<p>The PC GUI is the system brain. It owns:</p>
<ul>
<li>radio profile selection</li>
<li>band selection</li>
<li>RF-to-VFO translation math</li>
<li>output assignment</li>
<li>session restore</li>
<li>safety monitoring</li>
<li>calibration workflow</li>
</ul>

<p>The Arduino Nano is the execution engine. It receives frequency and RF enable
commands over USB serial and drives the SI5351 hardware.</p>

<h3>Design Rule</h3>
<p>Radio-specific math stays in <b>radio_profiles.json</b> and the Python math
engine. The Nano firmware should remain simple and only generate the final
frequency it is told to generate.</p>

<h3>Simplified System View</h3>
<pre>
Main Window
    |
    +-- SerialLink ---- USB COM ---- Arduino Nano
    |                                  |
    |                              TCA9548A
    |                              /     \
    |                         SI5351 #1  SI5351 #2
    |                         OUT0-2     OUT3-5
    |
    +-- Output Manager
    +-- Profile Editor
    +-- Calibration Window
    +-- Developer Console
</pre>
""",
    },
    {
        "title": "Hardware Wiring Overview",
        "keywords": "wiring nano tca9548a si5351 i2c mux bnc output clk hardware",
        "body": """
<h2>Hardware Wiring Overview</h2>
<ul>
<li>Controller: Arduino Nano / ATmega328.</li>
<li>I2C mux: TCA9548A at address 0x70.</li>
<li>SI5351 module #1: behind mux channel 0.</li>
<li>SI5351 module #2: behind mux channel 1.</li>
</ul>

<h3>Output Mapping</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Operator Label</th><th>Firmware Name</th><th>Physical Source</th></tr>
<tr><td>Output 1 / BNC 1</td><td>OUT0</td><td>SI5351 #1 CLK0</td></tr>
<tr><td>Output 2 / BNC 2</td><td>OUT1</td><td>SI5351 #1 CLK1</td></tr>
<tr><td>Output 3 / BNC 3</td><td>OUT2</td><td>SI5351 #1 CLK2</td></tr>
<tr><td>Output 4 / BNC 4</td><td>OUT3</td><td>SI5351 #2 CLK0</td></tr>
<tr><td>Output 5 / BNC 5</td><td>OUT4</td><td>SI5351 #2 CLK1</td></tr>
<tr><td>Output 6 / BNC 6</td><td>OUT5</td><td>SI5351 #2 CLK2</td></tr>
</table>

<p>Operators see Output 1 through Output 6. Firmware commands use OUT0 through
OUT5.</p>
""",
    },
    {
        "title": "Main Window Controls",
        "keywords": "main window controls frequency tuning arrows wheel compact monitor rf spot connect disconnect",
        "body": """
<h2>Main Window Controls</h2>
<h3>Connect / Disconnect</h3>
<p><b>Connect</b> opens the selected USB COM port and connects the GUI to the
Arduino Nano. <b>Disconnect</b> turns RF off and closes the serial connection.</p>

<h3>Radio and Band</h3>
<p>The <b>Radio</b> dropdown selects a radio profile. The <b>Band</b> dropdown
selects one band within that profile. Changing radio or band recalculates the
required SI5351 output frequency.</p>

<h3>Frequency Display</h3>
<p>The large display is the RF operating frequency. Use the mouse wheel or Up/Down
arrow keys to tune. Use Left/Right arrow keys or click on a digit to change the
tuning step.</p>

<h3>RF ON / RF OFF</h3>
<p><b>RF ON</b> enables the selected RF output. <b>RF OFF</b> disables it.</p>

<h3>SPOT</h3>
<p><b>SPOT</b> enables a receive-only carrier for checking oscillator injection,
zero-beating, or receiver alignment. SPOT is forced off during disconnect and is
not restored at startup.</p>

<h3>COMPACT</h3>
<p><b>COMPACT</b> reduces the window to a smaller operating view. Use <b>FULL</b>
to return to the full control view.</p>
""",
    },
    {
        "title": "RF Safety Notes",
        "keywords": "safety rf tx spot output conflict same band warning",
        "body": """
<h2>RF Safety Notes</h2>
<ul>
<li>Startup forces RF and SPOT off.</li>
<li>Session restore never restores RF ON, SPOT ON, or TX state.</li>
<li>SPOT is receive-only carrier generation.</li>
<li>TX has priority over SPOT.</li>
<li>The Output Manager prevents two windows from owning the same output.</li>
<li>The safety monitor warns about same-band TX conflicts.</li>
</ul>

<p>The current safety monitor is warning-only. It does not physically block RF.
Always verify output routing, transmitter connections, and frequency before
enabling RF.</p>
""",
    },
    {
        "title": "Output Manager",
        "keywords": "output manager bnc owner assigned conflict window out0 output1 rf off reassignment",
        "body": """
<h2>Output Manager</h2>
<p>The Output Manager tracks which radio window owns each RF output. It helps
prevent accidental double assignment of one output to multiple radios.</p>

<h3>What It Tracks</h3>
<ul>
<li>Operator label: Output 1 through Output 6.</li>
<li>Firmware name: OUT0 through OUT5.</li>
<li>Owning window.</li>
<li>Selected radio and band.</li>
<li>RF frequency and calculated VFO frequency.</li>
<li>RF, SPOT, and TX status.</li>
</ul>

<h3>Ownership Rule</h3>
<p>One output may have only one owner. If another radio window already owns an
output, the Output Manager will reject the assignment and display a conflict
message.</p>

<h3>Safety During Reassignment</h3>
<p>When an output is reassigned, RF, SPOT, and TX state are forced off for that
assignment. This prevents stale RF state from following a radio to a different
connector.</p>
""",
    },
    {
        "title": "Frequency Entry and Tuning",
        "keywords": "frequency entry mhz khz hz examples set frequency tuning step vfo rf",
        "body": """
<h2>Frequency Entry and Tuning</h2>
<p>The frequency entry box accepts several formats:</p>
<ul>
<li><b>7.100</b> = 7.100 MHz</li>
<li><b>7100</b> = 7100 kHz</li>
<li><b>7100000</b> = 7,100,000 Hz</li>
<li><b>14.250 MHz</b> = 14.250 MHz</li>
</ul>

<p>The program converts the RF input through the selected radio profile and sends
the resulting SI5351 output frequency to the selected output.</p>

<h3>RF Frequency vs. VFO Frequency</h3>
<p>The RF frequency is the operating frequency shown to the operator. The VFO
frequency is the actual oscillator frequency generated by the SI5351. These may
be different for vintage radios using offsets, multipliers, or mapped VFO ranges.</p>
""",
    },
    {
        "title": "Radio Profiles and Translation Modes",
        "keywords": "profile radio_profiles json band translation direct multiply divide linear_map vfo math",
        "body": """
<h2>Radio Profiles and Translation Modes</h2>
<p>A radio profile describes how a vintage radio expects its VFO signal. Each
profile contains one or more bands. Each band defines the allowed RF range and
the math needed to calculate the SI5351 output frequency.</p>

<h3>Translation Modes</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Mode</th><th>Purpose</th></tr>
<tr><td>direct</td><td>SI5351 output equals the desired RF frequency.</td></tr>
<tr><td>multiply</td><td>Radio multiplies the VFO internally; SI5351 output is RF divided by multiplier.</td></tr>
<tr><td>divide</td><td>Used by profile tools for radios needing divide-style translation.</td></tr>
<tr><td>linear_map</td><td>Maps an RF tuning range onto a separate VFO tuning range.</td></tr>
</table>

<h3>Why Profiles Matter</h3>
<p>The same SI5351 hardware can emulate many different vintage VFOs because each
radio's math is stored in the profile file instead of being hard-coded into the
firmware.</p>
""",
    },
    {
        "title": "Profile Editor Instructions",
        "keywords": "profile editor add duplicate delete band save backup validate translation json reload",
        "body": """
<h2>Profile Editor Instructions</h2>
<p>Use <b>Profile Editor</b> to edit <b>radio_profiles.json</b>.</p>

<h3>Profile Operations</h3>
<ul>
<li><b>New</b>: creates a new initialized radio profile.</li>
<li><b>Duplicate</b>: copies an existing radio profile.</li>
<li><b>Delete</b>: removes the selected profile after confirmation.</li>
</ul>

<h3>Band Operations</h3>
<ul>
<li><b>Add Band</b>: adds a new initialized band.</li>
<li><b>Duplicate Band</b>: copies the selected band.</li>
<li><b>Delete Band</b>: removes the selected band after confirmation.</li>
<li><b>Apply Band Changes</b>: applies detail-panel edits into the in-memory model.</li>
</ul>

<h3>Saving</h3>
<p><b>Save</b> writes the JSON file and creates an automatic timestamped backup.
This protects the existing profile database before replacing it.</p>

<h3>Validation</h3>
<p><b>Validate Profiles</b> checks the profile database for common problems such as
blank IDs, duplicate names, invalid frequency ranges, missing VFO data, or invalid
translation modes.</p>

<p>After saving profile changes, return to the main VFO window and click
<b>Reload</b> or <b>Reload Profiles</b>.</p>
""",
    },
    {
        "title": "Reload Profiles",
        "keywords": "reload profiles profile editor restart json update",
        "body": """
<h2>Reload Profiles</h2>
<p>Use <b>Reload</b> after saving changes in the Profile Editor.</p>
<p>This reloads <b>radio_profiles.json</b> without restarting the main program. It
keeps the same profile and band selected when possible.</p>
<p>If a profile or band was deleted, the program selects the nearest available
profile or band.</p>
""",
    },
    {
        "title": "SI5351 Calibration Procedure",
        "keywords": "calibration calibrate si5351 counter 10 mhz eeprom xc c0 c1 out0 out3 bnc1 bnc4 save cal exit cal enter cal",
        "body": """
<h2>SI5351 Calibration Procedure</h2>
<p>The calibration system corrects the crystal oscillator error of each physical
SI5351 module.</p>
<p>Calibration values are stored in the Arduino Nano EEPROM. This means each
physical VFO box carries its own calibration values and can be moved between PCs
without recalibration.</p>

<h3>SI5351 Module Mapping</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>SI5351 Module</th><th>Outputs</th><th>Calibration Output</th></tr>
<tr><td>SI5351 #1</td><td>OUT0, OUT1, OUT2</td><td>OUT0 / Output 1 / BNC1</td></tr>
<tr><td>SI5351 #2</td><td>OUT3, OUT4, OUT5</td><td>OUT3 / Output 4 / BNC4</td></tr>
</table>

<h3>Equipment Required</h3>
<ul>
<li>Frequency counter capable of accurately measuring 10 MHz.</li>
<li>GPS-disciplined reference or other accurate frequency reference recommended.</li>
<li>USB connection to the Nano controller.</li>
<li>Powered SI5351 VFO hardware.</li>
</ul>

<h3>Opening the Calibration Window</h3>
<ol>
<li>Start the SI5351 Multi-Radio VFO application.</li>
<li>Connect to the Nano using the COM-port <b>Connect</b> button.</li>
<li>Click <b>Calibration</b>.</li>
</ol>

<h3>Calibrating SI5351 #1</h3>
<ol>
<li>Select <b>SI5351 #1</b> in the Target dropdown.</li>
<li>Connect the frequency counter to <b>OUT0 / Output 1 / BNC1</b>.</li>
<li>Click <b>ENTER CAL</b>.</li>
<li>The Nano disables normal RF outputs and generates a fixed <b>10.000000 MHz</b> signal on OUT0.</li>
<li>Use <b>UP</b> and <b>DOWN</b> to adjust the correction until the counter reads exactly <b>10.000000 MHz</b>.</li>
<li>Use larger steps such as <b>1000</b> for coarse movement, then <b>100</b>, <b>10</b>, or <b>1</b> for fine adjustment.</li>
<li>Click <b>SAVE CAL</b> to store the correction in Nano EEPROM.</li>
<li>Click <b>EXIT CAL</b> to leave calibration mode.</li>
</ol>

<h3>Calibrating SI5351 #2</h3>
<ol>
<li>If calibration is active for SI5351 #1, first click <b>EXIT CAL</b>.</li>
<li>Select <b>SI5351 #2</b> in the Target dropdown.</li>
<li>Move the frequency counter to <b>OUT3 / Output 4 / BNC4</b>.</li>
<li>Click <b>ENTER CAL</b>.</li>
<li>The Nano generates a fixed <b>10.000000 MHz</b> signal on OUT3.</li>
<li>Use <b>UP</b>, <b>DOWN</b>, and the step selector until the counter reads exactly <b>10.000000 MHz</b>.</li>
<li>Click <b>SAVE CAL</b>.</li>
<li>Click <b>EXIT CAL</b> or <b>EXIT</b>.</li>
</ol>

<h3>EXIT CAL vs. EXIT</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Button</th><th>Function</th></tr>
<tr><td><b>EXIT CAL</b></td><td>Exits Nano calibration mode but keeps the Calibration Window open.</td></tr>
<tr><td><b>EXIT</b></td><td>Exits Nano calibration mode if needed, then closes the Calibration Window.</td></tr>
<tr><td><b>Window X</b></td><td>Also safely exits calibration mode before closing.</td></tr>
</table>

<h3>Safety Notes</h3>
<ul>
<li>Calibration mode disables normal RF outputs.</li>
<li>Only one calibration output is active at a time.</li>
<li>Do not calibrate while connected to a transmitter input unless that is intentional and safe.</li>
<li>Always exit calibration mode before returning to normal VFO operation.</li>
</ul>

<h3>Verifying Saved Calibration</h3>
<p>Calibration values are restored automatically after Nano reboot. To view them,
open the Developer Console or Monitor and send:</p>
<pre>XC0;
XC1;</pre>
""",
    },
    {
        "title": "Developer Console",
        "keywords": "developer console serial monitor command history up down id xc c0 c1 cx f0 e0",
        "body": """
<h2>Developer Console</h2>
<p>The Developer Console is an engineering terminal built into the application.
It sends manual commands to the Arduino Nano through the same SerialLink used by
the main GUI.</p>

<h3>Why It Exists</h3>
<p>The console removes the need to close the GUI and open the Arduino Serial
Monitor. This prevents COM-port conflicts and allows testing while the VFO
application remains connected.</p>

<h3>Command History</h3>
<ul>
<li><b>Up Arrow</b>: recall older commands.</li>
<li><b>Down Arrow</b>: move forward through command history.</li>
<li>Recalled commands remain editable before sending.</li>
</ul>

<h3>Useful Commands</h3>
<pre>
ID;       firmware identification
XC0;      read SI5351 #1 calibration
XC1;      read SI5351 #2 calibration
C0;       enter SI5351 #1 calibration mode
C1;       enter SI5351 #2 calibration mode
CX;       exit calibration mode
E01;      OUT0 RF ON
E00;      OUT0 RF OFF
</pre>

<p>Most firmware commands end with a semicolon. The Developer Console adds the
semicolon automatically if the operator forgets it.</p>
""",
    },
    {
        "title": "Monitor ON/OFF and Serial Responses",
        "keywords": "monitor on off serial response id test read calibration xc debug log hidden",
        "body": """
<h2>Monitor ON/OFF and Serial Responses</h2>
<p>The <b>Monitor ON/OFF</b> button controls whether the serial/debug log panel is
visible.</p>
<p>When the button says <b>Monitor OFF</b>, the monitor panel is hidden. Click it
once to show the monitor. The button will then say <b>Monitor ON</b>.</p>

<h3>Important</h3>
<p>Some buttons send commands to the Nano and show their results only in the
monitor/log panel.</p>
<ul>
<li><b>ID Test</b> sends <code>ID;</code> to the Nano.</li>
<li><b>Read Calibration</b> reads calibration values from the Nano.</li>
</ul>

<h3>Example Monitor Responses</h3>
<pre>
IDNANO-SI5351-TCA9548A-OUT0-OUT5;
XC0,+000019790;
XC1,-000000320;
</pre>
<p>Use the monitor when checking firmware identity, calibration values, serial
command responses, or troubleshooting COM-port behavior.</p>
""",
    },
    {
        "title": "Session Save and Restore",
        "keywords": "session restore save load windows compact reboot automatic startup shutdown",
        "body": """
<h2>Session Save and Restore</h2>
<p>The session system saves window layout and operating configuration.</p>

<h3>Automatic Restore</h3>
<p>When the program closes normally, it saves the current operating layout. On the
next startup, the program automatically restores the last operating state.</p>

<h3>Manual Save / Load</h3>
<ul>
<li><b>Save</b>: saves a named session profile.</li>
<li><b>Load</b>: loads a previously saved session profile.</li>
</ul>

<h3>What Is Restored</h3>
<ul>
<li>Main window position.</li>
<li>Floating radio windows.</li>
<li>Compact/full states.</li>
<li>Selected radio, band, output, frequency, and step size.</li>
</ul>

<h3>What Is Not Restored</h3>
<p>RF ON, SPOT ON, and TX state are not restored. Those are always forced off for
safety.</p>
""",
    },
    {
        "title": "Troubleshooting",
        "keywords": "troubleshooting no com port no rf wrong frequency calibration output assigned busy serial",
        "body": """
<h2>Troubleshooting</h2>
<h3>No COM Port Listed</h3>
<ul>
<li>Verify the Arduino Nano USB cable is connected.</li>
<li>Try a different USB cable.</li>
<li>Click <b>Refresh</b>.</li>
<li>Check Windows Device Manager for the COM port.</li>
</ul>

<h3>COM Port Busy</h3>
<p>Close Arduino Serial Monitor, PuTTY, another terminal, or any other program
using the same COM port.</p>

<h3>No RF Output</h3>
<ul>
<li>Verify the program is connected to the Nano.</li>
<li>Verify the correct output/BNC connector is selected.</li>
<li>Click <b>RF ON</b> or <b>SPOT ON</b>.</li>
<li>Check the Output Manager for ownership conflicts.</li>
<li>Check hardware power and SI5351 module wiring.</li>
</ul>

<h3>Wrong Frequency</h3>
<ul>
<li>Verify the correct radio profile and band are selected.</li>
<li>Check the VFO frequency display, not just the RF display.</li>
<li>Use the Profile Editor validation tool.</li>
<li>Recheck calibration using a 10 MHz counter.</li>
</ul>

<h3>Calibration Does Not Produce 10 MHz</h3>
<ul>
<li>Confirm the Nano is connected.</li>
<li>For SI5351 #1, measure OUT0 / Output 1 / BNC1.</li>
<li>For SI5351 #2, measure OUT3 / Output 4 / BNC4.</li>
<li>Use the Developer Console to test <code>C0;</code>, <code>C1;</code>, and <code>CX;</code>.</li>
</ul>

<h3>Output Already Assigned</h3>
<p>Another radio window already owns that output. Use the Output Manager to see
which window owns each output.</p>
""",
    },
    {
        "title": "Future Development",
        "keywords": "future rf bench oscillator eeprom viewer si5351 register viewer i2c scanner macros timestamps log",
        "body": """
<h2>Future Development</h2>
<p>The current release is focused on a stable, documented Multi-Radio VFO
platform. Possible future enhancements include:</p>
<ul>
<li>RF Bench Oscillator mode.</li>
<li>Developer Console macro buttons.</li>
<li>Save Log and Copy Log functions.</li>
<li>Timestamped TX/RX console messages.</li>
<li>Firmware command reference inside the console.</li>
<li>EEPROM Viewer.</li>
<li>SI5351 Register Viewer.</li>
<li>I2C Scanner.</li>
</ul>
<p>These are future concepts and are not required for normal Version 1.0 VFO use.</p>
""",
    },
]


class HelpWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("SI5351 Multi-Radio VFO Help")
        self.resize(900, 650)

        self.filtered_topics = list(HELP_TOPICS)

        self.build_ui()
        self.populate_topic_list()

        if self.topic_list.count() > 0:
            self.topic_list.setCurrentRow(0)

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)

        title = QLabel(APP_VERSION)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold; padding: 6px;")
        main_layout.addWidget(title)

        search_row = QHBoxLayout()
        search_label = QLabel("Search:")
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Type a word such as calibration, console, wiring, safety, profile, output, session..."
        )
        self.clear_button = QPushButton("Clear")

        search_row.addWidget(search_label)
        search_row.addWidget(self.search_edit)
        search_row.addWidget(self.clear_button)
        main_layout.addLayout(search_row)

        body_row = QHBoxLayout()
        self.topic_list = QListWidget()
        self.topic_list.setMinimumWidth(260)

        self.help_text = QTextEdit()
        self.help_text.setReadOnly(True)

        body_row.addWidget(self.topic_list, 1)
        body_row.addWidget(self.help_text, 3)
        main_layout.addLayout(body_row)

        bottom_row = QHBoxLayout()
        self.close_button = QPushButton("Close")
        bottom_row.addStretch()
        bottom_row.addWidget(self.close_button)
        main_layout.addLayout(bottom_row)

        self.search_edit.textChanged.connect(self.on_search_changed)
        self.clear_button.clicked.connect(self.clear_search)
        self.topic_list.currentItemChanged.connect(self.on_topic_selected)
        self.close_button.clicked.connect(self.close)

    def populate_topic_list(self):
        self.topic_list.blockSignals(True)
        self.topic_list.clear()

        for topic in self.filtered_topics:
            item = QListWidgetItem(topic["title"])
            item.setData(Qt.UserRole, topic)
            self.topic_list.addItem(item)

        self.topic_list.blockSignals(False)

        if self.topic_list.count() > 0:
            self.topic_list.setCurrentRow(0)
        else:
            self.help_text.setHtml(
                "<h2>No matching help topics</h2><p>Try a different search word.</p>"
            )

    def on_search_changed(self, text):
        query = text.strip().lower()

        if not query:
            self.filtered_topics = list(HELP_TOPICS)
        else:
            matches = []
            for topic in HELP_TOPICS:
                haystack = " ".join(
                    [
                        topic.get("title", ""),
                        topic.get("keywords", ""),
                        topic.get("body", ""),
                    ]
                ).lower()

                if query in haystack:
                    matches.append(topic)

            self.filtered_topics = matches

        self.populate_topic_list()

    def clear_search(self):
        self.search_edit.clear()

    def on_topic_selected(self, current, previous):
        if current is None:
            return

        topic = current.data(Qt.UserRole)
        if not topic:
            return

        self.help_text.setHtml(topic.get("body", ""))
