import os
import sys
import unittest

from metadown.collectors.geonetwork import GeoNetworkCollector

from metadown.downloader import XmlDownloader

class GeoNetworkTest(unittest.TestCase):

    scratch_dir = os.path.join(os.path.dirname(__file__),'scratch')

    isos = GeoNetworkCollector("http://data.glos.us/metadata").run()
    XmlDownloader.run(isos, scratch_dir, namer=GeoNetworkCollector.namer, modifier=GeoNetworkCollector.modifier)