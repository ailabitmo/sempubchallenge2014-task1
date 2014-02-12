# -*- coding: utf-8 -*-
from grab.spider import Spider, Task, Data
from grab.tools.logs import default_logging
from grab import Grab

def format_str(text):
        text=text.encode('utf8')
        text=' '.join(text.split())
        return text



class KinoSpider(Spider):
    def task_initial(self, grab, task):
        #for xpath in grab.tree.xpath('//*/table/tbody/tr/td/b/font/a/@href'):
        # yield Task('workshop_parse', 'http://ceur-ws.org/Vol-1124/')
        for xpath in grab.tree.xpath('//body//b/font/a/@href'):
            url = xpath.encode('utf8')
            print url
            yield Task('workshop_parse', url=url)

    def task_workshop_parse(self,grab, task):
        print task.url
        workshop_uri="<"+task.url+">"
        self.out.write( workshop_uri + " <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://swrc.ontoware.org/ontology#Proceedings> .\n")

        workshop_vol_acronym=format_str(grab.tree.xpath('//*/span[@class="CEURVOLACRONYM"]/text()')[0])
        print workshop_vol_acronym


def main():
    initial_urls = ["http://ceur-ws.org/"]
    threads = 50
    default_logging(grab_log="log.txt")
    fl = open("out.txt","w")
    flval = open("outval.txt","w")

    bot = KinoSpider(thread_number=threads,network_try_limit=2)
    bot.initial_urls = initial_urls
    bot.out = fl
    bot.validate = flval;
    try: bot.run()
    except KeyboardInterrupt: pass
    fl.close()

    print(bot.render_stats())

if __name__ == '__main__':
    main()
