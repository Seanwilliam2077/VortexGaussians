"""Fetch only the public Playground burnable foreground, validating the ZIP member and ranges."""
import argparse
import hashlib
from html.parser import HTMLParser
from pathlib import Path
import struct
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zlib

HERE=Path(__file__).resolve().parent
FILE_ID="1NFXzr0YU3q1_ezjWVEgTmd-R8JX4J0lL"
DRIVE="https://drive.usercontent.google.com/download"
ARCHIVE_BYTES=1049696735
OFFSET=689019218
MEMBER="Playground/fg/fg_opac_0_burnable.ply"
SIZE=19847234
PACKED=17965855
CRC=168304271


class DownloadForm(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active=False
        self.fields={}

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=="form":
            self.active=(attrs.get("id")=="download-form" and attrs.get("action")==DRIVE)
        if self.active and tag=="input" and attrs.get("type")=="hidden":
            self.fields[attrs["name"]]=attrs["value"]

    def handle_endtag(self,tag):
        if tag=="form": self.active=False


def fetch():
    url=DRIVE+"?"+urlencode(dict(id=FILE_ID,export="download"))
    headers={"User-Agent":"Mozilla/5.0","Accept-Encoding":"identity"}
    with urlopen(Request(url,headers=headers),timeout=30) as response:
        if "text/html" in response.headers.get("Content-Type",""):
            form=DownloadForm()
            form.feed(response.read(65536).decode())
            if form.fields.get("id")!=FILE_ID or form.fields.get("confirm")!="t":
                raise ValueError("Unexpected public download form")
            url=DRIVE+"?"+urlencode(form.fields)

    def part(start,length):
        end=start+length-1
        req=Request(url+"&range_start="+str(start),headers={**headers,"Range":f"bytes={start}-{end}"})
        with urlopen(req,timeout=60) as response:
            if response.status!=206 or response.headers.get("Content-Range")!=f"bytes {start}-{end}/{ARCHIVE_BYTES}":
                raise ValueError("Server did not return the requested member range")
            data=response.read(length+1)
            if len(data)!=length: raise ValueError("Truncated range")
            return data

    meta=struct.unpack("<4s5H3I2H",part(OFFSET,30))
    if meta[0]!=b"PK\x03\x04" or meta[3]!=8 or not 1<=meta[-2]<=512 or meta[-1]>2048:
        raise ValueError("Unexpected ZIP header")
    name_extra=part(OFFSET+30,meta[-2]+meta[-1])
    if name_extra[:meta[-2]].decode()!=MEMBER: raise ValueError("Unexpected ZIP member")
    compressed=part(OFFSET+30+len(name_extra),PACKED)
    dec=zlib.decompressobj(-15)
    raw=dec.decompress(compressed,SIZE+1)
    if not dec.eof or dec.unused_data or len(raw)!=SIZE or zlib.crc32(raw)!=CRC:
        raise ValueError("Invalid ZIP member or CRC")
    return raw


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,help="An already downloaded copy of the original foreground")
    args=ap.parse_args()
    out=HERE/"local"/"foreground.ply"
    out.parent.mkdir(exist_ok=True)
    data=args.source.read_bytes() if args.source else out.read_bytes() if out.exists() else fetch()
    if len(data)!=SIZE or zlib.crc32(data)!=CRC: raise ValueError("Incorrect original foreground")
    if not out.exists(): out.write_bytes(data)
    print(len(data),hashlib.sha256(data).hexdigest())
