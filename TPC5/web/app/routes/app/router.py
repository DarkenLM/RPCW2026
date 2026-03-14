from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, abort
from app.util import PAGE, TEMPLATE, RENDER, toSplitProperCase, pickFromObj, pickFromObjAllExcept, RDFRef
from app.logger import Logger
from app.services.sparqlService import execQuery, getFields, jsonprint

RDF_PREFIX = "http://example.org/biblioteca-temporal#"

appRouterName = "app"
appRouterHook = "/"
appRouter = Blueprint(appRouterName, __name__)
logger = Logger(f"{appRouterName}/router")

@appRouter.get("/")
def root():
    return RENDER("app/root")

@appRouter.get("/livros")
def livros():
    q = f"""
PREFIX : <{RDF_PREFIX}>
SELECT ?id ?titulo ?tipoLivro ?nomeAutor ?paisOrigemAutor WHERE {{
    ?livro a :Livro .
    ?livro a ?_tipoLivro .
    FILTER(?_tipoLivro IN (:LivroHistorico, :LivroFiccional, :LivroParadoxal)) .
    ?livro :escritoPor ?_autor .
    ?_autor :nome ?nomeAutor ;
            :paisOrigem ?paisOrigemAutor .
    OPTIONAL {{ ?livro :titulo ?titulo }} .
    BIND(STRAFTER(STR(?livro), "#") AS ?id)
    BIND(STRAFTER(STR(?_tipoLivro), "#") AS ?tipoLivro)
}}
ORDER BY ?id
    """
    res = execQuery(q)
    # livros = []
    # if (res != None):
    #     livros = list(map(lambda l: {
    #         "id": l["id"]["value"],
    #         "titulo": l["titulo"]["value"] if ("titulo" in l) else "N/A",
    #         "tipoLivro": l["tipoLivro"]["value"],
    #         "nomeAutor": l["nomeAutor"]["value"],
    #         "paisOrigemAutor": l["paisOrigemAutor"]["value"],
    #     }, res["results"]["bindings"]))
    livros = getFields(q, res, ["id"])

    return RENDER("app/livros", { 
        "tableHeaders": [
            ("id", "Id"), 
            ("titulo", "Título"), 
            ("tipoLivro", "Tipo de Livro"), 
            ("nomeAutor", "Autor"), 
            ("paisOrigemAutor", "País de Origem")
        ], 
        "tableBody": livros,
        "tableMeta": {
            "_linkTorwards": {
                "*": {
                    "from": ["id", "titulo", "tipoLivro", "nomeAutor", "paisOrigemAutor"],
                    "to": lambda r: f"/livro/{r['id']}"
                }
            }
        } 
    })

@appRouter.get("/livro/<livro>")
def livro(livro):
    q = f"""
PREFIX : <{RDF_PREFIX}>
SELECT ?livro ?titulo ?tipoLivro ?nomeAutor ?paisOrigemAutor ?linhaTemporal ?eventoId ?eventoNome ?eventoDesc WHERE {{
    BIND(:{livro} as ?livro)
    ?livro a :Livro .
    OPTIONAL {{ ?livro :titulo ?titulo }} .
    
    ?livro a ?_tipoLivro .
    FILTER(?_tipoLivro IN (:LivroHistorico, :LivroFiccional, :LivroParadoxal)) .
    BIND(STRAFTER(STR(?_tipoLivro), "#") AS ?tipoLivro)
    
    ?livro :escritoPor ?_autor .
    ?_autor :nome ?nomeAutor ;
            :paisOrigem ?paisOrigemAutor .
    
    ?livro :existeEm ?linhaTemporal .
    OPTIONAL {{ 
        ?livro :refereEvento ?eventoId . 
        ?eventoId :designacao ?eventoNome .
        ?eventoId :descricao ?eventoDesc .
    }} .
}}
ORDER BY ?id
    """
    res = execQuery(q)
    fields = getFields(q, res, ["livro", "titulo", "tipoLivro", "nomeAutor", "paisOrigemAutor", "linhaTemporal", "eventoId"])
    if (len(fields) == 0): return abort(404)

    print(jsonprint(f"{fields}".replace("'", '"')))
    field = fields[0]
    # print(jsonprint(f"{field}".replace("'", '"')))
    return RENDER("app/livro", {
        "entryName": field["titulo"],
        "entryValues": {
            "_main": pickFromObjAllExcept(field, "eventoId", "eventoNome", "eventoDesc"),
            # "evento": pickFromObj(field, "eventoId", "eventoNome", "eventoDesc")
            **{ k:v for (k,v) in map(
                lambda f: (f"Evento: {f['eventoNome']}", pickFromObj(f, "eventoId", "eventoNome", "eventoDesc")), 
                fields
            ) }
        },
        "entryKeyMap": {
            "livro": "Id",
            "titulo": "Título",
            "tipoLivro": "Tipo",
            "nomeAutor": "Autor",
            "paisOrigemAutor": "País de Origem",
            "linhaTemporal": ("Linha Temporal", "Linhas Temporais"),
            "evento": "Evento",
            "eventoId": "Id",
            "eventoNome": "Designação",
            "eventoDesc": ("Descrição", "Descrições"),
        }
    })

@appRouter.get("/eventos")
def eventos():
    q = f"""
PREFIX : <{RDF_PREFIX}>
SELECT * WHERE {{
    ?evento a :Evento ;
            :designacao ?designacao ;
    		:descricao ?descricao .
    ?livro a :Livro ;
           :refereEvento ?evento .
}}
ORDER BY ?evento
    """
    res = execQuery(q)
    fields = getFields(q, res, ["evento"])

    return RENDER("app/livros", { 
        "tableHeaders": [
            ("evento", "Evento"), 
            ("designacao", "Designação"), 
            ("descricao", "Descrição"), 
            ("livro", "Livros com referência")
        ], 
        "tableBody": fields,
        "tableMeta": {
            "_linkTorwards": {
                "*": {
                    "from": ["livro"],
                    "to": lambda r: (lambda r2: "/livro/" + r2.uri.split('#')[1]) \
                        if (isinstance(r['livro'], list)) \
                        else ("/livro/" + r['livro'].uri.split('#')[1])
                }
            }
        } 
    })
