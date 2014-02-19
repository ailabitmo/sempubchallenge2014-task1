#! /usr/bin/env python
# -*- coding: utf-8 -*-

import traceback
import items
import re

class NoTemplateError(Exception):
    pass

class NoPublicationsError(Exception):
    pass

def parse_publications(repo, grab, task):
    parse_templates = ['template1','template4']

    for parse_template in parse_templates:
        try:
            publications = eval(parse_template+'(grab, task)')
            for publication in publications:
                pass
                #pub.pretty_print()
                #publication.save(repo)
            print "Parse done", task.url, ". Count of publications: ", len(publications), " ",parse_template
            return
        except NoPublicationsError as e:
            # print "ERROR ",e.message
            # print traceback.format_exc()
            pass

    raise NoTemplateError(task.url)


def template1( grab, task):
    publications = []
    workshop = task.url
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)

    for publication in grab.tree.xpath('//div[@class="CEURTOC"]/*[@rel="dcterms:hasPart"]/li'):
        publication_name = publication.find('a[@typeof="bibo:Article"]/span').text_content()
        publication_link = publication.find('a[@typeof="bibo:Article"]').get('href')
        editors = []
        for publication_editor in publication.findall('span/span[@rel="dcterms:creator"]'):
            publication_editor_name = publication_editor.find('span[@property="foaf:name"]').text_content();
            editors.append(items.Creator(publication_editor_name))
        publications.append(items.Publication(volume_number, publication_name, workshop+publication_link ,editors))

    if(len(publications)==0):
        raise NoPublicationsError()

    return publications


def template4( grab, task):
    publications = []
    workshop = task.url
    volume_number = re.match(r'.*http://ceur-ws.org/Vol-(\d+).*', workshop).group(1)


    for publication in grab.tree.xpath('//div[@class="CEURTOC"]//li'):
        try:
            publication_name = publication.find_class('CEURTITLE')[0].text
            publication_link = publication.find('a').get('href')
            editors = []
            for publication_editor in publication.find_class('CEURAUTHORS'):
                for publication_editor_name in publication_editor.text_content().split(","):
                    editors.append(items.Creator(publication_editor_name.strip()))
            publications.append(items.Publication(volume_number, publication_name, workshop+publication_link, editors))
        except:
            pass

    if(len(publications)==0):
        raise NoPublicationsError()

    return publications

# def check_for_valid_paper(publication):
#     if(publication.link)

if __name__ == '__main__':
    print "not runnable"
