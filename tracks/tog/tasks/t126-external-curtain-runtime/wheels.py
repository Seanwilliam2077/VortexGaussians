"""Verify sizes/hashes against official PyPI, then stage a binary-only dependency set in a named temporary target."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
from urllib.parse import quote,urlparse
from urllib.request import urlopen

HERE=Path(__file__).resolve().parent
CAP=65*1024*1024


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--plan",type=Path,required=True)
    p.add_argument("--wheel-dir",type=Path,required=True);p.add_argument("--target",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True);a=p.parse_args()
    info=json.loads(a.plan.read_text(encoding="utf8"));rows=[]
    for item in info["install"]:
        package,version=item["metadata"]["name"],item["metadata"]["version"]
        release_url="https://pypi.org/pypi/"+quote(package)+"/"+quote(version)+"/json"
        with urlopen(release_url,timeout=30) as response:release=json.load(response)
        uri=item["download_info"]["url"];assert urlparse(uri).hostname=="files.pythonhosted.org"
        file=next(x for x in release["urls"] if x["url"]==uri)
        assert file["filename"].endswith(".whl") and not file["yanked"]
        digest=file["digests"]["sha256"];assert digest==item["download_info"]["archive_info"]["hashes"]["sha256"]
        rows.append(dict(package=package,version=version,filename=file["filename"],sha256=digest,size=file["size"],url=uri))
    total=sum(r["size"] for r in rows);assert total<=CAP and any(r["package"].lower()=="mujoco" and r["version"]=="3.3.7" for r in rows)
    a.receipt.parent.mkdir(parents=True,exist_ok=True)
    a.receipt.write_text(json.dumps(dict(added_wheel_bytes=total,limit_bytes=CAP,wheels=rows),indent=2)+"\n",encoding="utf8")
    a.wheel_dir.mkdir(parents=True,exist_ok=False)
    files=[]
    for r in rows:
        with urlopen(r["url"],timeout=60) as reader:data=reader.read(r["size"]+1)
        assert len(data)==r["size"] and hashlib.sha256(data).hexdigest()==r["sha256"]
        dest=a.wheel_dir/r["filename"];dest.write_bytes(data);files.append(str(dest))
    subprocess.run([sys.executable,"-m","pip","install","--only-binary=:all:","--no-index","--no-deps",
                    "--disable-pip-version-check","--target",str(a.target),*files],check=True)
    print("Verified downloadable wheel bytes:",total)


if __name__=="__main__":main()
