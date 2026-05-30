# File: help_window.py
#
# Searchable help window for the SI5351 Multi-Radio VFO Control Platform.
#
# This file is intentionally self-contained so the installed application can
# display operating help without internet access or external documentation files.

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

APP_VERSION = "SI5351 Multi-Radio VFO Platform - Help v1.1"


HELP_TOPICS = [
    {
        "title": "Quick Start",
        "keywords": "start connect com port radio band output frequency spot rf",
        "body": """
<h2>Quick Start</h2>
<ol>
<li>Select the USB COM port for the Arduino Nano controller.</li>
<li>Click <b>Connect</b>.</li>
<li>Select the radio profile.</li>
<li>Select the band.</li>
<li>Select the output connector.</li>
<li>Enter the desired RF operating frequency.</li>
<li>Click <b>Set Frequency</b>.</li>
<li>Use <b>SPOT</b> for receive-only carrier checking and zero-beat setup.</li>
</ol>
<p>The main frequency field is the desired RF operating frequency. The VFO field shows the calculated SI5351 output frequency sent to the hardware.</p>
""",
    },
    {
        "title": "Version / Freeze Points",
        "keywords": "version freeze stable release profile editor reload profiles",
        "body": """
<h2>Version / Freeze Points</h2>
<p>Current major platform milestone:</p>
<ul>
<li><b>SI5351_VFO_PLATFORM_v7_CALIBRATION_GUI_INTEGRATED_STABLE</b></li>
</ul>
<p>Current profile editor milestone:</p>
<ul>
<li><b>SI5351_VFO_PROFILE_EDITOR_v1_9_VALIDATION_WARNINGS_STABLE</b></li>
</ul>
<p>The platform now supports live profile editing, safe JSON persistence, profile reload, validation warnings, multi-output operation, session restore, per-SI5351 EEPROM calibration, and a dedicated calibration GUI.</p>
""",
    },
    {
        "title": "Architecture Overview",
        "keywords": "architecture gui brain nano executor profiles json radio math si5351",
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
</ul>
<p>The Arduino Nano is the execution engine. It receives frequency and RF enable commands over USB serial and drives the SI5351 hardware.</p>
<p>Radio-specific math stays in <b>radio_profiles.json</b> and the Python math engine. Do not move radio-profile math into the Nano firmware.</p>
""",
    },
    {
        "title": "Hardware Wiring Overview",
        "keywords": "wiring nano tca9548a si5351 i2c mux bnc output clk",
        "body": """
<h2>Hardware Wiring Overview</h2>
<ul>
<li>Controller: Arduino Nano / ATmega328.</li>
<li>I2C mux: TCA9548A at address 0x70.</li>
<li>SI5351 module #1: behind mux channel 0.</li>
<li>SI5351 module #2: behind mux channel 1.</li>
</ul>
<p>Output mapping:</p>
<ul>
<li>BNC 1 = OUT0 = SI5351 #1 CLK0</li>
<li>BNC 2 = OUT1 = SI5351 #1 CLK1</li>
<li>BNC 3 = OUT2 = SI5351 #1 CLK2</li>
<li>BNC 4 = OUT3 = SI5351 #2 CLK0</li>
<li>BNC 5 = OUT4 = SI5351 #2 CLK1</li>
<li>BNC 6 = OUT5 = SI5351 #2 CLK2</li>
</ul>
<p>Operator labels use Output 1 through Output 6. Firmware protocol uses OUT0 through OUT5.</p>
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
<li>TX overrides SPOT.</li>
<li>The safety monitor warns about same-band TX conflicts.</li>
</ul>
<p>The current safety monitor is warning-only. It does not physically block RF. Always verify output routing and transmitter connections before enabling RF.</p>
""",
    },
    {
        "title": "Monitor ON/OFF and Serial Responses",
        "keywords": "monitor on off serial response id test read calibration xc debug log hidden",
        "body": """
<h2>Monitor ON/OFF and Serial Responses</h2>
<p>The <b>Monitor ON/OFF</b> button controls whether the serial/debug log panel is visible.</p>
<p>When the button says <b>Monitor OFF</b>, the monitor panel is hidden. Click it once to turn the monitor on. The button will then say <b>Monitor ON</b>.</p>
<h3>Important</h3>
<p>Some buttons send commands to the Nano and show their results only in the monitor/log panel.</p>
<ul>
<li><b>ID Test</b> sends <code>ID;</code> to the Nano.</li>
<li><b>Read Calibration</b> reads calibration values from the Nano.</li>
</ul>
<p>If the monitor is hidden, the commands may still work, but you may not see the returned text.</p>
<h3>Example monitor responses</h3>
<pre>IDNANO-SI5351-TCA9548A-OUT0-OUT5-CALV5;
XC0,+000019790;
XC1,-000000320;</pre>
<p>Use the monitor when checking firmware identity, calibration values, serial command responses, or troubleshooting COM-port behavior.</p>
""",
    },
    {
        "title": "SI5351 Calibration Procedure",
        "keywords": "calibration calibrate si5351 counter 10 mhz eeprom xc c0 c1 out0 out3 bnc1 bnc4 save cal exit cal",
        "body": """
<h2>SI5351 Calibration Procedure</h2>
<p>The calibration system corrects the crystal oscillator error of each physical Adafruit SI5351 module.</p>
<p>Calibration values are stored in the Arduino Nano EEPROM. This means each physical VFO box carries its own calibration values and can be moved between PCs without recalibration.</p>
<h3>SI5351 module mapping</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>SI5351 Module</th><th>Outputs</th><th>Calibration Output</th></tr>
<tr><td>SI5351 #1</td><td>OUT0, OUT1, OUT2</td><td>OUT0 / BNC1</td></tr>
<tr><td>SI5351 #2</td><td>OUT3, OUT4, OUT5</td><td>OUT3 / BNC4</td></tr>
</table>
<h3>Equipment required</h3>
<ul>
<li>Frequency counter capable of accurately measuring 10 MHz.</li>
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
<li>Connect the frequency counter to <b>OUT0 / BNC1</b>.</li>
<li>Click <b>START CAL</b>.</li>
<li>The Nano disables normal RF outputs and generates a fixed <b>10.000000 MHz</b> signal on OUT0.</li>
<li>Use the <b>UP</b> and <b>DOWN</b> buttons to walk the counter reading to exactly <b>10.000000 MHz</b>.</li>
<li>Use larger steps such as <b>1000</b> for coarse movement, then <b>100</b>, <b>10</b>, or <b>1</b> for fine adjustment.</li>
<li>Click <b>SAVE CAL</b> to store the correction in Nano EEPROM.</li>
<li>Click <b>EXIT CAL</b> to leave calibration mode, or click <b>EXIT</b> to leave calibration mode and close the window.</li>
</ol>
<h3>Calibrating SI5351 #2</h3>
<ol>
<li>If calibration is active for SI5351 #1, first click <b>EXIT CAL</b>.</li>
<li>Select <b>SI5351 #2</b> in the Target dropdown.</li>
<li>Move the frequency counter to <b>OUT3 / BNC4</b>.</li>
<li>Click <b>START CAL</b>.</li>
<li>The Nano generates a fixed <b>10.000000 MHz</b> signal on OUT3.</li>
<li>Use <b>UP</b>, <b>DOWN</b>, and the step selector until the counter reads exactly <b>10.000000 MHz</b>.</li>
<li>Click <b>SAVE CAL</b>.</li>
<li>Click <b>EXIT CAL</b> or <b>EXIT</b>.</li>
</ol>
<h3>Target dropdown behavior</h3>
<p>The Target dropdown is intentionally disabled during active calibration. This prevents accidentally switching between SI5351 modules while one module is outputting the calibration signal.</p>
<p>To change from SI5351 #1 to SI5351 #2, first click <b>EXIT CAL</b>. The Target dropdown will become available again.</p>
<h3>EXIT CAL vs EXIT</h3>
<table border="1" cellspacing="0" cellpadding="4">
<tr><th>Button</th><th>Function</th></tr>
<tr><td><b>EXIT CAL</b></td><td>Exits Nano calibration mode but keeps the Calibration Window open.</td></tr>
<tr><td><b>EXIT</b></td><td>Exits Nano calibration mode if needed, then closes the Calibration Window.</td></tr>
<tr><td><b>Window X</b></td><td>Also safely exits calibration mode before closing.</td></tr>
</table>
<h3>Safety notes</h3>
<ul>
<li>Calibration mode disables normal RF outputs.</li>
<li>Only one calibration output is active at a time.</li>
<li>Do not calibrate while connected to a transmitter input unless that is intentional and safe.</li>
<li>Always exit calibration mode before returning to normal VFO operation.</li>
</ul>
<h3>Verifying saved calibration</h3>
<p>Calibration values are restored automatically after Nano reboot. To view them, turn <b>Monitor ON</b> and use <b>Read Calibration</b>, or send serial commands:</p>
<pre>XC0;
XC1;</pre>
""",
    },
    {
        "title": "Profile Editor Instructions",
        "keywords": "profile editor add duplicate delete band save backup validate",
        "body": """
<h2>Profile Editor Instructions</h2>
<p>Use <b>Profile Editor</b> to edit <b>radio_profiles.json</b>.</p>
<ul>
<li><b>New</b>: creates a new initialized radio profile.</li>
<li><b>Duplicate</b>: copies an existing radio profile.</li>
<li><b>Delete</b>: removes the selected profile after confirmation.</li>
<li><b>Add Band</b>: adds a new initialized band.</li>
<li><b>Duplicate Band</b>: copies the selected band.</li>
<li><b>Delete Band</b>: removes the selected band after confirmation.</li>
<li><b>Apply Band Changes</b>: applies detail-panel edits into the in-memory model.</li>
<li><b>Save</b>: writes JSON and creates an automatic backup.</li>
<li><b>Validate Profiles</b>: checks the profile database for common errors.</li>
</ul>
<p>After saving profile changes, return to the main VFO window and click <b>Reload Profiles</b>.</p>
""",
    },
    {
        "title": "Reload Profiles",
        "keywords": "reload profiles profile editor restart json update",
        "body": """
<h2>Reload Profiles</h2>
<p>Use <b>Reload Profiles</b> after saving changes in the Profile Editor.</p>
<p>This reloads <b>radio_profiles.json</b> without restarting the main program. It keeps the same profile and band selected when possible.</p>
<p>If a profile or band was deleted, the program selects the nearest available profile or band.</p>
""",
    },
    {
        "title": "Frequency Entry",
        "keywords": "frequency entry mhz khz hz examples set frequency",
        "body": """
<h2>Frequency Entry</h2>
<p>The frequency entry box accepts several formats:</p>
<ul>
<li><b>7.100</b> = 7.100 MHz</li>
<li><b>7100</b> = 7100 kHz</li>
<li><b>7100000</b> = 7,100,000 Hz</li>
<li><b>14.250 MHz</b> = 14.250 MHz</li>
</ul>
<p>The program converts the RF input through the selected radio profile and sends the resulting SI5351 output frequency to the selected output.</p>
""",
    },
    {
        "title": "Output Manager",
        "keywords": "output manager bnc owner assigned conflict window",
        "body": """
<h2>Output Manager</h2>
<p>The Output Manager tracks which radio window owns each RF output. It helps prevent accidental double assignment of one output to multiple radios.</p>
<p>Each output has:</p>
<ul>
<li>operator label</li>
<li>internal OUT number</li>
<li>current owning window</li>
<li>radio and band state</li>
<li>RF / SPOT / TX status</li>
</ul>
""",
    },
    {
        "title": "Session Restore",
        "keywords": "session restore save load windows compact reboot",
        "body": """
<h2>Session Restore</h2>
<p>The session system saves window layout and operating configuration.</p>
<p>It restores:</p>
<ul>
<li>main window position</li>
<li>floating radio windows</li>
<li>compact/full states</li>
<li>selected radio, band, output, frequency, and step size</li>
</ul>
<p>It does not restore RF ON, SPOT ON, or TX state. Those are always forced off for safety.</p>
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
            "Type a word such as calibration, monitor, wiring, safety, profile, output, session..."
        )
        self.clear_button = QPushButton("Clear")

        search_row.addWidget(search_label)
        search_row.addWidget(self.search_edit)
        search_row.addWidget(self.clear_button)
        main_layout.addLayout(search_row)

        body_row = QHBoxLayout()
        self.topic_list = QListWidget()
        self.topic_list.setMinimumWidth(240)

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
