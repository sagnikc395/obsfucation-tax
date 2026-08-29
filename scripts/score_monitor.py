#!/usr/bin/env python3
import argparse
from obfuscation_tax.cli import cmd_score_monitor

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--dataset", default=None)
    p.add_argument("--dummy", action="store_true")
    args = p.parse_args()
    cmd_score_monitor(args)
