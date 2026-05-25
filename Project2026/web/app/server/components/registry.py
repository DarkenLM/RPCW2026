# pyright: reportImplicitOverride=false
from __future__ import annotations

import os
import time
# import warnings
import traceback
from pathlib import Path
from typing import TYPE_CHECKING

from flask import Flask, Response, g
from jinja2 import Template
if TYPE_CHECKING: from jinja2 import Environment

from watchdog.observers import Observer
from watchdog.observers.api import BaseObserver
from watchdog.events import FileSystemEvent, FileSystemEventHandler

from app.logger import Logger
from .component import Component
from .preprocessor import ComponentPreprocessor


class ComponentWatcher(FileSystemEventHandler):
    logger: Logger

    def __init__(self, registry: "ComponentRegistry", debounceTime: float = 0.25):
        self.registry: ComponentRegistry = registry
        self.debounceTime: float = debounceTime
        self._last: dict[Path, float] = {}

        self.logger = Logger(type(self).__name__)
        self.logger.setLevel(Logger.LOG_DEBUG, registry.debug)

    def on_modified(self, event: FileSystemEvent):
        self.logger.debug("Received OnModified event:", str(event))
        if event.is_directory: return

        path = Path(str(event.src_path))
        # path = str(event.src_path)
        if not path.name.endswith(self.registry.fileExt): return

        # Debounce duplicate events
        now = time.time()
        last = self._last.get(path, 0)

        if now - last < 0.25: return
        self._last[path] = now

        self.registry.reloadComponent(path)

    def on_created(self, event):
        self.logger.debug("Received OnCreated event:", str(event))
        self.on_modified(event)

    def on_deleted(self, event):
        self.logger.debug("Received OnDeleted event:", str(event))
        if event.is_directory: return

        path = Path(str(event.src_path))
        self.registry.removeComponent(path)

