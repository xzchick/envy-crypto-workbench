"""A native ENVY Cryptography Workbench window: a real desktop app, not a web view.

Built with PyQt6 and styled in the ENVY palette with a live animated header.
A Workbench tab chains encoding and classical-cipher operations over your text;
an Analysis tab shows frequency, entropy and a ROT brute force.
"""

from __future__ import annotations

import math
import os
import sys

from . import __version__
from .core import CAPTIONS, CryptoError, OPERATIONS, analyze, run_steps

BG = "#050713"
PANEL = "#0a0e22"
PANEL_HI = "#121735"
INK = "#f2f4ff"
MUTED = "#b9c3df"
DIM = "#6f7898"
PINK = "#ff3db4"
CYAN = "#35e8ff"
LAVENDER = "#ac8cff"
VIOLET = "#8547e8"
LINE = "#1f2547"

# Each operation button's accent.
OP_ACCENT = {
    "base64-encode": PINK, "base64-decode": PINK,
    "hex-encode": CYAN, "hex-decode": CYAN,
    "rot": LAVENDER, "atbash": LAVENDER, "reverse": VIOLET,
}


def lerp(a, b, t):
    from PyQt6.QtGui import QColor
    ca, cb = QColor(a), QColor(b)
    return QColor(int(ca.red() + (cb.red() - ca.red()) * t),
                  int(ca.green() + (cb.green() - ca.green()) * t),
                  int(ca.blue() + (cb.blue() - ca.blue()) * t))


