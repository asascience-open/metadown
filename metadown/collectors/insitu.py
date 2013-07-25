import requests

from metadown.utils.etree import etree

class InSituCollector(object):
    def __init__(self, url, category):
        self.url = url
        self.category = category

    def run(self):
        isos = []

        resp = requests.get(self.url + "/sources.html").text
        tree = etree.HTML(resp)

        for source in tree.findall(".//li"):
            if source.text.lower() == self.category.lower():

                # get list of files in source
                dirlist = requests.get(self.url + "/" + source.text + '/list.html').text
                dirtree = etree.HTML(dirlist)

                for iso in dirtree.findall('.//li'):
                    isos.append(self.url + "/" + source.text + '/' + iso.text.strip())

        return isos
