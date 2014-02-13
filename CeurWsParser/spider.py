#! /usr/bin/env python
# -*- coding: utf-8 -*-

from grab.spider import Spider, Task, Data
from grab.tools.logs import default_logging
from grab import Grab
import re
import rdflib
import urllib
from rdflib.plugins.stores import sparqlstore

swrc = rdflib.Namespace("http://swrc.ontoware.org/ontology#")

def format_str(text):
    text = text.encode('utf8')
    text=' '.join(text.split())
    return text

def parse_workshop_summary(repo, tr):
    link = tr[0].find('.//td[last()]//a[@href]')
    proceedings = rdflib.URIRef(link.get('href'))
    repo.add((proceedings, rdflib.RDF.type, swrc.Proceedings))

    summary = tr[1].find('.//td[last()]').text_content()
    m = re.match(r"(.*)(\nEdited\s*by\s*:\s*)(.*)(\nSubmitted\s*by\s*:\s*)(.*)(\nPublished\s*on\s*CEUR-WS:\s*)(.*)(\nONLINE)(.*)", summary, re.I | re.M | re.S)
    extended_title = urllib.quote(m.group(1).encode('utf-8'))
    repo.add((proceedings, rdflib.RDFS.label, rdflib.Literal(extended_title)))
    editors = re.split(r",{1}\s*", m.group(3))
    #print editors
    submitters = m.group(5)
    #print submitters
    submittion_date = m.group(7)
    #print submittion_date

class KinoSpider(Spider):
    
    def prepare(self):
        store = sparqlstore.SPARQLUpdateStore(queryEndpoint = "http://192.168.134.110:8080/openrdf-sesame/repositories/sempubchallenge-max",
                    update_endpoint = "http://192.168.134.110:8080/openrdf-sesame/repositories/sempubchallenge-max/statements")
        graph = rdflib.Graph(store, identifier="http://ailab.ifmo.ru/context/sempubchallenge")
        self.repo = graph

    def task_initial(self, grab, task):
        #for xpath in grab.tree.xpath('//*/table/tbody/tr/td/b/font/a/@href'):
        #yield Task('workshop_parse', 'http://ceur-ws.org/Vol-1124/')
        if task.url.endswith('.pdf'):
            #parse a .pdf file
            print "Parsing .pdf file " + task.url
        elif 'Vol' in task.url:
            #parse a workshop
            print "Parsing a workshop"
            #yield Task('workshop', url = task.url)
        else:
            #parse the index page
            tr = grab.tree.xpath('/html/body/table[last()]/tr[td]')
            for i in range(0, len(tr) / 2, 2):
                parse_workshop_summary(self.repo, [tr[i], tr[i+1]])
                

    def task_workshop(self, grab, task):
        print "Parsing workshop " + task.url + "..."

        #self.out.write("<" + task.url + ">" + " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://swrc.ontoware.org/ontology#Proceedings> .\n")
        
        #workshop_vol_acronym=format_str(grab.tree.xpath('//*/span[@class="CEURVOLACRONYM"]/text()')[0])
        #print workshop_vol_acronym

def main():
    initial_urls = ["http://ceur-ws.org/", "http://ceur-ws.org/Vol-1/", "http://ceur-ws.org/Vol-315/paper8.pdf"]

    threads = 5
    default_logging(grab_log="log.txt")
    
    fl = open("out.txt","w")
    flval = open("outval.txt","w")

    bot = KinoSpider(thread_number=threads, network_try_limit = 2)
    bot.initial_urls = initial_urls
    bot.out = fl
    bot.validate = flval;
    try: bot.run()
    except KeyboardInterrupt: pass
    fl.close()
    flval.close()

    #print(bot.render_stats())

if __name__ == '__main__':
    main()