class ComponentRegistry:
    """
    Central registry for all components. Attaches to a Flask application to manage all its components.

    @example
        registry = ComponentRegistry(app, componentDirs=["app/components"])
    """
    
    fileExt: str
    logger: Logger
    debug: bool

    def __init__(
        self,
        app: Flask | None = None,
        componentDirs: list[str | Path] | None = None,
        fileExt: str = ".html",
    ):
        self._components: dict[str, Component] = {}
        self._dirs: list[Path] = []
        self.fileExt = fileExt
        self.jinjaEnv: Environment | None = None
        self.logger = Logger(type(self).__name__)
        self._observer: BaseObserver | None = None
        self.debug = False

        if app is not None:
            self.debug = app.debug and os.environ.get("WERKZEUG_RUN_MAIN") == "true"
            self.logger.info(f"IS DEBUG: {app.debug} {os.environ.get('WERKZEUG_RUN_MAIN') == 'true'}")
            self.logger.setLevel(Logger.LOG_DEBUG, app.debug)
            self.initApp(app, componentDirs or [])

    def initApp(self, app: Flask, component_dirs: list[str | Path] | None = None):
        self.jinjaEnv = app.jinja_env

        for d in (component_dirs or []):
            self.addDirectory(d)

        # Per-request CSS/JS collection
        @app.before_request
        def _beforeCollect():  # pyright: ignore[reportUnusedFunction]
            g._cmp_collected_css = set()
            g._cmp_collected_js = set()

        # Inject collected assets before </head>
        @app.after_request
        def _afterCollect(response: Response):  # pyright: ignore[reportUnusedFunction]
            if "text/html" not in response.content_type:
                return response

            namespacedCSS = getattr(g, "_cmp_collected_css", set[str]())
            namespacedJS = getattr(g, "_cmp_collected_js", set[str]())
            
            # Nothing to transform
            if not namespacedCSS and not namespacedJS: return response

            parts: list[str] = []

            # Concat all namespaced CSS fragments into one stylesheet.
            if namespacedCSS:
                cssBlock = "\n".join(
                    self._components[ns].namespacedCSS
                    for ns in namespacedCSS
                    if ns in self._components and self._components[ns].namespacedCSS.strip()
                )

                if cssBlock.strip(): parts.append(f"<style>\n{cssBlock}\n</style>")

            # Concat all namespaced JS fragments into one script.
            if namespacedJS:
                js_block = "\n".join(
                    f"/* {self._components[ns].name} */\n{self._components[ns].rawJS}"
                    for ns in namespacedJS
                    if ns in self._components and self._components[ns].rawJS.strip()
                )
                if js_block.strip():
                    parts.append(f"<script>\n{js_block}\n</script>")

            # If no non-empty fragments were found, do not inject.
            if not parts: return response

            inject = "\n".join(parts)
            html = response.get_data(as_text=True)

            # Inject at head tail if present, otherwise inject at body tail.
            if "</head>" in html:
                html = html.replace("</head>", f"{inject}\n</head>", 1)
            elif "</body>" in html:
                html = html.replace("</body>", f"{inject}\n</body>", 1)
            else:
                html += inject

            response.set_data(html)
            return response

        # Register the component preprocessor as a Jinja2 extension through a custom Environment. 
        # Monkey-patch _parse to preprocess component tags before Jinja2 sees the source.
        self._patchJinjaEnv(app.jinja_env)

    def shutdown(self):
        if self._observer:
            self._observer.stop()
            self._observer.join()

    def addDirectory(self, path: str | Path):
        """Load all component files from a directory."""
        self.logger.debug(f"Loading components from '{path}'...")

        p = Path(path)
        if not p.exists(): raise FileNotFoundError(f"Component directory not found: {p}")
        
        self._dirs.append(p)
        self._loadDirectory(p)
        if self.debug: self._watchDirectory(p)

        self.logger.debug(f"Successfully loaded components from '{path}'.")

    def _loadDirectory(self, directory: Path):
        for f in directory.rglob(f"*{self.fileExt}"):
            name = f.name.replace(self.fileExt, "")

            try:
                self.logger.debug(f"Attempting to load component '{name}'...")
                component = Component.fromFile(f, name)
                self._components[name] = component

                # Index by namespace for the collector
                self._components[component.namespace] = component
                self.logger.debug(f"Successfully loaded component '{name}'.")
            except Exception:
                # warnings.warn(f"Failed to load component {f}: {exc}", stacklevel=2)
                self.logger.warn(f"Failed to load component {f}:")
                traceback.print_exc(2)

    def _watchDirectory(self, directory: Path):
        if self._observer is None:
            self._observer = Observer()
            self._observer.start()
            self.logger.debug("Started component watcher.")

        handler = ComponentWatcher(self)
        _ = self._observer.schedule(handler, str(directory), recursive=True)
        self.logger.debug(f"Started watching {str(directory)}")

    def reloadComponent(self, path: Path):
        name = path.name.replace(self.fileExt, "")

        try:
            self.logger.debug(f"Reloading component '{name}'...")
            component = Component.fromFile(path, name)

            self._components[name] = component
            self._components[component.namespace] = component

            self.logger.debug(f"Successfully reloaded component '{name}'.")
        except Exception:
            # warnings.warn(f"Failed to reload {path}: {exc}")
            self.logger.warn(f"Failed to reload component {path}:")
            traceback.print_exc(2)

    def removeComponent(self, path: Path):
        name = path.stem
        _ = self._components.pop(name, None)

        self.logger.debug(f"Removed component '{name}'")

    def get(self, name: str) -> Component | None:
        return self._components.get(name)

    def collect(self, component: Component):
        """
            Adds the component's CSS and JS to the global collection.
        """
        namespacedCSS: set[str] = getattr(g, "_cmp_collected_css", set())
        namespacedCSS.add(component.namespace)
        g._cmp_collected_css = namespacedCSS

        namespacedJS: set[str] = getattr(g, "_cmp_collected_js", set())
        namespacedJS.add(component.namespace)
        g._cmp_collected_js = namespacedJS

    # def reload(self):
    #     """
    #         Re-scan all registered component directories.
    #     """
    #     self._components.clear()
    #     for directory in self._dirs:
    #         self._loadDirectory(directory)

    def _patchJinjaEnv(self, env: "Environment"):
        """
        Wrap the Jinja2 environment's _parse so that component tags are expanded before Jinja2 processes the 
        template source. This is achieved by installing a custom Loader wrapper that preprocesses the source at 
        load time.
        """
        registry = self

        origLoader = env.loader
        if origLoader is None: return

        from jinja2 import BaseLoader, TemplateNotFound

        # Somehow, Jinja2 is aware of this class, even though it is not passed to anything, and the BaseLoader class
        # does not appear to have any dundles that can handle it.
        class ComponentLoader(BaseLoader):  # pyright: ignore[reportUnusedClass]
            def get_source(self, environment, template):  # pyright: ignore[reportImplicitOverride, reportMissingParameterType]
                try:
                    source, filename, uptodate = origLoader.get_source(environment, template)
                except TemplateNotFound:
                    raise

                # In order to preprocess anything at all, source expansion must be defered at this point. 
                # This passthrough loader does exactly that.
                return source, filename, uptodate

        # Instead of patching the loader (which doesn't have access to the context), monkey-patch the template 
        # rendering function to preprocess the template before passing it on to the rest of the JInja2 pipeline.
        registry._installRenderHook(env)

    def _installRenderHook(self, env: "Environment"):
        """
        Install a hook so that after a template renders, its output is
        post-processed to expand component tags with access to the
        render context.
        """
        registry = self

        # Store original _render method on Template class
        origGenerate = Template.generate  # pyright: ignore[reportUnusedVariable]
        origRender = Template.render
        origStream = Template.stream  # pyright: ignore[reportUnusedVariable]

        def newRender(self: Template, *args, **kwargs):
            result = origRender(self, *args, **kwargs)
            if getattr(self, "_cmp_rendering", False): return result
            
            ctx = dict(*args, **kwargs) if args and isinstance(args[0], dict) else kwargs
            pp = ComponentPreprocessor(registry)
            # pp.logger.debug("PRERENDER:", "\n", str(ctx))
            # pp.logger.debug("PRERENDER:", "\n", result)
            processed = pp.process(result, ctx)
            # pp.logger.debug("POSTRENDER:", "\n", processed)
            return processed

        # Only patch if it was not already patched
        if not getattr(Template, "_cmp_patched", False):
            Template.render = newRender
            Template._cmp_patched = True  # pyright: ignore[reportAttributeAccessIssue]

        env._cmp_registry = registry  # pyright: ignore[reportAttributeAccessIssue]
