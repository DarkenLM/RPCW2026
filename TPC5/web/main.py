import os
import argparse
from app import createApp
from typing import List

__version__ = "1.0.0"

def main(argv: List[str] | None = None):
    parser = argparse.ArgumentParser(
        prog="web", 
        description="Web server for SPARQL queries", 
        add_help=True
    )
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    parser.add_argument(
        "--debug", "-d", 
        action=argparse.BooleanOptionalAction, default=False,
        help="Enables the debug mode."
    )
    parser.add_argument(
        "--host", 
        default=None, 
        help="Hostname to bind to"
    )
    parser.add_argument(
        "--port", "-p", 
        default=3000, 
        help="Port number to bind to"
    )
    args = parser.parse_args(argv)
    _debug = args.debug

    app = createApp(_debug)
    app.run(debug=_debug, host=args.host, port=args.port)

if __name__ == "__main__":
    raise SystemExit(main())