import os
from urlparse import urlsplit
from metadown.utils.etree import etree
import requests
import datetime


def set_date_stamp(fpath):
    namespaces = {
    "gmx":"http://www.isotc211.org/2005/gmx",
    "gsr":"http://www.isotc211.org/2005/gsr",
    "gss":"http://www.isotc211.org/2005/gss",
    "gts":"http://www.isotc211.org/2005/gts",
    "xs":"http://www.w3.org/2001/XMLSchema",
    "gml":"http://www.opengis.net/gml/3.2",
    "xlink":"http://www.w3.org/1999/xlink",
    "xsi":"http://www.w3.org/2001/XMLSchema-instance",
    "gco":"http://www.isotc211.org/2005/gco",
    "gmd":"http://www.isotc211.org/2005/gmd",
    "gmi":"http://www.isotc211.org/2005/gmi",
    "srv":"http://www.isotc211.org/2005/srv",
    }

                
    # Always modify date stamp!
    root = etree.parse(fpath)
    
    x_res = root.xpath(
    'gmd:dateStamp', 
    namespaces=namespaces
    )
    
    for dateStamp in x_res:
        
        # there should be only one - could be Date or dateTime - just delete it
        for i in xrange(len(dateStamp)):
            del dateStamp[i]
        
        dateTime = etree.SubElement(dateStamp, '{http://www.isotc211.org/2005/gco}DateTime')
        
        dateTime.text = datetime.datetime.now().isoformat()    

    root.write(fpath)


class XmlDownloader(object):

    @classmethod
    def run(cls, url_list, download_path, namer=None, modifier=None, **kwargs):
        for url in url_list:

            if namer is not None:
                # Custom naming function for saved file on disk
                try:
                    filename = namer(url, **kwargs)
                except:
                    print "Renaming failed on %s - skipping" % url
                    continue
            else:
                # By default, get the local file from the remove name name
                filename = os.path.basename(urlsplit(url).path)
            
            # Always save with a .xml extension
            if os.path.splitext(filename)[1] != ".xml":
                filename = filename + ".xml"

            if not os.path.exists(download_path):
                os.makedirs(download_path)

            # Absolute path to save file
            filepath = os.path.join(download_path, filename)
            
            if modifier is not None:
                try:
                    data = modifier(url, **kwargs)
                except:
                    print "Modifier failed on %s - skipping" % url
                    continue
            else:
                try:
                    data = requests.get(url).text
                except requests.exceptions.RequestException:
                    print "Error downloading %s" % url
                    continue

            # Need to use codecs.open for UTF-8 data
            with open(filepath, "w") as handle:
                handle.write(data)
                
            # Always modify date stamp!            
            set_date_stamp(filepath)

