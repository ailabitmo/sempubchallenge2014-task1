from datetime import datetime
import re
import urllib
from django.utils.unittest.case import _TypeEqualityDict

from grab.tools import rex, text
from grab.error import DataNotFound
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD, FOAF, DCTERMS, DC

from CeurWsParser.namespaces import SWRC
from base import Parser
from CeurWsParser import config


class ProceedingsSummaryParser(Parser):
    def parse_template_main(self):
        proceedings_list = []
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        for i in range(0, len(tr), 2):
            href = tr[i].find('.//td[last()]//a[@href]')
            if href.get('href') in config.input_urls:
                proceedings = dict()
                proceedings['volume_number'] = rex.rex(href.get('href'), r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)
                proceedings['url'] = href.get('href')
                summary_match = rex.rex(
                    tr[i + 1].find('.//td[last()]').text_content(),
                    r'(.*)(\nEdited\s*by\s*:\s*)(.*)(\nSubmitted\s*by\s*:\s*)(.*)(\nPublished\s*on\s*CEUR-WS:\s*)(.*)(\nONLINE)(.*)',
                    re.I | re.M | re.S)

                proceedings['label'] = re.sub(r'\n', '', text.normalize_space(summary_match.group(1), ' \n'))
                proceedings['editors'] = re.split(r",+\s*", text.normalize_space(summary_match.group(3)))
                proceedings['submission_date'] = datetime.strptime(text.normalize_space(summary_match.group(7), ' \n'),
                                                                   '%d-%b-%Y')

                proceedings_list.append(proceedings)

        self.data['proceedings_list'] = proceedings_list

        if len(proceedings_list) == 0:
            raise DataNotFound("There is no summary information to parse!")

    def write(self):
        triples = []
        for proceedings in self.data['proceedings_list']:
            resource = URIRef(proceedings['url'])
            triples.append((resource, RDF.type, SWRC.Proceedings))
            triples.append((resource, RDFS.label, Literal(proceedings['label'], datatype=XSD.string)))
            triples.append((resource, FOAF.homepage, Literal(proceedings['url'], datatype=XSD.anyURI)))
            triples.append((
                resource,
                DCTERMS.issued,
                Literal(proceedings['submission_date'].strftime('%Y-%m-%d'), datatype=XSD.date)))
            for editor in proceedings['editors']:
                agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
                triples.append((agent, RDF.type, FOAF.Agent))
                triples.append((agent, FOAF.name, Literal(editor, datatype=XSD.string)))
                triples.append((resource, SWRC.editor, agent))
                triples.append((agent, DC.creator, resource))

        self.write_triples(triples)


class EditorAffiliationParser(Parser):
    # def __init__(self, grab, task, graph):
    #     Parser.__init__(self, grab, task, graph)
    #     self.output = open('affiliations.txt', 'a')

    def parse_template_main(self):
        # editors = '\n'.join(self.grab.tree.xpath(r'/html/body//text()[preceding::*[contains(., "Edited by")] and'
        #                                          r' following::*[contains(.,"Table of Contents") or @class="CEURTOC"]]'))
        # self.output.write("%s\n" % self.task.url)
        # self.output.write(editors.encode('utf-8'))
        # self.output.write('\n====\n')
        pass

    def write(self):
        pass