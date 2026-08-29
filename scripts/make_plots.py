#!/usr/bin/env python3
import argparse
from obfuscation_tax.cli import cmd_analyze

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    args = p.parse_args()
    cmd_analyze(args)
