#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
import traceback

from grab.error import DataNotFound
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, FOAF, DCTERMS, DC, XSD

from CeurWsParser.parsers.base import Parser
from CeurWsParser.namespaces import SWRC
from CeurWsParser import config


class PublicationParser(Parser):
    def write(self):
        print "Parse done %s. Count of publications: %s" % (self.task.url, len(self.data['publications']))
        triples = []
        proceedings = URIRef(self.data['workshop'])
        for publication in self.data['publications']:
            resource = URIRef('%s#%s' % (self.data['workshop'], publication['file_name']))
            triples.append((proceedings, DCTERMS.hasPart, resource))
            triples.append((resource, RDF.type, FOAF.Document))
            triples.append((resource, DCTERMS.partOf, proceedings))
            triples.append((resource, RDF.type, SWRC.InProceedings))
            triples.append((resource, RDFS.label, Literal(publication['name'], datatype=XSD.string)))
            triples.append((resource, FOAF.homepage, Literal(publication['link'], datatype=XSD.anyURI)))
            for editor in publication['editors']:
                agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
                triples.append((agent, RDF.type, FOAF.Agent))
                triples.append((agent, FOAF.name, Literal(editor, datatype=XSD.string)))
                triples.append((agent, DC.creator, resource))

        self.write_triples(triples)

    def parse_template_1(self):
        publications = []
        self.data['workshop'] = self.task.url
        self.data['volume_number'] = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', self.task.url).group(1)

        for publication in self.grab.tree.xpath('//div[@class="CEURTOC"]/*[@rel="dcterms:hasPart"]/li'):
            try:
                publication_name = publication.find('a[@typeof="bibo:Article"]/span').text_content()
                publication_link = publication.find('a[@typeof="bibo:Article"]').get('href')
                editors = []
                for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
                    publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content()
                    editors.append(publication_editor_name)
                publication_object = {
                    'name': publication_name,
                    'file_name': publication_link.rsplit('.pdf')[0],
                    'link': self.task.url + publication_link,
                    'editors': editors
                }
                if self.check_for_workshop_paper(publication_name):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.check_for_completeness()

    def parse_template_2(self):
        publications = []
        self.data['workshop'] = self.task.url
        self.data['volume_number'] = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', self.task.url).group(1)

        for publication in self.grab.tree.xpath('//div[@class="CEURTOC"]//li'):
            try:
                publication_name = publication.find_class('CEURTITLE')[0].text
                publication_link = publication.find('a').get('href')
                editors = []
                for publication_editor in publication.find_class('CEURAUTHORS'):
                    for publication_editor_name in publication_editor.text_content().split(","):
                        editors.append(publication_editor_name.strip())
                publication_object = {
                    'name': publication_name,
                    'file_name': publication_link.rsplit('.pdf')[0],
                    'link': self.task.url + publication_link,
                    'editors': editors
                }
                if self.check_for_workshop_paper(publication_name):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.check_for_completeness()

    def parse_template_3(self):
        publications = []
        self.data['workshop'] = self.task.url
        self.data['volume_number'] = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', self.task.url).group(1)

        for publication in self.grab.tree.xpath('//li'):
            try:
                publication_name = publication.find('a').text_content()
                publication_link = publication.find('a').get('href')
                editors = []
                publication_editors = publication.find('i')
                if publication_editors is None:
                    publication_editors_str = publication.find('br').tail
                else:
                    publication_editors_str = publication_editors.text_content()

                for publication_editor_name in publication_editors_str.split(","):
                    editors.append(publication_editor_name.strip())

                publication_object = {
                    'name': publication_name,
                    'file_name': publication_link.rsplit('.pdf')[0],
                    'link': self.task.url + publication_link,
                    'editors': editors
                }
                if self.check_for_workshop_paper(publication_name):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.check_for_completeness()

    def check_for_completeness(self):
        if len(self.data['publications']) == 0:
            self.data = {}
            raise DataNotFound()

    def check_for_workshop_paper(self, publication):
        if publication.lower() == 'preface' \
                or publication.lower() == 'overview' \
                or publication.lower() == 'introduction':
            return False
        return True  # def parse_publications(repo, grab, task):


if __name__ == '__main__':
    print "not runnable"
