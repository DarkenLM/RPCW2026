from typing import Any, Callable
import re
from datetime import datetime
from flask import render_template
from types import SimpleNamespace as sn
from .types import RDFRef
from app.gvars import g

def pickFromObj(obj, *props):
    return { k:obj[k] for k in props if k in obj }

def pickFromObjAllExcept(obj, *props):
    return { k:obj[k] for k in obj.keys() if k not in props }

def sdToDict(ns: sn):
    return { k:(sdToDict(v) if isinstance(v, sn) else v) for (k,v) in vars(ns).items() }


def _toNQ(s):
    if (type(s) == str): return s.replace("\\", "\\\\").replace("'", "\\'")
    elif (type(s) == list): return [_toNQ(v) for v in s]
    elif (type(s) == dict): return { _toNQ(k):_toNQ(s) for (k,v) in s.items()  }
    return s

# Required because Jinja2 uses Python, until it fucking doesn't.
sd: Callable[[dict[str, Any]], sn] = lambda s: sn(**s)  # pyright: ignore[reportExplicitAny]
__RENDER_UTIL = sd({
    "isinstance": isinstance,
    "isdict": lambda o: type(o) == dict,
    "islist": lambda o: type(o) == list,
    "issn": lambda o: type(o) == sn,
    "range": range,
    "len": len,
    "max": max,
    "min": min,
    "tonq": _toNQ,
    "type": type,
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
    "pickFromObj": pickFromObj,
    "pickFromObjAllExcept": pickFromObjAllExcept,
    "sdToDict": sdToDict,
    "replaceInObj": lambda obj, **props: { **obj, **props }
})

PAGE: Callable[[str], str] = lambda p: f"pages/{p}.html"
TEMPLATE: Callable[[str], str] = lambda p: f"{p}.html.j2"
def RENDER(t: str, b: dict[str, Any] = {}):   # pyright: ignore[reportCallInDefaultInitializer, reportExplicitAny]
    return render_template(
        TEMPLATE(t), 
        **{ 
            "appName": g.appName,
            "data": datetime.now().isoformat(), 
            "util": __RENDER_UTIL, 
            "string_map__": { "string_map__": "INTERNAL NAME" },
            **b
        }
    )

def toSplitProperCase(s: str):
    parts: list[str] = re.split(r"([A-Z])", s)
    nparts: list[str] = []
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
