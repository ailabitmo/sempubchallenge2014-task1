#! /usr/bin/env python
# -*- coding: utf-8 -*-
import traceback
import urllib
import os
import tempfile
import re

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from rdflib import URIRef, Graph

from CeurWsParser.parsers.base import Parser
from CeurWsParser.namespaces import SWRC, BIBO, SWC, DBPEDIAOWL
from CeurWsParser import config

from SPARQLWrapper import SPARQLWrapper, SPARQLExceptions, JSON

def findCountryInDBpedia(text):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    sparql.setQuery("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX yago: <http://dbpedia.org/class/yago/>
    PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbprop: <http://dbpedia.org/property/>
    SELECT ?country  WHERE {  ?country rdf:type dbpedia-owl:Country .
        {?name_uri dbpedia-owl:wikiPageRedirects ?country.
        ?name_uri rdfs:label '"""+text+"""'@en}
        UNION
        { ?country rdfs:label '"""+text+"""'@en }
        }
    """)
    return sparql.query().convert()['results']['bindings']

def findUniversityInDBpedia(text):
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.setReturnFormat(JSON)

    sparql.setQuery("""
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    PREFIX yago: <http://dbpedia.org/class/yago/>
    PREFIX dbpedia-owl: <http://dbpedia.org/ontology/>
    PREFIX dbprop: <http://dbpedia.org/property/>
    SELECT ?university  WHERE {  ?university rdf:type dbpedia-owl:University .
        {?name_uri dbpedia-owl:wikiPageRedirects ?university.
        ?name_uri rdfs:label '"""+text+"""'@en}
        UNION
        { ?university rdfs:label '"""+text+"""'@en }
        }
    """)
    return sparql.query().convert()['results']['bindings']

def find_countries_in_text(text):
    country_cands = re.findall('[,\n]{1}([ ]*[A-Za-z]+[A-Za-z -]*)\n', text);
    #print country_cands
    countries=[]
    for country_cand in country_cands:
        results = findCountryInDBpedia(country_cand.strip())
        if results:
            countries.append(results[0]['country']['value'])
    return countries

def find_universities_in_text(text):
    university_cands = re.findall('[ \n]{1}([A-Za-z]+[A-Za-z -]*[ ]*)[,\n]', text);
    #print university_cands
    universities=[]
    for university_cand in university_cands:
        results = findUniversityInDBpedia(university_cand.strip())
        if results:
            universities.append(results[0]['university']['value'])
    return universities

def convert_pdf_to_txt( path):
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
        pagenos=set()
        for page in  PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)
        fp.close()
        device.close()
        str = retstr.getvalue()
        retstr.close()
        return str

class PDFParser(Parser):
    def write(self):
        print "Parse done %s. Count of countries: %s. Count of universities %s" % (self.data['publication'], len(self.data['countries']), len(self.data['universities']))
        triples = []
        publication = URIRef(self.data['publication'])
        for country in self.data['countries']:
            triples.append((publication, DBPEDIAOWL.country ,URIRef(country) ))
        for university in self.data['universities']:
            triples.append((publication,SWRC.affiliation,URIRef(university) ))
        self.write_triples(triples)



    def parse_template_1(self):
        link = self.task.url
        name = self.task.url.rsplit('.pdf')[0].rsplit('/')[-1]
        try:
            file_name = "%s/%s" % (tempfile.gettempdir(), name)
            try:
                urllib.urlretrieve(link, file_name)
                first_page = convert_pdf_to_txt(file_name)
                end = first_page.find('Abstract.')
                title = first_page[:end]
                self.data['countries']=find_countries_in_text(title)
                self.data['universities']=find_universities_in_text(title)

            except:
                print "[PDFParser] Error parse %s %s" % (link, name)
                traceback.print_exc()
                return None
            finally:
                os.remove(file_name)
        except:
            pass
        self.data['publication'] = self.task.url


if __name__ == '__main__':
    print "not runnable"
    first_page = convert_pdf_to_txt('../paper6.pdf')
    end = first_page.find('Abstract.')
    title = first_page[:end]
    print find_countries_in_text(title)
    print find_universities_in_text(title)
