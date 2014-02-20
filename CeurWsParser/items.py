import urllib

from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, FOAF, DC, DCTERMS, XSD

import config


SWRC = Namespace("http://swrc.ontoware.org/ontology#")
EVENT = Namespace("http://purl.org/NET/c4dm/event.owl#")
TIMELINE = Namespace("http://purl.org/NET/c4dm/timeline.owl#")
BIBO = Namespace("http://purl.org/ontology/bibo/")


class Model:
    def __setattr__(self, name, value):
        self.__dict__[name] = self.trim(value)

    def trim(self, obj):
        import re

        if obj is str or obj is unicode:
            return re.sub(r'\s{2,}|\n', '', obj)
        elif obj is list and len(obj) > 0 and (obj[0] is str or obj[0] is unicode):
            for i in range(0, len(obj)):
                obj[i] = self.trim(obj[i])
            return obj
        else:
            return obj


class Creator(Model):
    def __init__(self, name=None):
        self.name = name

    def pretty_print(self):
        print "EDITOR NAME: ", self.name

    def save(self, graph):
        agent = URIRef(config.id['person'] + urllib.quote(self.name.encode('utf-8')))
        graph.add((agent, RDF.type, FOAF.Agent))
        graph.add((agent, FOAF.name, Literal(self.name, datatype=XSD.string)))
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
        publication = URIRef(
            config.id['publication'] + urllib.quote('ceus-ws-' + self.volume_number + '-' + self.title))
        graph.add((proceedings, DCTERMS.hasPart, publication))
        graph.add((publication, RDF.type, FOAF.Document))
        graph.add((publication, DCTERMS.partOf, proceedings))
        graph.add((publication, RDF.type, SWRC.InProceedings))
        graph.add((publication, RDFS.label, Literal(self.title, datatype=XSD.string)))
        graph.add((publication, FOAF.homepage, Literal(self.link, datatype=XSD.anyURI)))
        for creator in self.creators:
            agent = creator.save(graph)
            graph.add((agent, DC.creator, publication))
        return publication