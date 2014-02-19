#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re
import traceback

from grab.spider import Spider, Task
from grab.tools.logs import default_logging
from grab.error import DataNotFound
import rdflib
from rdflib.plugins.stores import sparqlstore

from items import Proceedings
import publication_parser
import workshop_parser
import config


def parse_proceedings_summary(obj):
    link = obj[0].find('.//td[last()]//a[@href]')
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', link.get('href')).group(1)
    proceedings = Proceedings(volume_number)
    proceedings.url = link.get('href')
    summary_match = re.match(
        r'(.*)(\nEdited\s*by\s*:\s*)(.*)(\nSubmitted\s*by\s*:\s*)(.*)(\nPublished\s*on\s*CEUR-WS:\s*)(.*)(\nONLINE)(.*)',
        obj[1].find('.//td[last()]').text_content(), re.I | re.M | re.S)
    if summary_match:
        from datetime import datetime

        proceedings.label = re.sub(r'\n', '', summary_match.group(1))
        proceedings.editors = re.split(r",+\s*", summary_match.group(3))
        #submitters = m.group(5)
        proceedings.submission_date = datetime.strptime(proceedings.trim(summary_match.group(7)), '%d-%b-%Y')
        return proceedings
    else:
        #There is no summary information for a workshop
        pass


class CEURSpider(Spider):
    def prepare(self):
        self.publication_results_done = 0
        self.publication_results_failed = 0
        self.repo = rdflib.Graph(sparqlstore.SPARQLUpdateStore(
            queryEndpoint=config.sparqlstore['url'] + "/repositories/" + config.sparqlstore['repository'],
            update_endpoint=config.sparqlstore['url'] + "/repositories/" +
                            config.sparqlstore['repository'] + "/statements",
            context_aware=False))

    def task_initial(self, grab, task):
        if task.url.endswith('.pdf'):
            #parse a .pdf file
            #print "Parsing .pdf file " + task.url
            pass
        elif 'Vol' in task.url:
            #parse a workshop
            print "Parsing a workshop " + task.url
            yield Task('workshop', url=task.url)
        else:
            #parse the index page
            print "Parsing the index page..."
            tr = grab.tree.xpath('/html/body/table[last()]/tr[td]')
            for i in range(0, len(tr), 2):
                url = tr[i].find('.//td[last()]//a[@href]').get('href')
                if url in config.input_urls:
                    try:
                        workshop = workshop_parser.parse_workshop_summary([tr[i], tr[i + 1]])
                        workshop.save(self.repo)
                        proceedings = parse_proceedings_summary([tr[i], tr[i + 1]])
                        proceedings.save(self.repo)
                    except DataNotFound as dnf:
                        print "[WORKSHOP %s] Parsing of summary failed!" % url
                        traceback.print_exc()
                        pass

    def task_workshop(self, grab, task):
        try:
            publication_parser.parse_publications(self, grab, task)
            self.publication_results_done += 1
        except:
            self.validate.write(task.url + '\n')
            self.publication_results_failed += 1

    def print_stats(self):
        print "Publications done:", self.publication_results_done
        print "Publications failed:", self.publication_results_failed


def main():
    threads = 1
    default_logging(grab_log="log.txt")

    fl = open("out.txt", "w")
    flval = open("outval.txt", "w")

    bot = CEURSpider(thread_number=threads, network_try_limit=2)
    bot.initial_urls = config.input_urls
    bot.out = fl
    bot.validate = flval
    try:
        bot.run()
    except KeyboardInterrupt:
        pass
    fl.close()
    flval.close()

    bot.print_stats()
    #print(bot.render_stats())


if __name__ == '__main__':
    main()
