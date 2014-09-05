import os
import csv
import tempfile
import codecs
from urlparse import urlsplit
from shutil import abspath
from jinja2 import Template

import pytz
from copy import copy
from datetime import datetime
import requests

from dateutil.parser import parse as dateparse

from metadown.utils.etree import etree
from owslib.util import testXMLValue, testXMLAttribute
from owslib.util import nspath as nsp

from metadown import logger


class WaterQualityDataUs(object):

    def __init__(self, *args, **kwargs):
        self.meta   = "http://www.waterqualitydata.us/Station/search"
        self.data   = "http://www.waterqualitydata.us/Result/search"

        kwargs["mimeType"] = "xml"
        if kwargs.get("bBox"):
            kwargs["bBox"] = ",".join(map(unicode, kwargs.get("bBox")))

        # User supplied services
        self.services = kwargs.pop("services", None)
        self.params   = kwargs

    def run(self):

        stations = []
        lookup   = []

        # Get a list of stations from a Meta request
        meta     = requests.get(self.meta, params=self.params)
        wqx_meta = WqxOutbound(meta.text)
        if wqx_meta.failed is True:
            logger.info("WQX request returned no data: %s" % meta.url)
            return []
        for org in wqx_meta.organizations:
            for monitoring_location in org.locations:
                station_meta = dict(organization_id=org.description.id,
                                    organization_name=org.description.name)
                attribs = monitoring_location.__dict__
                del attribs["_root"]
                station_meta.update(attribs)

                # Now set the station's location
                vertical = 0
                try:
                    vertical = float(monitoring_location.vertical_measure_value)
                    if monitoring_location.vertical_measure_units == "ft":
                        vertical /= 3.28084
                except:
                    pass
                finally:
                    station_meta["vertical_measure_value"] = vertical
                    station_meta["vertical_measure_units"] = "m"
                stations.append(station_meta)
                lookup.append(monitoring_location.id)

        # Now request data for the results for each station
        results     = requests.get(self.data, params=self.params).text
        wqx_results = WqxOutbound(results)
        if wqx_results.failed is True:
            logger.info("WQX request returned no data: %s" % meta.url)
            return []
        for org in wqx_results.organizations:
            for a in org.activities:
                station = stations[lookup.index(a.location_id)]
                station["data"] = []
                for r in a.results:
                    vs = dict(time=a.start_time)
                    attribs = r.__dict__
                    del attribs["_root"]
                    vs.update(attribs)
                    station["data"].append(vs)

        common_metadata = dict(current_datetime=datetime.utcnow().replace(tzinfo=pytz.utc).isoformat())

        isos = []
        for stat in stations:

            # figure out time bounds
            times = list(set(map(lambda x: x["time"], station["data"])))
            stat["min_time"] = min(times).isoformat()
            stat["max_time"] = max(times).isoformat()

            variables = map(lambda x: dict(name=x["name"], units=x["units"], description=x["short_name"]), station["data"])
            stat["variables"] = variables

            stat.update(common_metadata)

            if self.services:
                common_services = copy(self.services)
                for c in common_services:
                    for k in c.keys():
                        c[k] = c[k].format(**stat)
                stat["services"] = common_services

            isos.append(station_to_xml(stat))

        return isos


def station_to_xml(station):
    text = ""
    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", "iso19115-2.xml")), "r") as r:
        text = r.read()
    template = Template(text)
    result = template.render(station)
    return result


class WqxOutbound(object):
    """
        An WQX formatted <wqx:WQX> block
    """
    def __init__(self, element):
        wqx_ns = "http://qwwebservices.usgs.gov/schemas/WQX-Outbound/2_0/"

        if isinstance(element, str) or isinstance(element, unicode):
            try:
                self._root = etree.fromstring(element)
            except ValueError:
                # Strip out the XML header due to UTF8 encoding declaration
                self._root = etree.fromstring(element[38:])
        else:
            self._root = element

        if hasattr(self._root, 'getroot'):
            self._root = self._root.getroot()

        self.failed = False
        self.organizations = []
        orgs = self._root.findall(nsp("Organization", wqx_ns))

        if orgs is None:
            self.failed = True
        else:
            for org in orgs:
                self.organizations.append(WqxOrganization(org, wqx_ns))


