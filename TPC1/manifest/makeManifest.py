import os
import re
import sys
import json
import argparse
from datetime import datetime
from typing import Dict

__DEBUG = False

__dirname = os.path.dirname(__file__)
cwd = os.getcwd()
DEFAULT_TEMPLATE = os.path.join(__dirname, "manifest.template")
DEFAULT_CONFIG = os.path.join(cwd, "manifest.json")
DEFAULT_OUTPUT = os.path.join(cwd, "README.md")
TEMPLATE_REGEX = r"{{(.+?)}}"
    
def error(*args): print(*args, file=sys.stderr)
def debug(*args): 
    global __DEBUG
    if (__DEBUG): print("debug:", *args, file=sys.stderr)

def cleanArtifacts(outputFile: str) -> Dict[str, bool]:
    removed = {}
    candidates = [outputFile]

    for p in candidates:
        if os.path.exists(p):
            try:
                os.remove(p)
                removed[p] = True
            except Exception as e:
                error(f"Failed to remove {p}: {e}")
                removed[p] = False
    return removed


def generate(output: str, template: str, config: str | None) -> int:
    if not os.path.exists(template):
        error(f"Template file not found: {template}")
        return 1

    tpl = ""
    with open(template, "r", encoding="utf-8") as fh:
        tpl = fh.read()

    context = {}
    if config:
        if os.path.exists(config):
            try:
                with open(config, "r", encoding="utf-8") as cf:
                    context = json.load(cf)
            except Exception as e:
                error(f"Error: failed to parse config as JSON: {e}")
                return 1
        else:
            error(f"Error: config file not found: {config}")
            return 1
        
    if (not "date" in context): context["date"] = datetime.today().strftime('%Y-%m-%d')
        
    debug("Context:", context)

    # Format Results
    if (not "results" in context):
        error("Error: missing required property 'results'.")
        return 1
    
    results = ""
    _results = context.get("results")
    _resultChapter = 1
    try:
        debug("Raw results:", _results)
        assert isinstance(_results, dict), "Results must be a nested object."

        resultKeys = _results.keys()
        for key in resultKeys:
            result = _results[key]
            assert isinstance(result, list), f"Result '{key}' must be an array."

            results += f"## {_resultChapter}. {key}\n"

            entryChapter = 1
            for entry in result:
                assert isinstance(entry, dict), f"Invalid result '{key}': Contains a non-object entry."
                assert "file" in entry, f"Invalid result '{key}': Contains an entry without a 'file' property."
                assert "desc" in entry, f"Invalid result '{key}': Contains an entry without a 'desc' property."
                results += f"  {entryChapter}. [{entry['file']}]({entry['file']}): {entry['desc']}\n"
                entryChapter += 1
            
            results += "\n"
            _resultChapter += 1

        context["results"] = results
    except Exception as e:
        error(f"Unable to format results: {e}")
        return 1

    try:
        def canReplace(key: str) -> bool: return key in context
        def replacePredicate(match: re.Match) -> str:
            key = (match.group(1) or "").strip()
            debug(match, key)
            if canReplace(key):
                val = context.get(key, "")
                return str(val) if val is not None else ""
            return match.group(0)
        formatted = re.sub(TEMPLATE_REGEX, replacePredicate, tpl)
    except Exception as e:
        error(f"Template substitution error: {e}")
        return 1

    outdir = os.path.dirname(output)
    if outdir and not os.path.exists(outdir):
        try:
            os.makedirs(outdir, exist_ok=True)
        except Exception as e:
            error(f"Failed to create output directory {outdir}: {e}")
            return 1

    with open(output, "w", encoding="utf-8") as out:
        out.write(formatted)

    print(f"Generated {output}")
    return 0


def makeCLI() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate a manifest from a template (or clean generated artifacts)."
    )
    p.add_argument("-o", "--output", type=str, default=DEFAULT_OUTPUT, help="Output file path")
    p.add_argument("-t", "--template", type=str, default=DEFAULT_TEMPLATE, help="Template file path")
    p.add_argument(
        "-c", "--config", 
        type=str, default=DEFAULT_CONFIG, 
        help="Config file path (JSON) used for templating"
    )
    p.add_argument(
        "-d", "--debug",
        type=bool, action=argparse.BooleanOptionalAction, default=False,
        help="Enables debug mode"
    )
    p.add_argument(
        "command", 
        nargs="?", choices=["clean"], 
        help="Optional command: 'clean' to remove generated artifacts"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    global __DEBUG
    argv = argv if argv is not None else sys.argv[1:]
    parser = makeCLI()
    args = parser.parse_args(argv)

    __DEBUG = args.debug
    if (__DEBUG): debug("ARGS:", args)

    if args.command == "clean":
        removed = cleanArtifacts(args.output)
        if removed:
            print("Removed files:")
            for k, v in removed.items():
                status = "OK" if v else "FAILED"
                print(f" - {k}: {status}")
            return 0
        else:
            print("No generated files found to remove.")
            return 0

    return generate(args.output, args.template, args.config)


if __name__ == "__main__":
    raise SystemExit(main())


