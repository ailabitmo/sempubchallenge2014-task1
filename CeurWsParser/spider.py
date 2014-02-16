#! /usr/bin/env python
# -*- coding: utf-8 -*-

from grab.spider import Spider, Task, Data
from grab.tools.logs import default_logging
from grab import Grab
from items import Publication
import re
import rdflib
from rdflib.namespace import FOAF, RDF, RDFS, XSD, DC, DCTERMS
import urllib
import config
from rdflib.plugins.stores import sparqlstore

SWRC = rdflib.Namespace("http://swrc.ontoware.org/ontology#")

def parse_workshop_publication_mf(repo, workshop, link):
    publication = Publication()
    publication.link = workshop + link.get('href')
    publication.title = link.find_class('CEURTITLE')[0].text
    publication.volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    print "Pub link:" + publication.link
    print "Pub label: " + publication.title

    publication.save(repo)

def parse_workshop_publication(repo, workshop, link):
    publication = Publication()
    publication.link = workshop + link.get('href')
    publication.title = link.text.strip()
    publication.volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    #br_tag = node.find("br")
    #i_tag = node.find("i")
    #if not i_tag is None:
    #    publication_authors = i_tag.text.split(',')
    #else:
    #    publication_authors = br_tag.tail.split(',')

    #print "**** FIND NEW PAPER *********"
    #print publication_label.strip()
    #print publication_link.strip()
    #for publication_author in publication_authors:
    #    print publication_author.strip()

    publication.save(repo)

def format_str(text):
    text = text.encode('utf8')
    text=' '.join(text.split())
    return text

def parse_workshop_summary(repo, tr):
    #Parsing the page
    link = tr[0].find('.//td[last()]//a[@href]') #link(<a>) to workshop
    url = link.get('href')
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', url).group(1)
    summary = tr[1].find('.//td[last()]').text_content() #desription of workshop (title, editors, etc.)
    summary_match = re.match(r"(.*)(\nEdited\s*by\s*:\s*)(.*)(\nSubmitted\s*by\s*:\s*)(.*)(\nPublished\s*on\s*CEUR-WS:\s*)(.*)(\nONLINE)(.*)", 
                    summary, re.I | re.M | re.S)
    if summary_match:
        print "Parsed summary of workshop " + url
        extended_title = re.sub(r'\n', '', summary_match.group(1)) #title of workshop
        editors = re.split(r",{1}\s*", summary_match.group(3)) #editors of workshop
        #submitters = m.group(5)
        #submittion_date = m.group(7)

        #Saving RDF to the repo
        proceedings = rdflib.URIRef(config.id['proceedings'] + volume_number)
        repo.add((proceedings, RDF.type, SWRC.Proceedings))
        repo.add((proceedings, RDFS.label, rdflib.Literal(extended_title, datatype = XSD.string)))
        repo.add((proceedings, FOAF.homepage, rdflib.Literal(url, datatype = XSD.anyURI)))
        for editor in editors:
            agent = rdflib.URIRef(config.id['person'] + urllib.quote(editor))
            repo.add((agent, RDF.type, FOAF.Agent))
            repo.add((agent, FOAF.name, rdflib.Literal(editor, datatype = XSD.string)))
            repo.add((proceedings, SWRC.editor, agent))
            repo.add((agent, DC.creator, proceedings))
    else:
        #There is no summary information for a workshop
        pass

class CEURSpider(Spider):

    def prepare(self):
        #Configure a Graph
        store = sparqlstore.SPARQLUpdateStore(
                    queryEndpoint = config.sparqlstore['url'] + "/repositories/" + config.sparqlstore['repository'],
                    update_endpoint = config.sparqlstore['url'] + "/repositories/" + config.sparqlstore['repository'] + "/statements", 
                    context_aware = False)
        graph = rdflib.Graph(store)
        self.repo = graph

    def task_initial(self, grab, task):
        if task.url.endswith('.pdf'):
            #parse a .pdf file
            #print "Parsing .pdf file " + task.url
            pass
        elif 'Vol' in task.url:
            #parse a workshop
            print "Parsing a workshop " + task.url
            yield Task('workshop', url = task.url)
        else:
            #parse the index page
            print "Parsing the index page..."
            tr = grab.tree.xpath('/html/body/table[last()]/tr[td]')
            for i in range(0, len(tr), 2):
                parse_workshop_summary(self.repo, [tr[i], tr[i+1]])

    def task_workshop(self, grab, task):
        #parse a workshop page
        for doc in grab.tree.xpath('//a[contains(@href, ".pdf")]'):
            if doc.find_class('CEURTITLE'):
                #workshop uses microformats
                #parse_workshop_publication_mf(self.repo, task.url, doc)
                pass
            else:
                parse_workshop_publication(self.repo, task.url, doc)

def main():

    threads = 5
    default_logging(grab_log="log.txt")
    
    fl = open("out.txt","w")
    flval = open("outval.txt","w")

    bot = CEURSpider(thread_number=threads, network_try_limit = 2)
    bot.initial_urls = config.input_urls
    bot.out = fl
    bot.validate = flval;
    try: bot.run()
    except KeyboardInterrupt: pass
    fl.close()
    flval.close()

    #print(bot.render_stats())

if __name__ == '__main__':
    main()