class WqxOrganization(object):
    """
        An WQX formatted <wqx:Organization> block
    """
    def __init__(self, element, wqx_ns):
        self._root = element

        self.description = WqxOrganizationDescription(self._root.find(nsp("OrganizationDescription",wqx_ns)), wqx_ns)

        self.locations = []
        mls = self._root.findall(nsp("MonitoringLocation",wqx_ns))
        for loc in mls:
            if loc is not None:
                self.locations.append(WqxMonitoringLocation(loc, wqx_ns))

        self.activities = []
        for act in self._root.findall(nsp("Activity", wqx_ns)):
            self.activities.append(WqxActivity(act, wqx_ns))


class WqxActivity(object):
    """
        An WQX formatted <wqx:Activity> block
    """
    def __init__(self, element, wqx_ns):
        self._root = element

        des = self._root.find(nsp("ActivityDescription", wqx_ns))
        if des is not None:
            self.id = testXMLValue(des.find(nsp("ActivityIdentifier", wqx_ns)))
            self.type = testXMLValue(des.find(nsp("ActivityTypeCode", wqx_ns)))
            self.media = testXMLValue(des.find(nsp("ActivityMediaName", wqx_ns)))

        # Date/Time
        sd = testXMLValue(des.find(nsp("ActivityStartDate", wqx_ns)))  # YYYY-MM-DD
        parse_string = "%s" % sd

        st = des.find(nsp("ActivityStartTime", wqx_ns))
        # If no time is defined, skip trying to pull it out and just use the date
        if st is not None:
            t = testXMLValue(st.find(nsp("Time", wqx_ns)))
            tz = testXMLValue(st.find(nsp("TimeZoneCode", wqx_ns)))

            parse_string = "%s %s" % (parse_string, t)
            if tz is not None:
                parse_string = "%s %s" % (parse_string, tz)

        self.start_time = dateparse(parse_string)
        if self.start_time.tzinfo is None:
            self.start_time = self.start_time.replace(tzinfo=pytz.utc)

        self.project = testXMLValue(des.find(nsp("ProjectIdentifier", wqx_ns)))
        self.location_id = testXMLValue(des.find(nsp("MonitoringLocationIdentifier", wqx_ns)))
        self.comment = testXMLValue(des.find(nsp("ActivityCommentText", wqx_ns)))

        self.method_id = None
        self.method_name = None
        self.method_context = None
        # Method
        smpl = self._root.find(nsp("SampleDescription", wqx_ns))
        if smpl is not None:
            self.sample_collection_equipment_name = testXMLValue(smpl.find(nsp("SampleCollectionEquipmentName", wqx_ns)))
            smplcol = smpl.find(nsp("SampleCollectionMethod", wqx_ns))
            if smplcol is not None:
                self.method_id = testXMLValue(smplcol.find(nsp("MethodIdentifier", wqx_ns)))
                self.method_context = testXMLValue(smplcol.find(nsp("MethodIdentifierContext", wqx_ns)))
                self.method_name = testXMLValue(smplcol.find(nsp("MethodName", wqx_ns)))

        self.results = []
        for res in self._root.findall(nsp("Result", wqx_ns)):
            self.results.append(WqxResult(res, wqx_ns))


