# pyright: reportAny=false, reportUnknownArgumentType=false, reportUnknownLambdaType=false, reportUnknownArgumentType=false, reportExplicitAny=false, reportUnknownMemberType=false, reportUnknownVariableType=false

import math
import os
import pprint
import re
from flask import Blueprint, request, abort
from app.util import RENDER
from app.logger import Logger
from app.services.sparqlService import execQuery

RDF_PREFIX: str = os.getenv("RDF_PREFIX")  # pyright: ignore[reportAssignmentType]

_STRING_MAP = {
    "id": "Identificador",
    "uri": "URI",
    "tid": "TID",
    "rights": "Acesso",
    "rights_uri": "URI de Acesso",
    "advisor": "Concelheiro",
    "author": "Autor",
    "accessioned": "Adquirido em",
    "available": "Disponibilizado em",
    "issued": "Emitido em",
    "submitted": "Submetido em",
    "title": "Título",
    "type": "Tipo",
    "subject": "Temas",
    "language": "Linguagem",
    "grade": "Nota final",
    "thumbnail": "Miniatura",
    "file": "Ficheiro",
    "name": "Nome",
    "originalName": "Nome Original",
    "description": "Descrição",
    "format": "Formato (MIME)",
    "size": "Tamanho",
    "checksum": "Checksum",
    "checksumAlgorithm": "Algoritmo de Checksum",
    "licence": "Licença",
    "contributors": "Contribuidores",
    "creator": "Criador",
    "contributedTo": "Contribuíu em",
    "created": "Criou"
}

ESCAPE_CHARS = lambda s: s.replace("'", r"’").replace('"', r"‟")

appRouterName = "app"
appRouterHook = "/"
appRouter = Blueprint(appRouterName, __name__)
logger = Logger(f"{appRouterName}/router")

@appRouter.get("/")
def root():
    return RENDER("root")

@appRouter.get("/acerca")
def acerca():
    return RENDER("acerca")

@appRouter.get("/search")
def search():
    return RENDER("search")

_NUM_RECORD_PAGES = 1
_NUM_PEOPLE_PAGES = 1
_NUM_CATEGORY_PAGES = 1
def makeNumPages():
    #region -------------- Record --------------
    global _NUM_RECORD_PAGES
    q = f"""
    PREFIX : <{RDF_PREFIX}>
    SELECT (COUNT(DISTINCT ?rec) AS ?num)
    WHERE {{
        ?rec a :Record ;
            :title ?title ;
            :createdBy ?author ;
            :submittedDate ?submitted .

        ?author :name ?authorName .
        OPTIONAL {{ ?rec :hasSubject ?_subject . }}
    }}
    """
    res = execQuery(q)
    _NUM_RECORD_PAGES = math.ceil(int(res["results"]["bindings"][0]["num"]["value"]) / 50)  # pyright: ignore[ reportConstantRedefinition, reportIndexIssue]
    logger.debug("MAX RECORDS PAGE:", str(_NUM_RECORD_PAGES))
    #endregion -------------- Record --------------
    
    #region -------------- People --------------
    global _NUM_PEOPLE_PAGES
    q = f"""
    PREFIX : <{RDF_PREFIX}>
    SELECT 
        (COUNT(DISTINCT ?personID) AS ?num)
    WHERE {{
        ?person a :Person ;
                :name ?name .
        OPTIONAL {{ 
            ?person :contributedTo ?contributed .
            ?contributed :title ?contributedTitle .
            BIND(STRAFTER(STR(?contributed), "#") AS ?contributedID) .
    		BIND(CONCAT(?contributedID, "␟", ?contributedTitle) AS ?contributedPair) .
        }}
        OPTIONAL {{ 
            ?person :created ?created .
            ?created :title ?createdTitle .
            BIND(STRAFTER(STR(?created), "#") AS ?createdID) .
    		BIND(CONCAT(?createdID, "␟", ?createdTitle) AS ?createdPair) .
        }}
        BIND(STRAFTER(STR(?person), "#") AS ?personID)
    }}
    """
    res = execQuery(q)
    _NUM_PEOPLE_PAGES = math.ceil(int(res["results"]["bindings"][0]["num"]["value"]) / 50)  # pyright: ignore[reportConstantRedefinition, reportIndexIssue]
    logger.debug("MAX PEOPLE PAGE:", str(_NUM_PEOPLE_PAGES))
    #endregion -------------- People --------------

    #region -------------- Category --------------
    global _NUM_CATEGORY_PAGES
    q = f"""
    PREFIX : <{RDF_PREFIX}>
    SELECT (COUNT(DISTINCT ?subject) AS ?num)
    WHERE {{
        ?subject a :Subject .
    }}
    """
    res = execQuery(q)
    _NUM_CATEGORY_PAGES = math.ceil(int(res["results"]["bindings"][0]["num"]["value"]) / 50)  # pyright: ignore[reportConstantRedefinition, reportIndexIssue]
    logger.debug("MAX CATEGORY PAGE:", str(_NUM_CATEGORY_PAGES))
    #endregion -------------- Category --------------

