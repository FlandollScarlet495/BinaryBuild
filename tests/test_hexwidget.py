from src.hexwidget import HexWidget


def test_hexwidget_roundtrip():
    data = bytes(range(64))
    w = HexWidget()
    w.load_bytes(data, offset=0, filepath='dummy')
    out = w.get_bytes()
    assert out == data
