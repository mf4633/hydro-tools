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
