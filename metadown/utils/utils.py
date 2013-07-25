import urlparse

def construct_url(root, url, path):

    if path[0] == "/":
        # Absolute paths
        cat = root + path
    elif path[0:4] == "http":
        # Full HTTP links
        cat = path
    else:
        # Relative paths.  Strip off last filename
        url = "/".join(urlparse.urlsplit(url).path.split("/")[0:-1])
        cat = root + url + "/" + path

    return cat
