import os
from urlparse import urlsplit

import requests

class XmlDownloader(object):

    @classmethod
    def run(cls, url_list, download_path, namer=None, modifier=None, **kwargs):
        for url in url_list:

            if namer is not None:
                # Custom naming function for saved file on disk
                filename = namer(url, **kwargs)
            else:
                # By default, get the local file from the remove name name
                filename = os.path.basename(urlsplit(url).path)
            
            # Always save with a .xml extension
            if os.path.splitext(filename)[1] != ".xml":
                filename = filename + ".xml"

            # Absolute path to save file
            filepath = os.path.join(download_path, filename)

            
            if modifier is not None:
                data = modifier(url, **kwargs)
            else:
                try:
                    data = requests.get(url).text
                except requests.exceptions.RequestException:
                    print "Error downloading %s" % url
                    continue
                
            # Need to use codecs.open for UTF-8 data
            with open(filepath, "w") as handle:
                handle.write(data)
