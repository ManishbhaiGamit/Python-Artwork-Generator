#!/usr/bin/env python3
"""Verify deterministic output and PNG integrity."""
import hashlib, os, struct, subprocess, sys, zlib
ROOT=os.path.dirname(os.path.abspath(__file__))
OUTPUT="/output/entry.png"
LIMIT=1024*1024

def run():
    subprocess.run([sys.executable,os.path.join(ROOT,"main.py")],check=True)
    with open(OUTPUT,"rb") as f: return f.read()

def inspect(data):
    assert data.startswith(b"\x89PNG\r\n\x1a\n"),"Bad PNG signature"
    assert len(data)<=LIMIT,f"PNG exceeds 1 MiB: {len(data)}"
    assert struct.unpack(">II",data[16:24])==(1024,1024),"Wrong dimensions"
    assert data[24]==8 and data[25]==2,"Expected 8-bit RGB"
    off=8; compressed=bytearray(); ended=False
    while off<len(data):
        n=struct.unpack(">I",data[off:off+4])[0]
        kind=data[off+4:off+8]; payload=data[off+8:off+8+n]
        crc=struct.unpack(">I",data[off+8+n:off+12+n])[0]
        assert zlib.crc32(kind+payload)&0xffffffff==crc,f"CRC error: {kind!r}"
        if kind==b"IDAT": compressed.extend(payload)
        if kind==b"IEND": ended=True; break
        off+=12+n
    assert ended,"Missing IEND"
    assert len(zlib.decompress(compressed))==1024*(1+1024*3),"Bad pixel stream"

def main():
    os.makedirs("/output",exist_ok=True)
    first=run(); second=run()
    assert first==second,"Nondeterministic image"
    inspect(first)
    print(f"PASS: {len(first):,} bytes; 1024x1024 RGB; deterministic")
    print("SHA-256:",hashlib.sha256(first).hexdigest())
if __name__=="__main__": main()
