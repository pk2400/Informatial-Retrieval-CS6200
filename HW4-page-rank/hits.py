from elasticsearch import Elasticsearch
import random
import math
import json
import os


class RootSet:

    def __init__(self):
        # this is the info to interact with Elasticsearch cloud server, already expired
        self.hosts = ["https://e677ecbec38f4ca6a93a6538d6dc2918.northamerica-northeast1.gcp.elastic-cloud.com:9243"]
        self.cloud_id = "ZC_CS6200:bm9ydGhhbWVyaWNhLW5vcnRoZWFzdDEuZ2NwLmVsYXN0aWMtY2xvdWQuY29tJGU2NzdlY2JlYzM4ZjRjYTZhOTNhNjUzOGQ2ZGMyOTE4JGUyYmZiMjAwNjY2NjRlOTVhNjc0ZWY0OWE5ODBhMzkz"
        self.index = "hw3"
        self.es = Elasticsearch(hosts=self.hosts, timeout=60, clould_id=self.cloud_id,
                                http_auth=('elastic', 'rlj3NbyVqLOIUKKHhH4OGAjC'))
        self.root_set = []

    def initialize(self):
        res = self.es.search(index=self.index,
                             body={
                                  "from": 0,
                                  "size": 1000,
                                  "query": {
                                    "match": {
                                      "text_content": "catholic church"
                                    }
                                  },
                                  "_source": ""
                             })['hits']['hits']
        for item in res:
            self.root_set.append(item['_id'])


class Hits:

    def __init__(self, root_set):
        self.in_links = {}
        self.out_links = {}
        self.root_set = root_set
        self.base_set = set(root_set)
        self.limit = 20
        self.authority = {}
        self.hub = {}

        self.initialize()

    def initialize(self):
        self.read_in_links()
        self.read_out_links()

    def update_base_set(self):
        add_out_pages = set()
        for page in self.base_set:
            if page in self.out_links:
                out_pages = self.out_links[page]
                if len(out_pages) <= self.limit:
                    add_out_pages.update(out_pages)
                else:
                    add_out_pages.update(random.sample(out_pages, self.limit))
        add_in_pages = set()
        for page in self.base_set:
            if page in self.in_links:
                in_pages = self.in_links[page]
                if len(in_pages) <= self.limit:
                    add_in_pages.update(in_pages)
                else:
                    add_in_pages.update(random.sample(in_pages, self.limit))
        print("out_links: ", len(add_out_pages))
        print("in_links: ", len(add_in_pages))
        self.base_set.update(add_out_pages)
        self.base_set.update(add_in_pages)
        print("length of base set: {}".format(len(self.base_set)))

    def compute_hits(self):
        # initialize both scores
        for page in self.base_set:
            self.authority[page] = 1.0
            self.hub[page] = 1.0
        k = 0
        while k < 30:
            self.update_authority()
            self.update_hub()
            print(self.authority[self.root_set[0]], self.hub[self.root_set[0]])
            k += 1

    def write_hits(self):
        if os.path.exists("./hits/authority.txt"):
            os.remove("./hits/authority.txt")
        if os.path.exists("./hits/hub.txt"):
            os.remove("./hits/hub.txt")
        autho_keys = sorted(self.authority, key=self.authority.get, reverse=True)[:500]
        hub_keys = sorted(self.hub, key=self.hub.get, reverse=True)[:500]
        with open("./hits/authority.txt", "a") as f:
            for key in autho_keys:
                line = "{0}    {1}\n".format(key, self.authority[key])
                f.write(line)
        with open("./hits/hub.txt", "a") as f:
            for key in hub_keys:
                line = "{0}    {1}\n".format(key, self.hub[key])
                f.write(line)

    def update_authority(self):
        norm = 0
        for page in self.base_set:
            new_authority = 0
            if page in self.in_links:
                for in_page in self.in_links[page]:
                    if in_page in self.base_set:
                        new_authority += self.hub[in_page]
                self.authority[page] = new_authority
                norm += new_authority ** 2
            else:
                self.authority[page] = 0
        norm = math.sqrt(norm)
        for page in self.base_set:
            self.authority[page] = self.authority[page] / norm

    # def update_authority(self):
    #     norm = 0
    #     for page in self.base_set:
    #         new_authority = 0
    #         if page in self.in_links:
    #             for in_page in self.in_links[page]:
    #                 if in_page in self.base_set:
    #                     new_authority += self.hub[in_page]
    #             self.authority[page] = new_authority
    #             norm += new_authority ** 2
    #         else:
    #             norm += self.authority[page] ** 2
    #     norm = math.sqrt(norm)
    #     for page in self.base_set:
    #         self.authority[page] = self.authority[page] / norm

    def update_hub(self):
        norm = 0
        for page in self.base_set:
            new_hub = 0
            if page in self.out_links:
                for out_page in self.out_links[page]:
                    if out_page in self.base_set:
                        new_hub += self.authority[out_page]
                norm += new_hub ** 2
                self.hub[page] = new_hub
            else:
                self.hub[page] = 0
        norm = math.sqrt(norm)
        for page in self.base_set:
            self.hub[page] = self.hub[page] / norm

    # def update_hub(self):
    #     norm = 0
    #     for page in self.base_set:
    #         new_hub = 0
    #         if page in self.out_links:
    #             for out_page in self.out_links[page]:
    #                 if out_page in self.base_set:
    #                     new_hub += self.authority[out_page]
    #             norm += new_hub ** 2
    #             self.hub[page] = new_hub
    #         else:
    #             norm += self.hub[page] ** 2
    #     norm = math.sqrt(norm)
    #     for page in self.base_set:
    #         self.hub[page] = self.hub[page] / norm

    def read_in_links(self):
        # with open('./links/new_in_links.json', "r") as f:
        #     for line in f.readlines():
        #         line = json.loads(line)
        #         for i in line:
        #             self.in_links[i] = line[i]
        with open("./links/new_in_links.txt", "r") as f:
            for line in f.readlines():
                new_line = line.replace(" \n", "")
                new_line = new_line.replace("\n", "")
                new_line = new_line.split(" ")
                if len(new_line) == 1:
                    self.in_links[new_line[0]] = []
                else:
                    self.in_links[new_line[0]] = new_line[1:]
        print("read in_links successful")

    def read_out_links(self):
        # with open('./links/new_out_links.json', "r") as f:
        #     for line in f.readlines():
        #         line = json.loads(line)
        #         for i in line:
        #             self.out_links[i] = line[i]
        with open("./links/out_links.txt", "r", encoding="utf-8") as f:
            for line in f.readlines():
                new_line = line.replace(" \n", "")
                new_line = new_line.replace("\n", "")
                new_line = new_line.split(" ")
                if len(new_line) == 1:
                    self.out_links[new_line[0]] = []
                else:
                    self.out_links[new_line[0]] = new_line[1:]
        print("read out_links successful")


my_root = RootSet()
my_root.initialize()

my_hits = Hits(my_root.root_set)
my_hits.update_base_set()
my_hits.compute_hits()
my_hits.write_hits()
