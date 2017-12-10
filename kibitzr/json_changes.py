from jinja2 import Environment, FunctionLoader, Markup
import re
import difflib
from slugify import slugify
from functools import partial



def fileloader(filename):
    with open(filename) as f:
        return "".join((a for a in f.read()))


jinja2env = Environment(loader=FunctionLoader(fileloader),
                  extensions=[
                       'jinja2.ext.with_',
                       ],
                  trim_blocks=True,
                  lstrip_blocks=True
                  )

def tokenize(text) :
    return re.split(r"(\s+)",text)

def show_diff(n_text,text):
    """
    http://stackoverflow.com/a/788780
    Unify operations between two compared strings seqm is a difflib.
    SequenceMatcher instance whose a & b are strings
    """
    seqm = difflib.SequenceMatcher(None, tokenize(text), tokenize(n_text))
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append("".join(seqm.a[a0:a1]))
        elif opcode == 'insert':
            output.append('<ins>' + "".join(seqm.b[b0:b1]) + "</ins>")
        elif opcode == 'delete':
            output.append('<del>' + "".join(seqm.a[a0:a1]) + "</del>")
        elif opcode == 'replace':
            # seqm.a[a0:a1] -> seqm.b[b0:b1]
            output.append(
                          "<ins>" + "".join(seqm.b[b0:b1]) + "</ins>" +
                          "<del>" + "".join(seqm.a[a0:a1]) + "</del>"
                          )
        else:
            raise RuntimeError("unexpected opcode")
    return Markup(''.join(output))

# as per http://stackoverflow.com/a/18900930/2743441
_js_escapes = {
        '\\': '\\u005C',
        '\'': '\\u0027',
        '"': '\\u0022',
        '>': '\\u003E',
        '<': '\\u003C',
        '&': '\\u0026',
        '=': '\\u003D',
        '-': '\\u002D',
        ';': '\\u003B',
        u'\u2028': '\\u2028',
        u'\u2029': '\\u2029'
}
# Escape every ASCII character with a value less than 32.
_js_escapes.update(('%c' % z, '\\u%04X' % z) for z in range(32))
def jinja2_escapejs_filter(value):
        retval = []
        for letter in value:
                if letter in _js_escapes:
                        retval.append(_js_escapes[letter])
                else:
                        retval.append(letter)
        return Markup("".join(retval))

jinja2env.filters["diff"]=show_diff
jinja2env.filters["escapejs"]=jinja2_escapejs_filter
jinja2env.filters["slug"]=partial(slugify,ok="/-",only_ascii=True)



if __name__=="__main__" :
    for pairs in [ ("Hallo","Hello"),
                   ("Die beste Wahl","Die einfachste Wahl") ] :
        print(show_diff(*pairs))

