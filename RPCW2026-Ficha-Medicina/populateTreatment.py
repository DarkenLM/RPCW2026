import os
import re
import sys
import csv
import argparse
import rdflib as r

__DEBUG = False
__dirname = os.path.dirname(__file__)
PREFIX = r.Namespace("http://www.example.org/disease-ontology#")

def trace(*args):
    global __DEBUG
    if (__DEBUG): print(*args, file=sys.stderr)

def makeCLI() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Populate an ontology using the Disease_Syntoms datasets."
    )
    p.add_argument(
        "-d", "--debug",
        type=bool, action=argparse.BooleanOptionalAction, default=False,
        help="Enables debug mode"
    )
    p.add_argument(
        "-o", "--output",
        type=str,
        default=f"{__dirname}/med_tratamentos.ttl",
        help="Outputs the ontology to a new file."
    )
    p.add_argument(
        "-s", "--dryrun",
        type=bool, action=argparse.BooleanOptionalAction, default=False,
        help="Disables output writing."
    )
    p.add_argument(
        "-f", "--format", 
        type=str,
        choices=["ttl", "xml"], 
        default="ttl",
        help="The format of the topology to output."
    )
    p.add_argument(
        "--ontology", 
        type=str, 
        default=f"{__dirname}/med_doencas.ttl", 
        help="The original ontology to load and process."
    )
    p.add_argument("--dataset", 
        type=str, 
        default=f"{__dirname}/Disease_Treatment.csv", 
        help="The datasets containing the data to populate."
    )
    return p

def main():
    global __DEBUG
    parser = makeCLI()
    args = parser.parse_args(sys.argv[1:])

    if (args.debug == True): __DEBUG = True
    trace("ARGS:", args)

    g = r.Graph()
    try:
        trace("Loading ontology...")
        with open(os.path.abspath(args.ontology)) as ontoFIn: g.parse(ontoFIn)
        trace("Ontology loaded.")
        
        trace("Loading dataset...")
        with open(os.path.abspath(args.dataset)) as dataFIn: 
            _data = csv.reader(dataFIn, delimiter=",")
            data = [list(filter(lambda c: len(c) > 0, [c.strip() for c in row])) for row in _data]
        trace("Dataset loaded.")
        
        diseases = {}
        for row in data[1:]:
            if (row[0] not in diseases): diseases[row[0]] = set()
            for c in row[1:]: diseases[row[0]].add(c)

        for (k,v) in diseases.items(): diseases[k] = list(v)
        for (k,v) in diseases.items(): 
            trueKey = k.replace(" ", "_").replace("(", "_").replace(")", "")
            nv = [
                re.sub(r"(\w) (\w)", r"\1_\2", 
                    re.sub(r"(\w) (\w)", r"\1_\2", 
                        re.sub(r"(\w) ?_ ?(\w)", r'\1_\2', c)
                    ).replace("(", "_").replace(")", "") 
                ).title().replace("_", "")
                for c in v
            ]
            print(f"Disease: {trueKey}")
            for c in nv: print(f"- {c}")
            q = g.query(f"""
            PREFIX : <http://www.example.org/disease-ontology#>
            SELECT DISTINCT ?s WHERE {{ 
                BIND(:{trueKey} AS ?d) 
                # BIND(:Flu AS ?d) 
                ?d a :Disease .
                ?d :hasTreatment ?_s .
                ?_s a :Treatment .
                BIND(STRAFTER(STR(?_s), "#") AS ?s)
            }}
            """)
            existing = set([s[0].value for s in list(q)])
            new = set(nv)
            diff = new - existing
            for s in diff: 
                g.add((PREFIX[s], r.RDF.type, PREFIX["Treatment"]))
                # g.add((PREFIX[trueKey], PREFIX["hasTreatment"], PREFIX[s]))

        if (not args.dryrun):
            ontoOut = g.serialize(format=args.format)
            with open(os.path.abspath(args.output), "w") as ontoFOut: ontoFOut.write(ontoOut)
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())