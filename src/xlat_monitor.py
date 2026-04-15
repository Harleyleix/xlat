"""
XLAT Mouse Latency Measurement Tool v3
Baud: 1,000,000 | Format: count;latency_us;avg_us;stdev_us
"""
import sys, csv, threading
from collections import deque
from datetime import datetime

import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import pyqtgraph as pg

BG=    "#1a1f2e"; BG2="#141824"; BG3="#0f1319"; PANEL="#1e2436"
BTN=   "#252d3d"; BTN2="#2e3850"; ACCENT="#f5a623"; RED="#e05252"
GREEN= "#52e08a"; TEXT="#c8d0e0"; DIM="#5a6275"; BORDER="#2a3248"
CHART= "#0d1018"


class Signals(QObject):
    data   = pyqtSignal(int, float, float, float, float, float)
    log    = pyqtSignal(str)
    status = pyqtSignal(bool, str)
    meta   = pyqtSignal(str)   # device info / settings status


class SerialReader(threading.Thread):
    def __init__(self, port, signals):
        super().__init__(daemon=True)
        self.port = port
        self.sig  = signals
        self._stop_evt = threading.Event()
        self._min = self._max = None

    def stop(self):
        self._stop_evt.set()

    def run(self):
        try:
            s = serial.Serial(self.port, 1000000, timeout=0.05)
            self._serial_ref = s
        except Exception as e:
            self.sig.status.emit(False, str(e))
            return

        self.sig.status.emit(True, f"Connected {self.port} @ 1Mbaud")
        self.sig.log.emit(f"[{self._ts()}] Connected to {self.port}")
        # Request status và device info từ board
        import time
        time.sleep(0.5)
        s.write(b"status\n")
        s.write(b"info\n")
        buf = ""

        while not self._stop_evt.is_set():
            try:
                n = s.in_waiting
                if n:
                    raw = s.read(n)
                    buf += raw.decode("utf-8", errors="ignore")
                    while "\n" in buf:
                        line, buf = buf.split("\n", 1)
                        line = line.strip()
                        if line:
                            self.sig.log.emit(f"[{self._ts()}] {line}")
                            self._parse(line)
            except Exception as e:
                self.sig.log.emit(f"[{self._ts()}] ERROR: {e}")
                break

        try:
            s.close()
        except:
            pass
        self.sig.status.emit(False, "Disconnected")

    def _parse(self, line):
        # Device info lines
        if line.startswith("device:") or line.startswith("status:") or line.startswith("ok:"):
            self.sig.meta.emit(line)
            return

        # Data: count;latency_us;avg_us;stdev_us
        parts = line.split(";")
        if len(parts) != 4:
            return
        try:
            count = int(parts[0])
            last  = float(parts[1])
            avg   = float(parts[2])
            std   = float(parts[3])
        except ValueError:
            return
        if self._min is None or last < self._min: self._min = last
        if self._max is None or last > self._max: self._max = last
        self.sig.data.emit(count, last, avg, std, self._min, self._max)

    def send_command(self, cmd):
        """Gửi lệnh xuống board qua UART"""
        try:
            if hasattr(self, '_serial_ref') and self._serial_ref and self._serial_ref.is_open:
                self._serial_ref.write((cmd + "\n").encode())
        except:
            pass

    def reset_minmax(self):
        self._min = self._max = None

    @staticmethod
    def _ts():
        return datetime.now().strftime("%H:%M:%S.%f")[:-3]


