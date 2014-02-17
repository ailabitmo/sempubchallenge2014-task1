#! /usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
import items
import re

class NoTemplateError(Exception):
    pass



def parse_publications(self, grab, task):
    parse_templates = ['template1','template2','template3','template4']

    for parse_template in parse_templates:
        try:
            result = eval(parse_template+'(self, grab, task)')
            for pub in result:
                pub.pretty_print()
                #pub.save()
            return
        except Exception as e:
            # print "ERROR ",e.message
            # print traceback.format_exc()
            pass

    raise NoTemplateError(task.url)


def template1(self, grab, task):
    publications = []
    workshop = task.url
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/ol[@rel="dcterms:hasPart"]/li'):
        publication_name = publication.find('a[@typeof="bibo:Article"]/span').text_content()
        publication_link = publication.find('a[@typeof="bibo:Article"]').get('href')
        editors = []
        for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
            publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content();
            editors.append(items.Creator(publication_editor_name))
        publications.append(items.Publication(volume_number, publication_name, workshop+publication_link ,editors))

    if(len(publications)==0):
        raise Exception()

    print "Parse done. Count of publications: ", len(publications)
    return publications


def template2(self, grab, task):
    publications = []
    workshop = task.url
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/ul/li'):
        if publication.find('a/span') is not None:
            publication_name = publication.find('a/span').text_content()
        else:
            publication_name = publication.find('a').text_content()
        publication_link = publication.find('a').get('href')
        editors = []
        for publication_editor in publication.findall('span[@class="CEURAUTHORS"]'):
            for publication_editor_name in publication_editor.text_content().split(","):
                editors.append(items.Creator(publication_editor_name.strip()))
        publications.append(items.Publication(volume_number, publication_name, workshop+publication_link, editors))

    if(len(publications)==0):
        raise Exception()

    print "Parse done. Count of publications: ", len(publications)
    return publications


def template3(self, grab, task):
    publications = []
    workshop = task.url
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/ol[@rel="dcterms:hasPart"]/li'):
        publication_name = publication.find_class('CEURTITLE')[0].text
        publication_link = publication.find('a').get('href')
        editors = []
        for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
            publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content();
            editors.append(items.Creator(publication_editor_name))
        publications.append(items.Publication(volume_number, publication_name, workshop+publication_link ,editors))

    if(len(publications)==0):
        raise Exception()

    print "Parse done. Count of publications: ", len(publications)
    return publications

def template4(self, grab, task):
    publications = []
    workshop = task.url
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/ol/li'):
        publication_name = publication.find_class('CEURTITLE')[0].text
        publication_link = publication.find('a').get('href')
        editors = []
        for publication_editor in publication.find_class('CEURAUTHORS'):
            for publication_editor_name in publication_editor.text_content().split(","):
                editors.append(items.Creator(publication_editor_name.strip()))
        publications.append(items.Publication(volume_number, publication_name, workshop+publication_link, editors))

    if(len(publications)==0):
        raise Exception()

    print "Parse done. Count of publications: ", len(publications)
    return publications

if __name__ == '__main__':
    print "not runnable"
