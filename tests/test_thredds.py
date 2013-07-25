import os
import sys
import unittest

from metadown.collectors.thredds import ThreddsCollector

from metadown.downloader import XmlDownloader

class ThreddsTest(unittest.TestCase):

    # datasets: The ID in THREDDS needs to contain one of these strings to be identified.
    # skips: The LINK path in the actual thredds catalog webpage can't be equal to any of these strings
    scratch_dir = os.path.join(os.path.dirname(__file__),'scratch')
    # We only want the Agg datasets
    datasets = ["SST-Agg"]
    # Don't process the "files/" lists
    skips = ["files/"]
    isos = ThreddsCollector("http://tds.glos.us:8080/thredds/mtri/aoc.html", datasets=datasets, skips=skips).run()
    # 5 Lake ISOs
    assert len(isos) == 5
    XmlDownloader.run(isos, scratch_dir)
    assert os.path.isfile(os.path.join(scratch_dir, "LakeErieSST-Agg.xml"))
    assert os.path.isfile(os.path.join(scratch_dir, "LakeHuronSST-Agg.xml"))
    assert os.path.isfile(os.path.join(scratch_dir, "LakeMichiganSST-Agg.xml"))
    assert os.path.isfile(os.path.join(scratch_dir, "LakeSuperiorSST-Agg.xml"))
    assert os.path.isfile(os.path.join(scratch_dir, "LakeOntarioSST-Agg.xml"))


    # We only want the Agg and Latest
    datasets = ["Nowcast-Agg", "Lastest-Forecast"]
    # Don't process the "files/" lists
    skips = ["Nowcast - Individual Files/", "Forecast - Individual Files/"]
    isos = ThreddsCollector("http://tds.glos.us:8080/thredds/hecwfs/hecwfs.html", datasets=datasets, skips=skips).run()
    # 2 ISOs (Nowcast and latest Forecast)
    assert len(isos) == 2
    XmlDownloader.run(isos, scratch_dir)
    assert os.path.isfile(os.path.join(scratch_dir, "HECWFS-Latest-Forecast.nc.xml"))
    assert os.path.isfile(os.path.join(scratch_dir, "HECWFS-Nowcast-Agg.nc.xml"))
