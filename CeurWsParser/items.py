import config
import urllib
from rdflib import URIRef, Literal, Namespace, BNode
from rdflib.namespace import RDF, RDFS, FOAF, DC, DCTERMS, XSD

SWRC = Namespace("http://swrc.ontoware.org/ontology#")
EVENT = Namespace("http://purl.org/NET/c4dm/event.owl#")
TIMELINE = Namespace("http://purl.org/NET/c4dm/timeline.owl#")
BIBO = Namespace("http://purl.org/ontology/bibo/")

class Model:

    def __setattr__(self, name, value):
        self.__dict__[name] = self.trim(value)
    
    def trim(self, obj):
        import re
        if isinstance(obj, str) or isinstance(obj, unicode):
            return re.sub(r'\s{2,}|\n', '', obj)
        else:
            return obj

class Publication(Model):
    def save(self, graph):
        proceedings = URIRef(config.id['proceedings'] + self.volume_number)
        publication = URIRef(config.id['publication'] + urllib.quote('ceus-ws-' + self.volume_number + '-' + self.title))
        graph.add((proceedings, DCTERMS.hasPart, publication))
        graph.add((publication, RDF.type, FOAF.Document))
        graph.add((publication, DCTERMS.partOf, proceedings))
        graph.add((publication, RDF.type, SWRC.InProceedings))
        graph.add((publication, RDFS.label, Literal(self.title, datatype=XSD.string)))
        graph.add((publication, FOAF.homepage, Literal(self.link, datatype=XSD.anyURI)))

class Workshop(Model):
    def __init__(self):
        self.time = []

    def save(self, graph):
        from datetime import datetime
        workshop = URIRef(config.id['workshop'] + self.proceedings.volume_number)
        proceedings = URIRef(config.id['proceedings'] + self.proceedings.volume_number)
        graph.add((workshop, RDF.type, BIBO.Workshop))
        graph.add((workshop, RDFS.label, Literal(self.label, datatype=XSD.string)))
        graph.add((proceedings, BIBO.presentedAt, workshop))
        if isinstance(self.time, list) and len(self.time) > 0:
            graph.add((workshop, TIMELINE.beginsAtDateTime, Literal(self.time[0].strftime('%Y-%m-%d'), datatype=XSD.date)))
            graph.add((workshop, TIMELINE.endsAtDateTime, Literal(self.time[1].strftime('%Y-%m-%d'), datatype=XSD.date)))
        elif isinstance(self.time, datetime):
            graph.add((workshop, TIMELINE.atDate, Literal(self.time.strftime('%Y-%m-%d'), datatype=XSD.date)))

class Proceedings(Model):
    def save(self, graph):
        proceedings = URIRef(config.id['proceedings'] + self.volume_number)
        graph.add((proceedings, RDF.type, SWRC.Proceedings))
        graph.add((proceedings, RDFS.label, Literal(self.label, datatype = XSD.string)))
        graph.add((proceedings, FOAF.homepage, Literal(self.url, datatype = XSD.anyURI)))
        graph.add((proceedings, DCTERMS.issued, Literal(self.submittion_date.strftime('%Y-%m-%d'), datatype=XSD.date)))
        for editor in self.editors:
            agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
            graph.add((agent, RDF.type, FOAF.Agent))
            graph.add((agent, FOAF.name, Literal(editor, datatype = XSD.string)))
            graph.add((proceedings, SWRC.editor, agent))
            graph.add((agent, DC.creator, proceedings))
