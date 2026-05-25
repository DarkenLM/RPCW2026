# pyright: reportImportCycles=false, reportExplicitAny=false, reportAny=false
"""
Pre-processor that replaces <ComponentName ...> tags with rendered HTML.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from app.gvars import g
from app.logger import Logger

from .component import Component, REQUIRED_MARK

if TYPE_CHECKING:
    from .registry import ComponentRegistry

Context = dict[str, str]

#region ============== Constants ==============
# Matches any component (PascalCase name) opening tag.
# Group 1: tag name; Group 2: attributes; Group 3: "/" if tag is self-closing
_OPEN_TAG_REGEX = re.compile(r"<([A-Z][A-Za-z0-9_]*)(.*?)(/?)>", re.DOTALL)

# Extracts the properties of an HTML tag.
# Accepts properties in the form `key="val"`, `key='val'`, `key={expr}`, or just `key`
# Group 1: property key; Group 2 (optional): value of the property.
# _ATTR_REGEX = re.compile(r"""([A-Za-z_][A-Za-z0-9_:-]*)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|\{([^}]*)\}))?""")
_ATTR_REGEX = re.compile(
    r"""([A-Za-z_][A-Za-z0-9_:-]*)(?:\s*=\s*(?:\"((?:[^\"\\]|\\.)*)\"|'((?:[^'\\]|\\.)*)'|\{((?:[^\}\\]|\\.)*)\}))?"""
)

# Extracts tags from an HTML string.
# Group 1: closing tag slash, or None; Group 2: tag name; 
# Group 3: tag properties, or None; Group 4: self-closing slash, or None.
_ELEMENT_REGEX = re.compile(r"<(/?)([a-zA-Z][a-zA-Z0-9]*)([^>]*?)(/?)>", re.DOTALL)

# Extracts data from self-closing named slots (`<slot name="foo"/>`)`
# Group 1: Slot name
_NAMED_SLOT_REGEX= re.compile(r'<slot\s+name=["\']([^"\']+)["\']\s*/?>')

# Extracts data from block named slots (`<slot name="foo">some content</slot>`)
# Group 1: Slot name; Group 2: Slot child content or None
_BLOCK_SLOT_REGEX= re.compile(r'<slot\s+name=["\']([^"\']+)["\']\s*>(.*?)</slot>', flags=re.DOTALL)

# Extracts data from default slots: (`<slot/>`) or (`<slot>some content</slot>`)
# Group 1: Slot child content or None
_DEFAULT_SLOT_REGEX= re.compile(r"<slot\s*>(.*?)</slot>", flags=re.DOTALL)

# Extracts data from templates fror a given slot name.
# Group 1: Slot name; Group 2: Slot child content or None
_NAMED_TEMPLATE_REGEX = re.compile(r'<template\s+slot=["\']([^"\']+)["\']\s*>(.*?)</template>', re.DOTALL)
#endregion ============== Constants ==============

#region ============== Functions ==============
def _parseTagAttributes(attrStr: str) -> dict[str, str]:
    """
        Extracts the attributes from the attribute string of an HTML tag as a dictionary. If only the property key was
        defined, it assigns the value `True` for that property.

        @note This function assumes that the attribute string passed as an argument was extracted from the HTML tag
        already.
    """
    attrs: dict[str, str] = {}
    for m in _ATTR_REGEX.finditer(attrStr):
        name: str = m.group(1)
        val: str = (
            m.group(2) if m.group(2) is not None
               else m.group(3) if m.group(3) is not None
               else m.group(4) if m.group(4) is not None
               else "True"
        )
        attrs[name] = val
    return attrs

def _findClose(src: str, tag: str, start: int) -> int:
    """
        Finds the index of the matching closing tag for a given HTML tag, handling nesting as needed.
    """

    depth = 1
    pos = start
    openTagRegex = re.compile(rf"<{re.escape(tag)}(?:\s.*?|)(/?)>", re.DOTALL)
    closeTagRegex = re.compile(rf"</{re.escape(tag)}>")

    while depth > 0 and pos < len(src):
        nextOpen = openTagRegex.search(src, pos)
        nextClose = closeTagRegex.search(src, pos)

        if nextClose is None: raise ValueError(f"Unclosed component tag <{tag}>")

        # An opening tag that is self-closing doesn't increase depth
        if nextOpen and nextOpen.start() < nextClose.start():
            isSelfClosing = nextOpen.group(1) == "/"
            if not isSelfClosing: depth += 1
            pos = nextOpen.end()
        else:
            depth -= 1
            if depth == 0: return nextClose.start()
            pos = nextClose.end()

    raise ValueError(f"Unclosed component tag <{tag}>")


def _processSlots(templateSrc: str, slots: dict[str, str]) -> str:
    """
        Replaces <slot> placeholders with provided template content.
    """
    result = templateSrc

    # Self-closing named slot (`<slot name="foo"/>`)`
    result = _NAMED_SLOT_REGEX.sub(
        lambda m: slots.get(m.group(1), ""),
        result,
    )

    # Block named slot (`<slot name="foo">default</slot>`)
    result = _BLOCK_SLOT_REGEX.sub(
        lambda m: slots.get(m.group(1), m.group(2)),
        result
    )

    # Default slot: (`<slot/>`) or (`<slot></slot>`)
    default = slots.get("default", "")
    result = re.sub(r"<slot\s*/?>", default, result)
    result = _DEFAULT_SLOT_REGEX.sub(
        lambda m: default if default else m.group(1),
        result
    )

    # Remove any orphaned slot closing tags so that they don't royally fuck the HTML structure further down the line.
    result = result.replace("</slot>", "")
    return result
#endregion ============== Functions ==============

class ComponentPreprocessor:
    registry: ComponentRegistry
    logger: Logger

    def __init__(self, registry: "ComponentRegistry"):
        self.registry = registry
        self.logger = Logger(type(self).__name__)
        self.logger.setLevel(Logger.LOG_DEBUG, g.debug)

    def process(self, src: str, context: dict[str, Any]) -> str:
        """
            Expand all component tags in `src` using `context`.
        """
        result: list[str] = []
        pos = 0

        while pos < len(src):
            m = _OPEN_TAG_REGEX.search(src, pos)
            if m is None:
                result.append(src[pos:])
                break
            
            # Extract groups. See comment on OPEN_TAG_REGEX.
            tagName = m.group(1)
            rawAttrs = m.group(2).strip()
            isSelfClosing = bool(m.group(3)) or rawAttrs.endswith("/")
            if rawAttrs.endswith("/"): rawAttrs = rawAttrs[:-1].strip()

            # self.logger.debug(f"Process tag: {tagName}|{rawAttrs}|")
            # self.logger.debug(f"Registry: {self.registry._components}")

            component = self.registry.get(tagName)
            if component is None:
                # Unknown tag. Do not transform and continue.
                result.append(src[pos:m.end()])
                pos = m.end()
                continue

            result.append(src[pos:m.start()])

            if isSelfClosing:
                # If tag is self-closing, it holds no child content. Close position is the current tag close position.
                childContent = ""
                pos = m.end()
            else:
                # If tag is not self-closing, it holds child content. Search for the tag that closes the current one.
                closePos = _findClose(src, tagName, m.end())
                childContent = src[m.end():closePos]
                closeEnd = src.index(f"</{tagName}>", closePos) + len(f"</{tagName}>")
                pos = closeEnd

            # Extracts the attributes for this tag, expanding Jinja2 templates.
            attrs = _parseTagAttributes(rawAttrs)
            resolved = {
                k: self._evalTagAttribute(v, context) 
                    if isinstance(v, str) else v  # pyright: ignore[reportUnnecessaryIsInstance]
                    for k, v in attrs.items()
            }

            # self.logger.debug("Component Attrs:", str(resolved))

            slots = self._extractSlots(childContent, context)
            rendered = self._renderComponent(component, resolved, slots, context)
            result.append(rendered)

        # self.logger.debug("Component processing:", str(result).replace("\\n", "\n"))
        return "".join(result)

    def _evalTagAttribute(self, value: str, ctx: Context) -> Any:
        """
            Evaluate attribute value as Jinja2 or Python expressions.
        """

        # self.logger.debug(f"EVALTAGATTR: |{value}|{ctx}|")

        # Process Jinja2 expression
        if "{{" in value or "{%" in value:
            env = self.registry.jinjaEnv
            try:
                assert env
                return env.from_string(value).render(**ctx)
            except Exception:
                return value

        # Process regular python expressions
        try:
            return eval(value, {"__builtins__": {}}, ctx)
        except Exception:
            return value

    def _extractSlots(self, child_content: str, ctx: Context) -> dict[str, str]:
        """
        Pull out `<template slot="name">...</template>` blocks into named slots.
        The remaining text is assigned to the "default" slot.
        
        @note Recursively process component tags within slot content.
        """
        slots: dict[str, str] = {}
        for m in _NAMED_TEMPLATE_REGEX.finditer(child_content):
            slot_src = m.group(2)
            slots[m.group(1)] = self.process(slot_src, ctx)

        remainder = _NAMED_TEMPLATE_REGEX.sub("", child_content).strip()
        if remainder: slots["default"] = self.process(remainder, ctx)

        return slots

    def _hasPendingComponentRenders(self, src: str):
        return re.search(fr"<({'|'.join(self.registry._components.keys())})(.*?)(/?)>", src, re.DOTALL) != None

    def _renderComponent(
        self,
        component: Component,
        attrs: dict[str, Any],
        slots: dict[str, str],
        parentCtx: Context,
    ) -> str:
        self.registry.collect(component)

        SENTINEL = component.params.get(REQUIRED_MARK)

        # Build a fresh context with only public parent variables, to avoid leaking internal keys like __ns__.
        ctx: Context = { k: v for (k,v) in parentCtx.items() if not k.startswith("__") }

        # Apply declared params
        for param, default in component.params.items():
            if param == REQUIRED_MARK:
                continue
            if param in attrs:
                ctx[param] = attrs[param]
            elif default is SENTINEL:
                raise ValueError(
                    f"<{component.name}> missing required param '{param}'"
                )
            else:
                ctx[param] = default

        # Extra attrs not in def
        for k, v in attrs.items():
            ctx[k] = v

        ctx["__ns__"] = component.namespace

        # Expand slots in template source
        tmpl_src = _processSlots(component.templateSrc, slots)

        # Recursively process nested component tags
        # tmpl_src = self.process(tmpl_src, ctx)
        
        # self.logger.debug(f"Preprocessed component: |||\n{tmpl_src}\n|||")

        # Render with Jinja2
        env = self.registry.jinjaEnv
        try:
            # self.logger.debug("RENDER CTX:\n", str(ctx))
            assert env
            # rendered = env.from_string(tmpl_src).render(**ctx)
            tmpl = env.from_string(tmpl_src)
            tmpl._cmp_rendering = True  # pyright: ignore[reportAttributeAccessIssue] - prevent early double-processing 
            rendered = tmpl.render(**ctx)
        except Exception as exc:
            raise RuntimeError(
                f"Error rendering <{component.name}>: {exc}"
            ) from exc

        # Stamp namespace class onto outermost elements
        # return _applyNamespace(rendered, component.namespace)
        namespacedSrc =  _applyNamespace(rendered, component.namespace)
        # self.logger.debug(f"Iteration component: |||\n{namespacedSrc}\n|||")
        if (self._hasPendingComponentRenders(namespacedSrc)): 
            return self.process(namespacedSrc, ctx)
        else:
            return namespacedSrc

#region ============== Namespace Injectors ==============
def _applyNamespace(html_src: str, ns: str) -> str:
    """
        Add `ns` class to every HTML element on the source. 
        Might smash with nested components, but that's the responsibility of the caller to figure it out, fuck them.
    """

    result: list[str] = []
    pos = 0
    depth = 0

    # print("CALLED APPLY NAMESPACE")

    for m in _ELEMENT_REGEX.finditer(html_src):
        is_close = bool(m.group(1))
        tag = m.group(2)
        attrs = m.group(3)
        is_self = bool(m.group(4))
        full = m.group(0)

        result.append(html_src[pos:m.start()])
        pos = m.end()

        # print(f"MAY APPLY NAMESPACE TO: |||{tag}|{attrs}|{is_self}|{is_close}|{depth}|||")

        if is_close:
            depth -= 1
            result.append(full)
        elif (ns not in attrs):
            result.append(_injectNamespaceClass(tag, attrs, ns, is_self))
        else:
            result.append(full) 

    result.append(html_src[pos:])
    return "".join(result)


def _injectNamespaceClass(tag: str, attrs: str, ns: str, self_close: bool) -> str:
    """
        Injects the CSS namespace into the classlist of HTML elements.
    """
    # print(f"INJECTING FOR CLASS: |||{tag}{attrs}|||")
    slash = " /" if self_close else ""
    class_re = re.compile(r'\bclass\s*=\s*"([^"]*)"', re.IGNORECASE)
    m = class_re.search(attrs)
    if m:
        new_attrs = attrs[:m.start()] + f'class="{ns} {m.group(1)}"' + attrs[m.end():]
    else:
        new_attrs = attrs + f' class="{ns}"'
    return f"<{tag}{new_attrs}{slash}>"
#endregion ============== Namespace Injectors ==============
