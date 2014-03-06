from datetime import datetime
import re
import urllib

from grab.tools import rex
from grab.error import DataNotFound
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

from base import Parser
from CeurWsParser import config
from CeurWsParser.parsers import utils
from CeurWsParser.namespaces import BIBO, TIMELINE, SWC, SWRC, SKOS


def extract_volume_number(url):
    return rex.rex(url, r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)


def extract_year(string):
    return '20' + string.strip()[-2:]


def create_workshop_uri(volume_number):
    return URIRef(config.id['workshop'] + volume_number)


def tonumber(string):
    if isinstance(string, basestring):
        if string.lower() == 'first':
            return 1
        elif string.lower() == 'second':
            return 2
        elif string.lower() == 'third':
            return 3
        elif string.lower() == 'forth' or string.lower() == 'fourth':
            return 4
        elif string.lower() == 'fifth':
            return 5
    return string


class WorkshopSummaryParser(Parser):
    def __init__(self, grab, task, graph):
        Parser.__init__(self, grab, task, graph, failonerror=True)

    def parse_template_main(self):
        workshops = []
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        for i in range(0, len(tr), 2):
            href = tr[i].find('.//td[last()]//a[@href]')
            if href.get('href') in config.input_urls or len(config.input_urls) == 1:
                workshop = {}
                summary = tr[i + 1].find('.//td[last()]').text_content()
                try:
                    title = rex.rex(summary, r'(.*)Edited\s*by.*', re.I | re.S).group(1)
                except DataNotFound as dnf:
                    print '[WORKSHOP %s] Summary information not found!' % href.get('href')
                    raise dnf

                workshop['volume_number'] = extract_volume_number(href.get('href'))
                workshop['label'] = href.text.replace('.', '')
                workshop['url'] = href.get('href')
                workshop['time'] = utils.parse_date(title)
                try:
                    workshop['edition'] = tonumber(
                        rex.rex(title,
                                r'.*Proceedings(\s*of)?(\s*the)?\s*(\d{1,}|first|second|third|forth|fourth|fifth)[thrd]*'
                                r'.*Workshop.*',
                                re.I, default=None).group(3))
                except:
                    #'edition' property is optional
                    pass
                workshops.append(workshop)

        self.data['workshops'] = workshops

        if len(workshops) == 0:
            raise DataNotFound("There is no summary information to parse!")

    def write(self):
        triples = []
        for workshop in self.data['workshops']:
            resource = create_workshop_uri(workshop['volume_number'])
            proceedings = URIRef(workshop['url'])
            triples.append((resource, RDF.type, BIBO.Workshop))
            triples.append((resource, RDFS.label, Literal(workshop['label'], datatype=XSD.string)))
            triples.append((proceedings, BIBO.presentedAt, resource))
            if 'edition' in workshop:
                triples.append((resource, SWRC.edition, Literal(workshop['edition'], datatype=XSD.integer)))

            if workshop['time'] and len(workshop['time']) > 1:
                triples.append((
                    resource,
                    TIMELINE.beginsAtDateTime,
                    Literal(workshop['time'][0].strftime('%Y-%m-%d'), datatype=XSD.date)))
                triples.append((
                    resource,
                    TIMELINE.endsAtDateTime,
                    Literal(workshop['time'][1].strftime('%Y-%m-%d'), datatype=XSD.date)))
            elif workshop['time'] and len(workshop['time']) > 0:
                triples.append((
                    resource,
                    TIMELINE.atDate,
                    Literal(workshop['time'][0].strftime('%Y-%m-%d'), datatype=XSD.date)))
        self.write_triples(triples)


class WorkshopRelationsParser(Parser):
    """
    Should parser the index page before WorkshopSummaryParser parser, because this parser updates config.input_urls.
    """
    def parse_template_main(self):
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        self.data['workshops'] = []
        for i in range(0, len(tr), 2):
            workshop_url = tr[i].find('.//td[last()]//a[@href]').get('href')
            if workshop_url in config.input_urls or len(config.input_urls) == 1:
                related = []
                for a in tr[i + 1].findall(".//td[1]//a[@href]"):
                    if len(a.get('href')) > 1:
                        related.append(a.get('href')[5:])
                workshop = {
                    'volume_number': extract_volume_number(workshop_url),
                    'related': related
                }
                self.data['workshops'].append(workshop)

    def write(self):
        triples = []
        for workshop in self.data['workshops']:
            if len(workshop['related']) > 0:
                resource = create_workshop_uri(workshop['volume_number'])
                for related in workshop['related']:
                    config.input_urls.append("http://ceur-ws.org/Vol-%s/" % related)
                    related_resource = create_workshop_uri(related)
                    triples.append((resource, SKOS.related, related_resource))
        self.write_triples(triples)


