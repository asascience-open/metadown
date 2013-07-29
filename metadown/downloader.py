import os
from urlparse import urlsplit

import requests

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