class Chart(pg.PlotWidget):
    def __init__(self):
        super().__init__(background=CHART)
        self._data = deque(maxlen=300)
        self._x    = deque(maxlen=300)
        self._n    = 0
        self._ymax = 2000

        self.setMenuEnabled(False)
        self.showGrid(x=False, y=True, alpha=0.12)
        self.setLabel("left",   "Latency", units="μs", color=ACCENT, size="9pt")
        self.setLabel("bottom", "Measurement Samples",  color=DIM,    size="9pt")
        self.getAxis("left").setTextPen(DIM)
        self.getAxis("bottom").setTextPen(DIM)
        self.getAxis("left").setPen(BORDER)
        self.getAxis("bottom").setPen(BORDER)
        self.setYRange(0, self._ymax)

        self._rlbl = pg.TextItem(f"Range: 0-{self._ymax}μs", color=ACCENT, anchor=(0,0))
        self._rlbl.setFont(QFont("Arial", 8))
        self.addItem(self._rlbl)
        self._rlbl.setPos(0, self._ymax)

        self._curve = self.plot(pen=pg.mkPen(color=ACCENT, width=1.5))

    def add(self, val):
        self._n += 1
        self._data.append(val)
        self._x.append(self._n)
        if val > self._ymax * 0.9:
            self._ymax = int(val * 1.5 / 500) * 500 + 500
            self.setYRange(0, self._ymax)
            self._rlbl.setText(f"Range: 0-{self._ymax}μs")
            self._rlbl.setPos(0, self._ymax)
        self._curve.setData(list(self._x), list(self._data))

    def clear(self):
        self._data.clear(); self._x.clear(); self._n = 0
        self._ymax = 2000; self.setYRange(0, self._ymax)
        self._rlbl.setText(f"Range: 0-{self._ymax}μs")
        self._curve.setData([], [])


def _sv(grid, lbl, row, col, vc=TEXT):
    l = QLabel(lbl); l.setStyleSheet(f"color:{DIM};font-size:12px;")
    v = QLabel("-"); v.setStyleSheet(f"color:{vc};font-size:13px;font-weight:600;")
    grid.addWidget(l, row, col); grid.addWidget(v, row, col+1)
    return v