class WqxResult(object):
    def __init__(self, element, wqx_ns):
        self._root = element

        des = self._root.find(nsp("ResultDescription", wqx_ns))
        self.name = None
        self.short_name = None
        self.status = None
        self.stastistical_base_code = None
        self.value_type = None
        self.weight_basis = None
        self.time_basis = None
        self.temperature_basis = None
        if des is not None:
            self.name = testXMLValue(des.find(nsp("CharacteristicName", wqx_ns)))
            self.short_name = testXMLValue(des.find(nsp("ResultSampleFractionText", wqx_ns)))
            self.status = testXMLValue(des.find(nsp("ResultStatusIdentifier", wqx_ns)))
            self.stastistical_base_code = testXMLValue(des.find(nsp("StatisticalBaseCode", wqx_ns)))
            self.value_type = testXMLValue(des.find(nsp("ResultValueTypeName", wqx_ns)))
            self.weight_basis = testXMLValue(des.find(nsp("ResultWeightBasisText", wqx_ns)))
            self.time_basis = testXMLValue(des.find(nsp("ResultTimeBasisText", wqx_ns)))
            self.temperature_basis = testXMLValue(des.find(nsp("ResultTemperatureBasisText", wqx_ns)))

        rm = des.find(nsp("ResultMeasure", wqx_ns))
        self.value = None
        self.units = None
        if rm is not None:
            self.value = testXMLValue(rm.find(nsp("ResultMeasureValue", wqx_ns)))
            self.units = testXMLValue(rm.find(nsp("MeasureUnitCode", wqx_ns)))

        qu = des.find(nsp("DataQuality", wqx_ns))
        self.quality = None
        if qu is not None:
            self.quality = testXMLValue(qu.find(nsp("PrecisionValue", wqx_ns)))

        am = self._root.find(nsp("ResultAnalyticalMethod", wqx_ns))
        self.analytical_method_id = None
        self.analytical_method_id_context = None
        if am is not None:
            self.analytical_method_id = testXMLValue(am.find(nsp("MethodIdentifier", wqx_ns)))
            self.analytical_method_id_context = testXMLValue(am.find(nsp("MethodIdentifierContext", wqx_ns)))

        # Skipping <ResultLabInformation> for now.


class WqxOrganizationDescription(object):
    """
        An WQX formatted <wqx:OrganizationDescription> block
    """
    def __init__(self, element, wqx_ns):
        self._root = element

        self.id = testXMLValue(self._root.find(nsp("OrganizationIdentifier", wqx_ns)))
        self.name = testXMLValue(self._root.find(nsp("OrganizationFormalName", wqx_ns)))


class WqxMonitoringLocation(object):
    """
        An WQX formatted <wqx:MonitoringLocation> block
    """
    def __init__(self, element, wqx_ns):
        self._root = element

        self.id = None
        self.name = None
        self.type = None
        self.description = None
        self.huc = None
        identity = self._root.find(nsp("MonitoringLocationIdentity", wqx_ns))
        if identity is not None:
            self.id = testXMLValue(identity.find(nsp("MonitoringLocationIdentifier", wqx_ns)))
            self.name = testXMLValue(identity.find(nsp("MonitoringLocationName", wqx_ns)))
            self.type = testXMLValue(identity.find(nsp("MonitoringLocationTypeName", wqx_ns)))
            self.description = testXMLValue(identity.find(nsp("MonitoringLocationDescriptionText", wqx_ns)))
            self.huc = testXMLValue(identity.find(nsp("HUCEightDigitCode", wqx_ns)))

        self.latitude = None
        self.longitude = None
        self.map_scale = None
        self.horizontal_collection_method = None
        self.horizontal_crs_name = None
        self.horizontal_crs = None
        self.vertical_crs_name = None
        self.vertical_crs = None
        geo = self._root.find(nsp("MonitoringLocationGeospatial", wqx_ns))
        if geo is not None:
            self.latitude = testXMLValue(geo.find(nsp("LatitudeMeasure", wqx_ns)))
            self.longitude = testXMLValue(geo.find(nsp("LongitudeMeasure", wqx_ns)))
            self.map_scale = testXMLValue(geo.find(nsp("SourceMapScaleNumeric", wqx_ns)))
            self.horizontal_collection_method = testXMLValue(geo.find(nsp("HorizontalCollectionMethodName", wqx_ns)))
            self.horizontal_crs_name = testXMLValue(geo.find(nsp("HorizontalCoordinateReferenceSystemDatumName", wqx_ns)))
            self.vertical_crs_name = testXMLValue(geo.find(nsp("VerticalCollectionMethodName", wqx_ns)))

        self.vertical_measure_value = None
        self.vertical_measure_units = None
        vm = geo.find(nsp("VerticalMeasure", wqx_ns))
        if vm is not None:
            self.vertical_measure_value = testXMLValue(vm.find(nsp("MeasureValue", wqx_ns)))
            self.vertical_measure_units = testXMLValue(vm.find(nsp("MeasureUnitCode", wqx_ns)))

        self.country = testXMLValue(geo.find(nsp("CountryCode", wqx_ns)))
        self.state = testXMLValue(geo.find(nsp("StateCode", wqx_ns)))
        self.county = testXMLValue(geo.find(nsp("CountyCode", wqx_ns)))
