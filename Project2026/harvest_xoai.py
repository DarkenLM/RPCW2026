import json
import requests
import xml.etree.ElementTree as ET
from collections import defaultdict

endpoint_url = "https://repositorium.uminho.pt/oai/request"
metadata_prefix = "xoai" # Conisderar xoai, dim, rioxx
XOAI = "{http://www.lyncode.com/xoai}"

def request_data(endpoint_url, params):
    response = requests.get(endpoint_url, params=params)
    response.raise_for_status()
    return response.content
    
def get_setSpec(setsTree, name):
    sets = setsTree.findall(".//{http://www.openarchives.org/OAI/2.0/}set")
    for s in sets:
        setSpec = s.find("{http://www.openarchives.org/OAI/2.0/}setSpec").text
        setName = s.find("{http://www.openarchives.org/OAI/2.0/}setName").text
        if setName == name:
            return setSpec
        
def safe_findall(element, path):
    if element is None:
        return None
    found = element.findall(path)
    return [f.text for f in found] if len(found) > 1 else found[0].text if found else None

# ListSets
getSets = { "verb": "ListSets" }
sets = request_data(endpoint_url, params=getSets)
setsTree = ET.fromstring(sets)

# ListRecords (com setSpec do Departamento de Informática)
setSpec = get_setSpec(setsTree, "Departamento de Informática")
recordsList = []
getRecords = {
    "verb": "ListRecords",
    "metadataPrefix": metadata_prefix,
    "set": setSpec
}
records = request_data(endpoint_url, params=getRecords)
recordsTree = ET.fromstring(records)
resumptionToken = recordsTree.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")

i = 0
while resumptionToken is not None:
    recs = recordsTree.findall(".//{http://www.openarchives.org/OAI/2.0/}record")
    for r in recs:
        rec = defaultdict(list)
        metadados = r.find(".//{http://www.openarchives.org/OAI/2.0/}metadata")
         
        identifiers_uri = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='identifier']/{XOAI}element[@name='uri']/{XOAI}element")
        identifiers_tid = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='identifier']/{XOAI}element[@name='tid']/{XOAI}element")
        title = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='title']/{XOAI}element")
        type = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='type']/{XOAI}element")
        contributors = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='contributor']")
        description = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='description']/{XOAI}element[@name='abstract']/{XOAI}element")
        subject = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='subject']/{XOAI}element")
        language = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='language']/{XOAI}element/{XOAI}element")
        date = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='date']")
        grade = metadados[0].find(f"{XOAI}element[@name='sdum']/{XOAI}element[@name='degree']/{XOAI}element[@name='grade']/{XOAI}element")
        rights = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='rights']/{XOAI}element")
        rights_uri = metadados[0].find(f"{XOAI}element[@name='dc']/{XOAI}element[@name='rights']/{XOAI}element[@name='uri']/{XOAI}element")

        bundles = metadados[0].find(f"{XOAI}element[@name='bundles']")

        rec["uri"] = safe_findall(identifiers_uri, f"{XOAI}field[@name='value']")
        rec["tid"] = safe_findall(identifiers_tid, f"{XOAI}field[@name='value']")
        rec["description"] = safe_findall(description, f"{XOAI}field[@name='value']")

        for cType in contributors:
            cTypeName = cType.attrib['name']
            cTypeValues = cType.find(f"{XOAI}element")
            rec[cTypeName] = safe_findall(cTypeValues, f"{XOAI}field[@name='value']")

        for dateType in date:
            dateTypeName = dateType.attrib['name']
            dateTypeValues = dateType.find(f"{XOAI}element")
            rec[dateTypeName] = safe_findall(dateTypeValues, f"{XOAI}field[@name='value']")

        rec["title"] = safe_findall(title, f"{XOAI}field[@name='value']")
        rec["type"] = safe_findall(type, f"{XOAI}field[@name='value']")
        rec["subject"] = safe_findall(subject, f"{XOAI}field[@name='value']")
        rec["language"] = safe_findall(language, f"{XOAI}field[@name='value']")
        rec["grade"] = safe_findall(grade, f"{XOAI}field[@name='value']")
        rec["rights"] = safe_findall(rights, f"{XOAI}field[@name='value']")
        rec["rights_uri"] = safe_findall(rights_uri, f"{XOAI}field[@name='value']")

        for b in bundles:
            obj = {}
            name = b.find(f"{XOAI}field[@name='name']").text
            bitstreams = b.find(f"{XOAI}element[@name='bitstreams']")
            for bs in bitstreams:
                fields = bs.findall(f"{XOAI}field")
                for f in fields:
                    obj[f.attrib['name']] = f.text
            rec[name] = obj

        recordsList.append(rec)

    newGetRecords = {
        "verb": "ListRecords",
        "resumptionToken": resumptionToken.text
    }
    records = request_data(endpoint_url, params=newGetRecords)
    recordsTree = ET.fromstring(records)
    resumptionToken = recordsTree.find(".//{http://www.openarchives.org/OAI/2.0/}resumptionToken")

    i += 1
    print(f"Iterated page {i}")
    # break

# Guardar resultados em JSON
with open("records_xoai.json", "w", encoding="utf-8") as f:
    json.dump(recordsList, f, ensure_ascii=False, indent=2)