"""
Tests for the pure-Python .dbf reader in ``hydro_tools.dbf``.

A minimal but valid dBASE III file is synthesized on disk so the reader is
exercised end-to-end (header parse, field descriptors, record streaming,
deleted-record skipping, numeric coercion).
"""
import struct

import pytest

from hydro_tools.dbf import read_dbf, dbf_to_list


def _field_descriptor(name: str, ftype: str, length: int) -> bytes:
    desc = bytearray(32)
    encoded = name.encode("ascii")
    desc[0 : len(encoded)] = encoded          # null-padded name (11 bytes)
    desc[11] = ord(ftype)                       # field type
    desc[16] = length                           # field length
    return bytes(desc)


def _make_dbf(fields, records):
    """fields: list of (name, type, length); records: list of (values, deleted)."""
    header = bytearray(32)
    header[0] = 0x03                            # dBASE III
    struct.pack_into("<I", header, 4, len(records))

    field_descs = b"".join(_field_descriptor(n, t, ln) for n, t, ln in fields)
    header_len = 32 + len(field_descs) + 1      # +1 for the 0x0D terminator
    rec_len = 1 + sum(ln for _, _, ln in fields)
    struct.pack_into("<H", header, 8, header_len)
    struct.pack_into("<H", header, 10, rec_len)

    out = bytes(header) + field_descs + b"\x0d"
    for values, deleted in records:
        row = bytearray()
        row.append(0x2A if deleted else 0x20)   # deletion flag
        for (_, _, ln), val in zip(fields, values):
            row += val.rjust(ln).encode("ascii")[:ln]
        assert len(row) == rec_len
        out += bytes(row)
    return out


@pytest.fixture
def sample_dbf(tmp_path):
    path = tmp_path / "sample.dbf"
    fields = [("NAME", "C", 10), ("FLOW", "N", 6)]
    records = [
        (["PipeA", "15"], False),
        (["GONE", "99"], True),        # deleted -> should be skipped
        (["PipeB", "17.66"], False),
    ]
    path.write_bytes(_make_dbf(fields, records))
    return str(path)


def test_read_dbf_skips_deleted_and_coerces_numbers(sample_dbf):
    rows = dbf_to_list(sample_dbf)
    assert rows == [
        {"NAME": "PipeA", "FLOW": 15},
        {"NAME": "PipeB", "FLOW": 17.66},
    ]


def test_read_dbf_numeric_types(sample_dbf):
    rows = dbf_to_list(sample_dbf)
    assert isinstance(rows[0]["FLOW"], int)     # "15" -> int
    assert isinstance(rows[1]["FLOW"], float)   # "17.66" -> float


def test_read_dbf_is_iterator(sample_dbf):
    gen = read_dbf(sample_dbf)
    first = next(gen)
    assert first["NAME"] == "PipeA"


def test_read_dbf_empty_file_raises(tmp_path):
    path = tmp_path / "empty.dbf"
    path.write_bytes(b"")
    with pytest.raises(ValueError):
        dbf_to_list(str(path))


def test_read_dbf_truncated_header_raises(tmp_path):
    path = tmp_path / "short.dbf"
    path.write_bytes(b"\x03\x00\x00")   # fewer than 32 header bytes
    with pytest.raises(ValueError):
        dbf_to_list(str(path))


def test_read_dbf_missing_terminator_raises(tmp_path):
    # valid 32-byte header claiming a header_len that never reaches a 0x0D
    fields = [("NAME", "C", 10)]
    good = _make_dbf(fields, [(["PipeA"], False)])
    # drop the 0x0D terminator and everything after -> truncated descriptor area
    truncated = good[:32] + good[32:48]   # header + a partial field descriptor
    path = tmp_path / "noterm.dbf"
    path.write_bytes(truncated)
    with pytest.raises(ValueError):
        dbf_to_list(str(path))


def test_read_dbf_truncated_record_stops_cleanly(tmp_path):
    # declare 3 records but only supply bytes for 1.5 -> reader returns the whole
    # records it has and stops instead of crashing
    fields = [("NAME", "C", 10), ("FLOW", "N", 6)]
    full = _make_dbf(fields, [(["PipeA", "15"], False), (["PipeB", "20"], False), (["PipeC", "25"], False)])
    rec_len = 1 + 16
    header_and_fields = 32 + 32 * len(fields) + 1
    # keep header+fields + 1 full record + a partial second record
    cutoff = header_and_fields + rec_len + (rec_len // 2)
    path = tmp_path / "trunc.dbf"
    path.write_bytes(full[:cutoff])
    rows = dbf_to_list(str(path))
    assert rows == [{"NAME": "PipeA", "FLOW": 15}]
