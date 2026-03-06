#!/usr/bin/env python3

import os
import sys
import json
import argparse
import rdflib as r

__DEBUG = False
def trace(*args):
    if (__DEBUG): print(*args, file=sys.stderr)

def makeCLI() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Script para população de uma ontologia base com indivíduos provenientes de um ficheiro JSON."
    )
    p.add_argument(
        "-d", "--debug",
        type=bool, action=argparse.BooleanOptionalAction, default=False,
        help="Ativa o modo de debug."
    )
    p.add_argument(
        "-o", "--output",
        type=str,
        help="Ficheiro de output para a ontologia populada."
    )
    p.add_argument(
        "-f", "--format", 
        nargs=1, choices=["ttl", "xml"], default=["ttl"], 
        help="O formato utilizado na ontologia."
    )
    p.add_argument("ontologia", nargs=1, help="O ficheiro contendo a ontologia base para popular.")
    p.add_argument("população", nargs=1, help="O ficheiro contendo a ontologia base para popular.")
    return p

def main():
    global __DEBUG

    parser = makeCLI()
    args = parser.parse_args(sys.argv[1:])
    __DEBUG = args.debug

    trace("ARGS:", args)

    g = r.Graph()
    try:
        with open(os.path.abspath(args.população[0])) as popFile:
            pop = json.load(popFile)

        with open(os.path.abspath(args.ontologia[0])) as fileIn:
            g.parse(fileIn)

        if (not isinstance(pop, list)): raise TypeError("Ficheiro de população tem que ser um array de objetos.")

        namespaces = dict(g.namespaces())
        trace("NAMESPACES:", namespaces)

        def resolveURI(name: str) -> r.URIRef:
            """Resolve a short name to a URIRef by searching all namespaces in the graph."""
            for _, ns in namespaces.items():
                candidate = r.URIRef(str(ns) + name)
                if ((candidate, None, None) in g or (None, None, candidate) in g or (None, candidate, None) in g):
                    return candidate
                
            base_ns = namespaces.get("", next(iter(namespaces.values()), ""))
            return r.URIRef(str(base_ns) + name)

        for i, ind in enumerate(pop):
            if (not isinstance(ind, dict)): raise TypeError(f"Elemento #{i} não é um objeto.")
            if ("id" not in ind): raise KeyError(f"Elemento #{i} não tem propriedade 'id'.")
            if ("tipo" not in ind): raise KeyError(f"Elemento #{i} não tem propriedade 'tipo'.")

            indId   = ind["id"]
            indTipo = ind["tipo"]

            # Check if there exists a class for "tipo"
            baseURI = resolveURI(indTipo)
            if (
                (baseURI, r.RDF.type, r.OWL.Class) not in g \
                    and (baseURI, r.RDF.type, r.RDFS.Class) not in g
            ):
                raise ValueError(f"Classe '{indTipo}' ({baseURI}) não encontrada na ontologia.")

            # Check if individual already exists; create/reuse its URI and try to merge missing triples
            indURI = resolveURI(indId)
            if ((indURI, r.RDF.type, None) in g):
                trace(f"Indivíduo '{indId}' já existe. O script irá adicionar os triplos em falta, se aplicável.")

            # Do not add the triple if it already exists
            tipoTriplo = (indURI, r.RDF.type, baseURI)
            if (tipoTriplo not in g):
                g.add(tipoTriplo)
                trace(f"TRIPLE ADDED | tipo: {indURI} rdf:type {baseURI}")

            # Iterate over all remaining keys as object properties, skipping the built-in ones
            skip = {"id", "tipo"}
            for k, v in ind.items():
                if (k in skip): continue

                propURI = resolveURI(k)
                isObjProp = (propURI, r.RDF.type, r.OWL.ObjectProperty) in g
                isDataProp   = (propURI, r.RDF.type, r.OWL.DatatypeProperty) in g
                trace(f"PROP '{k}': {isObjProp} {isDataProp}")

                # If value is a list, register each item as a separate triple, else do a single iteration for its 
                # string value.
                values = v if isinstance(v, list) else [v]
                for val in values:
                    if (isObjProp):
                        value = resolveURI(str(val))
                    elif (isDataProp):
                        value = r.Literal(val)
                    else:
                        raise ValueError(f"Propriedade desconhecida: '{k}'")
                    
                    # If the triple already exists, skip it.
                    triple  = (indURI, propURI, value)
                    if triple in g:
                        trace(f"DUPLICATE: {triple}")
                        continue

                    g.add(triple)
                    trace(f"TRIPLE ADDED | {indURI} {propURI} {value}")

        onto = g.serialize(format=args.format[0])

        if (outfile := getattr(args, "output", None)):
            with open(os.path.abspath(outfile), "w") as fileOut:
                fileOut.write(onto)
        else:
            print(onto)
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())