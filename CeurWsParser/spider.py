#! /usr/bin/env python
# -*- coding: utf-8 -*-

import re

from grab.spider import Spider, Task
from grab.tools.logs import default_logging
import rdflib
from rdflib.namespace import FOAF, DC, DCTERMS

from CeurWsParser.namespaces import BIBO, SWRC, TIMELINE, SWC, SKOS
from CeurWsParser.parsers import WorkshopSummaryParser, WorkshopPageParser, ProceedingsSummaryParser, \
    PublicationParser, ProceedingsRelationsParser, PDFParser, WorkshopAcronymParser, WorkshopRelationsParser, \
    JointWorkshopsEditorsParser
from CeurWsParser import config


mappings = dict(
    url_mappings={
        r'^http://ceur-ws\.org/*$': 'index',
        r'^http://ceur-ws\.org/Vol-\d+/*$': 'workshop',
        r'^http://ceur-ws\.org/Vol-\d+/.*\.pdf$': 'publication'
    },
    parser_mappings={
        'index': [
            ProceedingsRelationsParser,
            WorkshopSummaryParser,
            WorkshopAcronymParser,
            WorkshopRelationsParser,
            ProceedingsSummaryParser
        ],
        'workshop': [
            WorkshopPageParser,
            JointWorkshopsEditorsParser,
            PublicationParser
        ],
        'publication': []
    }
)


class CEURSpider(Spider):
    def __init__(self):
        Spider.__init__(self, thread_number=1)
        self.setup_grab(timeout=240)
        self.publication_results_done = 0
        self.publication_results_failed = 0
        # self.repo = rdflib.Graph(sparqlstore.SPARQLUpdateStore(
        #     queryEndpoint=config.sparqlstore['url'] + "/repositories/" + config.sparqlstore['repository'],
        #     update_endpoint=config.sparqlstore['url'] + "/repositories/" +
        #                     config.sparqlstore['repository'] + "/statements",
        #     context_aware=False))
        self.repo = rdflib.Graph(store='default')
        self.repo.bind('foaf', FOAF)
        self.repo.bind('swc', SWC)
        self.repo.bind('skos', SKOS)
        self.repo.bind('swrc', SWRC)
        self.repo.bind('bibo', BIBO)
        self.repo.bind('dcterms', DCTERMS)
        self.repo.bind('dc', DC)
        self.repo.bind('timeline', TIMELINE)

    def load_initial_urls(self):
        if self.initial_urls:
            for url in self.initial_urls:
                if re.match(r'^http://ceur-ws\.org/*$', url, re.I):
                    self.add_task(Task('initial', url=url, priority=0))
                else:
                    self.add_task(Task('initial', url=url, priority=1))

    def task_initial(self, grab, task):
        print "[TASK %s] started" % task.url
        for url_rex in mappings['url_mappings']:
            if re.match(url_rex, task.url, re.I):
                value = mappings['url_mappings'][url_rex]
                for parser in mappings['parser_mappings'][value]:
                    p = parser(grab, task, self.repo, spider=self)
                    try:
                        p.parse()
                    except Exception as ex:
                        print "[TASK %s][PARSER %s] Error: %s" % (task.url, parser, ex)
                        import traceback

                        traceback.print_exc()

    def shutdown(self):
        Spider.shutdown(self)
        f = open('rdfdb.ttl', 'w')
        self.repo.serialize(f, format='turtle')
        self.repo.close()

    # def task_workshop(self, grab, task):
    #     try:
    #         publication_parser.parse_publications(self, grab, task)
    #         self.publication_results_done += 1
    #     except:
    #         self.validate.write(task.url + '\n')
    #         self.publication_results_failed += 1

    def print_stats(self):
        print "Publications done:", self.publication_results_done
        print "Publications failed:", self.publication_results_failed


def main():
    default_logging(grab_log="log.txt")

    fl = open("out.txt", "w")
    flval = open("outval.txt", "w")

    bot = CEURSpider()
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
    print(bot.render_stats())


if __name__ == '__main__':
    main()
