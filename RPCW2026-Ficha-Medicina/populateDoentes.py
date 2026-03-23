import os
import re
import sys
import json
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
        description="Populate an ontology using the doentes dataset."
    )
    p.add_argument(
        "-d", "--debug",
        type=bool, action=argparse.BooleanOptionalAction, default=False,
        help="Enables debug mode"
    )
    p.add_argument(
        "-o", "--output",
        type=str,
        default=f"{__dirname}/med_doentes.ttl",
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
        default=f"{__dirname}/med_tratamentos.ttl", 
        help="The original ontology to load and process."
    )
    p.add_argument("--dataset", 
        type=str, 
        default=f"{__dirname}/doentes.json", 
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
            data = json.load(dataFIn)
        trace("Dataset loaded.")

        g.add((PREFIX["name"], r.RDF.type, r.OWL.DatatypeProperty))
        
        i = 0
        for v in data: 
            i += 1
            nv = [
                re.sub(r"(\w) (\w)", r"\1_\2", 
                    re.sub(r"(\w) ?_ ?(\w)", r'\1_\2', c)
                ).replace("(", "_").replace(")", "") 
                for c in v["sintomas"]
            ]
            trueKey = "D_" + f"{i}".zfill(5)

            g.add((PREFIX[trueKey], r.RDF.type, PREFIX["Patient"]))
            g.add((PREFIX[trueKey], PREFIX["name"], r.Literal(v["nome"])))
            for c in nv: g.add((PREFIX[trueKey], PREFIX["exhibitsSymptom"], PREFIX[c]))

        if (not args.dryrun):
            ontoOut = g.serialize(format=args.format)
            with open(os.path.abspath(args.output), "w") as ontoFOut: ontoFOut.write(ontoOut)
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())