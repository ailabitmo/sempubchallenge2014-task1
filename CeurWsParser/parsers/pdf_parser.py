#! /usr/bin/env python
# -*- coding: utf-8 -*-
import re

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

from CeurWsParser.parsers.base import Parser
from CeurWsParser.namespaces import SWRC, BIBO, SWC
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
    """
    )

    return sparql.query().convert()['results']['bindings']

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

class PDFParser():
    pass




if __name__ == '__main__':
    print "not runnable"
    first_page = convert_pdf_to_txt('../paper-1-1.pdf')
    end = first_page.find('Abstract.')
    title = first_page[:end]
    country_cands = re.findall('[,\n]{1}([ ]*[A-Za-z]+[A-Za-z -]*)\n', title);
    print country_cands

    for country_cand in country_cands:
        results = findCountryInDBpedia(country_cand.strip())
        if results:
            print results[0]['country']['value']