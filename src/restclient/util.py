import os
from urllib.parse import urlparse
import xml.dom.minidom
import json


__all__ = ['file_check', 'url_check', 'prettify_xml', 'prettify_json']


def file_check(filename: str) -> bool:
    return os.path.isfile(filename) and os.path.exists(filename)


def url_check(url: str) -> bool:
    parsed = urlparse(url)
    return all([parsed.scheme, parsed.netloc])


def prettify_xml(xmlstr: str) -> str:
    dom = xml.dom.minidom.parseString(xmlstr)
    return dom.toprettyxml(indent='  ')


def prettify_json(jsonstr: str) -> str:
    return json.dumps(json.loads(jsonstr), indent=2)

