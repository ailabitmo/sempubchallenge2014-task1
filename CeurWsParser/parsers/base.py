import inspect

from grab.error import DataNotFound


class NoTemplateError(Exception):
    pass


class Parser:
    def __init__(self, grab, task, graph):
        self.grab = grab
        self.task = task
        self.graph = graph
        self.data = {}

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
            raise NoTemplateError("%s" % self.task.url)

    def write(self):
        raise Exception("Method doesn't have implementation!")

    def write_triples(self, triples):
        if isinstance(triples, list):
            for triple in triples:
                if isinstance(triple, tuple):
                    self.graph.add(triple)
                else:
                    raise Exception("%s should be a tuple" % repr(triple))
        elif isinstance(triples, tuple):
            self.graph.add(triples)
        else:
            raise Exception("%s is wrong parameter! Should be a list of tuples or a tuple" % repr(triples))