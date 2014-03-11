import inspect

from grab.error import DataNotFound
from grab.tools import rex


class NoTemplateError(Exception):
    pass


class Parser:
    def __init__(self, grab, task, graph, failonerror=True, spider=None):
        """
        Args:
            failonerror (boolean): if True, then parse() method doesn't raise NoTemplateError and write() is not called
        """
        self.grab = grab
        self.task = task
        self.graph = graph
        self.data = {}
        self.failonerror = failonerror
        self.spider = spider
        self.step = 1000

    def parse(self):
        parsed = False
        for method in inspect.getmembers(self, predicate=inspect.ismethod):
            method_name = method[0]
            if method_name.startswith('parse_template_'):
                try:
                    eval('self.' + method_name + '()')
                    parsed = True
                    break
                except DataNotFound:
                    # import traceback
                    # traceback.print_exc()
                    pass
        if not parsed:
            if self.failonerror:
                raise NoTemplateError("%s" % self.task.url)
        else:
            self.write()

    def write(self):
        raise Exception("Method doesn't have implementation!")

    def write_triples(self, triples):
        if isinstance(triples, list):
            for triple in triples:
                self.graph.add(triple)
            # length = len(triples)
            # print length
            # if length < self.step:
            #     self.graph.addN(triples)
            # else:
            #     for i in range(0, length, self.step):
            #         self.graph.addN(triples[i: i + self.step if i + self.step < length else length])
        elif isinstance(triples, tuple):
            self.graph.add(triples)
        else:
            raise Exception("%s is wrong parameter! Should be a list of tuples or a tuple" % repr(triples))

    def rex(self, body, patterns, flags=0, default=rex.NULL):
        result = None
        lastexception = DataNotFound()
        found = False
        for pattern in patterns:
            try:
                result = rex.rex(body, pattern, flags, default)
                found = True
                if not result:
                    break
            except DataNotFound as dnf:
                lastexception = dnf
        if found:
            return result
        else:
            raise lastexception