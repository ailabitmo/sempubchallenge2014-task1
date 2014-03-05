#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib

from grab.error import DataNotFound
from grab.tools import rex
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, FOAF, DCTERMS, DC, XSD
from PyPDF2 import PdfFileReader

from CeurWsParser.parsers.base import Parser
from CeurWsParser.namespaces import SWRC, BIBO, SWC
from CeurWsParser import config


class PublicationParser(Parser):
    def begin_template(self):
        self.data['workshop'] = self.task.url
        self.data['volume_number'] = rex.rex(self.task.url, r'.*http://ceur-ws.org/Vol-(\d+).*').group(1)

    def end_template(self):
        self.check_for_completeness()

    def is_invited(self, publication):
        if rex.rex(publication['link'], r'.*(keynote|invite).*', re.I, default=None):
            return True
        else:
            return False

    def get_num_of_pages(self, link, name):
        try:
            file_name = "/tmp/%s" % name
            urllib.urlretrieve(link, file_name)
            pdf = PdfFileReader(file_name)
            return pdf.getNumPages()
        except:
            return None

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
            if publication['is_invited']:
                triples.append((resource, RDF.type, SWC.InvitedPaper))
            if publication['num_of_pages']:
                triples.append((resource, BIBO.numPages, Literal(publication['num_of_pages'], datatype=XSD.integer)))
            for editor in publication['editors']:
                agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
                triples.append((agent, RDF.type, FOAF.Agent))
                triples.append((agent, FOAF.name, Literal(editor, datatype=XSD.string)))
                triples.append((agent, DC.creator, resource))

        self.write_triples(triples)

    def parse_template_1(self):
        self.begin_template()
        publications = []

        for publication in self.grab.tree.xpath('//div[@class="CEURTOC"]/*[@rel="dcterms:hasPart"]/li'):
            try:
                name = publication.find('a[@typeof="bibo:Article"]/span').text_content()
                publication_link = publication.find('a[@typeof="bibo:Article"]').get('href')
                editors = []
                for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
                    publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content()
                    editors.append(publication_editor_name)
                file_name = publication_link.rsplit('.pdf')[0].rsplit('/')[-1]
                publication_object = {
                    'name': name,
                    'file_name': file_name,
                    'link': self.task.url + publication_link,
                    'editors': editors,
                    'num_of_pages': self.get_num_of_pages(self.task.url + publication_link, file_name)
                }
                publication_object['is_invited'] = self.is_invited(publication_object)
                if self.check_for_workshop_paper(publication_object):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.end_template()

    def parse_template_2(self):
        """
        Examples:
            - http://ceur-ws.org/Vol-1008/
        """

        self.begin_template()
        publications = []

        for element in self.grab.tree.xpath('/html/body//*[@class="CEURTOC"]//*[a and '
                                            'descendant-or-self::*[@class="CEURAUTHORS"] and '
                                            'descendant-or-self::*[@class="CEURTITLE"]]'):
            try:
                name = element.find_class('CEURTITLE')[0].text
                link = element.find('a').get('href')
                editors = []
                for editor_name in element.find_class('CEURAUTHORS')[0].text_content().split(","):
                    editors.append(editor_name.strip())
                file_name = link.rsplit('.pdf')[0].rsplit('/')[-1]
                publication_object = {
                    'name': name,
                    'file_name': file_name,
                    'link': self.task.url + link,
                    'editors': editors,
                    'num_of_pages': self.get_num_of_pages(self.task.url + link, file_name)
                }
                publication_object['is_invited'] = self.is_invited(publication_object)
                if self.check_for_workshop_paper(publication_object):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.end_template()

    def parse_template_3(self):
        self.begin_template()
        publications = []

        for publication in self.grab.tree.xpath('//li'):
            try:
                name = publication.find('a').text_content()
                link = publication.find('a').get('href')
                editors = []
                publication_editors = publication.find('i')
                if publication_editors is None:
                    publication_editors_str = publication.find('br').tail
                else:
                    publication_editors_str = publication_editors.text_content()

                for publication_editor_name in publication_editors_str.split(","):
                    editors.append(publication_editor_name.strip())
                file_name = link.rsplit('.pdf')[0].rsplit('/')[-1]
                publication_object = {
                    'name': name,
                    'file_name': file_name,
                    'link': self.task.url + link,
                    'editors': editors,
                    'num_of_pages': self.get_num_of_pages(self.task.url + link, file_name)
                }
                publication_object['is_invited'] = self.is_invited(publication_object)
                if self.check_for_workshop_paper(publication_object):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.end_template()

    def check_for_completeness(self):
        if len(self.data['publications']) == 0:
            self.data = {}
            raise DataNotFound()

    def check_for_workshop_paper(self, publication):
        if rex.rex(publication['name'], r'.*(preface|overview|introduction).*', re.I, default=None):
            return False
        if not publication['link'].endswith('.pdf'):
            return False
        return True


if __name__ == '__main__':
    print "not runnable"
