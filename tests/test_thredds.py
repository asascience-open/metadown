import os
import sys
import unittest

from metadown.collectors.thredds import ThreddsCollector

from metadown.downloader import XmlDownloader

class ThreddsTest(unittest.TestCase):

    def setUp(self):
        self.scratch = os.path.join(os.path.dirname(__file__),'scratch')

    def test_thredds_custom_skips(self):
        # We only want the Agg datasets
        selects = [".*SST-Agg.*"]
        # Don't process the "files/" lists
        skips = ["files/"]
        isos = ThreddsCollector("http://tds.glos.us:8080/thredds/mtri/aoc.html", selects=selects, skips=skips).run()
        # 5 Lake ISOs
        #print isos
        #assert len(isos) == 5
        XmlDownloader.run(isos, self.scratch)
        #assert os.path.isfile(os.path.join(self.scratch, "LakeErieSST-Agg.xml"))
        #assert os.path.isfile(os.path.join(self.scratch, "LakeHuronSST-Agg.xml"))
        #assert os.path.isfile(os.path.join(self.scratch, "LakeMichiganSST-Agg.xml"))
        #assert os.path.isfile(os.path.join(self.scratch, "LakeSuperiorSST-Agg.xml"))
        #assert os.path.isfile(os.path.join(self.scratch, "LakeOntarioSST-Agg.xml"))

    def test_thredds_default_skips(self):
        # We only want the Agg and Latest
        selects = [".*Nowcast-Agg.*", ".*Lastest-Forecast.*"]
        isos = ThreddsCollector("http://tds.glos.us:8080/thredds/hecwfs/hecwfs.html", selects=selects).run()
        # 2 ISOs (Nowcast and latest Forecast)
        #assert len(isos) == 2
        XmlDownloader.run(isos, self.scratch)
        #assert os.path.isfile(os.path.join(self.scratch, "HECWFS-Latest-Forecast.nc.xml"))
        #assert os.path.isfile(os.path.join(self.scratch, "HECWFS-Nowcast-Agg.nc.xml"))