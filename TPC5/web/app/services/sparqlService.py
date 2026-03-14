import re
import os
import sys
from typing import List
from SPARQLWrapper import SPARQLWrapper, JSON
from app.util import RDFRef

# GRAPHDB_ENDPOINT = "http://localhost:7200/repositories/BibliotecaTemporal_T5"
GRAPHDB_ENDPOINT = os.getenv("GRAPHDB_ENDPOINT")

def jsonprint(json: str, indent="  "):
    res = ""
    i = 0
    il = 0
    escapeNext = False
    inStringLiteral = False

    while i < len(json):
        c = json[i]

        if inStringLiteral:
            res += c
            if escapeNext:
                escapeNext = False
            elif c == "\\":
                escapeNext = True
            elif c == '"':
                inStringLiteral = False
        else:
            if c.isspace():
                i += 1
                continue
            elif c == '"':
                inStringLiteral = True
                res += c
            elif c in "{[":
                res += c
                il += 1
                res += "\n" + indent * il
            elif c in "}]":
                il -= 1
                res += "\n" + indent * il + c
            elif c == ",":
                res += ",\n" + indent * il
            elif c == ":":
                res += ": "
            else:
                res += c

        i += 1

    return res


def execQuery(query: str):
    sparql = SPARQLWrapper(GRAPHDB_ENDPOINT)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        return sparql.query().convert() # type: ignore
    except Exception as e:
        print(f"Error while executing SPARQL query: {e}", file=sys.stderr)
        return None


def _extractVar(binding, var):
    if var not in binding: return None
    return binding[var]["value"]
    
def _getFields(res: dict, groupBy: List[str] | None = None, prefix: str | None = None):
    """
    Converts a SPARQL query's JSON results into structured Python objects.

    @param {dict} res The results of the query
    @param {List[str] | None} groupBy Fields used as subject identifier (e.g. ['livro', 'titulo']).
        Rows with the same values for all keys will merge all other fields into lists.
    @param {str | None} prefix

    @returns {list[dict]} Structured objects with repeated predicates collapsed into lists. 
        Merges that result in a list with a single element will yield that element, independently of the groupBy 
        strategy used. All strings that start with the `prefix` will be transformed into {@link RDFRef}
    """

    _vars = res["head"]["vars"]
    rows = res["results"]["bindings"]

    if (groupBy == None):
        return [{ v: _extractVar(row, v) for v in _vars if v in row } for row in rows]

    objects = {}

    for row in rows:
        key = tuple(_extractVar(row, g) for g in groupBy)
        if (None in key): continue

        if (key not in objects):
            obj = { g: _extractVar(row, g) for g in groupBy }
            objects[key] = obj

        obj = objects[key]

        for v in _vars:
            if (v in groupBy): continue

            val = _extractVar(row, v)
            if (val is None): continue

            if (v not in obj):
                obj[v] = val
            else:
                # Squash duplicates into list
                if (not isinstance(obj[v], list)): obj[v] = [obj[v]]
                if (val not in obj[v]): obj[v].append(val)

    for obj in objects.values():
        for (key, val) in obj.items():
            if (isinstance(val, list) and len(val) == 1): obj[key] = val[0]

    # Transform subject URIs into RDFRef obejcts
    if (prefix != None):
        for obj in objects.values():
            for (key, val) in obj.items():
                if (isinstance(val, list)):
                    for (i, e) in enumerate(val):
                        if (e.startswith(prefix)): val[i] = RDFRef(prefix, e)
                else:
                    if (val.startswith(prefix)): obj[key] = RDFRef(prefix, val)

    return list(objects.values())

def getFields(q, res, groupBy = None, prefix = None):
    """
    Converts a SPARQL query's JSON results into structured Python objects.

    @param {str} q The original query text
    @param {dict} res The results of the query
    @param {List[str] | None} groupBy Fields used as subject identifier (e.g. ['livro', 'titulo']).
        Rows with the same values for all keys will merge all other fields into lists.

    @returns {list[dict]} Structured objects with repeated predicates collapsed into lists. 
        Merges that result in a list with a single element will yield that element, independently of the groupBy 
        strategy used. All strings that start with the `prefix` will be transformed into {@link RDFRef}
    """
    if (prefix == None):
        pm = re.search(r"prefix\s+:\s+<([^>]+)>", q.lower())
        if (pm): prefix = pm.group(1)

    if (groupBy != None):
        return _getFields(res, groupBy, prefix=prefix)
    else:
        gb = re.search(r"group\s+by\s+\(?([^\)]+)\)?", q.lower())
        if (gb): _vars = re.findall(r"\?(\w+)", gb.group(1))
        else: _vars = None
        return _getFields(res, _vars, prefix=prefix)