class WorkshopPageParser(Parser):
    def __init__(self, grab, task, graph):
        Parser.__init__(self, grab, task, graph, failonerror=False)

    def begin_template(self):
        self.data['volume_number'] = extract_volume_number(self.task.url)

    def end_template(self):
        # print self.task.url
        # print self.data['acronym']
        # print self.data['year']
        pass

    def parse_template_1(self):
        """
        Examples:
            - http://ceur-ws.org/Vol-1008/
            - http://ceur-ws.org/Vol-1081/
            - http://ceur-ws.org/Vol-1085/
        """
        self.begin_template()
        try:
            colocated = rex.rex(self.grab.tree.xpath('//span[@class="CEURCOLOCATED"]/text()')[0],
                                r'([a-zA-Z\s*]+)[\s\']*(\d{4}|\d{2})', re.I)
        except IndexError as ex:
            raise DataNotFound(ex)
        self.data['acronym'] = colocated.group(1).strip()
        self.data['year'] = extract_year(colocated.group(2))

        self.end_template()

    def parse_template_2(self):
        """
        Examples:
            - http://ceur-ws.org/Vol-996/
            - http://ceur-ws.org/Vol-937/
            - http://ceur-ws.org/Vol-838/
            - http://ceur-ws.org/Vol-840/
            - http://ceur-ws.org/Vol-859/
        """
        self.begin_template()

        try:
            colocated = self.rex(self.grab.tree.xpath('//span[@class="CEURFULLTITLE"]/text()')[0],
                                 [
                                     r".*proceedings of the\s*([a-zA-Z]{2,})[\s'-]*(\d{4}|\d{2})\s+"
                                     r"(workshop|conference|posters).*",
                                     r".*at\s+([a-zA-Z]{2,})[\s'-]*(\d{4}|\d{2})\)+",
                                     r"^([a-zA-Z]{2,})[\s'-]*(\d{2}|\d{4})\s+workshop"
                                 ], re.I)
        except IndexError as ex:
            raise DataNotFound(ex)
        self.data['acronym'] = colocated.group(1).strip()
        self.data['year'] = extract_year(colocated.group(2))

        self.end_template()

    def parse_template_3(self):
        """
        Examples:
            - http://ceur-ws.org/Vol-951/
        """
        self.begin_template()
        header = ' '.join(self.grab.tree.xpath(r'/html/body//*[following-sibling::*[contains(., "Edited by")] '
                                               r'and not(self::table)]/descendant-or-self::*/text()'))
        colocated = self.rex(header, [
            r".*(in\s+conjun?ction|co[l-]?located)\s+with.*conference.*\(\s*([a-zA-Z]{2,})[-'\s]*(\d{4}|\d{2})\s*\).*",
            r".*(proceedings\s+of\s+the)\s+([a-zA-Z]{2,})[\s'-]*(\d{4}|\d{2})\s+workshop.*",
            r".*(workshop\s+at\s+|a\s+workshop\s+of\s+).*\(\s*([a-zA-Z-]{2,})[\s'-]*(\d{4}|\d{2})\s*\).*",
            r".*(proceedings\s+of).*\(.*at\s+([a-zA-Z]{2,})[\s'-]*(\d{4}|\d{2})\).*",
            r".*(co-located\s+with|a\s+workshop\s+of).*conference[\s,]+([a-zA-Z]{3,})[\s'-]*(\d{4}|\d{2}).*"
        ], re.IGNORECASE | re.DOTALL)

        self.data['acronym'] = colocated.group(2).strip()
        self.data['year'] = extract_year(colocated.group(3))

        self.end_template()

    def write(self):
        triples = []
        workshop = create_workshop_uri(self.data['volume_number'])
        conference = URIRef(config.id['conference'] + urllib.quote(self.data['acronym'] + "-" + self.data['year']))
        triples.append((conference, RDF.type, SWC.OrganizedEvent))
        triples.append((conference, RDFS.label, Literal(self.data['acronym'], datatype=XSD.string)))
        triples.append((conference, TIMELINE.atDate, Literal(self.data['year'], datatype=XSD.gYear)))
        triples.append((workshop, SWC.isSubEventOf, conference))

        self.write_triples(triples)