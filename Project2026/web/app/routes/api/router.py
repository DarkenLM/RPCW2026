import os
from flask import Blueprint, request, jsonify
from app.services import userService
from app.logger import Logger
from app.services.sparqlService import execQuery

apiRouterName = "api"
apiRouterHook = f"/{apiRouterName}"
apiRouter = Blueprint(apiRouterName, __name__)
logger = Logger(f"{apiRouterName}/router")

RDF_PREFIX: str = os.getenv("RDF_PREFIX")  # pyright: ignore[reportAssignmentType]

@apiRouter.get("/ping")
def ping():
    return "Pong"

@apiRouter.post("/execute")
def execute():
    userQuery = request.json["query"]
    query = f"""
    PREFIX : <{RDF_PREFIX}>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
    { userQuery }
    """
    res = execQuery(query)
    if (isinstance(res, Exception)):
        return jsonify({
            "success": False,
            "message": str(res)
        })
    else:
        return jsonify({
            "success": True,
            "value": res
        })
