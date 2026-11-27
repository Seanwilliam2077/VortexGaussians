"""Fetch one bounded range containing the three adjacent upstream label/mapping members."""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import struct
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zlib

DRIVE = "https://drive.usercontent.google.com/download"
PUBLIC_ID = "1NFXzr0YU3q1_ezjWVEgTmd-R8JX4J0lL"
SIZE, START, END = 1049696735, 73, 575496
MEMBERS = {
    "mask_pts_in_grids.pth": (73, 79141, 1269193, 0xb62bae2e),
    "material_grid.npy": (79324, 162269, 134217856, 0x9e8f2274),
    "indices_pts_in_grids.pth": (243345, 332039, 1921298, 0xdd272a88),
}


class Form(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active, self.fields = False, {}

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self.active = a.get("id") == "download-form" and a.get("action") == DRIVE
        if self.active and tag == "input" and a.get("type") == "hidden":
            self.fields[a["name"]] = a["value"]

    def handle_endtag(self, tag):
        if tag == "form":
            self.active = False


def obtain():
    params = dict(id=PUBLIC_ID, export="download")
    headers = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    endpoint = DRIVE + "?" + urlencode(params)
    with urlopen(Request(endpoint, headers=headers), timeout=30) as resp:
        first_type = resp.headers.get("Content-Type", "")
        if "text/html" in first_type:
            form = Form()
            form.feed(resp.read(65536).decode())
            if form.fields.get("id") != PUBLIC_ID or form.fields.get("confirm") != "t":
                raise ValueError("Unrecognized upstream file-confirmation form")
            endpoint = DRIVE + "?" + urlencode(form.fields)
    wanted = f"bytes {START}-{END}/{SIZE}"
    headers["Range"] = f"bytes={START}-{END}"
    with urlopen(Request(endpoint + "&range_start=" + str(START), headers=headers), timeout=45) as resp:
        if resp.status != 206 or resp.headers.get("Content-Range") != wanted:
            raise ValueError(f"Unexpected archive response {resp.status}, {resp.headers.get('Content-Range')}")
        b = resp.read(END - START + 2)
    if len(b) != END - START + 1:
        raise ValueError("Range length mismatch")
    return b, dict(public_file_id=PUBLIC_ID, archive_bytes=SIZE, returned_content_range=wanted,
                   range_bytes=len(b), range_sha256=hashlib.sha256(b).hexdigest(), status=206)


def extract(data, folder):
    records = {}
    for name, (offset, packed, raw_len, crc) in MEMBERS.items():
        pos = offset - START
        fields = struct.unpack_from("<4s5H3I2H", data, pos)
        assert fields[0] == b"PK\x03\x04" and fields[3] == 8
        n, extra = fields[-2:]
        assert data[pos + 30 : pos + 30 + n].decode() == "Playground/" + name
        begin = pos + 30 + n + extra
        d = zlib.decompressobj(-15)
        raw = d.decompress(data[begin : begin + packed], raw_len + 1)
        assert d.eof and not d.unused_data and len(raw) == raw_len and zlib.crc32(raw) == crc
        (folder / name).write_bytes(raw)
        records[name] = dict(offset=offset, deflate_bytes=packed, bytes=raw_len, crc32=f"{crc:08x}",
                             sha256=hashlib.sha256(raw).hexdigest())
    return records


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("cache", type=Path)
    p.add_argument("--receipt", type=Path, required=True)
    args = p.parse_args()
    args.cache.mkdir(parents=True, exist_ok=True)
    data, receipt = obtain()
    receipt["members"] = extract(data, args.cache)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(receipt["range_bytes"], list(receipt["members"]))
