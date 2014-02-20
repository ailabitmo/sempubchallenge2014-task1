from datetime import datetime
import re
import urllib

from grab.tools import rex, text
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD, FOAF, DCTERMS, DC

from CeurWsParser.namespaces import SWRC
from base import Parser
from CeurWsParser import config


class ProceedingsSummaryParser(Parser):
    def parse(self):
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        for i in range(0, len(tr), 2):
            href = tr[i].find('.//td[last()]//a[@href]')
            if href.get('href') in config.input_urls:
                self.data['volume_number'] = rex.rex(href.get('href'), r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)
                self.data['url'] = href.get('href')
                summary_match = rex.rex(
                    tr[i + 1].find('.//td[last()]').text_content(),
                    r'(.*)(\nEdited\s*by\s*:\s*)(.*)(\nSubmitted\s*by\s*:\s*)(.*)(\nPublished\s*on\s*CEUR-WS:\s*)(.*)(\nONLINE)(.*)',
                    re.I | re.M | re.S)

                self.data['label'] = re.sub(r'\n', '', summary_match.group(1))
                self.data['editors'] = re.split(r",+\s*", summary_match.group(3))
                self.data['submission_date'] = datetime.strptime(text.normalize_space(summary_match.group(7), ' \n'),
                                                                 '%d-%b-%Y')

    def write(self):
        triples = []
        proceedings = URIRef(config.id['proceedings'] + self.data['volume_number'])
        triples.append((proceedings, RDF.type, SWRC.Proceedings))
        triples.append((proceedings, RDFS.label, Literal(self.data['label'], datatype=XSD.string)))
        triples.append((proceedings, FOAF.homepage, Literal(self.data['url'], datatype=XSD.anyURI)))
        triples.append((
            proceedings,
            DCTERMS.issued,
            Literal(self.data['submission_date'].strftime('%Y-%m-%d'), datatype=XSD.date)))
        for editor in self.data['editors']:
            agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
            triples.append((agent, RDF.type, FOAF.Agent))
            triples.append((agent, FOAF.name, Literal(editor, datatype=XSD.string)))
            triples.append((proceedings, SWRC.editor, agent))
            triples.append((agent, DC.creator, proceedings))

        self.write_triples(triples)