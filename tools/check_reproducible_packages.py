#!/usr/bin/env python3
from pathlib import Path
import argparse
import hashlib


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(directory):
    root=Path(directory); files=sorted([*root.glob("*.zip"),root/"release-set.json"],key=lambda path:path.name)
    missing=[path for path in files if not path.exists()]
    if missing: raise ValueError(f"missing release files: {[path.name for path in missing]}")
    return {path.name:sha256(path) for path in files}


def main():
    parser=argparse.ArgumentParser(); parser.add_argument("first"); parser.add_argument("second"); args=parser.parse_args(); first=inventory(args.first); second=inventory(args.second)
    if first != second:
        missing=sorted(set(first)-set(second)); extra=sorted(set(second)-set(first)); changed=sorted(name for name in set(first)&set(second) if first[name]!=second[name]); raise SystemExit(f"package reproducibility FAIL missing={missing} extra={extra} changed={changed}")
    print("package reproducibility PASS")


if __name__=="__main__": main()
