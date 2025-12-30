import hashlib
import zlib

try:
    import pefile
except Exception:
    pefile = None


def get_pe_summary(path: str) -> str:
    if pefile is None:
        return "pefile not installed"
    try:
        pe = pefile.PE(path, fast_load=True)
        pe.parse_data_directories()
        s = []
        s.append(f"EntryPoint: 0x{pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}")
        s.append(f"ImageBase: 0x{pe.OPTIONAL_HEADER.ImageBase:08X}")
        s.append("Sections:")
        for sec in pe.sections:
            name = sec.Name.decode(errors='ignore').rstrip('\x00')
            s.append(f"  {name} @ {sec.VirtualAddress:08X} size={sec.SizeOfRawData}")
        return '\n'.join(s)
    except Exception as e:
        return f"Not a PE or parse error: {e}"


def compute_hashes(path: str) -> dict:
    hashes = {"md5": None, "sha1": None, "sha256": None, "crc32": None}
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    crc = 0
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
            crc = zlib.crc32(chunk, crc)
    hashes['md5'] = md5.hexdigest()
    hashes['sha1'] = sha1.hexdigest()
    hashes['sha256'] = sha256.hexdigest()
    hashes['crc32'] = f"{crc & 0xFFFFFFFF:08X}"
    return hashes
