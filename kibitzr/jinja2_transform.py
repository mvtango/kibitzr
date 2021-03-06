from lxml import etree
from lxml.etree import XPathEvalError
from collections import MutableMapping
from bs4 import BeautifulSoup

import re
import six

from jinja2 import Environment, FunctionLoader

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin


spaces_re = re.compile(r"^\s*(.*\S)\s*$")


def strip_whitespace(a):
    m = spaces_re.search(a)
    if m:
        return m.groups()[0]
    else:
        return a


class LazyDict(MutableMapping):

    def __getitem__(self, key):
        return NotImplementedError()

    def __len__(self):
        pass

    def __delitem__(self, key):
        pass

    def __iter__(self):
        return iter(())

    def __setitem__(self, key, value):
        pass


class XPathDict(LazyDict):
    """
        Dictionary-like extraction of XPath expressions.
        Constructed with a XML string. Dict Attributes are searched as
        xpath expressions and returned as texts

        xpathdict=XPathDict('''<area alt="alt attr" shape="shape attr"/>
                            text node</area>''')

        xpathdict["//@alt"] == "alt attr"

        xpathdict["//text()] == "text node"
    """

    def __init__(self, html):
        self.root = etree.fromstring(html, parser=etree.HTMLParser())

    def __getitem__(self, key):
        try:
            elements = self.root.xpath(key)
        except XPathEvalError as exc:
            raise ValueError(
             "Xpath evaluation of '{key}' failed: {exc}".format(**locals())
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
               "XPath expression {key} not found in {0}".format(
                   etree.tostring(self.root),
                   **locals()
                )
               )


class CSSDict(LazyDict):
    """
        Dictionary-like extraction of CSS expressions.
        Constructed with HTML string  a starting value.
        Attributes are searched with CSS expressions and
        returned as texts

        cssdict=CSSDict('''<area class="alt">class alt</area>
        <area class="new" id="here">id here</area>''')

        cssdict["area.alt"] == "<area class="alt">class alt</area>"

        cssdict["area#id"]  == "<area id="here">id here</area>"
    """

    def __init__(self, html):
        self.soup = BeautifulSoup(html, "html.parser")

    def __getitem__(self, selector):
        element = self.soup.select_one(selector)
        if element:
            return six.text_type(element)
        else:
            raise KeyError('CSS selector not found: %r', selector)


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


env.filters["xpath"] = xpath_filter
env.filters["css"] = css_filter
env.filters["urljoin"] = joinurl
env.filters["match"] = match


def jinja2_render(template, *args, **kwargs):
    t = env.from_string(template)
    return(t.render(*args, **kwargs))


if __name__ == "__main__":
    xpd = XPathDict('''
    <area alt="alt attr" shape="shape attr"/>text node</area>
    ''')
    for template, result in [("{xpath[//@alt]}", "alt attr"),
                             ("{xpath[//text()]}", "text node")]:
                            assert template.format(xpath=xpd) == result
    xpd = CSSDict('''
    <area alt="alt attr" class="one" shape="shape attr"/>class one</area>
    <area id="two">id two</area>
    ''')
    for template, result in [("{css[area.one]}", "class one"),
                             ("{css[area#two]}", "id two")]:
        try:
            assert template.format(css=xpd) == result
        except AssertionError:
            print("{template} == {},  != {result}".format(
                    template.format(css=xpd),
                    **locals()
                    ))
