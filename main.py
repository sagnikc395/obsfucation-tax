"""Thin wrapper around obfuscation_tax CLI. Also smoke-test entry point."""

from obfuscation_tax.cli import main as cli_main


def main():
    print("Hello from obsfucation-tax!")
    print("Use `obfuscation-tax --help` or `python -m obfuscation_tax.cli --help` for experiment stages.")


if __name__ == "__main__":
    # if called with args, dispatch to CLI; otherwise smoke print
    import sys

    if len(sys.argv) > 1:
        cli_main()
    else:
        main()
