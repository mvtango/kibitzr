from lxml import etree
from collections import MutableMapping


class XPathDict(MutableMapping) :
    """
        Dictionary-like extraction of XPath expressions.
        Constructed with a parsed etree as a starting value. Attributes are searched as xpath expressions and returned as texts

        xpathdict=XPathDict(etree.fromstring('<area alt="alt attr" shape="shape attr"/>text node</area>',parser=etree.HTMLParser()))

        xpathdict["//@alt"] == "alt attr"

        xpathdict["//text()] == "text node"


    """

    def __init__(self,root) :
        self.root=root


    def __getitem__(self,key) :
        elements = self.root.xpath(key)
        if elements:
            if type(elements[0]) == etree._Element :
                return etree.tostring(
                    next(iter(elements)),
                    method='html',
                    pretty_print=True,
                    encoding='unicode',
                )
            else : # xpath expression selected a string, i.e. an element value
                return "\t".join(elements)
        else :
            raise ValueError("XPath expression {key} not found in {0}".format(etree.tostring(self.root),**locals()))

    def __len__(self) :
        pass

    def __delitem__(self,key) :
        pass

    def __iter__(self) :
        return iter(())

    def __setitem__(self,key,value) :
        pass

if __name__=="__main__" :
    xpd=XPathDict(etree.fromstring('<area alt="alt attr" shape="shape attr"/>text node</area>',parser=etree.HTMLParser()))
    for template,result  in [("{xpath[//@alt]}","alt attr"),
                             ("{xpath[//text()]}","text node")] :
                            assert template.format(xpath=xpd) == result

