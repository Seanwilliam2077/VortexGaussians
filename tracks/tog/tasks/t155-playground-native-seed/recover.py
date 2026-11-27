"""Recover bounded official ranges and verify the original real-scene member."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
import hashlib
import json
from pathlib import Path
import struct
from threading import Lock
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import zlib

import acquire as a


def recover(folder, first, receipt):
    started = time.perf_counter()
    prior = json.loads(first.read_bytes())
    old = {r["start"]: r for r in prior["ranges"]}
    common = {"User-Agent": "Mozilla/5.0", "Accept-Encoding": "identity"}
    endpoint = a.base.DRIVE + "?" + urlencode(dict(id=a.base.PUBLIC_ID, export="download"))
    log = dict(status="confirmation", public_file_id=a.base.PUBLIC_ID, archive_bytes=a.base.SIZE,
               member=a.NAME, limit_s=420, ranges=[], retries=[])
    def save(status):
        log.update(status=status, elapsed_s=time.perf_counter() - started)
        receipt.write_text(json.dumps(log, indent=2) + "\n", encoding="utf8")
    def remaining():
        left = 417 - (time.perf_counter() - started)
        if left < 1:
            raise TimeoutError("Recovery deadline")
        return min(55, left)
    save("confirmation")
    with urlopen(Request(endpoint, headers=common), timeout=remaining()) as response:
        if "text/html" in response.headers.get("Content-Type", ""):
            form = a.base.Form()
            form.feed(response.read(65536).decode())
            assert form.fields.get("id") == a.base.PUBLIC_ID and form.fields.get("confirm") == "t"
            endpoint = a.base.DRIVE + "?" + urlencode(form.fields)
    folder.mkdir(parents=True, exist_ok=True)
    blocks = folder / "recovery-ranges"
    blocks.mkdir(exist_ok=False)
    lock = Lock()
    def read_range(item):
        start, size = item
        end = start + size - 1
        headers = dict(common, Range=f"bytes={start}-{end}")
        req = Request(endpoint + "&start155=" + str(start), headers=headers)
        while True:
            try:
                with urlopen(req, timeout=remaining()) as res:
                    assert res.status == 206 and res.headers.get("Content-Range") == f"bytes {start}-{end}/{a.base.SIZE}"
                    data = res.read(size + 1)
                if len(data) != size:
                    raise OSError("Short range")
                break
            except (OSError, URLError) as exc:
                if isinstance(exc, HTTPError) and exc.code not in (408,429,500,502,503,504):
                    raise
                with lock:
                    if len(log["retries"]) >= 2:
                        raise
                    log["retries"].append(dict(start=start, error=type(exc).__name__))
        sha = hashlib.sha256(data).hexdigest()
        if start in old:
            assert sha == old[start]["sha256"] and size == old[start]["bytes"]
        (blocks / str(start)).write_bytes(data)
        return dict(start=start, bytes=size, sha256=sha)

    head = prior["local_header_bytes"]
    end = a.OFFSET + head + a.PACKED
    plan = [(a.OFFSET, 512)]
    for begin in range(a.OFFSET + 512, end, a.CHUNK):
        plan.append((begin, min(a.CHUNK, end-begin)))
    assert len(plan) <= 27 and set(old).issubset(dict(plan))
    with ThreadPoolExecutor(max_workers=6) as pool:
        submitted = [pool.submit(read_range, item) for item in sorted(plan, key=lambda p: p[0] in old)]
        for future in as_completed(submitted):
            log["ranges"].append(future.result())
            with lock:
                save("receiving")
    partial = folder / "scene_point_cloud.partial"
    out_path = folder / "verified-assembly.partial"
    full_hash = hashlib.sha256()
    packed_hash = hashlib.sha256()
    crc = decoded_bytes = prior_checked = 0
    decoder = zlib.decompressobj(-15)
    with partial.open("rb") as earlier, out_path.open("xb") as out:
        for start, size in plan:
            data = (blocks / str(start)).read_bytes()
            if start == a.OFFSET:
                fields = struct.unpack_from("<4s5H3I2H", data)
                n, extra = fields[-2:]
                assert fields[0] == b"PK\x03\x04" and fields[3] == 8
                assert data[30:30+n].decode() == a.NAME and 30+n+extra == head
                data = data[head:]
            packed_hash.update(data)
            decoded = decoder.decompress(data, a.DECODED - decoded_bytes + 1)
            assert not decoder.unconsumed_tail and len(decoded) + decoded_bytes <= a.DECODED
            full_hash.update(decoded)
            crc = zlib.crc32(decoded, crc)
            out.write(decoded)
            decoded_bytes += len(decoded)
            overlap = earlier.read(len(decoded))
            assert decoded.startswith(overlap)
            prior_checked += len(overlap)
        assert decoder.eof and not decoder.unused_data
        assert crc == a.CRC and decoded_bytes == a.DECODED and earlier.read(1) == b""
        assert prior_checked == partial.stat().st_size
    out_path.rename(folder / "scene_point_cloud.ply")
    log["ranges"].sort(key=lambda p: p["start"])
    log.update(local_header_bytes=head, compressed_bytes=a.PACKED, decoded_bytes=decoded_bytes,
               crc32=f"{crc:08x}", sha256=full_hash.hexdigest(), deflate_sha256=packed_hash.hexdigest(),
               validated_earlier_range_hashes=len(old), validated_earlier_decoded_bytes=prior_checked)
    save("complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cache", type=Path)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    recover(args.cache, args.first, args.receipt)
