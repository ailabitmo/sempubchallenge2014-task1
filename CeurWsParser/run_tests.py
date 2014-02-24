#! /usr/bin/env python
# -*- coding: utf-8 -*-
import os
import csv
import traceback

from rdflib import Graph, URIRef, Literal
from rdflib.plugins.stores import sparqlstore
from rdflib.namespace import FOAF, DCTERMS, DC
from rdflib.query import ResultRow

from CeurWsParser import config
from CeurWsParser.namespaces import SWRC, BIBO, TIMELINE


QUERY_FILENAME = 'query.sparql'
EXPECTED_FILENAME = 'expected.output'
TESTS_ROOT_DIR = 'tests'


def topython(term):
    if isinstance(term, URIRef):
        return term.n3()
    elif isinstance(term, Literal):
        return topython(term.toPython())
    elif isinstance(term, bool):
        if term:
            return "true"
        else:
            return "false"
    else:
        return term


def read_csv(utf8_data, dialect=csv.excel, **kwargs):
    csv_reader = csv.reader(utf8_data, dialect=dialect, **kwargs)
    lines = []
    for row in csv_reader:
        lines.append([unicode(cell, 'utf-8') for cell in row])
    return lines


def print_list(l):
    for row in l:
        if isinstance(row, list):
            print ', '.join(map(repr, row))
        else:
            print row


def main():
    number_of_passed = 0
    number_of_failed = 0

    graph = Graph(
        sparqlstore.SPARQLStore(config.sparqlstore['url'] + "/repositories/" + config.sparqlstore['repository'],
                                context_aware=False))
    graph.bind('foaf', FOAF)
    graph.bind('swrc', SWRC)
    graph.bind('bibo', BIBO)
    graph.bind('dcterms', DCTERMS)
    graph.bind('dc', DC)
    graph.bind('timeline', TIMELINE)

    print "Configured a SPARQLStore"

    for f in os.listdir(TESTS_ROOT_DIR):
        print "[TEST %s] Running..." % f
        try:
            passed = True
            query = open('%s/%s/%s' % (TESTS_ROOT_DIR, f, QUERY_FILENAME)).read()
            result = graph.query(query)

            results = []
            for r in result:
                result_line = map(topython, r)
                results.append(result_line)

            print "[TEST %s] Number of results: %s" % (f, len(results))

            with open('%s/%s/%s' % (TESTS_ROOT_DIR, f, EXPECTED_FILENAME), 'rb') as expected_file:
                expected = read_csv(expected_file)
                print "[TEST %s] Number of expected results: %s" % (f, len(expected))
                if len(results) != len(expected):
                    passed = False
                else:
                    for row in expected:
                        if row not in results:
                            print "[TEST %s] [%s] not found!" % (f, ', '.join(map(repr, row)))
                            print "[TEST %s] Query results:" % f
                            print_list(results)
                            passed = False
                            break

            if passed:
                print "[TEST %s] Passed!" % f
                number_of_passed += 1
            else:
                print "[TEST %s] Failed!" % f
                number_of_failed += 1

        except:
            print "[TEST %s] Failed with exception!" % f
            traceback.print_exc()

    print "\n======RESULTS======\n"
    print "Passed: %s" % number_of_passed
    print "Failed: %s" % number_of_failed


if __name__ == '__main__':
    main()