"""Stream one known PLY member from the official Playground archive."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zlib

HERE = Path(__file__).resolve().parent
prior = HERE.parent / "t152-playground-brush-clearance/fetch.py"
spec = importlib.util.spec_from_file_location("drive_form", prior)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
NAME = "Playground/point_cloud/iteration_30000/scene_point_cloud.ply"
OFFSET, PACKED, DECODED, CRC = 706985269, 282741922, 314566964, 0x294a82e5
CHUNK = 12 * 1024 * 1024


def acquire(cache, receipt):
    start = time.perf_counter()
    common = {"User-Agent":"Mozilla/5.0", "Accept-Encoding":"identity"}
    endpoint = base.DRIVE+"?"+urlencode(dict(id=base.PUBLIC_ID, export="download"))
    log = dict(status="running", archive_bytes=base.SIZE, public_file_id=base.PUBLIC_ID,
               member=NAME, limit_s=420, ranges=[], retries=[])
    def save(status):
        log.update(status=status, elapsed_s=time.perf_counter()-start)
        receipt.write_text(json.dumps(log, indent=2)+"\n", encoding="utf8")
    def remaining():
        left = 417 - (time.perf_counter() - start)
        if left < 1:
            raise TimeoutError("Overall source acquisition deadline")
        return min(45, left)
    def part(begin, size):
        end=begin+size-1
        for _ in range(3):
            try:
                headers = dict(common, Range=f"bytes={begin}-{end}")
                req = Request(endpoint+"&start155="+str(begin), headers=headers)
                with urlopen(req, timeout=remaining()) as response:
                    expected = f"bytes {begin}-{end}/{base.SIZE}"
                    if response.status!=206 or response.headers.get("Content-Range")!=expected:
                        raise ValueError(f"Unexpected source range {response.status}/{response.headers.get('Content-Range')}")
                    block=response.read(size+1)
                if len(block)!=size:
                    raise OSError("Short response for requested range")
            except (URLError, OSError) as err:
                if isinstance(err, HTTPError) and err.code not in (408,429,500,502,503,504):
                    raise
                if len(log["retries"]) >= 2:
                    raise
                log["retries"].append(dict(begin=begin, kind=type(err).__name__))
                continue
            log["ranges"].append(dict(start=begin, bytes=size, sha256=hashlib.sha256(block).hexdigest()))
            return block
        raise RuntimeError("Range retries exhausted")

    cache.mkdir(parents=True, exist_ok=True)
    final=cache/"scene_point_cloud.ply"
    partial=cache/"scene_point_cloud.partial"
    if final.exists() or partial.exists():
        raise FileExistsError("Use a fresh private source directory")
    save("confirmation")
    try:
        with urlopen(Request(endpoint,headers=common),timeout=remaining()) as response:
            if "text/html" in response.headers.get("Content-Type",""):
                form=base.Form(); form.feed(response.read(65536).decode())
                if form.fields.get("id")!=base.PUBLIC_ID or form.fields.get("confirm")!="t":
                    raise ValueError("Unexpected public member confirmation")
                endpoint=base.DRIVE+"?"+urlencode(form.fields)
        initial=part(OFFSET,512)
        fields=struct.unpack_from("<4s5H3I2H",initial)
        n, extra=fields[-2:]
        assert fields[0]==b"PK\x03\x04" and fields[3]==8 and initial[30:30+n].decode()==NAME
        header_size=30+n+extra
        assert 30<=header_size<=len(initial)
        log["local_header_bytes"]=header_size
        compressed=hashlib.sha256(); hashed=hashlib.sha256(); size=crc=count=0
        decoder=zlib.decompressobj(-15)
        with partial.open("xb") as out:
            payload=initial[header_size:]
            while True:
                compressed.update(payload); count+=len(payload)
                decoded=decoder.decompress(payload,DECODED-size+1)
                size+=len(decoded)
                if size>DECODED or decoder.unconsumed_tail: raise ValueError("Excess member payload")
                hashed.update(decoded); crc=zlib.crc32(decoded,crc); out.write(decoded)
                save("receiving")
                if count==PACKED: break
                payload=part(OFFSET+header_size+count,min(CHUNK,PACKED-count))
        if len(log["ranges"])>27 or not decoder.eof or decoder.unused_data or size!=DECODED or crc!=CRC:
            raise ValueError("Original ZIP payload validation failed")
        log.update(decoded_bytes=size, compressed_bytes=count, crc32=f"{crc:08x}",
                   sha256=hashed.hexdigest(),deflate_sha256=compressed.hexdigest())
        partial.rename(final)
        save("complete")
    except Exception as err:
        log["error"]=type(err).__name__
        save("failed")
        raise


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache",type=Path)
    parser.add_argument("--receipt",type=Path,required=True)
    args=parser.parse_args()
    acquire(args.cache,args.receipt)
