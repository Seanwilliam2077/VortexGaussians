"""Verify the portable occupied-cell and ignition ledger with the standard library."""
import gzip
import json
from pathlib import Path

here = Path(__file__).resolve().parent
check = json.loads((here/"CHECK.json").read_bytes())
data = json.loads(gzip.decompress((here/"occupied-and-ignited.json.gz").read_bytes()))
ids = data["flat_ids"]
assert ids == sorted(set(ids)) and all(0 <= i < 128**3 for i in ids)
remaining = {(i//(128*128), (i//128)%128, i%128) for i in ids}
sizes = []
while remaining:
    work = [remaining.pop()]
    count = 0
    while work:
        x,y,z = work.pop()
        count += 1
        for n in ((x+1,y,z),(x-1,y,z),(x,y+1,z),(x,y-1,z),(x,y,z+1),(x,y,z-1)):
            if n in remaining:
                remaining.remove(n)
                work.append(n)
    sizes.append(count)
assert sorted(sizes,reverse=True) == check["component_sizes"]
for row in check["checkpoints"]:
    hot = data[str(row["step"])]
    assert len(hot) == row["ignited"] and len(ids) == row["occupied"]
    assert hot == sorted(set(hot)) and all(0 <= i < len(ids) for i in hot)
print(len(ids),"occupied cells,",len(sizes),"components,",len(check["checkpoints"]),"checked native ledgers")
