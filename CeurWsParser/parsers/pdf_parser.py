#! /usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import os
import tempfile
import re
from cStringIO import StringIO
from urllib2 import HTTPError

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from rdflib import URIRef, Graph
from rdflib.plugins.stores.sparqlstore import SPARQLStore

from CeurWsParser import config
from CeurWsParser.parsers.base import Parser
from CeurWsParser.namespaces import SWRC, DBPEDIAOWL


def find_country_in_dbpedia(graph, tokens):
    print tokens
    values = ' '.join(['"' + token.strip() + '"' for token in tokens])
    try:
        results = graph.query("""SELECT DISTINCT ?country {
            VALUES ?search {
                """ + values + """
            }
            ?country a dbpedia-owl:Country .
            {
                ?name_uri dbpedia-owl:wikiPageRedirects ?country ;
                        rdfs:label ?search .
            }
            UNION
            { ?country rdfs:label ?search }
        }""")
        return [row[0] for row in results]
    except HTTPError as er:
        print "[ERROR] DBPedia is inaccessible! HTTP code: %s" % er.code
    return []


def find_university_in_dbpedia(graph, tokens):
    print tokens
    values = ' '.join(['"' + token.strip() + '"' for token in tokens])
    try:
        results = graph.query("""SELECT DISTINCT ?university {
            VALUES ?search {
                """ + values + """
            }
            ?university a dbpedia-owl:University .
            {
                ?name_uri dbpedia-owl:wikiPageRedirects ?university ;
                    rdfs:label ?search .
            }
            UNION
            { ?university rdfs:label ?search }
        }""")
        return [row[0] for row in results]
    except HTTPError as er:
        print "[ERROR] DBPedia is inaccessible! HTTP code: %s" % er.code
    return []


def find_countries_in_text(graph, text):
    country_cands = re.findall('[,\n]{1}([ ]*[A-Za-z]+[A-Za-z -]*)\n', text, re.I)
    #print country_cands
    return find_country_in_dbpedia(graph, country_cands)


def find_universities_in_text(graph, text):
    university_cands = re.findall('[ \n]{1}([A-Za-z]+[A-Za-z -]*[ ]*)[,\n]', text)
    #print university_cands
    return find_university_in_dbpedia(graph, university_cands)


def convert_pdf_to_txt(path):
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 1
    caching = True
    pagenos = set()
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password, caching=caching,
                                  check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    result = retstr.getvalue()
    retstr.close()
    return result


class PDFParser(Parser):
    def __init__(self, grab, task, graph, spider=None):
        Parser.__init__(self, grab, task, graph, spider=spider)
        #DBPedia SPARQL Endpoint
        # self.dbpedia = Graph('SPARQLStore', namespace_manager=self.graph.namespace_manager)
        # self.dbpedia.open('http://dbpedia.org/sparql')

        #DBPedia's dump of countries and universities
        self.dbpedia = Graph(SPARQLStore(config.sparqlstore['url'] + "/repositories/" +
                                         config.sparqlstore['dbpedia_dump'],
                                         context_aware=False), namespace_manager=self.graph.namespace_manager)

    def write(self):
        print "[TASK %s][PDFParser] Count of countries: %s. Count of universities %s" % (
            self.task.url, len(self.data['countries']), len(self.data['universities']))
        triples = []

        results = self.graph.query("""SELECT DISTINCT ?pub {
            ?pub a foaf:Document;
                 foaf:homepage ?pub_link .
            FILTER(?pub_link = '""" + self.task.url + """'^^xsd:anyURI)
        }
        LIMIT 1""")
        publication = None
        for row in results:
            publication = row[0]
            breakz
        if publication is not None:
            for country in self.data['countries']:
                triples.append((publication, DBPEDIAOWL.country, URIRef(country)))
            for university in self.data['universities']:
                triples.append((publication, SWRC.affiliation, URIRef(university)))
        self.write_triples(triples)

    def parse_template_1(self):
        self.data['file_name'] = self.task.url.rsplit('/')[-1]
        self.data['id'] = self.data['file_name'].rsplit('.', 1)[:-1][0]
        self.data['file_location'] = "%s/%s" % (tempfile.gettempdir(), self.data['file_name'])
        try:
            try:
                self.grab.response.save(self.data['file_location'])
                first_page = convert_pdf_to_txt(self.data['file_location'])
                end = re.search(r'Abstract|Introduction', first_page, re.I).start(0)
                title = first_page[:end]
                print title
                self.data['countries'] = find_countries_in_text(self.dbpedia, title)
                self.data['universities'] = find_universities_in_text(self.dbpedia, title)

            except:
                print "[TASK %s][PDFParser] Error parse%s" % (self.task.url, self.data['file_name'])
                traceback.print_exc()
                return None
            finally:
                os.remove(self.data['file_location'])
        except:
            pass


if __name__ == '__main__':
    print "not runnable"
    first_page = convert_pdf_to_txt('../paper6.pdf')
    end = first_page.find('Abstract.')
    title = first_page[:end]
    print find_countries_in_text(title)
    print find_universities_in_text(title)
