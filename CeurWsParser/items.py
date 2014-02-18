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
        elif isinstance(obj, list) and len(obj) > 0 and (isinstance(obj[0], str) or isinstance(obj[0], unicode)):
            for i in range(0, len(obj)):
                obj[i] = self.trim(obj[i])
            return obj
        else:
            return obj

class Creator(Model):
    def __init__(self, name=None):
        self.name = name

    def pretty_print(self):
        print "EDITOR NAME: ",self.name

    def save(self, graph):
        agent = URIRef(config.id['person'] + urllib.quote(self.name.encode('utf-8')))
        graph.add((agent, RDF.type, FOAF.Agent))
        graph.add((agent, FOAF.name, Literal(self.name, datatype = XSD.string)))
        return agent



class Publication(Model):
    def __init__(self, volume_number=None, title=None, link=None, creators=None):
        self.volume_number = volume_number
        self.title = title
        self.link = link
        self.creators = creators

    def pretty_print(self):
        print "PUB NAME: ", self.title
        print "PUB LINK: ", self.link
        for editor in self.creators:
            editor.pretty_print()

    def save(self, graph):
        proceedings = URIRef(config.id['proceedings'] + self.volume_number)
        publication = URIRef(config.id['publication'] + urllib.quote('ceus-ws-' + self.volume_number + '-' + self.title))
        graph.addN([
                    (proceedings, DCTERMS.hasPart, publication, ''),
                    (publication, RDF.type, FOAF.Document, ''),
                    (publication, DCTERMS.partOf, proceedings, ''),
                    (publication, RDF.type, SWRC.InProceedings, ''),
                    (publication, RDFS.label, Literal(self.title, datatype=XSD.string, ''),
                    (publication, FOAF.homepage, Literal(self.link, datatype=XSD.anyURI, ''))
                ])
        for creator in self.creators:
            agent = creator.save(graph)
            graph.add((agent, DC.creator, publication))
        return publication


class Workshop(Model):
    def __init__(self):
        self.time = []

    def save(self, graph):
        from datetime import datetime
        workshop = URIRef(config.id['workshop'] + self.proceedings.volume_number)
        proceedings = URIRef(config.id['proceedings'] + self.proceedings.volume_number)
        graph.addN([
                    (workshop, RDF.type, BIBO.Workshop, ''),
                    (workshop, RDFS.label, Literal(self.label, datatype=XSD.string), ''),
                    (proceedings, BIBO.presentedAt, workshop, '')
                ])
        if isinstance(self.time, list) and len(self.time) > 0:
            graph.addN([
                        (workshop, TIMELINE.beginsAtDateTime, Literal(self.time[0].strftime('%Y-%m-%d'), datatype=XSD.date), ''),
                        (workshop, TIMELINE.endsAtDateTime, Literal(self.time[1].strftime('%Y-%m-%d'), datatype=XSD.date), '')
                    ])
        elif isinstance(self.time, datetime):
            graph.add((workshop, TIMELINE.atDate, Literal(self.time.strftime('%Y-%m-%d'), datatype=XSD.date)))

class Proceedings(Model):
    def save(self, graph):
        proceedings = URIRef(config.id['proceedings'] + self.volume_number)
        graph.addN([(proceedings, RDF.type, SWRC.Proceedings, ''),
                    (proceedings, RDFS.label, Literal(self.label, datatype = XSD.string), ''),
                    (proceedings, FOAF.homepage, Literal(self.url, datatype = XSD.anyURI), ''),
                    (proceedings, DCTERMS.issued, Literal(self.submittion_date.strftime('%Y-%m-%d'), datatype=XSD.date), '')])
        for editor in self.editors:
            agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
            graph.addN([(agent, RDF.type, FOAF.Agent, ''), 
                        (agent, FOAF.name, Literal(editor, datatype = XSD.string), ''),
                        (proceedings, SWRC.editor, agent, ''), 
                        (agent, DC.creator, proceedings, '')
                    ])
