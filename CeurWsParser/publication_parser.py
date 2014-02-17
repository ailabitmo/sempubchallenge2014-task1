#! /usr/bin/env python
# -*- coding: utf-8 -*-

import traceback

class NoTemplateError(Exception):
    pass

#TODO Надо перенести в items.py
class Editor(object):
    def __init__(self, name=None):
        self.name = name

    def pretty_print(self):
        print "EDITOR NAME: ",self.name

    def process_rdf_data(self):
        pass

#TODO Надо перенести в items.py
class Publication(object):
    def __init__(self, workshop=None, name=None, link=None, editors=None):
        self.workshop = workshop
        self.name = name
        self.link = workshop+link
        self.editors = editors

    def pretty_print(self):
        print "PUB NAME: ", self.name
        print "PUB LINK: ", self.link
        for editor in self.editors:
            editor.pretty_print()

    def process_rdf_data(self):
        for editor in self.editors:
            editor.process_rdf_data()

def parse_publications(self, grab, task):
    parse_templates = ['template1','template2']

    for parse_template in parse_templates:
        try:
            result = eval(parse_template+'(self, grab, task)')
            for pub in result:
                pub.process_rdf_data()
            return
        except Exception as e:
            #print "ERROR ",e.message
            #print traceback.format_exc()
            pass

    raise NoTemplateError(task.url)

def template1(self, grab, task):
    publications = []
    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/ol[@rel="dcterms:hasPart"]/li'):
        publication_name = publication.find('a[@typeof="bibo:Article"]/span').text_content()
        publication_link = publication.find('a[@typeof="bibo:Article"]').get('href')
        editors = []
        for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
            publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content();
            editors.append(Editor(publication_editor_name))
        publications.append(Publication(task.url, publication_name,publication_link,editors))

    for publication in publications:
        publication.pretty_print()

    if(len(publications)==0):
        raise Exception()

    print "Parse done. Count of publications: ", len(publications)
    return publications


def template2(self, grab, task):
    publications = []
    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/ul/li'):
        if publication.find('a/span') is not None:
            publication_name = publication.find('a/span').text_content()
        else:
            publication_name = publication.find('a').text_content()
        publication_link = publication.find('a').get('href')
        editors = []
        for publication_editor in publication.findall('span[@class="CEURAUTHORS"]'):
            editors.append(Editor(publication_editor.text_content().strip(",")))
        publications.append(Publication(task.url, publication_name,publication_link,editors))

    for publication in publications:
        publication.pretty_print()

    if(len(publications)==0):
        raise Exception()

    print "Parse done. Count of publications: ", len(publications)
    return publications

if __name__ == '__main__':
    print "not runnable"
