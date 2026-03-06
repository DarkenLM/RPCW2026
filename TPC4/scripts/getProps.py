#!/usr/bin/env python3

import os
import sys
import json
import argparse

__DEBUG = False
def trace(*args):
    if (__DEBUG): print(*args, file=sys.stderr)

def makeCLI() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Extrai classes, propriedades e valores possíveis de um ficheiro de população em JSON."
    )
    p.add_argument(
        "-d", "--debug",
        type=bool, action=argparse.BooleanOptionalAction, default=False,
        help="Ativa o modo de debug"
    )

    sub = p.add_subparsers(dest="command", required=True)

    #region ------- Classes Command -------
    sub.add_parser(
        "classes",
        help="Lista todas as classes, sem duplicados, presentes no ficheiro de população."
    )
    #endregion ------- Classes Command -------

    #region ------- Props Command -------
    p_props = sub.add_parser(
        "props",
        help="Lista todas as chaves de propriedades, sem duplicados, (excluindo 'id' e 'tipo')."
    )
    p_props.add_argument(
        "--classe", dest="filter_class", metavar="CLASSE",
        help="Filtra propriedades que aparecem em indivíduos do tipo indicado."
    )
    #endregion ------- Props Command -------

    #region ------- Values Command -------
    p_vals = sub.add_parser(
        "values",
        help="Lista os valores possíveis para uma dada propriedade."
    )
    p_vals.add_argument(
        "prop",
        help="Nome da propriedade cujos valores listar."
    )
    p_vals.add_argument(
        "--classe", dest="filter_class", metavar="CLASSE",
        help="Restringe a pesquisa a indivíduos do tipo indicado."
    )
    #endregion ------- Values Command -------

    #region ------- Summary Command -------
    sub.add_parser(
        "summary",
        help="Mostra um resumo de cada classe com as suas propriedades e valores possíveis."
    )
    #endregion ------- Summary Command -------

    #region ------- Positional args -------
    p.add_argument(
        "população",
        nargs=1,
        help="Ficheiro JSON de população."
    )
    #endregion ------- Positional args -------

    return p


SKIP_KEYS = {"id", "tipo"}


def loadPopulation(path: str) -> list:
    with open(os.path.abspath(path)) as f:
        pop = json.load(f)
    if not isinstance(pop, list):
        raise TypeError("Ficheiro de população tem que ser um array de objetos.")
    return pop


def getClasses(pop: list) -> list[str]:
    return sorted({ind["tipo"] for ind in pop if "tipo" in ind})


def getProps(pop: list, filter_class: str | None = None) -> list[str]:
    props = set()
    for ind in pop:
        if filter_class and ind.get("tipo") != filter_class: continue
        for key in ind:
            if key not in SKIP_KEYS: props.add(key)
    return sorted(props)


def getValues(pop: list, prop: str, filter_class: str | None = None) -> list[str]:
    values = set()
    for ind in pop:
        if filter_class and ind.get("tipo") != filter_class: continue

        val = ind.get(prop)
        if val is None: continue

        if isinstance(val, list):
            values.update(str(v) for v in val)
        else:
            values.add(str(val))
    return sorted(values)


def getSummary(pop: list) -> dict:
    """Returns {class: {prop: [values]}} for every class."""
    classes = getClasses(pop)
    summary = {}
    for cls in classes:
        props = getProps(pop, filter_class=cls)
        summary[cls] = {
            prop: getValues(pop, prop, filter_class=cls)
            for prop in props
        }
    return summary

def main():
    global __DEBUG

    parser = makeCLI()
    args = parser.parse_args(sys.argv[1:])
    __DEBUG = args.debug

    trace("ARGS:", args)

    try:
        pop = loadPopulation(args.população[0])
        trace(f"Loaded {len(pop)} individuals.")

        if args.command == "classes":
            classes = getClasses(pop)
            trace(f"Found {len(classes)} classes.")
            for c in classes:
                print("-", c)

        elif args.command == "props":
            props = getProps(pop, filter_class=getattr(args, "filter_class", None))
            trace(f"Found {len(props)} properties.")
            for p in props:
                print("-", p)

        elif args.command == "values":
            values = getValues(pop, args.prop, filter_class=getattr(args, "filter_class", None))
            trace(f"Found {len(values)} values for '{args.prop}'.")
            for v in values:
                print("-", v)

        elif args.command == "summary":
            summary = getSummary(pop)
            print(json.dumps(summary, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())