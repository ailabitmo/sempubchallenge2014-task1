#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import urllib
import os
import tempfile
import traceback

from grab.error import DataNotFound
from grab.tools import rex
from grab.spider import Task
from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, FOAF, DCTERMS, DC, XSD
from PyPDF2 import PdfFileReader

from base import Parser, create_proceedings_uri, create_publication_uri, clean_string
from namespaces import SWRC, BIBO, SWC
import config


class PublicationParser(Parser):
    def begin_template(self):
        self.data['workshop'] = self.task.url
        self.data['volume_number'] = self.extract_volume_number(self.task.url)
        proceedings = create_proceedings_uri(self.data['volume_number'])
        self.data['workshops'] = []
        for workshop in self.graph.objects(proceedings, BIBO.presentedAt):
            try:
                label = self.graph.objects(workshop, BIBO.shortTitle).next()
                self.data['workshops'].append((workshop, label.toPython()))
            except StopIteration:
                pass
            except:
                traceback.print_exc()

    def end_template(self):
        self.check_for_completeness()

    @staticmethod
    def is_invited(publication):
        if rex.rex(publication['link'], r'.*(keynote|invite).*', re.I, default=None):
            return True
        else:
            return False

    def write(self):
        print "[TASK %s][PublicationParser] Count of publications: %s" % (self.task.url, len(self.data['publications']))
        triples = []
        proceedings = URIRef(self.data['workshop'])
        for publication in self.data['publications']:

            if len(publication['file_name'].split()) > 0:
                self.spider.add_task(Task('initial', url=publication['link']))

            resource = create_publication_uri(self.data['workshop'], publication['file_name'])
            triples.append((proceedings, DCTERMS.hasPart, resource))
            triples.append((resource, RDF.type, FOAF.Document))
            triples.append((resource, DCTERMS.partOf, proceedings))
            triples.append((resource, RDF.type, SWRC.InProceedings))
            triples.append((resource, DC.title, Literal(publication['name'], datatype=XSD.string)))
            triples.append((resource, FOAF.homepage, Literal(publication['link'], datatype=XSD.anyURI)))
            if publication['is_invited']:
                triples.append((resource, RDF.type, SWC.InvitedPaper))
            for editor in publication['editors']:
                agent = URIRef(config.id['person'] + urllib.quote(editor.encode('utf-8')))
                triples.append((agent, RDF.type, FOAF.Agent))
                triples.append((agent, FOAF.name, Literal(editor, datatype=XSD.string)))
                triples.append((resource, DC.creator, agent))
                triples.append((resource, FOAF.maker, agent))
                triples.append((agent, FOAF.made, resource))
            if 'presentedAt' in publication and len(publication['presentedAt']) > 0:
                for w in publication['presentedAt']:
                    triples.append((resource, BIBO.presentedAt, w))

        self.write_triples(triples)

    def parse_template_1(self):
        self.begin_template()
        publications = []

        for publication in self.grab.tree.xpath('//div[@class="CEURTOC"]/*[@rel="dcterms:hasPart"]/li'):
            try:
                name = clean_string(publication.find('a[@typeof="bibo:Article"]/span').text_content())
                publication_link = publication.find('a[@typeof="bibo:Article"]').get('href')
                editors = []
                for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
                    publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content()
                    editors.append(clean_string(publication_editor_name))
                file_name = publication_link.rsplit('.pdf')[0].rsplit('/')[-1]
                publication_object = {
                    'name': name,
                    'file_name': file_name,
                    'link': self.task.url + publication_link,
                    'editors': editors
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
            - http://ceur-ws.org/Vol-1043/
        """

        self.begin_template()
        publications = []

        for element in self.grab.tree.xpath('/html/body//*[@class="CEURTOC"]//*[a and '
                                            'descendant-or-self::*[@class="CEURAUTHORS"] and '
                                            'descendant-or-self::*[@class="CEURTITLE"]]'):
            try:
                name_el = element.find_class('CEURTITLE')[0]
                name = clean_string(name_el.text_content()).strip()
                if name is None or not name:
                    # In case of unclosed span element with the author list
                    # Example: http://ceur-ws.org/Vol-640
                    name = clean_string(name_el.tail)
                href = element.find('a').get('href')
                link = href if href.startswith('http://') else self.task.url + href
                editors = []
                editors_list_el = element.find_class('CEURAUTHORS')[0]
                editors_list = clean_string(editors_list_el.text_content())
                if not editors_list:
                    # In case of unclosed span element with the author list
                    # Example: http://ceur-ws.org/Vol-1043
                    editors_list = clean_string(editors_list_el.tail)

                for editor_name in editors_list.split(","):
                    editor_name = clean_string(editor_name.strip())
                    if editor_name:
                        editors.append(editor_name)

                if not editors:
                    #a publication should have non-empty list of authors
                    raise DataNotFound(link)

                file_name = link.rsplit('.pdf')[0].rsplit('/')[-1]
                publication_object = {
                    'name': name,
                    'file_name': file_name,
                    'link': link,
                    'editors': editors
                }
                publication_object['is_invited'] = self.is_invited(publication_object)

                if len(self.data['workshops']) > 1:
                    try:
                        session = self.grab.tree.xpath(
                            '//a[@href="%s"]/preceding::*[@class="CEURSESSION"][1]' % href)[0]
                        publication_object['presentedAt'] = []
                        for w in self.data['workshops']:
                            if w[1] is not None and w[1] in session.text:
                                publication_object['presentedAt'].append(w[0])
                    except:
                        # traceback.print_exc()
                        pass

                if self.check_for_workshop_paper(publication_object):
                    publications.append(publication_object)
            except Exception as ex:
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.end_template()

    def parse_template_3(self):
        self.begin_template()
        publications = []

        elements = self.grab.tree.xpath('//li[a[@href] and (i or em or br)]')
        if elements is None or len(elements) == 0:
            elements = self.grab.tree.xpath('//p[a[@href] and (i or em)]')

        for publication in elements:
            try:
                name = clean_string(publication.find('a').text_content())
                if rex.rex(name, r'.*(preface|first\s+pages|author\s+list|foreword).*', re.I, default=None):
                    #Examples: 180, 186
                    continue
                link = publication.find('a').get('href')
                editors = []
                editors_tag = None
                if publication.find('i') is not None:
                    editors_tag = publication.findall('i')[-1]
                elif publication.find('em') is not None:
                    editors_tag = publication.find('em')

                if editors_tag is None:
                    editors_tag_content = publication.find('br').tail
                else:
                    editors_tag_content = editors_tag.text_content()

                editors_tag_content = re.sub(r'\s*[,\s]*and\s+', ',', editors_tag_content, flags=re.I | re.S).strip()

                if not editors_tag_content:
                    #a publication should have non-empty list of authors
                    raise DataNotFound(link)

                for publication_editor_name in editors_tag_content.split(","):
                    pen = clean_string(publication_editor_name.strip())
                    if pen:
                        editors.append(pen)

                file_name = link.rsplit('.pdf')[0].rsplit('/')[-1]
                publication_object = {
                    'name': name,
                    'file_name': file_name,
                    'link': self.task.url + link,
                    'editors': editors
                }
                publication_object['is_invited'] = self.is_invited(publication_object)
                if self.check_for_workshop_paper(publication_object):
                    publications.append(publication_object)
            except Exception as ex:
                #traceback.print_exc()
                raise DataNotFound(ex)

        self.data['publications'] = publications
        self.end_template()

    def parse_template_4(self):
        self.begin_template()
        publications = []

        for publication in self.grab.tree.xpath('/html/body//a[@href and '
                                                'preceding::*[contains(.,"Table of Contents")]]'):
            try:
                name = clean_string(publication.text_content())
                link = publication.get('href')
                editors = []

                if publication.getprevious().tag == 'br' and publication.getprevious().getprevious().tag == 'i':
                    editors_tag_content = publication.getprevious().getprevious().text_content()
                    editors_tag_content = re.sub(r'\s*[,\s]*and\s+', ',', editors_tag_content, flags=re.I | re.S)

                    for publication_editor_name in editors_tag_content.split(","):
                        editors.append(clean_string(publication_editor_name.strip()))
                    file_name = link.rsplit('.pdf')[0].rsplit('/')[-1]
                    publication_object = {
                        'name': name,
                        'file_name': file_name,
                        'link': self.task.url + link,
                        'editors': editors
                    }
                    publication_object['is_invited'] = self.is_invited(publication_object)
                    if self.check_for_workshop_paper(publication_object):
                        publications.append(publication_object)
            except AttributeError:
                pass
            except Exception:
                traceback.print_exc()

        self.data['publications'] = publications
        self.end_template()

    def check_for_completeness(self):
        if len(self.data['publications']) == 0:
            self.data = {}
            raise DataNotFound()

    @staticmethod
    def check_for_workshop_paper(publication):
        if rex.rex(publication['name'].strip(), r'^(preface|overview|introduction|einleitung|foreword)$', re.I, default=None):
            return False
        if not publication['link'].endswith('.pdf'):
            return False
        return True


class PublicationNumOfPagesParser(Parser):
    def begin_template(self):
        self.data['proceedings_url'] = "http://ceur-ws.org/Vol-%s/" % self.extract_volume_number(self.task.url)
        self.data['file_name'] = self.task.url.rsplit('/')[-1]
        self.data['id'] = self.data['file_name'].rsplit('.', 1)[:-1][0]
        self.data['file_location'] = "%s/%s" % (tempfile.gettempdir(), self.data['file_name'])
        self.grab.response.save(self.data['file_location'])

    def end_template(self):
        try:
            os.remove(self.data['file_location'])
        except:
            pass

    def parse_template_1(self):
        try:
            self.begin_template()
            if self.task.url.endswith('.pdf'):
                with open(self.data['file_location'], 'rb') as f:
                    pdf = PdfFileReader(f)
                    self.data['num_of_pages'] = pdf.getNumPages()
            else:
                raise DataNotFound()
        finally:
            self.end_template()

    def write(self):
        triples = []
        resource = create_publication_uri(self.data['proceedings_url'], self.data['id'])
        if 'num_of_pages' in self.data:
            triples.append((resource, BIBO.numPages, Literal(self.data['num_of_pages'], datatype=XSD.integer)))

        self.write_triples(triples)
