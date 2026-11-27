"""Acquire only the two predeclared members of the original fitted Bonsai archive."""
import binascii
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import struct
import threading
from time import perf_counter, sleep
import urllib.request
import zlib


HERE = Path(__file__).resolve().parent
LOCAL = HERE / "local"
URL = "https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/pretrained/models.zip"
TOTAL = 14660630999
TAIL_SHA = "3d535f59621f16992a0faf99b0f793c92f9f0f4bddf31dcdc64644d3e199e5f5"
TARGETS = {
    "bonsai/cameras.json": ("cameras.json", 37076, 116695, 0xf963b75c),
    "bonsai/point_cloud/iteration_30000/point_cloud.ply": ("scene.ply", 260603022, 308716644, 0x3088ffa4),
}
CHUNK = 4 * 1024**2
RETRY_BUDGET = 64 * 1024**2
transfer = {"normal_bytes": 0, "retry_bytes": 0, "requests": 0, "errors": []}
counter_lock = threading.Lock()


def fetch(pair):
    start, stop = pair
    length = stop - start + 1
    for attempt in range(3):
        bucket = "retry_bytes" if attempt else "normal_bytes"
        with counter_lock:
            if transfer[bucket] + length > (RETRY_BUDGET if attempt else 262000000):
                raise RuntimeError("Registered HTTP budget exhausted")
            transfer[bucket] += length
            transfer["requests"] += 1
        received = 0
        try:
            request = urllib.request.Request(URL + f"?vortex_range={start}-{stop}", headers={
                "Range": f"bytes={start}-{stop}", "Accept-Encoding": "identity"})
            with urllib.request.urlopen(request, timeout=55) as reply:
                if reply.status != 206 or reply.headers.get("Content-Range") != f"bytes {start}-{stop}/{TOTAL}":
                    raise RuntimeError("Server did not confirm the precise range")
                if reply.headers.get("Content-Encoding", "identity") != "identity":
                    raise RuntimeError("Server used an unexpected transfer encoding")
                declared = reply.headers.get("Content-Length")
                if declared is not None and int(declared) != length:
                    raise RuntimeError("Wrong range length")
                parts = []
                while received < length:
                    piece = reply.read(min(262144, length-received))
                    if not piece:
                        raise IOError("Incomplete range")
                    parts.append(piece)
                    received += len(piece)
                return b"".join(parts)
        except (OSError, RuntimeError) as exc:
            with counter_lock:
                transfer["errors"].append(dict(start=start, stop=stop, attempt=attempt+1,
                                              received=received, error=str(exc)))
            if attempt == 2:
                raise
            sleep(1+attempt)
        finally:
            with counter_lock:
                transfer[bucket] -= length - received


def member_directory():
    tail = fetch((TOTAL-131072, TOTAL-1))
    if hashlib.sha256(tail).hexdigest() != TAIL_SHA:
        raise ValueError("Archive directory fingerprint changed")
    offset = tail.find(b"PK\x01\x02")
    records = {}
    while offset >= 0 and tail[offset:offset+4] == b"PK\x01\x02":
        fields = struct.unpack_from("<4s6H3L5H2L", tail, offset)
        name_len, extra_len, comment_len = fields[10:13]
        name = tail[offset+46:offset+46+name_len].decode("utf8")
        offset += 46 + name_len + extra_len + comment_len
        if name in TARGETS:
            if fields[3:5] != (0, 8) or (fields[8], fields[9], fields[7]) != TARGETS[name][1:]:
                raise ValueError("Member sizes, method or CRC differ")
            records[name] = fields[16]
    if set(records) != set(TARGETS):
        raise ValueError("Registered archive members missing")
    return records


def acquire_member(name, start):
    filename, compressed, size, crc = TARGETS[name]
    header = struct.unpack("<4s5H3L2H", fetch((start, start+29)))
    if header[0] != b"PK\x03\x04" or header[2:4] != (0, 8) or header[6:9] != (crc, compressed, size):
        raise ValueError("Local ZIP member header disagrees")
    name_len, extra_len = header[-2:]
    if fetch((start+30, start+29+name_len)).decode() != name:
        raise ValueError("Local ZIP member name differs")
    payload = start + 30 + name_len + extra_len
    ranges = [(i, min(i+CHUNK, payload+compressed)-1) for i in range(payload, payload+compressed, CHUNK)]
    dest = LOCAL / filename
    if dest.exists():
        raise FileExistsError(dest)
    temp = dest.with_suffix(dest.suffix + ".part")
    decoder = zlib.decompressobj(-15)
    checksum = 0
    decoded = 0
    sha = hashlib.sha256()
    clock = perf_counter()
    with ThreadPoolExecutor(max_workers=4) as pool, temp.open("wb") as out:
        # Bounded batches limit the number of downloaded ranges retained on a slow first read.
        for offset in range(0, len(ranges), 4):
            for block in pool.map(fetch, ranges[offset:offset+4]):
                part = decoder.decompress(block, size-decoded+1)
                decoded += len(part)
                if decoded > size or decoder.unconsumed_tail or decoder.unused_data:
                    raise ValueError("Deflate stream exceeded the registered member")
                out.write(part)
                checksum = binascii.crc32(part, checksum)
                sha.update(part)
    if decoder.flush() or not decoder.eof or checksum != crc or decoded != size:
        raise ValueError("Incomplete or corrupt member")
    temp.replace(dest)
    return dict(member=name, local_filename=filename, data_offset=payload, compressed=compressed,
                decoded=size, crc32=f"{crc:08x}", sha256=sha.hexdigest(), elapsed_s=perf_counter()-clock)


def main():
    LOCAL.mkdir(exist_ok=True)
    start = perf_counter()
    published = HERE / "ACQUISITION.json"
    expected = {}
    if published.exists():
        expected = {m["member"]:m for m in json.loads(published.read_bytes())["members"]}
    if len(expected)==len(TARGETS):
        for name, (filename, _, _, _) in TARGETS.items():
            path = LOCAL / filename
            if path.exists():
                with path.open("rb") as stream:
                    if hashlib.file_digest(stream,"sha256").hexdigest()!=expected[name]["sha256"]:
                        raise ValueError(f"Existing file differs: {filename}")
        if all((LOCAL/v[0]).is_file() for v in TARGETS.values()):
            print("Both private files match the published digests")
            return
    result = dict(url=URL, archive_bytes=TOTAL, tail_sha256=TAIL_SHA, members=[])
    try:
        for name, offset in member_directory().items():
            if name in expected and (LOCAL/TARGETS[name][0]).exists():
                result["members"].append(dict(expected[name],status="already_present"))
                continue
            member = acquire_member(name, offset)
            if name in expected and member["sha256"]!=expected[name]["sha256"]:
                raise ValueError("Payload differs from published SHA-256")
            result["members"].append(member)
        result["status"] = "complete"
    except Exception as exc:
        result.update(status="failed", error=str(exc).replace(str(LOCAL), "<private_cache>"))
        raise
    finally:
        result.update(elapsed_s=perf_counter()-start, transfer=transfer)
        # Reproductions preserve the historical network cost and machine timing.
        receipt = LOCAL / "acquisition-run.json" if published.exists() or result["status"]!="complete" else published
        receipt.write_text(json.dumps(result, indent=2)+"\n", encoding="utf8")


if __name__ == "__main__":
    main()
