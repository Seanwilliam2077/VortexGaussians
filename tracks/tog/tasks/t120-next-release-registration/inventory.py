"""Refresh the small public FieryGS inventory; no dataset or linked media is requested."""
import hashlib
import json
import re
import subprocess
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
REPO = "https://github.com/PKU-VCL-Geometry/FieryGS"
PROJECT = "https://pku-vcl-geometry.github.io/FieryGS/"
PIN = "f70fbe26d22431c7acd93a745861dd47ba4307d7"


def read(url, limit=1_000_000):
    req = Request(url, headers={"User-Agent": "VortexGaussians-FieryGS-metadata-check"})
    with urlopen(req, timeout=20) as response:
        raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError(f"Metadata budget exceeded: {url}")
    return raw


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href")
        if tag == "a" and href and href not in self.hrefs:
            self.hrefs.append(href)


def main():
    refs = subprocess.check_output(
        ["git", "ls-remote", "--symref", REPO + ".git", "HEAD", "refs/tags/*"],
        text=True, timeout=30).splitlines()
    head = next(row.split()[0] for row in refs if row.endswith("\tHEAD") and not row.startswith("ref:"))
    if head != PIN:
        raise ValueError("Upstream HEAD changed. Review the new release before revising the registration.")
    raw_url = f"https://raw.githubusercontent.com/PKU-VCL-Geometry/FieryGS/{head}/"
    raw_readme = read(raw_url + "README.md")
    md = raw_readme.decode()
    data = re.search(r"(?ms)^##\s+Data[ \t]*\n(.*?)(?=^##\s|\Z)", md).group(1)
    rows = re.findall(r"(?m)^\|\s*([^|]+?)\s*\|\s*\[[^\]]+\]\((https?://[^)]+)\)\s*\|", data)
    if len(rows) != 2 or {r[0] for r in rows} != {"Firewoods_sand_dark", "Playground"}:
        raise ValueError("Named data inventory changed; revisit the frozen selection.")
    page = Links()
    page.feed(read(PROJECT).decode())
    release_html = unescape(read(REPO + "/releases").decode()).replace("’", "'")
    if not re.search(r"aren.t any releases here", release_html, re.I):
        raise ValueError("GitHub Releases page no longer explicitly reports an empty list.")
    license_bytes = read(raw_url + "LICENSE")
    if "Apache License" not in license_bytes[:120].decode() or "Version 2.0" not in license_bytes[:120].decode():
        raise ValueError("Check repo license.")
    try:
        read(raw_url + "LICENSE.md")
    except HTTPError as err:
        if err.code != 404:
            raise
    else:
        raise ValueError("README license target now exists; inspect it.")
    record = {
        "repo": REPO, "head": head, "tags": [r.split()[1] for r in refs if "\trefs/tags/" in r],
        "release_page": REPO + "/releases", "release_entries": 0,
        "readme": REPO + f"/blob/{head}/README.md#data",
        "readme_sha256": hashlib.sha256(raw_readme).hexdigest(),
        "data_rows": [dict(scene=name, url=url) for name, url in rows],
        "official_project_page": PROJECT, "project_anchor_destinations": page.hrefs,
        "repository_license_path": REPO + f"/blob/{head}/LICENSE",
        "repository_license_sha256": hashlib.sha256(license_bytes).hexdigest(),
        "repository_license": "Apache-2.0", "readme_license_md_http_status": 404,
        "data_rights_note": "The public data table supplies download links without separate grant text. No upstream asset bytes are published here.",
        "already_examined": {"Firewoods_sand_dark": "T42, T86, T108, T109", "Playground": "T101, T111, T113, T115"},
        "unused_qualifying_release_scene": None,
    }
    dst = HERE / "UPSTREAM.json"
    result = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    if dst.exists() and json.loads(dst.read_bytes()) != record:
        raise ValueError("Metadata changed; review before replacing the frozen inventory.")
    if not dst.exists():
        dst.write_bytes(result.encode())
    print(head, len(rows), "named archives;", len(record["tags"]), "tags;", 0, "GitHub releases")


if __name__ == "__main__":
    main()