@appRouter.get("/registos")
def registos():
    page = min(math.floor(int(request.args.get("page") or "1")), (_NUM_RECORD_PAGES - 1))
    q = f"""
        PREFIX : <{RDF_PREFIX}>
        SELECT ?recordID ?title ?authorName ?submitted (GROUP_CONCAT(DISTINCT ?subject; separator="␞") AS ?subjects) 
        WHERE {{
            ?rec a :Record ;
                :title ?title ;
                :createdBy ?author ;
                :submittedDate ?submitted .
            ?author :name ?authorName .
            OPTIONAL {{ ?rec :hasSubject ?_subject . }} .
            BIND(STRAFTER(STR(?_subject), "#") AS ?subject) .
            BIND(STRAFTER(STR(?rec), "#") AS ?recordID) .
        }}
        GROUP BY ?recordID ?title ?authorName ?submitted
        ORDER BY ?submitted
        LIMIT 50
        OFFSET {page * 50}
    """
    res = execQuery(q)
    if (not res): return abort(500)

    # logger.debug(f"REGISTOS ({page}):")
    # pprint.pprint(res)

    records = []
    for rec in res["results"]["bindings"]:  # pyright: ignore[reportIndexIssue]
        records.append({
            "tid": rec["recordID"]["value"],
            "title": ESCAPE_CHARS(rec["title"]["value"]),
            "author": rec["authorName"]["value"],
            "submitted": rec["submitted"]["value"],
            "subjects": rec["subjects"]["value"].split("␞") if ("subjects" in rec and rec["subjects"] != None) else []
        })

    # with open("/home/rafaelsf/Desktop/Cadeiras/4ano/2sem/RPCW/RPCW2026/Project_RPCW2026/web/fodase.txt", "w") as f:
    #     json.dump(records, f)

    ctx = {
        "records": list(map(
            lambda c: {
                "tid": { "type": "link", "link": f"/registo/{c['tid']}", "value": c["tid"] },
                "title": { "type": "link", "link": f"/registo/{c['tid']}", "value": c["title"] },
                "author": { "type": "link", "link": f"/pessoa/{c['author']}", "value": c["author"] },
                "subjects": list(map(
                    lambda cc: { "type": "link", "link": f"/categoria/{cc.replace(' ', '_')}", "value": f"{cc}" }, 
                    # cast(Any, c["subjects"])
                    [cc for cc in c["subjects"] if cc]
                )),
                "submitted": { "type": "link", "link": f"/registo/{c['tid']}", "value": c["submitted"] },
            },  
            records
        )),
        "string_map__": _STRING_MAP,
        "currentPage": page,
        "maxPage": _NUM_RECORD_PAGES
    }
    # with open("/home/rafaelsf/Desktop/Cadeiras/4ano/2sem/RPCW/RPCW2026/Project_RPCW2026/web/fodase.txt", "w") as f:
    #     json.dump(ctx["records"], f)

    return RENDER("records", ctx)

