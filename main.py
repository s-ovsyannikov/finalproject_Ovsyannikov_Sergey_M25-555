#!/usr/bin/env python3

from valutatrade_hub.cli.interface import TradingCLI


def main():
    
    cli = TradingCLI()
    cli.run()


if __name__ == "__main__":
    main()