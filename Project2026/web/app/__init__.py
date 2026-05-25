import os
import atexit
from typing import Any
from flask import Flask

from app.server.components import ComponentRegistry
# import jinjax
from .routes.api.router import apiRouter, apiRouterHook, logger as apiLogger
from .routes.app.router import appRouter, appRouterHook, logger as appLogger, makeNumPages
from app.util import RENDER
from app.logger import Logger
from app.gvars import g

__dirname = os.path.dirname(__file__)

def page_not_found(e: Any):  # pyright: ignore[reportExplicitAny]
    return RENDER("templates/404"), 404

def createApp(debug = False):
    logger = Logger(__name__)
    logger.setLevel(Logger.LOG_DEBUG, debug)
    logger.debug("Static directory:", f"{__dirname}/public")

    app = Flask(
        __name__, 
        static_folder=f"{__dirname}/public", static_url_path="/static",
        template_folder=f"{__dirname}/pages"
    )
    _ = app.config.from_mapping(
        SECRET_KEY="dev" if debug else os.getenv("WEB_SECRET"),
        DEBUG=debug,
    )

    #region ------- Store globals -------
    g.app = app
    g.debug = debug
    g.logger = logger
    g.appName = os.getenv("APP_NAME") or "Flask App"
    #endregion ------- Store globals -------
    
    #region ------- Register components -------
    componentRegistry = ComponentRegistry(
        app,
        componentDirs=[f"{__dirname}/components"],
        fileExt=".html.j2",
    )
    g.componentRegistry = componentRegistry
    _ = atexit.register(componentRegistry.shutdown)
    #endregion ------- Register components -------

    #region ------- Register routes -------
    app.register_blueprint(apiRouter, url_prefix=apiRouterHook)
    apiLogger.setLevel(Logger.LOG_DEBUG, debug)

    app.register_blueprint(appRouter, url_prefix=appRouterHook)
    appLogger.setLevel(Logger.LOG_DEBUG, debug)
    makeNumPages()

    app.register_error_handler(404, page_not_found)
    #endregion ------- Register routes -------

    return app