@appRouter.get("/registo/<registo>")
def registo(registo: str):
    q = f"""
        PREFIX : <{RDF_PREFIX}>
        SELECT 
            ?registoID ?title ?contributorName 
            ?submittedDate ?issuedDate ?accessionedDate ?availableDate ?rights ?language ?type ?grade 
            ?originalName ?originalOriginalName ?originalDescription ?originalFormat ?originalURL
            ?thumbnailName ?thumbnailOriginalName ?thumbnailDescription ?thumbnailFormat ?thumbnailURL
            (GROUP_CONCAT(DISTINCT ?subject; separator="␞") AS ?subjects)
            (GROUP_CONCAT(DISTINCT ?contributorName; separator="␞") AS ?contributorNames)
            (GROUP_CONCAT(DISTINCT ?creatorName; separator="␞") AS ?creatorNames)
        WHERE {{
            BIND(:{registo} AS ?registo) .
            ?registo :title ?title ;
            OPTIONAL {{ ?registo :createdBy ?creator . ?creator :name ?creatorName . }}
            OPTIONAL {{ ?registo :contributionBy ?contributor . ?contributor :name ?contributorName . }}
            OPTIONAL {{ ?registo :submittedDate ?submittedDate . }}
            OPTIONAL {{ ?registo :issuedDate ?issuedDate . }}
            OPTIONAL {{ ?registo :accessionedDate ?accessionedDate . }}
            OPTIONAL {{ ?registo :availableDate ?availableDate . }}
            OPTIONAL {{ ?registo :language ?language . }}
            OPTIONAL {{ ?registo :type ?type . }}
            OPTIONAL {{ ?registo :grade ?grade . }}
            OPTIONAL {{ ?registo :rights ?rights . }}
            OPTIONAL {{ ?registo :rightsURI ?rightsURI . }}
            OPTIONAL {{ 
                ?registo :hasOriginal ?original . 
                OPTIONAL {{ ?original :name ?originalName . }}
                OPTIONAL {{ ?original :originalName ?originalOriginalName . }}
                OPTIONAL {{ ?original :description ?originalDescription . }}
                OPTIONAL {{ ?original :format ?originalFormat . }}
                OPTIONAL {{ ?original :url ?originalURL . }}
            }}
            OPTIONAL {{
                ?registo :hasThumbnail ?thumbnail .
                OPTIONAL {{ ?thumbnail :name ?thumbnailName . }}
                OPTIONAL {{ ?thumbnail :originalName ?thumbnailOriginalName . }}
                OPTIONAL {{ ?thumbnail :description ?thumbnailDescription . }}
                OPTIONAL {{ ?thumbnail :format ?thumbnailFormat . }}
                OPTIONAL {{ ?thumbnail :url ?thumbnailURL . }}
            }}
            OPTIONAL {{ 
                ?registo :hasSubject ?_subject . 
                BIND(STRAFTER(STR(?_subject), "#") AS ?subject) . 
            }}
            
            BIND(STRAFTER(STR(?registo), "#") AS ?registoID)
        }}
        GROUP BY ?registoID ?title ?creatorName ?contributorName ?submittedDate ?issuedDate ?accessionedDate 
            ?availableDate ?rights ?language ?type ?grade ?originalName ?originalOriginalName ?originalDescription 
            ?originalFormat ?originalURL ?thumbnailName ?thumbnailOriginalName ?thumbnailDescription ?thumbnailFormat 
            ?thumbnailURL
                    
    """
    res = execQuery(q)
    if (not res): return abort(500)

    record = {"tid": "", "title": "", "creator": [], "contributors": [], "submitted": "", "issued": "", "accessioned": "", "available": "", "rights": "", "language": "", "type": "", "grade": None, "original": {}, "thumbnail": {}, "subject": []}
    for r in res["results"]["bindings"]:  # pyright: ignore[reportIndexIssue]
        record["tid"] = r["registoID"]["value"]
        record["title"] = r["title"]["value"]
        record["creator"] = [ 
            { "type": "link", "link": f"/pessoa/{c}", "value": c} 
            for c in r["creatorNames"]["value"].split("␞")
        ] if "creatorNames" in r else []
        record["contributors"] = [ 
            { "type": "link", "link": f"/pessoa/{c}", "value": c} 
            for c in r["contributorNames"]["value"].split("␞")
        ] if "contributorNames" in r else []
        record["submitted"] = r["submittedDate"]["value"]
        record["issued"] = r["issuedDate"]["value"]
        record["accessioned"] = r["accessionedDate"]["value"]
        record["available"] = r["availableDate"]["value"]
        record["rights"] = { "type": "lockicon", "value": r["rights"]["value"], "inline": True }
        record["language"] = r["language"]["value"]
        record["type"] = r["type"]["value"]
        record["grade"] = r["grade"]["value"] if "grade" in r else None
        record["original"] = {
            "type": "file",
            "value": {
                "name": r["originalName"]["value"] if ("originalName" in r) else None,
                "originalName": r["originalOriginalName"]["value"] if ("originalOriginalName" in r) else None,
                "description": r["originalDescription"]["value"] if ("originalDescription" in r) else None,
                "format": r["originalFormat"]["value"] if ("originalFormat" in r) else None,
                "url": r["originalURL"]["value"] if ("originalURL" in r) else None,
                "size": None,
                "checksum": None,
                "checksumAlgorithm": None
            }
        } if "originalURL" in r else None
        record["thumbnail"] = {
            "type": "file",
            "value": {
                "name": r["thumbnailName"]["value"] if ("thumbnailName" in r) else None,
                "originalName": r["thumbnailOriginalName"]["value"] if ("thumbnailOriginalName" in r) else None,
                "description": r["thumbnailDescription"]["value"] if ("thumbnailDescription" in r) else None,
                "format": r["thumbnailFormat"]["value"] if ("thumbnailFormat" in r) else None,
                "url": r["thumbnailURL"]["value"] if ("thumbnailURL" in r) else None,
                "size": None,
                "checksum": None,
                "checksumAlgorithm": None
            }
        } if "thumbnailURL" in r else None
        record["subject"] = r["subjects"]["value"].split("␞") if "subjects" in r else []

    return RENDER("record", {
        "highlights": list(map(lambda s: {
            "type": "link",
            "link": f"/categoria/{s.replace(' ', '_')}",
            "value": s
        }, record["subject"])),
        "record": record,
        "string_map__": _STRING_MAP
    })

