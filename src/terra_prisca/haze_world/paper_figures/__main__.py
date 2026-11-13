"""Build every display item: uv run python -m terra_prisca.haze_world.paper_figures"""

import argparse
import importlib

ITEMS = ("fig1", "fig2", "fig3", "fig4", "table_s1")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("items", nargs="*", default=ITEMS, choices=ITEMS)
    for name in parser.parse_args().items:
        module = importlib.import_module(f"{__package__}.{name}")
        print(name, module.main())


if __name__ == "__main__":
    main()
