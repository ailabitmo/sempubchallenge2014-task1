from datetime import datetime
import re

from grab.tools import rex
from grab.error import DataNotFound
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

from base import Parser
from CeurWsParser import config
from CeurWsParser.namespaces import BIBO, TIMELINE


class WorkshopSummaryParser(Parser):
    def parse_template_main(self):
        workshops = []
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        for i in range(0, len(tr), 2):
            href = tr[i].find('.//td[last()]//a[@href]')
            if href.get('href') in config.input_urls:
                workshop = {}
                summary = tr[i + 1].find('.//td[last()]').text_content()
                title = rex.rex(summary, r'(.*)Edited\s*by.*', re.I | re.S).group(1)

                workshop['volume_number'] = rex.rex(href.get('href'), r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)
                workshop['label'] = href.text
                workshop['url'] = href.get('href')
                workshop['time'] = []

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
                        workshop['time'] = datetime.strptime(
                            time_match_1.group(1) + "-" + time_match_1.group(2) + "-" + time_match_1.group(3),
                            '%B-%d-%Y')
                    except:
                        pass
                elif time_match_2:
                    try:
                        workshop['time'] = [
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
                        workshop['time'] = [
                            datetime.strptime(
                                time_match_3.group(1) + "-" + time_match_3.group(2) + "-" + time_match_3.group(5),
                                '%B-%d-%Y'),
                            datetime.strptime(
                                time_match_3.group(3) + "-" + time_match_3.group(4) + "-" + time_match_3.group(5),
                                '%B-%d-%Y')
                        ]
                    except:
                        pass

                workshops.append(workshop)

        self.data['workshops'] = workshops

        if len(workshops) == 0:
            raise DataNotFound("There is no summary information to parse!")

    def write(self):
        triples = []
        for workshop in self.data['workshops']:
            resource = URIRef(config.id['workshop'] + workshop['volume_number'])
            proceedings = URIRef(config.id['proceedings'] + workshop['volume_number'])
            triples.append((resource, RDF.type, BIBO.Workshop))
            triples.append((resource, RDFS.label, Literal(workshop['label'], datatype=XSD.string)))
            triples.append((proceedings, BIBO.presentedAt, resource))

            if isinstance(workshop['time'], list) and len(workshop['time']) > 0:
                triples.append((
                    resource,
                    TIMELINE.beginsAtDateTime,
                    Literal(workshop['time'][0].strftime('%Y-%m-%d'), datatype=XSD.date)))
                triples.append((
                    resource,
                    TIMELINE.endsAtDateTime,
                    Literal(workshop['time'][1].strftime('%Y-%m-%d'), datatype=XSD.date)))
            elif isinstance(workshop['time'], datetime):
                triples.append((
                    resource,
                    TIMELINE.atDate,
                    Literal(workshop['time'].strftime('%Y-%m-%d'), datatype=XSD.date)))

        self.write_triples(triples)


class WorkshopPageParser(Parser):
    def write(self):
        #print self.data['volume_number']
        pass

    def parse_template_main(self):
        #self.data['volume_number'] = rex.rex(self.task.url, r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)
        pass