@appRouter.get("/pessoas")
def pessoas():
    page = min(math.floor(int(request.args.get("page") or "1")), (_NUM_RECORD_PAGES - 1))
    q = f"""
        PREFIX : <{RDF_PREFIX}>
        SELECT 
            ?personID 
            ?name 
        	(GROUP_CONCAT(DISTINCT ?contributedPair; separator="␞") AS ?contributedPairs)
		    (GROUP_CONCAT(DISTINCT ?createdPair; separator="␞") AS ?createdPairs)
        WHERE {{
            ?person a :Person ;
                    :name ?name .
            OPTIONAL {{ 
                ?person :contributedTo ?contributed .
                ?contributed :title ?contributedTitle .
                BIND(STRAFTER(STR(?contributed), "#") AS ?contributedID) .
        		BIND(CONCAT(?contributedID, "␟", ?contributedTitle) AS ?contributedPair) .
            }}
            OPTIONAL {{ 
                ?person :created ?created .
                ?created :title ?createdTitle .
                BIND(STRAFTER(STR(?created), "#") AS ?createdID) .
        		BIND(CONCAT(?createdID, "␟", ?createdTitle) AS ?createdPair) .
            }}
            BIND(STRAFTER(STR(?person), "#") AS ?personID)
        }}
        GROUP BY ?personID ?name
        ORDER BY ?name
        LIMIT 50
        OFFSET {page * 50}
    """
    res = execQuery(q)
    if (not res): return abort(500)

    def _processPair(prefix: str):
        def _processPair_(pair: str):
            if (not pair): return None
            id, name = pair.split('␟')
            return { "type": "link", "link": f"{prefix}/{id}", "value": name }
        return _processPair_

    contributors = []
    for r in res["results"]["bindings"]:  # pyright: ignore[reportIndexIssue]
        contributors.append({
            "id": r["personID"]["value"],
            "name": r["name"]["value"],
            "contributedTo": list(map(
                _processPair("/registo"), 
                r["contributedPairs"]["value"].split("␞") if "contributedPairs" in r else [], 
            )),
            "created": list(map(
                _processPair("/registo"), 
                r["createdPairs"]["value"].split("␞") if "createdPairs" in r else [], 
            )),
        })

    # logger.debug(f"PESSOAS:")
    # pprint.pprint(res)

    return RENDER("contributors", {
        "contributors": list(map(
            lambda c: {
                "id": { "type": "link", "link": f"/pessoa/{c['id']}", "value": c["id"] },
                "name": { "type": "link", "link": f"/pessoa/{c['id']}", "value": c["name"] },
                "contributedTo": [cc for cc in c["contributedTo"] if cc],
                "created": [cc for cc in c["created"] if cc],
            },  
            contributors
        )),
        "string_map__": _STRING_MAP,
        "currentPage": page,
        "maxPage": _NUM_PEOPLE_PAGES
    })

