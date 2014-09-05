metadown
========

A programatic collector/downloader for IOOS like 19115-2 metadata written in Python.

Services supported:

* [THREDDS](http://www.unidata.ucar.edu/projects/THREDDS/) (ISO service must be enabled)
* [GeoNetwork](http://geonetwork-opensource.org/)

## Installation

metadown is available on pypi and is easiest installed using `pip`.

```bash
pip install metadown
```
`lxml`, `requests`, and `thredds_crawler` will be installed automatically

## Usage

### THREDDS

The ThreddsCollector can take three optional arguments. Both are strongly suggested so you don't crawl an
entire THREDDS server (unless that is what you want to do).

* `debug` (bool) - Print what is happening to the console.  Useful for debugging what to put into `selects` and `skips`.
* `selects` (list) - Select datasets based on their THREDDS ID. Python regex is supported.
* `skips` (list) - Skip datasets based on their name and catalogRefs based on their xlink:title. By default, the crawler uses some common regular expressions to skip lists of thousands upon thousands of individual files that are part of aggregations or FMRCs (they are below.)  Setting the `skip` parameter to anything other than a superset of the defaults below runs the risk of having some angry system admins after you.

    *  `.*files.*`
    *  `.*Individual Files.*`
    *  `.*File_Access.*`
    *  `.*Forecast Model Run.*`
    *  `.*Constant Forecast Offset.*`
    *  `.*Constant Forecast Date.*`

You can access the default `skip` list through the ThreddsCollector.SKIPS class variable
```python
> from metadown.collectors.thredds import ThreddsCollector
> print ThreddsCollector.SKIPS
[
  '.*files.*',
  '.*Individual Files.*',
  '.*File_Access.*',
  '.*Forecast Model Run.*',
  '.*Constant Forecast Offset.*',
  '.*Constant Forecast Date.*'
]
```

If you need to remove or add a new `skip`, it is **strongly** encouraged you use the `SKIPS` class variable as a starting point!

```python
> from metadown.collectors.thredds import ThreddsCollector
> skips = ThreddsCollector.SKIPS + [".*-Day-Aggregation"]
> metadata_urls = ThreddsCollector("http://tds.maracoos.org/thredds/MODIS.xml", selects=[".*-Agg"], skips=skips).run()
> print metadata_urls
[
  'http://tds.maracoos.org/thredds/iso/MODIS-Agg.nc?dataset=MODIS-Agg&catalog=http://tds.maracoos.org/thredds/MODIS.xml',
  'http://tds.maracoos.org/thredds/iso/MODIS-2009-Agg.nc?dataset=MODIS-2009-Agg&catalog=http://tds.maracoos.org/thredds/MODIS.xml',
  'http://tds.maracoos.org/thredds/iso/MODIS-2010-Agg.nc?dataset=MODIS-2010-Agg&catalog=http://tds.maracoos.org/thredds/MODIS.xml',
  'http://tds.maracoos.org/thredds/iso/MODIS-2011-Agg.nc?dataset=MODIS-2011-Agg&catalog=http://tds.maracoos.org/thredds/MODIS.xml',
  'http://tds.maracoos.org/thredds/iso/MODIS-2012-Agg.nc?dataset=MODIS-2012-Agg&catalog=http://tds.maracoos.org/thredds/MODIS.xml',
  'http://tds.maracoos.org/thredds/iso/MODIS-2013-Agg.nc?dataset=MODIS-2013-Agg&catalog=http://tds.maracoos.org/thredds/MODIS.xml'
]
```


### GeoNetwork

```python
from metadown.collectors.geonetwork import GeoNetworkCollector

gnc = GeoNetworkCollector("http://data.glos.us/metadata")
metadata_urls = gnc.run()
print metadata_urls
[
 ...
 'http://data.glos.us/metadata/srv/en/iso19139.xml?id=39848',
 'http://data.glos.us/metadata/srv/en/iso19139.xml?id=39846',
 'http://data.glos.us/metadata/srv/en/iso19139.xml?id=39845'
]
```


### WaterQualityData.us

The WaterQualityDataUs constructor accepts any parameters that the webservice
supports.  Please see parameter table [here](http://waterqualitydata.us/webservices_documentation.jsp) for a list of options.


```python
from metadown.collectors.waterqualitydataus import WaterQualityDataUs

bbox = (-78, 28, -70, 32)
isos = WaterQualityDataUs(bBox=bbox).run()
for iso in isos:
    with open("your_save_path.xml", "w") as f:
        f.write(iso)
```

You can also load the ISO into an XML object.  For more information on the ISO
object, please see the [OWSLib](https://github.com/kwilcox/OWSLib/blob/master/owslib/iso.py) project.

```python
from metadown.collectors.waterqualitydataus import WaterQualityDataUs
from owslib.iso import MD_Metadata

bbox = (-78, 28, -70, 32)
isos = WaterQualityDataUs(bBox=bbox).run()
for iso in isos:
    xml_obj  = MD_Metadata(etree.fromstring(str(iso)))
```

**Note:** The WaterQualityDataUs object does not return URLs to ISO files, it creates
the ISO files manually from metadata avaialble through the webservice.  You will
need to save the XML strings to a file yourself.

## Downloading resulting ISO files

Once you have the metadata urls for the data you want, do whatever you want!
If you would like to rename or modify the metadata files, there is a helper class called `XmlDownloader`

XmlDownloader takes in three parameters:

* `url_list` (required) - a list of URLs
* `download_path` (required) - folder to download files to on your local machine
* `namer` (optional) - a python function for renaming the metadata files before saving them to your local machine.  It should take in a single url and return a string filename for the url to be saved as.

    Example `namer` function that renames GeoNetwork URLs
    ```python
    from urlparse import urlsplit
    def geonetwork_renamer(url, **kwargs):
        uid = urlsplit(url).query
        uid = uid[uid.index("=")+1:]
        return "GeoNetwork-" + uid + ".xml"
    ```

* `modifier` (optional) - a python function for full control over the metadata content.  It should take in a single url and return a `str` representation of ISO19115-2.

    Example `modifier` function that translates GeoNetwork's ISO19139 to ISO19115-2
    ```python
    from metadown.utils.etree import etree
    def geonetwork_modifier(url, **kwargs):
        gmi_ns = "http://www.isotc211.org/2005/gmi"
        etree.register_namespace("gmi",gmi_ns)
        new_root = etree.Element("{%s}MI_Metadata" % gmi_ns)
        old_root = etree.parse(url).getroot()
        # carry over an attributes we need
        [new_root.set(k,v) for k,v in old_root.attrib.items()]
        # carry over children
        [new_root.append(e) for e in old_root]
        return etree.tostring(new_root, encoding="UTF-8", pretty_print=True, xml_declaration=True)
    ```

```python
from metadown.downloader import XmlDownloader
XmlDownloader.run(metadata_urls, download_directory, namer=geonetwork_renamer, modifier=geonetwork_modifier)
```
