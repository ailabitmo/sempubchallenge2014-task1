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

def parse_workshop_publication( workshop, node):
    link = node.find("a")
    publication_link = workshop+link.get('href')
    publication_label = link.text
    br_tag = node.find("br")
    i_tag = node.find("i")
    if not i_tag is None:
        publication_authors = i_tag.text.split(',')
    else:
        publication_authors = br_tag.tail.split(',')

    print "**** FIND NEW PAPER *********"
    print publication_label.strip()
    print publication_link.strip()
    for publication_author in publication_authors:
        print publication_author.strip()

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

class CEURSpider(Spider):

    def prepare(self):
        #Для доступа к Sesame нужен VPN, пока оставлю закоменченным
        #store = sparqlstore.SPARQLUpdateStore(queryEndpoint = "http://192.168.134.110:8080/openrdf-sesame/repositories/sempubchallenge-max",
        #            update_endpoint = "http://192.168.134.110:8080/openrdf-sesame/repositories/sempubchallenge-max/statements")
        #graph = rdflib.Graph(store, identifier="http://ailab.ifmo.ru/context/sempubchallenge")
        graph = rdflib.Graph()
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

        self.out.write("<" + task.url + ">" + " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://swrc.ontoware.org/ontology#Proceedings> .\n")
        
        # parse workshops
        # vol-1
        for node in grab.tree.xpath('//*/ul/li | //*/ol/li'):
            parse_workshop_publication(task.url, node)

def main():
    initial_urls = ["http://ceur-ws.org/Vol-1"]
    full_initial_urls = ["http://ceur-ws.org/",
                    "http://ceur-ws.org/Vol-315/paper8.pdf",
                    "http://ceur-ws.org/Vol-1085/",
                    "http://ceur-ws.org/Vol-1081/",
                    "http://ceur-ws.org/Vol-1044/",
                    "http://ceur-ws.org/Vol-1019/",
                    "http://ceur-ws.org/Vol-1008/",
                    "http://ceur-ws.org/Vol-996/",
                    "http://ceur-ws.org/Vol-994/",
                    "http://ceur-ws.org/Vol-981/",
                    "http://ceur-ws.org/Vol-979/",
                    "http://ceur-ws.org/Vol-951/",
                    "http://ceur-ws.org/Vol-946/",
                    "http://ceur-ws.org/Vol-943/",
                    "http://ceur-ws.org/Vol-937/",
                    "http://ceur-ws.org/Vol-936/",
                    "http://ceur-ws.org/Vol-930/",
                    "http://ceur-ws.org/Vol-929/",
                    "http://ceur-ws.org/Vol-919/",
                    "http://ceur-ws.org/Vol-914/",
                    "http://ceur-ws.org/Vol-906/",
                    "http://ceur-ws.org/Vol-905/",
                    "http://ceur-ws.org/Vol-904/",
                    "http://ceur-ws.org/Vol-903/",
                    "http://ceur-ws.org/Vol-902/",
                    "http://ceur-ws.org/Vol-901/",
                    "http://ceur-ws.org/Vol-900/",
                    "http://ceur-ws.org/Vol-895/",
                    "http://ceur-ws.org/Vol-890/",
                    "http://ceur-ws.org/Vol-875/",
                    "http://ceur-ws.org/Vol-869/",
                    "http://ceur-ws.org/Vol-859/",
                    "http://ceur-ws.org/Vol-840/",
                    "http://ceur-ws.org/Vol-839/",
                    "http://ceur-ws.org/Vol-838/",
                    "http://ceur-ws.org/Vol-814/",
                    "http://ceur-ws.org/Vol-813/",
                    "http://ceur-ws.org/Vol-800/",
                    "http://ceur-ws.org/Vol-798/",
                    "http://ceur-ws.org/Vol-784/",
                    "http://ceur-ws.org/Vol-783/",
                    "http://ceur-ws.org/Vol-782/",
                    "http://ceur-ws.org/Vol-779/",
                    "http://ceur-ws.org/Vol-778/",
                    "http://ceur-ws.org/Vol-775/",
                    "http://ceur-ws.org/Vol-736/",
                    "http://ceur-ws.org/Vol-721/",
                    "http://ceur-ws.org/Vol-671/",
                    "http://ceur-ws.org/Vol-669/",
                    "http://ceur-ws.org/Vol-658/",
                    "http://ceur-ws.org/Vol-628/",
                    "http://ceur-ws.org/Vol-538/",
                    "http://ceur-ws.org/Vol-369/",
                    "http://ceur-ws.org/Vol-315/",
                    "http://ceur-ws.org/Vol-232/",
                    "http://ceur-ws.org/Vol-1/"]

    threads = 5
    default_logging(grab_log="log.txt")
    
    fl = open("out.txt","w")
    flval = open("outval.txt","w")

    bot = CEURSpider(thread_number=threads, network_try_limit = 2)
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
