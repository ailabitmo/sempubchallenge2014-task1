
class Parser:
    def __init__(self, grab, task, graph):
        self.grab = grab
        self.task = task
        self.graph = graph
        self.data = {}

    def parse(self):
        pass

    def write(self):
        pass

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