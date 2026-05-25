import rdflib

g = rdflib.Graph()
g.parse('ontology.ttl', format='turtle')

q = """
CONSTRUCT {
    ?c :contributedTo ?r .
    ?a :created ?r .
    ?s :subjectOf ?r .
    ?o :isOriginalOf ?r .
    ?t :isThumbnailOf ?r .
}
WHERE {
    ?r a :Record ;
       :contributionBy ?c ;
       :createdBy ?a ;
       :hasSubject ?s ;
       :hasOriginal ?o ;
       :hasThumbnail ?t ;
}
"""

results = g.query(q)
g += results