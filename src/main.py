import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog, QMessageBox, QDockWidget, QTextEdit, QLabel, QToolBar, QStatusBar
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import os
import subprocess

from .hexwidget import HexWidget
from . import peinfo

WINDOW_READ = 65536  # 最初に読み込むバイト数（MVP）

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('BinaryBuild - MVP')
        self.hexwidget = HexWidget(self)
        self.setCentralWidget(self.hexwidget)
        self.current_path = None

        # dock: PE info
        self.pe_dock = QDockWidget('PE Info', self)
        self.pe_text = QTextEdit()
        self.pe_text.setReadOnly(True)
        self.pe_dock.setWidget(self.pe_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.pe_dock)

        # status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # toolbar/menu
        tb = QToolBar('Main')
        self.addToolBar(tb)
        act_open = QAction('Open', self)
        act_open.triggered.connect(self.open_file)
        tb.addAction(act_open)
        act_save = QAction('Save', self)
        act_save.triggered.connect(self.save_file)
        tb.addAction(act_save)
        act_saveas = QAction('Save As', self)
        act_saveas.triggered.connect(self.save_file_as)
        tb.addAction(act_saveas)
        act_run = QAction('Run', self)
        act_run.triggered.connect(self.run_binary)
        tb.addAction(act_run)
        act_hash = QAction('Hash', self)
        act_hash.triggered.connect(self.show_hashes)
        tb.addAction(act_hash)

        # paging / navigation
        act_prev = QAction('Prev', self)
        act_prev.triggered.connect(self.page_prev)
        tb.addAction(act_prev)
        act_next = QAction('Next', self)
        act_next.triggered.connect(self.page_next)
        tb.addAction(act_next)
        act_goto = QAction('GoTo', self)
        act_goto.triggered.connect(self.goto_dialog)
        tb.addAction(act_goto)

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open binary')
        if not path:
            return
        self.current_path = path
        try:
            size = os.path.getsize(path)
            self.file_size = size
            # load initial window
            self.hexwidget.load_file_window(path, offset=0, size=WINDOW_READ)
            self.status.showMessage(f'Opened {os.path.basename(path)} size={size} bytes (window {len(self.hexwidget.bytes)} shown)')
            # PE info
            pe_summary = peinfo.get_pe_summary(path)
            self.pe_text.setPlainText(pe_summary)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to open file: {e}')

    def save_file(self):
        if not self.current_path:
            return self.save_file_as()
        try:
            data = self.hexwidget.get_bytes()
            # write shown window bytes back to file at current offset
            with open(self.current_path, 'r+b') as f:
                f.seek(self.hexwidget.offset)
                f.write(data)
            self.status.showMessage(f'Saved {os.path.basename(self.current_path)} ({len(data)} bytes written at offset 0x{self.hexwidget.offset:X})')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save: {e}')

    def save_file_as(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Save As')
        if not path:
            return
        try:
            data = self.hexwidget.get_bytes()
            with open(path, 'wb') as f:
                f.write(data)
            self.status.showMessage(f'Saved as {os.path.basename(path)}')
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to save as: {e}')

    def page_prev(self):
        if not self.current_path:
            return
        new_off = max(0, self.hexwidget.offset - self.hexwidget.window_size)
        self.hexwidget.goto_offset(new_off)
        self.status.showMessage(f'Window @ 0x{self.hexwidget.offset:X}')

    def page_next(self):
        if not self.current_path:
            return
        new_off = self.hexwidget.offset + self.hexwidget.window_size
        if new_off >= getattr(self, 'file_size', 0):
            QMessageBox.information(self, 'Page', 'Already at end of file')
            return
        self.hexwidget.goto_offset(new_off)
        self.status.showMessage(f'Window @ 0x{self.hexwidget.offset:X}')

    def goto_dialog(self):
        if not self.current_path:
            return
        from PySide6.QtWidgets import QInputDialog
        txt, ok = QInputDialog.getText(self, 'Go To Offset', 'Enter offset (hex like 0xFF or decimal):')
        if not ok or not txt:
            return
        try:
            if txt.startswith('0x') or txt.startswith('0X'):
                off = int(txt, 16)
            else:
                off = int(txt, 10)
            if off < 0 or off >= getattr(self, 'file_size', 0):
                QMessageBox.warning(self, 'Go To', 'Offset out of range')
                return
            # align to row start
            aligned = (off // BYTES_PER_ROW) * BYTES_PER_ROW
            self.hexwidget.goto_offset(aligned)
            self.status.showMessage(f'Window @ 0x{self.hexwidget.offset:X}')
        except Exception as e:
            QMessageBox.warning(self, 'Go To', f'Invalid offset: {e}')

    def run_binary(self):
        if not self.current_path:
            QMessageBox.information(self, 'Run', 'No binary opened')
            return
        ok = QMessageBox.question(self, 'Run', f'Run "{self.current_path}"?')
        if ok != QMessageBox.Yes:
            return
        try:
            subprocess.Popen([self.current_path], shell=False)
        except Exception as e:
            QMessageBox.critical(self, 'Error', f'Failed to run: {e}')

    def show_hashes(self):
        if not self.current_path:
            QMessageBox.information(self, 'Hashes', 'No file opened')
            return
        hashes = peinfo.compute_hashes(self.current_path)
        text = '\n'.join([f'{k}: {v}' for k, v in hashes.items()])
        QMessageBox.information(self, 'Hashes', text)


def main(argv=None):
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    w = MainWindow()
    w.resize(1000, 700)
    w.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
