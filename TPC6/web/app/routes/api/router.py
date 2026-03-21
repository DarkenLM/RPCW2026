from flask import Blueprint, request, jsonify
from app.logger import Logger

apiRouterName = "api"
apiRouterHook = f"/{apiRouterName}"
apiRouter = Blueprint(apiRouterName, __name__)
logger = Logger(f"{apiRouterName}/router")

@apiRouter.get("/ping")
def ping():
    return "Pong"