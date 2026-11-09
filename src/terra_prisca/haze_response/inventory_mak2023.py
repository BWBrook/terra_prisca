"""Inventory Mak's ZIP with small HTTP range reads; never download its payload.

uv run python -m terra_prisca.haze_response.inventory_mak2023 local/haze/inventory
"""

import json
from pathlib import Path
import struct
import sys
import re
from urllib.request import Request, urlopen


API = "https://zenodo.org/api/records/8178651"


def get_json(url):
    with urlopen(url, timeout=30) as response:
        return json.load(response)


def byte_range(url, start, end):
    if end - start + 1 > 2_000_000:
        raise ValueError("This inventory permits only small metadata ranges")
    request = Request(url, headers={"Range": f"bytes={start}-{end}"})
    with urlopen(request, timeout=30) as response:
        if response.status != 206:
            raise RuntimeError("Server ignored byte range; refusing full download")
        expected = end - start + 1
        result = response.read(expected + 1)
    if len(result) != expected:
        raise RuntimeError("Unexpected range size")
    return result


def summarize(rows):
    scientific = [r for r in rows if not r["name"].startswith("__MACOSX/")
                  and re.search(r"/umglaa\.p[a-e]", r["name"])]
    cases = []
    for case in sorted({Path(r["name"]).parts[1] for r in scientific}):
        members = [r for r in scientific if Path(r["name"]).parts[1] == case]
        streams = {}
        for stream in ("pa", "pb", "pc", "pd", "pe"):
            subset = [r for r in members if f"/umglaa.{stream}" in r["name"] and r["size"] > 0]
            streams[stream] = dict(nonempty_files=len(subset),
                                   compressed_bytes=sum(r["compressed_size"] for r in subset),
                                   uncompressed_bytes=sum(r["size"] for r in subset))
        cases.append(dict(case=case, empty_files=sum(r["size"] == 0 for r in members), streams=streams))
    return dict(archive_bytes=38309598059, published_md5="849dfee2f006c76dfa17b489fa802c1f",
                entries=len(rows), cases=cases)


def main(outdir: Path):
    metadata = get_json(API)
    if len(metadata["files"]) != 1:
        raise ValueError("Expected the single published Mak ZIP")
    file = metadata["files"][0]
    url, size = file["links"]["self"], file["size"]
    if size != 38309598059 or file["checksum"] != "md5:849dfee2f006c76dfa17b489fa802c1f":
        raise ValueError("Archive metadata changed; review before reading")
    tail_start = size - 65536
    tail = byte_range(url, tail_start, size - 1)
    locator = tail.rfind(b"PK\x06\x07")
    if locator < 0:
        raise ValueError("Expected ZIP64 end-of-directory locator")
    _, _, zip64_offset, _ = struct.unpack_from("<4sLQL", tail, locator)
    zip64 = struct.unpack_from("<4sQ2H2L4Q", tail, zip64_offset - tail_start)
    count, directory_size, directory_offset = zip64[-3:]
    data = byte_range(url, directory_offset, directory_offset + directory_size - 1)
    rows, offset = [], 0
    while data[offset:offset + 4] == b"PK\x01\x02":
        header = struct.unpack_from("<4s6H3L5H2L", data, offset)
        method, crc, compressed, length = header[4], header[7], header[8], header[9]
        name_len, extra_len, comment_len = header[10:13]
        file_offset = header[-1]
        name = data[offset + 46:offset + 46 + name_len].decode("utf-8")
        extra = data[offset + 46 + name_len:offset + 46 + name_len + extra_len]
        extra_offset = 0
        while extra_offset + 4 <= len(extra):
            kind, extra_size = struct.unpack_from("<HH", extra, extra_offset)
            value = extra[extra_offset + 4:extra_offset + 4 + extra_size]
            extra_offset += 4 + extra_size
            if kind == 1:
                values = list(struct.unpack("<" + "Q" * (len(value) // 8), value))
                if length == 0xffffffff:
                    length = values.pop(0)
                if compressed == 0xffffffff:
                    compressed = values.pop(0)
                if file_offset == 0xffffffff:
                    file_offset = values.pop(0)
        rows.append(dict(name=name, size=length, compressed_size=compressed,
                         method=method, offset=file_offset, crc32=f"{crc:08x}"))
        offset += 46 + name_len + extra_len + comment_len
    if len(rows) != count:
        raise ValueError(f"Expected {count} entries, found {len(rows)}")
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "mak_api.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (outdir / "mak_zip_inventory.json").write_text(json.dumps(rows, indent=2) + "\n")
    (outdir / "mak_summary.json").write_text(json.dumps(summarize(rows), indent=2) + "\n")
    print(f"Read {65536 + directory_size} ZIP metadata bytes for {len(rows)} entries")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
