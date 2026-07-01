"""
dbf.py
Lightweight pure-Python DBF reader extracted from the many hand-rolled
struct-based parsers that were duplicated across the root scripts
(add_*.py, analyze_*.py, etc.).

Supports the simple dBASE III / ArcGIS .dbf files you commonly work with.
"""

import struct
from collections import OrderedDict
from typing import Iterator, Dict, Any, List

def read_dbf(path: str) -> Iterator[Dict[str, Any]]:
    """
    Yield rows from a .dbf file as dicts.
    Only reads the header once, then streams records.
    """
    with open(path, 'rb') as f:
        header = f.read(32)
        num_records = struct.unpack('<I', header[4:8])[0]
        header_len = struct.unpack('<H', header[8:10])[0]
        rec_len = struct.unpack('<H', header[10:12])[0]

        f.seek(32)
        fields: List[tuple] = []
        while True:
            field_desc = f.read(32)
            if field_desc[0] == 0x0D:   # end of field descriptor
                break
            name = field_desc[0:11].decode('ascii').rstrip('\x00')
            ftype = chr(field_desc[11])
            flen = field_desc[16]
            fields.append((name, ftype, flen))

        f.seek(header_len)
        for _ in range(num_records):
            record = f.read(rec_len)
            if record[0] == 0x2A:       # deleted record marker
                continue
            pos = 1
            row: Dict[str, Any] = OrderedDict()
            for name, ftype, flen in fields:
                raw = record[pos:pos+flen]
                pos += flen
                val = raw.decode('ascii', errors='replace').strip()
                if ftype == 'N':
                    try:
                        val = float(val) if '.' in val else int(val)
                    except ValueError:
                        pass
                row[name] = val
            yield row

def dbf_to_list(path: str) -> List[Dict[str, Any]]:
    """Convenience: return all rows as a list."""
    return list(read_dbf(path))