@appRouter.get("/pessoa/<pessoa>")
def pessoa(pessoa: str):
    truePerson = re.sub(r"[^\w]+", "_", pessoa).strip("_").replace(" ", "_")
    q = f"""
        PREFIX : <{RDF_PREFIX}>
        SELECT ?person ?name ?personID 
        (GROUP_CONCAT(DISTINCT ?contributedPair; separator="␞") AS ?contributedPairs)
		(GROUP_CONCAT(DISTINCT ?createdPair; separator="␞") AS ?createdPairs)
        WHERE {{
            BIND(:{truePerson} AS ?person).
            BIND(STRAFTER(STR(?person), "#") AS ?personID)
            ?person :name ?name .
            OPTIONAL {{ 
                ?person :contributedTo ?contributed .
                ?contributed :title ?contributedTitle .
                BIND(STRAFTER(STR(?contributed), "#") AS ?contributedID) .
        		BIND(CONCAT(?contributedID, "␟", ?contributedTitle) AS ?contributedPair) .
            }}
            OPTIONAL {{ 
                ?person :created ?created .
                ?created :title ?createdTitle .
                BIND(STRAFTER(STR(?created), "#") AS ?createdID) .
        		BIND(CONCAT(?createdID, "␟", ?createdTitle) AS ?createdPair) .
            }}
        }}
        GROUP BY ?person ?name ?personID
        ORDER BY ?name
    """
    res = execQuery(q)
    if (not res): return abort(500)

    def _processPair(prefix: str):
        def _processPair_(pair: str):
            if (not pair): return None
            id, name = pair.split('␟')
            return { "type": "link", "link": f"{prefix}/{id}", "value": name }
        return _processPair_

    contributor = {}
    r = res["results"]["bindings"][0]  # pyright: ignore[reportIndexIssue]
    contributor["id"] = r["personID"]["value"]
    contributor["name"] = r["name"]["value"]
    contributor["contributedTo"] = list(map(
        _processPair("/registo"), 
        r["contributedPairs"]["value"].split("␞") if "contributedPairs" in r else [], 
    ))
    contributor["created"] = list(map(
        _processPair("/registo"), 
        r["createdPairs"]["value"].split("␞") if "createdPairs" in r else [], 
    ))

    return RENDER("contributor", {
        "contributor": contributor,
        "string_map__": _STRING_MAP
    })

@appRouter.get("/categorias")
def categorias():
    page = min(math.floor(int(request.args.get("page") or "1")), (_NUM_RECORD_PAGES - 1))
    q = f"""
        PREFIX : <{RDF_PREFIX}>
        SELECT DISTINCT ?subject
        WHERE {{
            ?_subject a :Subject .
            BIND(STRAFTER(STR(?_subject), "#") AS ?subject) .
        }}
        LIMIT 50
        OFFSET {page * 50}
    """
    res = execQuery(q)

    # logger.debug(f"CATEGORIAS:")
    # pprint.pprint([c for c in res["results"]["bindings"]])
    categories = [c["subject"]["value"] for c in res["results"]["bindings"]]  # pyright: ignore[reportIndexIssue]

    return RENDER("categories", {
        "categories": list(map(
            lambda c: [{ "type": "link", "link": f"/categoria/{c}", "value": c.replace('_', ' ') }],  
            categories
        )),
        "string_map__": _STRING_MAP,
        "currentPage": page,
        "maxPage": _NUM_CATEGORY_PAGES
    })

@appRouter.get("/categoria/<categoria>")
def categoria(categoria: str):
    q = f"""
        PREFIX : <{RDF_PREFIX}>
        SELECT ?recordID ?title ?authorName ?submitted (GROUP_CONCAT(DISTINCT ?subject; separator="␞") AS ?subjects)
        WHERE {{
            ?rec a :Record ;
                :title ?title ;
                :createdBy ?author ;
                :submittedDate ?submitted ;
                :hasSubject :{categoria} .
            ?author :name ?authorName .
            OPTIONAL {{ 
                ?rec :hasSubject ?_subject . 
                BIND(STRAFTER(STR(?_subject), "#") AS ?subject)
            }}
            BIND(STRAFTER(STR(?rec), "#") AS ?recordID)
        }}
        GROUP BY ?recordID ?title ?authorName ?submitted
        ORDER BY ?submitted
    """
    res = execQuery(q)

    records = []
    for rec in res["results"]["bindings"]:  # pyright: ignore[reportIndexIssue]
        records.append({
            "tid": rec["recordID"]["value"],
            "title": rec["title"]["value"],
            "author": rec["authorName"]["value"],
            "submitted": rec["submitted"]["value"],
            "subject": rec["subjects"]["value"].split("␞") if ("subjects" in rec and rec["subjects"] != None) else []
        })

    logger.debug(f"CATEGORIA:")
    pprint.pprint(records)

    return RENDER("category", {
        "category": categoria.replace("_", " "),
        "records": list(map(
            lambda c: {
                "tid": { "type": "link", "link": f"/registo/{c['tid']}", "value": c["tid"] },
                "title": { "type": "link", "link": f"/registo/{c['tid']}", "value": c["title"] },
                "author": c["author"],
                "subject": list(map(
                    lambda cc: { "type": "link", "link": f"/categoria/{cc.replace(' ', '_')}", "value": cc },   
                    [cc for cc in c["subject"] if cc]
                )),
                "submitted": { "type": "link", "link": f"/registo/{c['tid']}", "value": c["submitted"] },
            },  
            records
        )),
        "string_map__": _STRING_MAP
    })

@appRouter.get("/queries")
def queries():
    return RENDER("queries")

