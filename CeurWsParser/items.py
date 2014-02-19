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


class Workshop(Model):
    def __init__(self, volume_number):
        self.time = []
        self.volume_number = volume_number
        self.uri = URIRef(config.id['workshop'] + self.volume_number)

    def save(self, graph):
        from datetime import datetime

        proceedings = URIRef(config.id['proceedings'] + self.volume_number)
        graph.add((self.uri, RDF.type, BIBO.Workshop))
        graph.add((self.uri, RDFS.label, Literal(self.label, datatype=XSD.string)))
        graph.add((proceedings, BIBO.presentedAt, self.uri))
        if isinstance(self.time, list) and len(self.time) > 0:
            graph.add(
                (self.uri, TIMELINE.beginsAtDateTime, Literal(self.time[0].strftime('%Y-%m-%d'), datatype=XSD.date)))
            graph.add(
                (self.uri, TIMELINE.endsAtDateTime, Literal(self.time[1].strftime('%Y-%m-%d'), datatype=XSD.date)))
        elif isinstance(self.time, datetime):
            graph.add((self.uri, TIMELINE.atDate, Literal(self.time.strftime('%Y-%m-%d'), datatype=XSD.date)))


class Proceedings(Model):
    def __init__(self, volume_number):
        self.volume_number = volume_number
        self.uri = URIRef(config.id['proceedings'] + self.volume_number)

    def save(self, graph):
        graph.add((self.uri, RDF.type, SWRC.Proceedings))
        graph.add((self.uri, RDFS.label, Literal(self.label, datatype=XSD.string)))
        graph.add((self.uri, FOAF.homepage, Literal(self.url, datatype=XSD.anyURI)))
        graph.add((self.uri, DCTERMS.issued, Literal(self.submission_date.strftime('%Y-%m-%d'), datatype=XSD.date)))
        for editor in self.editors:
            agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
            graph.add((agent, RDF.type, FOAF.Agent))
            graph.add((agent, FOAF.name, Literal(editor, datatype=XSD.string)))
            graph.add((self.uri, SWRC.editor, agent))
            graph.add((agent, DC.creator, self.uri))
