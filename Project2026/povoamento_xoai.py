import re
import json
import hashlib
 
with open("records_xoai.json", "r", encoding="utf-8") as f:
    recs = json.load(f)
 
with open("base.ttl", "r", encoding="utf-8") as f:
    ontology_base = f.read()
 
def clean_id(raw):
    return re.sub(r"[^\w]+", "_", raw).strip("_")
 
def normalize_name(raw):
    if "," in raw:
        return " ".join(reversed(raw.split(", ")))
    return raw
 
def normalize_date(raw):
    if not raw:
        date = ""
    elif re.fullmatch(r"^\d{4}$", raw):
        date = f"{raw}-01-01T00:00:00Z"
    elif re.fullmatch(r"^\d{4}-\d{2}$", raw):
        date = f"{raw}-01T00:00:00Z"
    elif re.fullmatch(r"^\d{4}-\d{2}-\d{2}$", raw):
        date = f"{raw}T00:00:00Z"
    else:
        date = raw
    return date
 
def escape_string(value):
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("\n", "\\n")
    return value
 
def turtle_literal(value):
    return f'"{escape_string(value)}"'
 
def check_unique_id(base, seen_ids):
    if base not in seen_ids:
        seen_ids.add(base)
        return base
    suffix = hashlib.md5(base.encode()).hexdigest()[:6]
    return f"{base}_{suffix}"
 
def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [v for v in value if v is not None]
    return [value]

 
subjectsSet = set()
peopleSet = set()
seen_orig_ids = set()
seen_thumb_ids = set()
 
subjects = ""
people = ""
records = ""
originals = ""
thumbnails = ""
skipped = []
 

for r in recs:
    tid_raw = r.get("tid")
    if tid_raw:
        recID = clean_id(as_list(tid_raw)[0])
    else:
        recID = clean_id(r["uri"].split("/", 3)[-1])
 
    title    = r.get("title")
    type_    = r.get("type")
    language = r.get("language")
    rights   = r.get("rights")
 
    desc_list = as_list(r.get("description"))
 
    if not (title and type_ and language and rights and desc_list):
        skipped.append(recID)
        continue
 
    raw_authors  = as_list(r.get("author"))
    raw_advisors = as_list(r.get("advisor"))
    authors  = [normalize_name(a) for a in raw_authors]
    advisors = [normalize_name(a) for a in raw_advisors]
 
    recSubjects = [clean_id(s) for s in as_list(r.get("subject")) if clean_id(s)]
 
    grade      = r.get("grade")        
    rights_uri = r.get("rights_uri")   
 
    issued_dt    = normalize_date(r.get("issued", ""))
    available_dt = normalize_date(r.get("available", ""))
    accession_dt = normalize_date(r.get("accessioned", ""))
    submitted_dt = normalize_date(r.get("submitted", ""))
 
    orig  = r.get("ORIGINAL") or {}
    thumb = r.get("THUMBNAIL") or {}
 
    record_predicates    = []
    original_predicates  = []
    thumbnail_predicates = []
 
    record_predicates.append(f":title {turtle_literal(title)}")
    record_predicates.append(f":type {turtle_literal(type_)}")
    record_predicates.append(f":description {', '.join(turtle_literal(d) for d in desc_list)}")
    record_predicates.append(f":language {turtle_literal(language)}")
    record_predicates.append(f":rights {turtle_literal(rights)}")
 
    if authors:
        author_ids = [clean_id(a) for a in authors]
        peopleSet.update(zip(author_ids, authors))
        record_predicates.append(f":createdBy {', '.join(f':{i}' for i in author_ids)}")
    if advisors:
        advisor_ids = [clean_id(a) for a in advisors]
        peopleSet.update(zip(advisor_ids, advisors))
        record_predicates.append(f":contributionBy {', '.join(f':{i}' for i in advisor_ids)}")
    if recSubjects:
        subjectsSet.update(recSubjects)
        record_predicates.append(f":hasSubject {', '.join(f':{s}' for s in recSubjects)}")
    if issued_dt:
        record_predicates.append(f':issuedDate "{issued_dt}"^^xsd:dateTime')
    if available_dt:
        record_predicates.append(f':availableDate "{available_dt}"^^xsd:dateTime')
    if accession_dt:
        record_predicates.append(f':accessionedDate "{accession_dt}"^^xsd:dateTime')
    if submitted_dt:
        record_predicates.append(f':submittedDate "{submitted_dt}"^^xsd:dateTime')
    if grade:
        record_predicates.append(f":grade {turtle_literal(grade)}")
    if rights_uri:
        record_predicates.append(f":rightsURI {turtle_literal(rights_uri)}")
 
    # ORIGINAL
    orig_name = orig.get("name")
    if orig_name:
        origName = check_unique_id(clean_id(orig_name), seen_orig_ids)
        record_predicates.append(f":hasOriginal :{origName}")
        original_predicates.append(f":name {turtle_literal(orig_name)}")
        if orig.get("originalName"):
            original_predicates.append(f":originalName {turtle_literal(orig['originalName'])}")
        if orig.get("description"):
            original_predicates.append(f":description {turtle_literal(orig['description'])}")
        if orig.get("format"):
            original_predicates.append(f":format {turtle_literal(orig['format'])}")
        if orig.get("url"):
            original_predicates.append(f":url {turtle_literal(orig['url'])}")
    else:
        origName = f"orig_{recID}"
        record_predicates.append(f":hasOriginal :{origName}")
 
    # THUMBNAIL
    thumb_name = thumb.get("name")
    if thumb_name:
        thumbName = check_unique_id(clean_id(thumb_name), seen_thumb_ids)
        record_predicates.append(f":hasThumbnail :{thumbName}")
        thumbnail_predicates.append(f":name {turtle_literal(thumb_name)}")
        if thumb.get("description"):
            thumbnail_predicates.append(f":description {turtle_literal(thumb['description'])}")
        if thumb.get("format"):
            thumbnail_predicates.append(f":format {turtle_literal(thumb['format'])}")
        if thumb.get("url"):
            thumbnail_predicates.append(f":url {turtle_literal(thumb['url'])}")
    else:
        thumbName = f"thumb_{recID}"
        record_predicates.append(f":hasThumbnail :{thumbName}")
 
    indent = "\n\t"
    records   += f":{recID} a :Record ;\n\t" + f" ;{indent}".join(record_predicates) + " .\n\n"
    originals  += (f":{origName} a :Original ;\n\t"  + f" ;{indent}".join(original_predicates)  + " .\n\n"
                   if original_predicates else f":{origName} a :Original .\n\n")
    thumbnails += (f":{thumbName} a :Thumbnail ;\n\t" + f" ;{indent}".join(thumbnail_predicates) + " .\n\n"
                   if thumbnail_predicates else f":{thumbName} a :Thumbnail .\n\n")
 
 
# PEOPLE & SUBJECTS
for p in peopleSet:
    pid, name = p
    people += f":{pid} a :Person ;\n\t:name {turtle_literal(name)} .\n"
 
for s in subjectsSet:
    subjects += f":{s} a :Subject .\n"
 
 
genOntology = (
    ontology_base
    .replace("###@@@People@@@",     people)
    .replace("###@@@Subjects@@@",   subjects)
    .replace("###@@@Records@@@",    records)
    .replace("###@@@Originals@@@",  originals)
    .replace("###@@@Thumbnails@@@", thumbnails)
)
 
with open("ontology.ttl", "w", encoding="utf-8") as f:
    f.write(genOntology)
