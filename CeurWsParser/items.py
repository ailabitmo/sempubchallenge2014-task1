import config
import urllib
from rdflib import URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, FOAF, DCTERMS, XSD

SWRC = Namespace("http://swrc.ontoware.org/ontology#")

class Model:

    def __setattr__(self, name, value):
        self.__dict__[name] = self.trim(value)
    
    def trim(self, string):
        import re
        return re.sub(r'\s{2,}|\n', '', string)

class Publication(Model):
    def save(self, graph):
        proceedings = URIRef(config.id['proceedings'] + self.volume_number)
        publication = URIRef(config.id['publication'] + urllib.quote('ceus-ws-' + self.volume_number + '-' + self.title))
        graph.add((proceedings, DCTERMS.partOf, publication))
        graph.add((publication, RDF.type, FOAF.Document))
        graph.add((publication, DCTERMS.partOf, proceedings))
        graph.add((publication, RDF.type, SWRC.InProceedings))
        graph.add((publication, RDFS.label, Literal(self.title, datatype=XSD.string)))
        graph.add((publication, FOAF.homepage, Literal(self.link, datatype=XSD.anyURI)))
