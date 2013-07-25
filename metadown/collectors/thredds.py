import urlparse

import requests

from metadown.utils.utils import construct_url
from metadown.utils.etree import etree

class ThreddsCollector(object):
    def __init__(self, catalog_url, datasets=None, skips=[]):
        u = urlparse.urlsplit(catalog_url)

        self.datasets = datasets
        # Skip these dataset links, such as a list of files
        # ie. "files/"
        self.skips = skips
        self.url = catalog_url
        self.base_url = u.scheme + "://" + u.netloc

    def run(self, url=None):
        if url is None:
            url = self.url

        try:
            r = requests.get(url)
        except requests.exceptions.RequestException:
            print "Error connecting to %s" % url
            return []

        tree = etree.HTML(r.text)

        isos = []

        others = tree.findall('.//tr/td/a[@href]')
        if len(others) > 0:
            # Catalog page
            for a in others:
                if a.find("tt").text in self.skips:
                    continue
                cat = construct_url(self.base_url, url, a.attrib.get('href'))
                i = self.run(url=cat)
                for x in i:
                    if x is not None:
                        isos.append(x)
        else:
            # If subset is defined, select only those.
            # There are TDS ID's in the catalog.            
            if self.datasets is not None:
                good = False
                lis = tree.findall(".//body/ul/li")[0:4]
                for li in lis:
                    try:
                        li.find("em").text.find("ID:")
                        for d in self.datasets:
                            if etree.tostring(li).find(d) != -1:
                                good = True
                                break
                    except:
                        pass

                if not good:
                    return []

            # Dataset page
            datasets = tree.findall('.//ol/li')

            for d in datasets:
                # Look for ISO links:
                try:
                    d.find("b").text.index("ISO")
                except:
                    continue

                iso_url = construct_url(self.base_url, url, d.find("a").attrib.get("href"))

                return [iso_url]

        return filter(None,isos)
        
