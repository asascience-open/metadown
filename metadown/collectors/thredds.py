import urlparse

import requests

from thredds_crawler.crawl import Crawl

class ThreddsCollector(object):
    def __init__(self, url, selects=None, skips=None):
        self.selects    = selects
        self.skips      = skips
        self.url        = url

    def run(self):
        c = Crawl(self.url, self.selects, self.skips)
        urls = ["%s?dataset=%s&catalog=%s" % (s.get("url"), d.id, d.catalog_url) for d in c.datasets for s in d.services if s.get("service").lower() == "iso"]
        return urls
