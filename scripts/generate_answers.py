#!/usr/bin/env python3
import argparse
from obfuscation_tax.cli import cmd_generate

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--condition", required=True)
    p.add_argument("--dataset", default=None)
    p.add_argument("--split", default=None)
    p.add_argument("--limit", type=int, default=None)
    p.add_argument("--dummy", action="store_true")
    args = p.parse_args()
    cmd_generate(args)
