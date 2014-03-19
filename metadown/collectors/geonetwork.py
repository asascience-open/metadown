import os
import csv
import tempfile
import codecs
from urlparse import urlsplit
from shutil import abspath

import requests

from metadown.utils.etree import etree

class GeoNetworkCollector(object):
    def __init__(self, base_url):
        self.data = base_url + '/srv/en/csv.search?'
        self.download = base_url + '/srv/en/iso19139.xml?id='

    def utf_8_encoder(self, unicode_csv_data):
        for line in unicode_csv_data:
            yield line.encode('utf-8')

    def run(self):

        isos = []

        o, t =  tempfile.mkstemp()
        with codecs.open(t, "w+", "utf-8") as h:
            h.write(requests.get(self.data).text)

        with codecs.open(t, "rb", "utf-8") as f:
            reader = csv.DictReader(self.utf_8_encoder(f))
            for row in reader:
                if row.get('schema') != 'iso19139':
                    continue

                download_url = self.download + row.get('id')
                isos.append(download_url)

        os.unlink(f.name)

        return isos

    @staticmethod
    def namer(url, **kwargs):
        uid = urlsplit(url).query
        uid = uid[uid.index("=")+1:]
        return "GeoNetwork-" + uid + ".xml"

    @staticmethod
    def modifier(url, **kwargs):
        # translate ISO19139 to ISO19115
        gmi_ns = "http://www.isotc211.org/2005/gmi"
        etree.register_namespace("gmi",gmi_ns)

        new_root = etree.Element("{%s}MI_Metadata" % gmi_ns)
        old_root = etree.parse(url).getroot()

        # carry over an attributes we need
        [new_root.set(k,v) for k,v in old_root.attrib.items()]
        # carry over children
        [new_root.append(e) for e in old_root]

        return etree.tostring(new_root, encoding="UTF-8", pretty_print=True, xml_declaration=True)
                
