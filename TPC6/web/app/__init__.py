import os
from flask import Flask, render_template
from .routes.api.router import apiRouter, apiRouterHook, logger as apiLogger
from .routes.app.router import appRouter, appRouterHook, logger as appLogger
from app.util import PAGE, TEMPLATE
from app.logger import Logger
from app.gvars import g

__dirname = os.path.dirname(__file__)

def page_not_found(e):
    return render_template(TEMPLATE("404")), 404

def createApp(debug = False):
    logger = Logger(__name__)
    logger.setLevel(Logger.LOG_DEBUG, debug)
    logger.debug("Static directory:", f"{__dirname}/public")

    app = Flask(
        __name__, 
        static_folder=f"{__dirname}/public", static_url_path="/static",
        template_folder=f"{__dirname}/pages"
    )
    app.config.from_mapping(
        SECRET_KEY="dev" if debug else os.getenv("WEB_SECRET")
    )
    
    app.register_blueprint(apiRouter, url_prefix=apiRouterHook)
    apiLogger.setLevel(Logger.LOG_DEBUG, debug)

    app.register_blueprint(appRouter, url_prefix=appRouterHook)
    appLogger.setLevel(Logger.LOG_DEBUG, debug)

    app.register_error_handler(404, page_not_found)

    g.app = app

    return app