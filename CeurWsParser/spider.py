#! /usr/bin/env python
# -*- coding: utf-8 -*-

from grab.spider import Spider, Task, Data
from grab.tools.logs import default_logging
from grab import Grab
from items import Publication, Proceedings, Workshop
import re

import publication_parser

import rdflib
from rdflib.namespace import FOAF, RDF, RDFS, XSD, DC, DCTERMS
import urllib
import config
from rdflib.plugins.stores import sparqlstore

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
    publication.save(repo)

def format_str(text):
    text = text.encode('utf8')
    text=' '.join(text.split())
    return text

def parse_workshop_summary(repo, tr):
    link = tr[0].find('.//td[last()]//a[@href]') #link(<a>) to workshop
    if link.get('href') not in config.input_urls:
        return
    workshop = Workshop()
    proceedings = Proceedings()
    workshop.label = link.text
    workshop.url = link.get('href')
    workshop.proceedings = proceedings
    proceedings.workshop = workshop
    proceedings.url = link.get('href')
    proceedings.volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', proceedings.url).group(1)
    summary = tr[1].find('.//td[last()]').text_content() #desription of workshop (title, editors, etc.)
    summary_match = re.match(r"(.*)(\nEdited\s*by\s*:\s*)(.*)(\nSubmitted\s*by\s*:\s*)(.*)(\nPublished\s*on\s*CEUR-WS:\s*)(.*)(\nONLINE)(.*)", 
                    summary, re.I | re.M | re.S)
    if summary_match:
        from datetime import datetime
        print "Parsed summary of workshop " + proceedings.url
        proceedings.label = re.sub(r'\n', '', summary_match.group(1)) #title of workshop
        proceedings.editors = re.split(r",{1}\s*", summary_match.group(3)) #editors of workshop
        #submitters = m.group(5)
        time_match_1 = re.match(r'.*,\s*([a-zA-Z]+)[,\s]*(\d{1,2})[\w\s]*,\s*(\d{4})', proceedings.label, re.I)
        time_match_2 = re.match(r'.*,\s*([a-zA-Z]+)[,\s]*(\d{1,2})[\w\s]*-\s*(\d{1,2})[\w\s,]*(\d{4})', proceedings.label, re.I)
        time_match_3 = re.match(r'.*,\s*([a-zA-Z]+)\s*(\d+)\s*-\s*([a-zA-Z]+)\s*(\d+)\s*,\s*(\d{4})', proceedings.label, re.I)
        if time_match_1:
            try:
                workshop.time = datetime.strptime(time_match_1.group(1) + "-" + time_match_1.group(2) + "-" + time_match_1.group(3), '%B-%d-%Y')
            except:
                pass
        elif time_match_2:
            try:
                workshop.time = [
                                    datetime.strptime(time_match_2.group(1) + "-" + time_match_2.group(2) + "-" + time_match_2.group(4), '%B-%d-%Y'),
                                    datetime.strptime(time_match_2.group(1) + "-" + time_match_2.group(3) + "-" + time_match_2.group(4), '%B-%d-%Y')
                                ]
            except:
                pass
        elif time_match_3:
            try:
                workshop.time = [
                                    datetime.strptime(time_match_3.group(1) + "-" + time_match_3.group(2) + "-" + time_match_3.group(5), '%B-%d-%Y'),
                                    datetime.strptime(time_match_3.group(3) + "-" + time_match_3.group(4) + "-" + time_match_3.group(5), '%B-%d-%Y')
                                ]
            except:
                pass
        else:
            #There is no event time information
            pass
        proceedings.submittion_date = datetime.strptime(proceedings.trim(summary_match.group(7)), '%d-%b-%Y')
        workshop.save(repo)
        proceedings.save(repo)
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

        self.publication_results_done=0
        self.publication_results_failed=0


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
        try:
            publication_parser.parse_publications(self.repo,grab,task)
            self.publication_results_done+=1
        except:
            self.validate.write(task.url+'\n')
            self.publication_results_failed+=1


    def print_stats(self):
        print "Publications done:",self.publication_results_done
        print "Publications failed:",self.publication_results_failed
def main():

    threads = 1
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

    bot.print_stats()
    #print(bot.render_stats())

if __name__ == '__main__':
    main()