def _build():
    from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
    from PyQt6.QtGui import (QColor, QPainter, QLinearGradient, QRadialGradient, QFont,
                             QPen, QBrush, QGuiApplication)
    from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QPlainTextEdit,
                                 QVBoxLayout, QHBoxLayout, QGridLayout, QSpinBox, QListWidget,
                                 QTabWidget, QFrame)

    class Header(QWidget):
        def __init__(self):
            super().__init__()
            self.setFixedHeight(176)
            self.phase = 0.0
            self.stars = [(((i * 139 + 37) % 1000) / 1000.0,
                           ((i * 83 + 19) % 176) / 176.0,
                           0.6 + (i % 3) * 0.5, (i % 7) / 7.0) for i in range(58)]

        def tick(self, phase):
            self.phase = phase
            self.update()

        def paintEvent(self, _event):
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            w, h = self.width(), self.height()
            p.fillRect(self.rect(), QColor(BG))
            for cx, cy, rad, col, a in ((w - 120, 60, 250, CYAN, 60),
                                        (60, h, 280, PINK, 55), (w * 0.5, -40, 240, VIOLET, 45)):
                g = QRadialGradient(cx, cy, rad)
                c = QColor(col); c.setAlpha(a); g.setColorAt(0, c)
                c2 = QColor(col); c2.setAlpha(0); g.setColorAt(1, c2)
                p.setBrush(QBrush(g)); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(cx, cy), rad, rad)
            for sx, sy, sr, ph in self.stars:
                tw = 0.5 + 0.5 * math.sin(self.phase / 0.5 + ph * 6.28)
                c = QColor(205, 217, 255); c.setAlphaF(0.15 + 0.6 * tw)
                p.setBrush(c); p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(sx * w, sy * h), sr, sr)
            pulse = 0.5 + 0.5 * math.sin(self.phase)
            p.setFont(QFont("Helvetica", 24))
            p.setPen(QColor(CYAN) if pulse > 0.5 else QColor(PINK))
            p.drawText(QRectF(24, 30, 42, 44), Qt.AlignmentFlag.AlignCenter, "⌨")
            p.setFont(QFont("Helvetica", 38, QFont.Weight.Bold))
            grad = QLinearGradient(70, 0, 420, 0)
            grad.setColorAt(0, QColor(PINK))
            grad.setColorAt(0.5, QColor(lerp(PINK, "#ffffff", 0.2 * pulse)))
            grad.setColorAt(1, QColor(CYAN))
            glow = QColor(CYAN); glow.setAlpha(int(55 + 55 * pulse))
            p.setPen(QPen(glow, 1))
            for dx, dy in ((1.3, 1.3), (-1.3, 1.3), (1.3, -1.3)):
                p.drawText(QRectF(70 + dx, 36 + dy, 520, 52), Qt.AlignmentFlag.AlignVCenter, "ENVY CRYPTO")
            p.setPen(QPen(QBrush(grad), 1))
            p.drawText(QRectF(70, 36, 520, 52), Qt.AlignmentFlag.AlignVCenter, "ENVY CRYPTO")
            p.setFont(QFont("Courier New", 11, QFont.Weight.Bold))
            p.setPen(QColor(LAVENDER))
            p.drawText(QRectF(74, 92, 520, 20), Qt.AlignmentFlag.AlignVCenter,
                       "OFFLINE  ·  CLASSICAL  ·  ANALYSIS")
            y = 128
            p.setPen(QPen(QColor(LINE), 2)); p.drawLine(74, y, w - 54, y)
            p.setPen(QPen(QColor(CYAN), 3)); p.drawLine(74, y, 146, y)
            span = (w - 54) - 74
            x = 74 + span * ((self.phase * 0.12) % 1.0)
            halo = QRadialGradient(x, y, 15)
            hc = QColor(PINK); hc.setAlpha(170); halo.setColorAt(0, hc)
            hc2 = QColor(PINK); hc2.setAlpha(0); halo.setColorAt(1, hc2)
            p.setBrush(QBrush(halo)); p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(QPointF(x, y), 15, 15)
            p.setBrush(QColor("#ffffff")); p.drawEllipse(QPointF(x, y), 2.5, 2.5)
            p.end()

    class Window(QWidget):
        def __init__(self):
            super().__init__()
            self.steps = []
            self.setWindowTitle("ENVY Cryptography Workbench")
            self.resize(940, 880)
            self.setMinimumSize(780, 720)
            self.setStyleSheet(STYLE)
            root = QVBoxLayout(self); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
            self.header = Header(); root.addWidget(self.header)
            tabs = QTabWidget(); tabs.setObjectName("tabs")
            tabs.addTab(self._workbench_tab(), "Workbench")
            tabs.addTab(self._analysis_tab(), "Analysis")
            tabs.currentChanged.connect(lambda i: self._recompute() if i == 1 else None)
            wrap = QWidget(); wrap.setObjectName("body")
            wl = QVBoxLayout(wrap); wl.setContentsMargins(22, 14, 22, 18); wl.addWidget(tabs)
            root.addWidget(wrap, 1)
            self.phase = 0.0
            self.timer = QTimer(self); self.timer.timeout.connect(self._animate); self.timer.start(33)
            self.inp.setPlainText("Uryyb, Jbeyq!")  # a friendly ROT13 starter
            self._recompute()

        # ----- tabs ---------------------------------------------------------
        def _workbench_tab(self):
            tab = QWidget(); g = QVBoxLayout(tab); g.setSpacing(10)
            g.addWidget(self._tag("INPUT TEXT"))
            self.inp = QPlainTextEdit(); self.inp.setObjectName("mono"); self.inp.setMinimumHeight(84)
            self.inp.textChanged.connect(self._recompute)
            g.addWidget(self.inp, 2)

            ops = QGridLayout(); ops.setSpacing(8)
            order = ["base64-encode", "base64-decode", "hex-encode", "hex-decode", "rot", "atbash", "reverse"]
            for i, op in enumerate(order):
                b = QPushButton(CAPTIONS[op]); b.setObjectName("op"); b.setMinimumHeight(44)
                b.setStyleSheet(f"#op{{border:1px solid {OP_ACCENT[op]};}}#op:hover{{background:{PANEL_HI};}}")
                b.setCursor(Qt.CursorShape.PointingHandCursor)
                b.clicked.connect(lambda _=False, o=op: self._add_step(o))
                ops.addWidget(b, i // 4, i % 4)
            self.shift = QSpinBox(); self.shift.setRange(-25, 25); self.shift.setValue(13)
            self.shift.setPrefix("ROT ")
            ops.addWidget(self.shift, 1, 3)
            g.addWidget(self._tag("ADD A STEP"))
            holder = QWidget(); holder.setLayout(ops); g.addWidget(holder)

            recipe_row = QHBoxLayout()
            self.recipe = QListWidget(); self.recipe.setObjectName("recipe"); self.recipe.setFixedHeight(96)
            recipe_row.addWidget(self.recipe, 1)
            col = QVBoxLayout()
            rm = QPushButton("Remove"); rm.setObjectName("pick"); rm.clicked.connect(self._remove_step)
            clr = QPushButton("Clear"); clr.setObjectName("pick"); clr.clicked.connect(self._clear)
            col.addWidget(rm); col.addWidget(clr); col.addStretch(1)
            recipe_row.addLayout(col)
            g.addWidget(self._tag("RECIPE (RUNS TOP TO BOTTOM)"))
            holder2 = QWidget(); holder2.setLayout(recipe_row); g.addWidget(holder2)

            g.addWidget(self._tag("OUTPUT"))
            self.out = QPlainTextEdit(); self.out.setObjectName("mono"); self.out.setReadOnly(True); self.out.setMinimumHeight(84)
            g.addWidget(self.out, 2)
            bottom = QHBoxLayout()
            copy = QPushButton("Copy output"); copy.setObjectName("go"); copy.clicked.connect(self._copy)
            self.status = QLabel("Build a recipe by adding steps."); self.status.setObjectName("status")
            bottom.addWidget(copy); bottom.addWidget(self.status, 1)
            g.addLayout(bottom)
            return tab

        def _analysis_tab(self):
            tab = QWidget(); g = QVBoxLayout(tab); g.setSpacing(10)
            g.addWidget(self._tag("READ-ONLY ANALYSIS OF THE INPUT"))
            self.stats = QLabel("—"); self.stats.setObjectName("stats"); self.stats.setWordWrap(True)
            g.addWidget(self.stats)
            g.addWidget(self._tag("ROT BRUTE FORCE (ALL 26 SHIFTS)"))
            self.brute = QPlainTextEdit(); self.brute.setObjectName("mono"); self.brute.setReadOnly(True)
            g.addWidget(self.brute, 1)
            copy_a = QPushButton("Copy analysis"); copy_a.setObjectName("go"); copy_a.clicked.connect(self._copy_analysis)
            g.addWidget(copy_a)
            note = QLabel("Frequency and entropy describe text; they never prove encryption or wrongdoing.")
            note.setObjectName("foot"); note.setWordWrap(True); g.addWidget(note)
            return tab

        def _tag(self, text):
            lab = QLabel(text); lab.setObjectName("tag"); return lab

        # ----- behavior -----------------------------------------------------
        def _add_step(self, op):
            step = {"op": op}
            if op == "rot":
                step["shift"] = self.shift.value()
            self.steps.append(step)
            label = CAPTIONS[op] + (f"  (shift {step['shift']})" if op == "rot" else "")
            self.recipe.addItem(label)
            self._recompute()

        def _remove_step(self):
            row = self.recipe.currentRow()
            if row < 0 and self.steps:
                row = len(self.steps) - 1
            if 0 <= row < len(self.steps):
                self.steps.pop(row); self.recipe.takeItem(row); self._recompute()

        def _clear(self):
            self.steps.clear(); self.recipe.clear(); self._recompute()

        def _copy(self):
            QGuiApplication.clipboard().setText(self.out.toPlainText())
            self.status.setText("Output copied to the clipboard."); self.status.setStyleSheet(f"#status{{color:{CYAN};}}")

        def _copy_analysis(self):
            text = self.stats.text() + "\n\n" + self.brute.toPlainText()
            QGuiApplication.clipboard().setText(text.strip())
            self.status.setText("Analysis copied to the clipboard."); self.status.setStyleSheet(f"#status{{color:{CYAN};}}")

        def _recompute(self):
            data = self.inp.toPlainText().encode("utf-8")
            if not self.steps:
                self.out.setPlainText(self.inp.toPlainText())
                self.status.setText("No steps yet — output mirrors the input."); self.status.setStyleSheet("")
            else:
                try:
                    result, _ = run_steps(data, self.steps)
                    try:
                        self.out.setPlainText(result.decode("utf-8"))
                    except UnicodeDecodeError:
                        self.out.setPlainText(result.hex())
                        self.status.setText(f"{len(self.steps)} step(s) → binary, shown as hex."); self.status.setStyleSheet(f"#status{{color:{LAVENDER};}}")
                    else:
                        self.status.setText(f"{len(self.steps)} step(s) applied."); self.status.setStyleSheet(f"#status{{color:{CYAN};}}")
                except CryptoError as exc:
                    self.out.setPlainText(""); self.status.setText(str(exc)); self.status.setStyleSheet(f"#status{{color:{PINK};}}")
            if getattr(self, "stats", None) is not None:
                self._update_analysis(data)

        def _update_analysis(self, data):
            report = analyze(data)
            self.stats.setText(
                f"<b>{report['bytes']}</b> bytes &nbsp;·&nbsp; entropy "
                f"<b>{report['entropy_bits_per_byte']:.3f}</b> bits/byte &nbsp;·&nbsp; "
                f"index of coincidence <b>{report['index_of_coincidence']:.4f}</b> &nbsp;·&nbsp; "
                f"UTF-8 {'yes' if report['utf8'] else 'no'}")
            if report["rot_candidates"]:
                self.brute.setPlainText("\n".join(
                    f"ROT {c['shift']:>2}  {c['preview'][:80]}" for c in report["rot_candidates"]))
            else:
                self.brute.setPlainText("(input is not text)")

        def _animate(self):
            self.phase += 0.05
            self.header.tick(self.phase)

    return QApplication, Window


STYLE = f"""
#body {{ background: {BG}; }}
QWidget {{ color: {INK}; font-family: Helvetica, Arial, sans-serif; font-size: 13px; }}
#tag {{ color: {MUTED}; font-weight: bold; font-size: 11px; letter-spacing: 1px; }}
#status {{ color: {MUTED}; font-size: 12px; }}
#stats {{ color: {INK}; font-size: 14px; }}
#foot {{ color: {DIM}; font-size: 11px; }}
#mono, #recipe {{ background: {PANEL_HI}; border: 1px solid {LINE}; border-radius: 9px;
                  color: {INK}; font-family: "Courier New", monospace; font-size: 13px; padding: 6px; }}
#mono:focus {{ border: 1px solid {CYAN}; }}
QTabWidget#tabs::pane {{ border: 1px solid {LINE}; border-radius: 12px; background: {PANEL}; }}
QTabBar::tab {{ background: {PANEL_HI}; color: {MUTED}; padding: 8px 20px; margin-right: 6px;
                border-top-left-radius: 9px; border-top-right-radius: 9px; font-weight: bold; }}
QTabBar::tab:selected {{ color: {INK}; border-bottom: 2px solid {PINK}; }}
QPushButton#op {{ background: {PANEL}; border-radius: 9px; color: {INK}; font-weight: bold; padding: 9px 6px; }}
QPushButton#pick {{ background: {PANEL_HI}; border: 1px solid {LAVENDER}; border-radius: 8px;
                    color: {INK}; font-weight: bold; padding: 6px 14px; }}
QPushButton#pick:hover {{ background: #1b2150; }}
QPushButton#go {{ background: {PINK}; color: {BG}; border: none; border-radius: 10px;
                  font-weight: bold; padding: 9px 18px; }}
QSpinBox {{ background: {PANEL_HI}; border: 1px solid {LAVENDER}; border-radius: 9px; color: {INK}; padding: 6px; }}
QListWidget#recipe::item:selected {{ background: {VIOLET}; color: {INK}; }}
"""


def run_app() -> int:
    try:
        from PyQt6.QtWidgets import QApplication  # noqa: F401
    except Exception:
        print("PyQt6 is required for the workbench window. Use 'envy-crypto run' or 'analyze' in a terminal.")
        return 2
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        print("No display found. Use 'envy-crypto run' or 'analyze' in a terminal instead.")
        return 2
    try:
        QApplication, Window = _build()
        app = QApplication.instance() or QApplication(sys.argv)
        window = Window(); window.show()
        return app.exec()
    except Exception as exc:  # pragma: no cover
        print(f"Could not open the window: {exc}")
        return 2
