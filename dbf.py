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
        if len(header) < 32:
            raise ValueError(f"{path}: not a valid DBF (header truncated)")
        num_records = struct.unpack('<I', header[4:8])[0]
        header_len = struct.unpack('<H', header[8:10])[0]
        rec_len = struct.unpack('<H', header[10:12])[0]

        f.seek(32)
        fields: List[tuple] = []
        # Field descriptors are 32 bytes each and end with a 0x0D terminator.
        # Bound the loop by the declared header length so a missing terminator
        # can't spin to EOF.
        max_fields = max(0, (header_len - 32 - 1) // 32)
        for _ in range(max_fields + 1):
            field_desc = f.read(32)
            if not field_desc:
                raise ValueError(f"{path}: field descriptor block truncated / missing 0x0D terminator")
            if field_desc[0] == 0x0D:   # end of field descriptor (1-byte terminator)
                break
            if len(field_desc) < 32:
                raise ValueError(f"{path}: field descriptor truncated")
            name = field_desc[0:11].decode('ascii', errors='replace').rstrip('\x00')
            ftype = chr(field_desc[11])
            flen = field_desc[16]
            fields.append((name, ftype, flen))

        f.seek(header_len)
        for _ in range(num_records):
            record = f.read(rec_len)
            if len(record) < rec_len:   # truncated final record / short file
                break
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
