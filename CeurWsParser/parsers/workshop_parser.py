import re
import urllib

from grab.tools import rex
from grab.spider import Task
from grab.error import DataNotFound
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD

from CeurWsParser.parsers.base import Parser, ListParser, create_proceedings_uri
from CeurWsParser import config
from CeurWsParser.parsers import utils
from CeurWsParser.namespaces import BIBO, TIMELINE, SWC, SWRC, SKOS


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


class WorkshopSummaryParser(ListParser):
    XPATH_SUMMARY = '/html/body/table[last()]/tr[td]'
    XPATH_SUMMARY_TITLE = './/td[last()]//a[@href]'

    def __init__(self, grab, task, graph, spider=None):
        ListParser.__init__(self, grab, task, graph, failonerror=True, spider=spider)

    def add_workshop(self, workshop):
        if len(workshop) != 0:
            if 'workshops' not in self.data:
                self.data['workshops'] = [workshop]
            else:
                self.data['workshops'].append(workshop)

    def extract_list(self):
        tr = self.grab.tree.xpath(WorkshopSummaryParser.XPATH_SUMMARY)
        for i in range(0, len(tr), 2):
            element = list()
            #<a> with the title
            element.append(tr[i].find(WorkshopSummaryParser.XPATH_SUMMARY_TITLE))
            #text with the summary information
            element.append(tr[i + 1].find('.//td[last()]').text_content())

            if element[0].get('href') in config.input_urls or len(config.input_urls) == 1:
                self.list.append(element)

    def parse_template_1(self, element):
        """
        A template for joint proceedings of two workshops.

        Examples:
            - http://ceur-ws.org/Vol-1098/
            - http://ceur-ws.org/Vol-989/
        """
        workshop_1 = {'id': 1}
        workshop_2 = {'id': 2}
        summary = self.rex(element[1], [
            r"(joint\s+proceedings\s+of\s+([\s\w,]+)\(([a-zA-Z]+)['\s]?\d+\)[and,\s]+"
            r"([:\s\w-]+)\(([a-zA-Z]+)['\s]?\d+\)([\w\s\-.,^\(]*|[,\s]+workshops\s+of.*|[,\s]+co-located.*))Edited by.*",

            r"(proceedings\s+of\s+joint([\s\w,]+)\(([a-zA-Z]+)['\s]?\d{0,4}\)[and,\s]+"
            r"([:,\s\w-]+)\(([a-zA-Z]+)['\s]?\d{0,4}\)([\w\s\-.,^\(]*|[,\s]+workshops\s+of.*|[,\s]+co-located.*))Edited by.*"
        ], re.I | re.S)

        if len(summary.groups()) != 6:
            raise DataNotFound()

        title = summary.group(1)

        workshop_1['volume_number'] = workshop_2['volume_number'] = \
            WorkshopSummaryParser.extract_volume_number(element[0].get('href'))
        workshop_1['url'] = workshop_2['url'] = element[0].get('href')
        workshop_1['time'] = workshop_2['time'] = utils.parse_date(title)

        workshop_1['label'] = summary.group(2)
        workshop_1['short_label'] = summary.group(3)
        workshop_2['label'] = summary.group(4)
        workshop_2['short_label'] = summary.group(5)

        self.add_workshop(workshop_1)
        self.add_workshop(workshop_2)

    def parse_template_2(self, element):
        """
        A template for joint proceedings of three workshops.

        Examples:
            - http://ceur-ws.org/Vol-981/
            - http://ceur-ws.org/Vol-862/
            - http://ceur-ws.org/Vol-853/
        """
        workshop_1 = {'id': 1}
        workshop_2 = {'id': 2}
        workshop_3 = {'id': 3}
        summary = self.rex(element[1], [
            r'(joint\s+proceedings\s+of\s+[the]*.*workshops:\s*([\s\w]+)\(([a-zA-Z]+)\d+\)'
            r'[and,\s]+([\s\w]+)\(([a-zA-Z]+)\d+\)[and,\s]+([\s\w]+)\(([a-zA-Z]+)\d+\)[,\s]+.*)Edited by.*',

            r"(joint\s+proceedings\s+of\s+([\s\w,]+)\(([a-zA-Z]+)['\s]?\d+\)[and,\s]+([\s\w-]+)\(([a-zA-Z]+)['\s]?\d+\)"
            r"[and,\s]+([\s\w]+)\(([a-zA-Z]+)['\s]?\d+\)[,\s]+.*)Edited by.*"
        ],
                           re.I | re.S)

        if len(summary.groups()) != 7:
            raise DataNotFound()

        title = summary.group(1)

        workshop_1['volume_number'] = workshop_2['volume_number'] = workshop_3['volume_number'] = \
            WorkshopSummaryParser.extract_volume_number(element[0].get('href'))
        workshop_1['url'] = workshop_2['url'] = workshop_3['url'] = element[0].get('href')
        workshop_1['time'] = workshop_2['time'] = workshop_3['time'] = utils.parse_date(title)

        workshop_1['label'] = summary.group(2)
        workshop_1['short_label'] = summary.group(3)
        workshop_2['label'] = summary.group(4)
        workshop_2['short_label'] = summary.group(5)
        workshop_3['label'] = summary.group(6)
        workshop_3['short_label'] = summary.group(7)

        self.add_workshop(workshop_1)
        self.add_workshop(workshop_2)
        self.add_workshop(workshop_3)

    def parse_template_3(self, element):
        workshop = {}
        title = rex.rex(element[1], r'(.*)Edited\s*by.*', re.I | re.S).group(1)

        workshop['volume_number'] = WorkshopSummaryParser.extract_volume_number(element[0].get('href'))
        workshop['label'] = element[0].text.replace('.', '')
        workshop['url'] = element[0].get('href')
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

        self.add_workshop(workshop)

    def write(self):
        triples = []
        for workshop in self.data['workshops']:
            if 'id' in workshop:
                resource = create_workshop_uri("%s#%s" % (workshop['volume_number'], workshop['id']))
            else:
                resource = create_workshop_uri(workshop['volume_number'])
            proceedings = URIRef(workshop['url'])
            triples.append((resource, RDF.type, BIBO.Workshop))
            triples.append((resource, RDFS.label, Literal(workshop['label'], datatype=XSD.string)))
            triples.append((proceedings, BIBO.presentedAt, resource))
            if 'edition' in workshop:
                triples.append((resource, SWRC.edition, Literal(workshop['edition'], datatype=XSD.integer)))

            if 'short_label' in workshop:
                triples.append((resource, BIBO.shortTitle, Literal(workshop['short_label'], datatype=XSD.string)))

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

    WARNING: Ignores joint proceedings!
    """

    def parse_template_main(self):
        tr = self.grab.tree.xpath('/html/body/table[last()]/tr[td]')
        self.data['workshops'] = []
        for i in range(0, len(tr), 2):
            workshop_url = tr[i].find('.//td[last()]//a[@href]').get('href')
            if len(config.input_urls) == 1:
                self.spider.add_task(Task('initial', url=workshop_url))
            if workshop_url in config.input_urls or len(config.input_urls) == 1:
                related = []
                for a in tr[i + 1].findall(".//td[1]//a[@href]"):
                    if len(a.get('href')) > 1:
                        related.append(a.get('href')[5:])
                workshop = {
                    'volume_number': WorkshopRelationsParser.extract_volume_number(workshop_url),
                    'related': related
                }
                self.data['workshops'].append(workshop)

    def write(self):
        triples = []
        for workshop in self.data['workshops']:
            if len(workshop['related']) > 0:
                resource = create_workshop_uri(workshop['volume_number'])
                for related in workshop['related']:
                    if len(config.input_urls) > 1:
                        config.input_urls.append("http://ceur-ws.org/Vol-%s/" % related)
                    related_resource = create_workshop_uri(related)
                    triples.append((resource, SKOS.related, related_resource))
        self.write_triples(triples)


class WorkshopPageParser(Parser):
    def __init__(self, grab, task, graph, spider=None):
        Parser.__init__(self, grab, task, graph, failonerror=False, spider=spider)

    def begin_template(self):
        self.data['volume_number'] = WorkshopPageParser.extract_volume_number(self.task.url)

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
        proceedings = create_proceedings_uri(self.data['volume_number'])
        conference = URIRef(config.id['conference'] + urllib.quote(self.data['acronym'] + "-" + self.data['year']))
        triples.append((conference, RDF.type, SWC.OrganizedEvent))
        triples.append((conference, RDFS.label, Literal(self.data['acronym'], datatype=XSD.string)))
        triples.append((conference, TIMELINE.atDate, Literal(self.data['year'], datatype=XSD.gYear)))
        for workshop in self.graph.objects(proceedings, BIBO.presentedAt):
            triples.append((workshop, SWC.isSubEventOf, conference))

        self.write_triples(triples)