class SettingsDialog(QDialog):
    def __init__(self, parent=None, detected_mode="Mouse: Click", send_cmd=None):
        super().__init__(parent)
        self._send_cmd = send_cmd
        self._detected_mode = detected_mode
        self.setWindowTitle("Settings")
        self.resize(500, 380)
        self.setStyleSheet(f"""
            QDialog,QWidget{{background:{BG};color:{TEXT};}}
            QLabel{{color:{TEXT};font-size:12px;}}
            QComboBox{{background:{BTN};color:{TEXT};border:1px solid {BORDER};
                border-radius:4px;padding:5px 10px;font-size:12px;min-height:28px;}}
            QComboBox::drop-down{{border:none;width:22px;}}
            QComboBox QAbstractItemView{{background:{BTN};color:{TEXT};
                border:1px solid {BORDER};selection-background-color:{BTN2};}}
            QPushButton{{background:{BTN};color:{TEXT};border:none;border-radius:4px;
                padding:6px 16px;font-size:12px;}}
            QPushButton:hover{{background:{BTN2};}}
        """)
        self._build()

    def _build(self):
        lv = QVBoxLayout(self)
        lv.setContentsMargins(0,0,0,0); lv.setSpacing(0)

        # Title
        title = QLabel("  ⚙  Settings")
        title.setStyleSheet(f"background:{BG2};color:{TEXT};font-size:14px;font-weight:600;padding:14px;")
        lv.addWidget(title)

        # Tab buttons
        tr = QHBoxLayout(); tr.setSpacing(4); tr.setContentsMargins(12,10,12,0)
        self._tabs = []
        for i,txt in enumerate(["Mode","Detection","Trigger"]):
            b = QPushButton(txt); b.setCheckable(True)
            b.setChecked(i==0)
            b.setFixedHeight(34)
            self._tabs.append(b)
            tr.addWidget(b)
        tr.addStretch()
        lv.addLayout(tr)

        # Stack
        self._stack = QStackedWidget()
        lv.addWidget(self._stack)

        # Mode tab
        self._stack.addWidget(self._tab([
            ("Detection Mode:", ["Mouse: Click","Mouse: Motion","Keyboard: Keypress","Controller: Button"],
             self._detected_mode, "mode", {"Mouse: Click":0,"Mouse: Motion":1,"Keyboard: Keypress":2,"Controller: Button":3}),
        ]))

        # Detection tab
        self._stack.addWidget(self._tab([
            ("Detection Edge:",  ["Falling","Rising"], "Falling",
             "edge", {"Falling":0,"Rising":1}),
            ("Debounce Time:",   ["20ms","50ms","100ms","200ms","500ms","1000ms"], "100ms",
             "debounce", {"20ms":20,"50ms":50,"100ms":100,"200ms":200,"500ms":500,"1000ms":1000}),
            ("Input Bias:",      ["No Pull","Pull Up","Pull Down"], "No Pull",
             "bias", {"No Pull":0,"Pull Up":1,"Pull Down":2}),
        ]))

        # Trigger tab
        self._stack.addWidget(self._tab([
            ("Auto-trigger Level:",    ["Low","High"], "High",
             "level", {"Low":0,"High":1}),
            ("Auto-trigger Output:",   ["D6 (push-pull)","D11 (open-drain)"], "D11 (open-drain)",
             "output", {"D6 (push-pull)":6,"D11 (open-drain)":11}),
            ("Auto-trigger Interval:", ["100ms","200ms","300ms","400ms","500ms","600ms","700ms","800ms","900ms","1000ms"], "300ms",
             "interval", {f"{i*100}ms":i*100 for i in range(1,11)}),
        ]))

        # Tab connect
        for i,b in enumerate(self._tabs):
            b.clicked.connect(lambda _,idx=i: self._switch(idx))

        # Info
        info = QLabel("Note: Settings are controlled via board touchscreen.\nThis panel reflects detected/default values.")
        info.setStyleSheet(f"color:{DIM};font-size:10px;padding:8px 20px 4px;")
        lv.addWidget(info)

        # Close
        br = QHBoxLayout(); br.setContentsMargins(12,4,12,14); br.addStretch()
        cb = QPushButton("Close"); cb.setFixedWidth(100); cb.clicked.connect(self.accept)
        br.addWidget(cb); lv.addLayout(br)

        self._switch(0)

    def _tab(self, items):
        w = QWidget(); fl = QFormLayout(w)
        fl.setContentsMargins(20,16,20,8); fl.setSpacing(14)
        fl.setLabelAlignment(Qt.AlignLeft)
        for item in items:
            label, options, default = item[0], item[1], item[2]
            cmd_key = item[3] if len(item) > 3 else None
            val_map = item[4] if len(item) > 4 else {}
            cb = QComboBox(); cb.addItems(options)
            idx = options.index(default) if default in options else 0
            cb.setCurrentIndex(idx)
            if cmd_key and self._send_cmd:
                def on_change(text, key=cmd_key, vmap=val_map):
                    v = vmap.get(text, text)
                    if self._send_cmd:
                        self._send_cmd(f"{key}={v}")
                cb.currentTextChanged.connect(on_change)
            fl.addRow(label, cb)
        return w

    def _switch(self, idx):
        self._stack.setCurrentIndex(idx)
        for i,b in enumerate(self._tabs):
            b.setChecked(i==idx)
            b.setStyleSheet(f"""
                QPushButton{{background:{"#2e3850" if i==idx else BTN};color:{TEXT};
                    border:1px solid {BORDER};border-radius:4px;
                    padding:6px 20px;font-size:12px;font-weight:{"700" if i==idx else "400"};}}
                QPushButton:hover{{background:{BTN2};}}
            """)


class XlatTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XLAT Mouse Latency Measurement Tool")
        self.resize(1100, 500)
        self.setStyleSheet(f"QMainWindow,QWidget{{background:{BG};color:{TEXT};}}")
        self._reader = None
        self._sig    = Signals()
        self._csv    = []
        self._logn   = 0
        self._build()
        self._sig.data.connect(self._on_data)
        self._sig.log.connect(self._on_log)
        self._sig.status.connect(self._on_status)
        self._sig.meta.connect(self._on_meta)
        self._refresh_ports()
        t = QTimer(self); t.timeout.connect(self._refresh_ports); t.start(3000)

    def _build(self):
        sp = QSplitter(Qt.Horizontal)
        sp.setHandleWidth(2)
        sp.setStyleSheet(f"QSplitter::handle{{background:{BORDER};}}")

        # LEFT
        left = QWidget()
        lv = QVBoxLayout(left)
        lv.setContentsMargins(10,8,10,8); lv.setSpacing(6)

        # Header
        hdr = QHBoxLayout()

        # Logo
        lo = QLabel("⚡"); lo.setStyleSheet(f"color:{ACCENT};font-size:18px;")
        tc = QVBoxLayout(); tc.setSpacing(0)
        tc.addWidget(QLabel("XLAT", styleSheet=f"color:{TEXT};font-size:15px;font-weight:800;letter-spacing:2px;"))
        tc.addWidget(QLabel("Latency Tool", styleSheet=f"color:{DIM};font-size:9px;"))

        # Port
        pc = QVBoxLayout(); pc.setSpacing(3)
        pr = QHBoxLayout(); pr.setSpacing(4)
        self._port = QComboBox()
        self._port.setFixedHeight(26); self._port.setMinimumWidth(110)
        self._port.setStyleSheet(self._cs())
        rb = QPushButton("⟳"); rb.setFixedSize(26,26)
        rb.setStyleSheet(self._fb(BTN)); rb.clicked.connect(self._refresh_ports)
        pr.addWidget(self._port); pr.addWidget(rb)
        self._cb = QPushButton("Connect")
        self._cb.setFixedHeight(26)
        self._cb.setStyleSheet(self._fb(BTN2))
        self._cb.clicked.connect(self._toggle)
        pc.addLayout(pr); pc.addWidget(self._cb)

        # Status
        self._dot  = QLabel("●"); self._dot.setStyleSheet(f"color:{RED};font-size:13px;")
        self._slbl = QLabel("Disconnected"); self._slbl.setStyleSheet(f"color:{RED};font-size:11px;")
        sr = QHBoxLayout(); sr.setSpacing(4)
        sr.addWidget(self._dot); sr.addWidget(self._slbl); sr.addStretch()

        lc = QHBoxLayout(); lc.setSpacing(8)
        lc.addWidget(lo); lc.addLayout(tc); lc.addSpacing(10)
        lc.addLayout(pc)
        sc = QVBoxLayout(); sc.addLayout(sr)
        lc.addLayout(sc); lc.addStretch()

        # Top right
        tr = QVBoxLayout(); tr.setAlignment(Qt.AlignRight|Qt.AlignTop)
        self._dev_product = QLabel("No USB device found")
        self._dev_product.setStyleSheet(f"color:{TEXT};font-size:11px;font-weight:600;"); self._dev_product.setAlignment(Qt.AlignRight)
        self._dev_manuf = QLabel("")
        self._dev_manuf.setStyleSheet(f"color:{DIM};font-size:10px;"); self._dev_manuf.setAlignment(Qt.AlignRight)
        self._dev_vidpid = QLabel("")
        self._dev_vidpid.setStyleSheet(f"color:{DIM};font-size:9px;"); self._dev_vidpid.setAlignment(Qt.AlignRight)
        self._usb  = self._dev_product  # alias
        self._mode = QLabel("MODE: CLICK -  Data: locations not found")
        self._mode.setStyleSheet(f"color:{DIM};font-size:10px;"); self._mode.setAlignment(Qt.AlignRight)
        self._rdy  = QLabel("● READY")
        self._rdy.setStyleSheet(f"color:{RED};font-size:11px;font-weight:700;"); self._rdy.setAlignment(Qt.AlignRight)
        tr.addWidget(self._dev_product)
        tr.addWidget(self._dev_manuf)
        tr.addWidget(self._dev_vidpid)
        tr.addWidget(self._mode)
        tr.addWidget(self._rdy)

        hdr.addLayout(lc); hdr.addStretch(); hdr.addLayout(tr)
        lv.addLayout(hdr)

        self._msg = QLabel("Click to start measurement...")
        self._msg.setAlignment(Qt.AlignCenter)
        self._msg.setStyleSheet(f"color:{DIM};font-size:12px;")
        lv.addWidget(self._msg)

        # Chart + Stats
        cs = QHBoxLayout(); cs.setSpacing(10)
        self._chart = Chart(); self._chart.setMinimumHeight(200)
        cs.addWidget(self._chart, 3)

        sf = QFrame(); sf.setStyleSheet(f"background:{PANEL};border-radius:6px;")
        sg = QGridLayout(sf); sg.setContentsMargins(16,12,16,12); sg.setSpacing(10)
        sg.setColumnMinimumWidth(1,65); sg.setColumnMinimumWidth(3,65)
        self._vc = _sv(sg,"Count:",  0,0)
        self._vi = _sv(sg,"Min:",    0,2, GREEN)
        self._va = _sv(sg,"Average:",1,0)
        self._vx = _sv(sg,"Max:",    1,2, RED)
        self._vs = _sv(sg,"Stdev:",  2,0)
        self._vl = _sv(sg,"Last:",   2,2, ACCENT)
        self._vc.setStyleSheet(f"color:{TEXT};font-size:14px;font-weight:700;")
        cs.addWidget(sf, 1)
        lv.addLayout(cs)

        # Buttons
        br = QHBoxLayout(); br.setSpacing(4)
        for txt,fn in [("CLEAR",self._clear),("REBOOT",lambda:self._on_log("Reboot (N/A)")),
                       ("SETTINGS",lambda: self._open_settings()),("EXPORT CSV",self._export)]:
            b = QPushButton(txt); b.setFixedHeight(30)
            b.setStyleSheet(self._fb(BTN)); b.clicked.connect(fn)
            br.addWidget(b)
        trig = QPushButton("▶ TRIGGER"); trig.setFixedHeight(30)
        trig.setStyleSheet(f"QPushButton{{background:{BTN};color:{ACCENT};border:1px solid {ACCENT}33;border-radius:4px;padding:4px 12px;font-size:11px;font-weight:600;}}QPushButton:hover{{background:{ACCENT}22;}}")
        trig.clicked.connect(lambda: self._on_log("Trigger"))
        br.addWidget(trig)
        br.addWidget(QLabel("Ready", styleSheet=f"color:{DIM};font-size:11px;padding:0 8px;"))
        lv.addLayout(br)

        # Log
        lh = QHBoxLayout()
        self._logck = QCheckBox("Log (0)"); self._logck.setStyleSheet(f"color:{DIM};font-size:10px;")
        self._logck.toggled.connect(lambda c: self._logarea.setVisible(c))
        lh.addWidget(self._logck); lh.addStretch()
        lv.addLayout(lh)
        self._logarea = QTextEdit(); self._logarea.setReadOnly(True)
        self._logarea.setVisible(False); self._logarea.setMaximumHeight(70)
        self._logarea.setStyleSheet(f"QTextEdit{{background:{BG3};color:{DIM};border:1px solid {BORDER};font-family:Consolas;font-size:10px;}}")
        lv.addWidget(self._logarea)

        # RIGHT console
        right = QWidget(); right.setStyleSheet(f"background:{BG2};")
        rv = QVBoxLayout(right); rv.setContentsMargins(8,8,8,8)
        rv.addWidget(QLabel("=== XLAT Debug Console ===",
                            styleSheet=f"color:{DIM};font-size:11px;font-family:Consolas;"))
        self._con = QTextEdit(); self._con.setReadOnly(True)
        self._con.setStyleSheet(f"QTextEdit{{background:{BG3};color:{GREEN};border:none;font-family:Consolas;font-size:10px;}}")
        rv.addWidget(self._con)

        sp.addWidget(left); sp.addWidget(right); sp.setSizes([700,380])
        self.setCentralWidget(sp)

    def _cs(self):
        return f"QComboBox{{background:{BTN};color:{TEXT};border:1px solid {BORDER};border-radius:4px;padding:3px 8px;font-size:11px;}}QComboBox::drop-down{{border:none;width:18px;}}QComboBox QAbstractItemView{{background:{BTN};color:{TEXT};border:1px solid {BORDER};selection-background-color:{BTN2};}}"

    def _fb(self, bg, tc=TEXT):
        return f"QPushButton{{background:{bg};color:{tc};border:none;border-radius:4px;padding:4px 10px;font-size:11px;}}QPushButton:hover{{background:{BTN2};}}QPushButton:pressed{{background:{BORDER};}}"

    def _refresh_ports(self):
        cur = self._port.currentText()
        self._port.blockSignals(True); self._port.clear()
        for p in sorted(serial.tools.list_ports.comports(), key=lambda x: x.device):
            self._port.addItem(p.device, p.device)
        idx = self._port.findText(cur)
        if idx >= 0: self._port.setCurrentIndex(idx)
        self._port.blockSignals(False)

    def _toggle(self):
        if self._reader and self._reader.is_alive():
            self._reader.stop(); self._reader = None
        else:
            port = self._port.currentData()
            if not port: return
            self._reader = SerialReader(port, self._sig)
            self._reader.start()

    def _on_status(self, ok, msg):
        if ok:
            self._cb.setText("Disconnect")
            self._dot.setStyleSheet(f"color:{GREEN};font-size:13px;")
            self._slbl.setStyleSheet(f"color:{GREEN};font-size:11px;"); self._slbl.setText("Connected")
            self._rdy.setText("● READY"); self._rdy.setStyleSheet(f"color:{GREEN};font-size:11px;font-weight:700;")
            self._msg.setText("Measuring...")
        else:
            self._cb.setText("Connect")
            self._dot.setStyleSheet(f"color:{RED};font-size:13px;")
            self._slbl.setStyleSheet(f"color:{RED};font-size:11px;"); self._slbl.setText("Disconnected")
            self._rdy.setText("● READY"); self._rdy.setStyleSheet(f"color:{RED};font-size:11px;font-weight:700;")

    def _on_data(self, count, last, avg, std, mn, mx):
        self._chart.add(last)
        self._vc.setText(str(count))
        self._vl.setText(f"{last:.0f} μs")
        self._va.setText(f"{avg:.0f} μs")
        self._vs.setText(f"{std:.0f} μs")
        self._vi.setText(f"{mn:.0f} μs")
        self._vx.setText(f"{mx:.0f} μs")
        self._csv.append({"timestamp":datetime.now().isoformat(),
                          "count":count,"latency_us":last,
                          "avg_us":avg,"stdev_us":std,"min_us":mn,"max_us":mx})

    def _on_log(self, msg):
        self._con.append(msg)
        self._con.verticalScrollBar().setValue(self._con.verticalScrollBar().maximum())
        self._logn += 1; self._logck.setText(f"Log ({self._logn})")
        if self._logck.isChecked(): self._logarea.append(msg)

    def _open_settings(self):
        dlg = SettingsDialog(self,
            detected_mode=getattr(self,'_detected_mode','Mouse: Click'),
            send_cmd=self._send_cmd)
        dlg.exec_()

    def _clear(self):
        self._csv.clear(); self._chart.clear()
        if self._reader: self._reader.reset_minmax()
        for v in [self._vc,self._vl,self._va,self._vs,self._vi,self._vx]: v.setText("-")

    def _export(self):
        if not self._csv: return
        path,_ = QFileDialog.getSaveFileName(self,"Export CSV",
            f"xlat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv","CSV (*.csv)")
        if not path: return
        with open(path,"w",newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(self._csv[0].keys()))
            w.writeheader(); w.writerows(self._csv)
        self._on_log(f"Exported {len(self._csv)} rows → {path}")

    def closeEvent(self, e):
        if self._reader: self._reader.stop()
        e.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    XlatTool().show()
    sys.exit(app.exec_())

