import logging
import json
from lxml import etree
from lxml.etree import XPathEvalError
from collections import OrderedDict
from bs4 import BeautifulSoup
import re
import six
import jmespath
from jinja2 import Environment, FunctionLoader

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from .utils import bake_parametrized
from .html import deep_recursion, extract_text

from .jinja_transform import LazyHTML
from .jinja_transform import LazyXML as originalLazyXML
from .jinja_transform import  LazyJSON as originalLazyJSON


class LazyJSON(originalLazyJSON) :

    def jmespath(self,expression) :
        return jmespath.search(expression,self.json,
                 jmespath.Options(dict_cls=OrderedDict))


class LazyXML(originalLazyXML) :

    def xpath(self, selector):
        try:
            elements = self.root.xpath(selector)
        except XPathEvalError as exc:
            raise ValueError(
               "Xpath evaluation of '{selector}' failed: {exc}".format(
                **locals())
            ) from exc
        if elements:
            if type(elements[0]) == etree._Element:
                return strip_whitespace(etree.tostring(
                    next(iter(elements)),
                    method='html',
                    pretty_print=True,
                    encoding='unicode',
                ))
            else:  # xpath expression selected a string, i.e. an element value
                return strip_whitespace("\t".join(elements))
        else:
            raise ValueError(
                  "XPath expression {selector} not found in {0}".format(
                      etree.tostring(self.root)[:90],
                      **locals())
                  )



#
logger = logging.getLogger(__name__)

spaces_re = re.compile(r"^\s*(.*\S)\s*$")


def object_transform(code, content, conf) :
    html_object=LazyHTML(content)
    xml_object=LazyXML(content)
    json_object=LazyJSON(content)
    obj = OrderedDict()
    for (k, v) in code.items():
        if "{" not in v:
            v = "{{ %s }}" % v
        obj[k] = jinja2_render(v, config=conf,
                                  css=html_object.css,
                                  xpath=xml_object.xpath,
                                  jp=json_object.jmespath,
                                  object=obj)
    return True, json.dumps(obj)






def strip_whitespace(a):
    m = spaces_re.search(a)
    if m:
        return m.groups()[0]
    else:
        return a

def xpath_filter(html, path):
    root = etree.fromstring(html, parser=etree.HTMLParser())
    try:
        elements = root.xpath(path)
    except XPathEvalError as exc:
        raise ValueError(
           "Xpath evaluation of '{path}' failed: {exc}".format(
            **locals())
        ) from exc
    if elements:
        if type(elements[0]) == etree._Element:
            return strip_whitespace(etree.tostring(
                next(iter(elements)),
                method='html',
                pretty_print=True,
                encoding='unicode',
            ))
        else:  # xpath expression selected a string, i.e. an element value
            return strip_whitespace("\t".join(elements))
    else:
        raise ValueError(
              "XPath expression {path} not found in {0}".format(
                  etree.tostring(root)[:90],
                  **locals())
              )


def css_filter(html, expression):
    soup = BeautifulSoup(html, "html.parser")
    element = soup.select_one(expression)
    if element:
        return six.text_type(element)
    else:
        raise KeyError('CSS selector not found: %r', expression)


def fileloader(filename):
    with open(filename) as f:
        return "".join((a for a in f.read()))


env = Environment(loader=FunctionLoader(fileloader),
                  extensions=[
                       'jinja2.ext.with_',
                       'jinja2_slug.SlugExtension'
                       ]
                  )


def joinurl(url, base):
    return urljoin(base, url)


def match(text, exp):
    r = re.compile(exp)
    m = r.search(text)
    if m:
        if m.groups():
            if len(m.groups()) == 1:
                return m.groups()[0]
            else:
                return m.groups()
        elif m.groupdict():
            return m.groupdict()
    else:
        return("")


# env.filters["xpath"] = xpath_filter
# env.filters["css"] = css_filter
env.filters["urljoin"] = joinurl
env.filters["match"] = match


def jinja2_render(template, *args, **kwargs):
    t = env.from_string(template)
    return(t.render(*args, **kwargs))


OBJECT_REGISTRY= {
    'object': bake_parametrized(object_transform, pass_conf=True)
}
