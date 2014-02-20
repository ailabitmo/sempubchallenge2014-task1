from datetime import datetime
import re

from grab.tools import rex
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

from base import Parser
from CeurWsParser import config
from CeurWsParser.namespaces import BIBO, TIMELINE


class WorkshopSummaryParser(Parser):
    def parse(self):
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        for i in range(0, len(tr), 2):
            url = tr[i].find('.//td[last()]//a[@href]').get('href')
            if url in config.input_urls:
                href = tr[i].find('.//td[last()]//a[@href]')
                summary = tr[i + 1].find('.//td[last()]').text_content()
                title = rex.rex(summary, r'(.*)Edited\s*by.*', re.I | re.S).group(1)

                self.data['volume_number'] = rex.rex(href.get('href'), r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)
                self.data['label'] = href.text
                self.data['url'] = href.get('href')

                time_match_1 = rex.rex(title, r'.*,\s*([a-zA-Z]+)[,\s]*(\d{1,2})[\w\s]*,\s*(\d{4})', re.I,
                                       default=None)
                time_match_2 = rex.rex(title, r'.*,\s*([a-zA-Z]+)[,\s]*(\d{1,2})[\w\s]*-\s*(\d{1,2})[\w\s,]*(\d{4})',
                                       re.I,
                                       default=None)
                time_match_3 = rex.rex(title, r'.*,\s*([a-zA-Z]+)\s*(\d+)\s*-\s*([a-zA-Z]+)\s*(\d+)\s*,\s*(\d{4})',
                                       re.I,
                                       default=None)
                if time_match_1:
                    try:
                        self.data['time'] = datetime.strptime(
                            time_match_1.group(1) + "-" + time_match_1.group(2) + "-" + time_match_1.group(3),
                            '%B-%d-%Y')
                    except:
                        pass
                elif time_match_2:
                    try:
                        self.data['time'] = [
                            datetime.strptime(
                                time_match_2.group(1) + "-" + time_match_2.group(2) + "-" + time_match_2.group(4),
                                '%B-%d-%Y'),
                            datetime.strptime(
                                time_match_2.group(1) + "-" + time_match_2.group(3) + "-" + time_match_2.group(4),
                                '%B-%d-%Y')
                        ]
                    except:
                        pass
                elif time_match_3:
                    try:
                        self.data['time'] = [
                            datetime.strptime(
                                time_match_3.group(1) + "-" + time_match_3.group(2) + "-" + time_match_3.group(5),
                                '%B-%d-%Y'),
                            datetime.strptime(
                                time_match_3.group(3) + "-" + time_match_3.group(4) + "-" + time_match_3.group(5),
                                '%B-%d-%Y')
                        ]
                    except:
                        pass

    def write(self):
        triples = []
        workshop = URIRef(config.id['workshop'] + self.data['volume_number'])
        proceedings = URIRef(config.id['proceedings'] + self.data['volume_number'])
        triples.append((workshop, RDF.type, BIBO.Workshop))
        triples.append((workshop, RDFS.label, Literal(self.data['label'], datatype=XSD.string)))
        triples.append((proceedings, BIBO.presentedAt, workshop))

        if self.data['time'] is list and len(self.data['time']) > 0:
            triples.append((
                workshop,
                TIMELINE.beginsAtDateTime,
                Literal(self.data['time'][0].strftime('%Y-%m-%d'), datatype=XSD.date)))
            triples.append((
                workshop,
                TIMELINE.endsAtDateTime,
                Literal(self.data['time'][1].strftime('%Y-%m-%d'), datatype=XSD.date)))
        elif self.data['time'] is datetime:
            triples.append((
                workshop,
                TIMELINE.atDate,
                Literal(self.data['time'].strftime('%Y-%m-%d'), datatype=XSD.date)))

        self.write_triples(triples)

class WorkshopPageParser(Parser):
    pass