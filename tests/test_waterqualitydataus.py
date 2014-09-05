import os
import sys
import unittest

from metadown.collectors.waterqualitydataus import WaterQualityDataUs, WqxOutbound

from owslib.iso import MD_Metadata, SV_ServiceIdentification

from metadown.downloader import XmlDownloader
from metadown.utils.etree import etree

class ThreddsTest(unittest.TestCase):

    def setUp(self):
        self.scratch = os.path.join(os.path.dirname(__file__), 'scratch')

    def test_bbox(self):
        bbox = (-78, 28, -70, 32)
        isos = WaterQualityDataUs(bBox=bbox).run()
        for iso in isos:
            # Results are a str
            xml_obj  = etree.fromstring(str(iso))
            metadata = MD_Metadata(xml_obj)
            assert metadata is not None

    def test_services(self):
        bbox = (-78, 28, -70, 32)
        services = [
            dict(name="NDBC SOS - GetCapabilities",
                 url="http://sdf.ndbc.noaa.gov/sos/server.php?request=GetCapabilities&service=SOS",
                 description="NDBC SOS GetCapabilities Request",
                 type="SOS"),
            dict(name="NDBC SOS - DescribeSensor",
                 url="http://sdf.ndbc.noaa.gov/sos/server.php?request=DescribeSensor&service=SOS&version=1.0.0&outputformat=text/xml;subtype=%22sensorML/1.0.1%22&procedure={id}",
                 description="NDBC SOS DescribeSensor Request",
                 type="SOS"),
            dict(name="NDBC SOS - GetObservation",
                 url="http://sdftest.ndbc.noaa.gov/sos/server.php?request=GetObservation&version=1.0.0&service=SOS&observedProperty=air_temperature&responseFormat=text%2Fxml%3Bsubtype%3D%22om%2F1.0.0%22&eventtime=latest&offering={id}",
                 description="NDBC SOS DescribeSensor Request",
                 type="SOS")
        ]
        isos = WaterQualityDataUs(bBox=bbox, services=services).run()
        for iso in isos:
            # Results are a str
            xml_obj  = etree.fromstring(str(iso))
            metadata = MD_Metadata(xml_obj)
            service_identification = next(x for x in metadata.identificationinfo if isinstance(x, SV_ServiceIdentification))
            self.assertEquals(len(service_identification.operations), len(services))
            for op in service_identification.operations:
                service = next(k for k in services if k["name"] == op["name"])
                self.assertEquals(service["url"], op["connectpoint"][0].url)
                self.assertEquals(service["type"], op["connectpoint"][0].name)
                self.assertEquals(service["description"], op["connectpoint"][0].description)

