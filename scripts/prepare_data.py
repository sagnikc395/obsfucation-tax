#!/usr/bin/env python3
from obfuscation_tax.cli import cmd_prepare_data
import argparse

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--dataset", default=None)
    args = p.parse_args()
    cmd_prepare_data(args)
