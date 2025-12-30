from PySide6.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout
from PySide6.QtCore import Qt

import mmap
BYTES_PER_ROW = 16

class HexWidget(QWidget):
    """ファイルウィンドウを扱う16進/ASCII/UTF-8表示・編集ウィジェット（MVP, mmap対応）"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = QTableWidget(self)
        self.table.setColumnCount(1 + BYTES_PER_ROW + 2)  # Offset + 16 bytes + ASCII + UTF-8
        headers = ["Offset"] + [f"{i:02X}" for i in range(BYTES_PER_ROW)] + ["ASCII", "UTF-8"]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.AllEditTriggers)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        self.setLayout(layout)

        # file window state
        self.filepath = None
        self.file_size = 0
        self.offset = 0  # file offset of first shown byte
        self.window_size = 65536  # default page size (64KB)
        self._mmap = None  # mmap object or None
        self.bytes = b''

    def _read_window(self, path: str, offset: int, size: int) -> bytes:
        # Try to use mmap for large files; fallback to file read
        file_size = os.path.getsize(path)
        if file_size == 0:
            return b''
        read_size = min(size, max(0, file_size - offset))
        if read_size <= 0:
            return b''
        # Use mmap for files > 1MB for efficiency
        if file_size > 1024 * 1024:
            with open(path, 'rb') as f:
                m = mmap.mmap(f.fileno(), length=0, access=mmap.ACCESS_READ)
                try:
                    return m[offset:offset + read_size]
                finally:
                    m.close()
        else:
            with open(path, 'rb') as f:
                f.seek(offset)
                return f.read(read_size)

    def load_file_window(self, path: str, offset: int = 0, size: int | None = None):
        if size is None:
            size = self.window_size
        self.filepath = path
        self.file_size = os.path.getsize(path)
        self.offset = max(0, min(offset, max(0, self.file_size - 1)))
        data = self._read_window(path, self.offset, size)
        self.load_bytes(data, offset=self.offset, filepath=path)

    def load_bytes(self, data: bytes, offset: int = 0, filepath: str | None = None):
        # populate table from given bytes buffer; used by both window loader and unit tests
        self.bytes = data
        self.offset = offset
        self.filepath = filepath
        rows = (len(data) + BYTES_PER_ROW - 1) // BYTES_PER_ROW
        self.table.setRowCount(rows)
        for r in range(rows):
            row_off = offset + r * BYTES_PER_ROW
            off_item = QTableWidgetItem(f"{row_off:08X}")
            off_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(r, 0, off_item)
            row_slice = data[r*BYTES_PER_ROW:(r+1)*BYTES_PER_ROW]
            # hex cells
            for c in range(BYTES_PER_ROW):
                if c < len(row_slice):
                    b = row_slice[c]
                    it = QTableWidgetItem(f"{b:02X}")
                    it.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(r, 1 + c, it)
                else:
                    it = QTableWidgetItem("")
                    it.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                    self.table.setItem(r, 1 + c, it)
            # ASCII column
            ascii_repr = ''.join([chr(b) if 0x20 <= b < 0x7F else '.' for b in row_slice])
            ascii_item = QTableWidgetItem(ascii_repr)
            ascii_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(r, 1 + BYTES_PER_ROW, ascii_item)
            # UTF-8 column (attempt decode)
            try:
                utf8_text = row_slice.decode('utf-8')
            except Exception:
                utf8_text = row_slice.decode('utf-8', errors='replace')
            utf8_item = QTableWidgetItem(utf8_text)
            utf8_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.table.setItem(r, 1 + BYTES_PER_ROW + 1, utf8_item)

    def get_bytes(self) -> bytes:
        # reconstruct bytes for currently displayed window; returns only present bytes
        rows = self.table.rowCount()
        out = bytearray()
        for r in range(rows):
            for c in range(BYTES_PER_ROW):
                cell = self.table.item(r, 1 + c)
                if cell is None:
                    continue
                txt = cell.text().strip()
                if txt == "":
                    continue
                try:
                    b = int(txt, 16) & 0xFF
                except Exception:
                    b = 0
                out.append(b)
        return bytes(out)

    def goto_offset(self, offset: int):
        # load window starting at offset
        self.load_file_window(self.filepath, offset, self.window_size)