# Patch: thêm Settings dialog vào XlatTool
_orig_init = XlatTool.__init__

def _new_settings(self):
    from PyQt5.QtWidgets import QDialog, QTabWidget, QFormLayout, QDialogButtonBox
    dlg = QDialog(self)
    dlg.setWindowTitle("⚙ Settings")
    dlg.resize(500, 420)
    dlg.setStyleSheet(f"QDialog,QWidget{{background:#1a1f2e;color:#c8d0e0;}}QLabel{{color:#c8d0e0;font-size:12px;}}QComboBox{{background:#252d3d;color:#c8d0e0;border:1px solid #2a3248;border-radius:4px;padding:5px 10px;font-size:12px;min-height:28px;}}QComboBox::drop-down{{border:none;width:22px;}}QComboBox QAbstractItemView{{background:#252d3d;color:#c8d0e0;border:1px solid #2a3248;selection-background-color:#2e3850;}}QPushButton{{background:#252d3d;color:#c8d0e0;border:none;border-radius:4px;padding:6px 16px;font-size:12px;}}QPushButton:hover{{background:#2e3850;}}")

    main_lv = QVBoxLayout(dlg)
    main_lv.setContentsMargins(0,0,0,0)

    # Title bar
    title = QLabel("  ⚙  Settings")
    title.setStyleSheet("background:#141824;color:#c8d0e0;font-size:14px;font-weight:600;padding:12px;")
    main_lv.addWidget(title)

    # Tab buttons
    tab_row = QHBoxLayout()
    tab_row.setSpacing(0)
    tab_row.setContentsMargins(12,8,12,0)

    def make_tab_btn(txt, active=False):
        b = QPushButton(txt)
        b.setCheckable(True); b.setChecked(active)
        b.setStyleSheet(f"""
            QPushButton{{background:{'#2e3850' if active else '#1e2436'};color:#c8d0e0;
                border:1px solid #2a3248;border-radius:4px;padding:8px 20px;font-size:12px;font-weight:600;}}
            QPushButton:checked{{background:#2e3850;}}
            QPushButton:hover{{background:#2e3850;}}
        """)
        return b

    btn_mode = make_tab_btn("Mode", True)
    btn_det  = make_tab_btn("Detection")
    btn_trig = make_tab_btn("Trigger")
    tab_row.addWidget(btn_mode); tab_row.addWidget(btn_det); tab_row.addWidget(btn_trig)
    tab_row.addStretch()
    main_lv.addLayout(tab_row)

    # Content stack
    stack = QStackedWidget()
    stack.setStyleSheet("background:#1a1f2e;")
    main_lv.addWidget(stack)

    def make_form(items):
        w = QWidget(); fl = QFormLayout(w)
        fl.setContentsMargins(20,16,20,8); fl.setSpacing(14)
        fl.setLabelAlignment(Qt.AlignLeft)
        combos = {}
        for label, options, default in items:
            cb = QComboBox(); cb.addItems(options)
            idx = options.index(default) if default in options else 0
            cb.setCurrentIndex(idx)
            fl.addRow(label, cb)
            combos[label] = cb
        return w, combos

    # Mode tab
    mode_w, mode_c = make_form([
        ("Detection Mode:", ["Mouse: Click","Mouse: Motion","Keyboard: Keypress","Controller: Button"],
         self._detected_mode if hasattr(self,'_detected_mode') else "Mouse: Click"),
    ])
    stack.addWidget(mode_w)

    # Detection tab
    det_w, det_c = make_form([
        ("Detection Edge:",  ["Falling","Rising"],  "Falling"),
        ("Debounce Time:",   ["20ms","50ms","100ms","200ms","500ms","1000ms"], "100ms"),
        ("Input Bias:",      ["No Pull","Pull Up","Pull Down"], "No Pull"),
    ])
    stack.addWidget(det_w)

    # Trigger tab
    trig_w, trig_c = make_form([
        ("Auto-trigger Level:",    ["Low","High"],  "High"),
        ("Auto-trigger Output:",   ["D6 (push-pull)","D11 (open-drain)"], "D11 (open-drain)"),
        ("Auto-trigger Interval:", ["100ms","200ms","300ms","400ms","500ms","600ms","700ms","800ms","900ms","1000ms"], "300ms"),
    ])
    stack.addWidget(trig_w)

    # Tab switching
    def switch(idx):
        for i,b in enumerate([btn_mode,btn_det,btn_trig]):
            b.setChecked(i==idx)
            b.setStyleSheet(b.styleSheet().replace(
                '#1e2436' if i==idx else '#2e3850',
                '#2e3850' if i==idx else '#1e2436'
            ))
        stack.setCurrentIndex(idx)

    btn_mode.clicked.connect(lambda: switch(0))
    btn_det.clicked.connect(lambda:  switch(1))
    btn_trig.clicked.connect(lambda: switch(2))

    # Info label
    info = QLabel("Note: Settings are applied on the board via touchscreen.\nThis panel shows current detected values.")
    info.setStyleSheet("color:#5a6275;font-size:10px;padding:8px 20px;")
    main_lv.addWidget(info)

    # Close button
    br = QHBoxLayout(); br.setContentsMargins(12,4,12,12)
    br.addStretch()
    close_btn = QPushButton("Close"); close_btn.setFixedWidth(100)
    close_btn.clicked.connect(dlg.accept)
    br.addWidget(close_btn)
    main_lv.addLayout(br)

    dlg.exec_()

XlatTool._settings = _new_settings
