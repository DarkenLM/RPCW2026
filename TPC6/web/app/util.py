import re
from datetime import datetime
from flask import render_template
from types import SimpleNamespace as sn
from .types import RDFRef

# Required because Jinja2 uses Python, until it fucking doesn't.
sd = lambda s: sn(**s)
__RENDER_UTIL = sd({
    "map": map,
    "filter": filter,
    "print": print,
    "isinstance": isinstance,
    "filters": sd({
        "nonEmpty": lambda e: len(e) > 0,
        "nonEmptyEntry": lambda e: len(e[1]) > 0,
    }),
    "types": sd({
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
        "list": list,
        "dict": dict,
        "tuple": tuple,
        "RDFRef": RDFRef
    }),
    "pluralize": lambda s, p = False: (s[1] if p else s[0]) if (not isinstance(s, str)) else (s + "s" if p else s),
    "getGlobal": lambda v, d = None: vars().get(v) if v in vars() else globals().get(v) if v in globals() else d 
})

PAGE = lambda p: f"pages/{p}.html"
TEMPLATE = lambda p: f"{p}.html.j2"
def RENDER(t, b = {}): 
    return render_template(TEMPLATE(t), **{ "data": datetime.now().isoformat(), "util": __RENDER_UTIL, **b })

def toSplitProperCase(s: str):
    parts = re.split(r"([A-Z])", s)
    nparts = []
    acc = ""
    for i in range(0, len(parts)):
        part = parts[i]
        if (len(part) == 1): 
            acc += part
            continue
        else:
            if (acc):
                nparts.append(acc + part)
                acc = ""
            else:
                nparts.append(part[0].upper() + part[1:])

    if (len(acc) > 0): nparts.append(acc)
    return " ".join(nparts)

def pickFromObj(obj, *props):
    return { k:obj[k] for k in props if k in obj }

def pickFromObjAllExcept(obj, *props):
    return { k:obj[k] for k in obj.keys() if k not in props }