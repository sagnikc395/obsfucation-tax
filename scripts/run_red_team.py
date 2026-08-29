#!/usr/bin/env python3
import argparse
from obfuscation_tax.cli import cmd_run_red_team

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/default.yaml")
    p.add_argument("--level", required=True)
    p.add_argument("--dataset", default=None)
    args = p.parse_args()
    cmd_run_red_team(args)
