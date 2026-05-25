# pyright: reportExplicitAny=false

"""
Component definition: parses a component file and stores its metadata.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REQUIRED_MARK = "__REQUIRED__"

_DEF_REGEX = re.compile(r"\{#-?\s*def\s+(.*?)\s*-?#\}", re.DOTALL)
_STYLE_REGEX = re.compile(r"<style(?:[^>]*)>(.*?)</style>", re.DOTALL | re.IGNORECASE)
_SCRIPT_REGEX = re.compile(r"<script(?:[^>]*)>(.*?)</script>", re.DOTALL | re.IGNORECASE)
_GLOBAL_REGEX = re.compile(r":global\(([^)]*)\)")


def _shash(text: str, length: int = 6) -> str:
    return hashlib.md5(text.encode()).hexdigest()[:length]

def _parseDefBlock(def_src: str) -> dict[str, Any]:
    """
    Parse component definition blocks `{# def param1, param2="default", param3 #}` into a dictionary.
    """
    REQUIRED = object.__new__(object) # Unique sentinel symbol
    params: dict[str, Any] = {}
    if not def_src.strip(): return params

    # Evaluate as a lambda signature to leverage Python's own parser
    try:
        import inspect
        sig_src = f"def _f({def_src.strip()}): pass"
        local = {}
        exec(compile(sig_src, "<component_def>", "exec"), {}, local)  # pyright: ignore[reportUnknownArgumentType]
        sig = inspect.signature(local["_f"])  # pyright: ignore[reportUnknownArgumentType]
        for name, p in sig.parameters.items():
            if p.default is inspect.Parameter.empty:  # pyright: ignore[reportAny]
                params[name] = REQUIRED
            else:
                params[name] = p.default  # pyright: ignore[reportAny]
    except SyntaxError as exc:
        raise ValueError(f"Invalid component def: {def_src!r}") from exc

    # Store the sentinel on the class so callers can test for it
    params[REQUIRED_MARK] = REQUIRED
    return params


def _namespaceCSS(css: str, ns: str) -> str:
    """
    Prefix every top-level CSS selector with `.<ns>`.
    Handles nested rules, @media, @keyframes, etc.
    """
    result: list[str] = []
    buf = ""
    i = 0
    depth = 0
    inString: str | None = None
    inComment = False

    while i < len(css):
        ch = css[i]

        # Handle CSS comments
        if not inString and css[i:i+2] == "/*":
            end = css.find("*/", i + 2)
            if end == -1:
                result.append(css[i:])
                break
            result.append(css[i:end+2])
            i = end + 2
            continue

        # Handle strings
        if ch in ('"', "'") and not inComment:
            if inString is None:
                inString = ch
            elif inString == ch:
                inString = None

            buf += ch
            i += 1
            continue

        if inString:
            buf += ch
            i += 1
            continue
        
        # Handle rules
        if ch == "{":
            if depth == 0:
                # buf contains selectors
                selector = buf.strip()
                if selector:
                    prefixed = _prefixSelectors(selector, ns)
                    result.append(prefixed + " {")
                else:
                    result.append("{")
                buf = ""
            else:
                result.append(buf + "{")
                buf = ""

            depth += 1
        elif ch == "}":
            depth -= 1
            result.append(buf + "}")
            buf = ""
        else:
            buf += ch

        i += 1

    if buf.strip(): result.append(buf)
    return "\n".join(result)


def _prefixSelectors(selectorBlock: str, ns: str) -> str:
    """
    Given a (possibly comma-separated) selector string, prefix each part with `.<ns>` unless it's an @-rule.
    """
    if selectorBlock.lstrip().startswith("@"): return selectorBlock  # @media, @keyframes, etc.

    parts = selectorBlock.split(",")
    prefixed: list[str] = []
    for part in parts:
        s = part.strip()
        if not s: continue

        # Whole selector is global. Do not namespace.
        globalSelectorSearch = _GLOBAL_REGEX.fullmatch(s)
        if globalSelectorSearch:
            prefixed.append(globalSelectorSearch.group(1))
            continue
            
        # Part of selector is global. Expand and namespace only what lies outside.
        if (_GLOBAL_REGEX.search(s)):
            s = _GLOBAL_REGEX.sub(r"\1", s)
            prefixed.append(f".{ns} {s}")
            continue

        if (s == ":root"):
            # Keep :root selectors as-is but narrow their scope
            prefixed.append(f".{ns}")
        elif (not s.startswith(".")):
            # If selector is not a class, use the expensive :is pseudoselector.
            prefixed.append(f".{ns}:is({s})")
        else:
            # If selector is a class, use compound class selectors.
            prefixed.append(f".{ns}{s}")
    return ", ".join(prefixed)


# ---------------------------------------------------------------------------
# Component
# ---------------------------------------------------------------------------

@dataclass
class Component:
    name: str              # e.g. "DataCard"
    namespace: str         # e.g. "datacard-f0da5e"
    params: dict[str, Any] # extracted from {# def ... #} blocks
    rawCSS: str            # extracted <style> content (original)
    namespacedCSS: str     # extracted inline stylesheet with all top-level selectors prefixed with the namespace
    rawJS: str             # extracted inline <script> content
    templateSrc: str       # Jinja2 template source with <style>/<script> removed
    filePath: Path         # file path to the component source

    @classmethod
    def fromFile(cls, path: Path, name: str | None = None) -> "Component":
        src = path.read_text(encoding="utf-8")
        if name is None: name = path.stem 

        # Namespace based on component name + file content hash for nonce
        ns = f"{name.lower()}-{_shash(src)}"

        # Process Component Definition Block
        def_match = _DEF_REGEX.search(src)
        params = _parseDefBlock(def_match.group(1)) \
            if def_match \
            else { REQUIRED_MARK: object() }
        noDefSrc = _DEF_REGEX.sub("", src)

        # Process inline stylesheet
        cssParts: list[str] = []
        def _collectCSS(m: re.Match[str]) -> str: cssParts.append(m.group(1)); return ""
        noStyleCSS = _STYLE_REGEX.sub(_collectCSS, noDefSrc)
        rawCSS = "\n".join(cssParts)
        namespacedCSS = _namespaceCSS(rawCSS, ns) if rawCSS.strip() else ""

        # Process inline scripts
        jsParts: list[str] = []
        def _collectJS(m: re.Match[str]) -> str: jsParts.append(m.group(1)); return ""
        noScriptSrc = _SCRIPT_REGEX.sub(_collectJS, noStyleCSS)
        rawJS = "\n".join(jsParts)

        templateSrc = noScriptSrc.strip()

        return cls(
            name=name,
            namespace=ns,
            params=params,
            rawCSS=rawCSS,
            namespacedCSS=namespacedCSS,
            rawJS=rawJS,
            templateSrc=templateSrc,
            filePath=path,
        )
