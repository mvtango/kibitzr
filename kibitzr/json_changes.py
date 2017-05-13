from jinja2 import Environment, FunctionLoader, Markup
import difflib


def fileloader(filename):
    with open(filename) as f:
        return "".join((a for a in f.read()))


jinja2env = Environment(loader=FunctionLoader(fileloader),
                  extensions=[
                       'jinja2.ext.with_',
                       'jinja2_slug.SlugExtension'
                       ]
                  )

def show_diff(text,n_text):
    """
    http://stackoverflow.com/a/788780
    Unify operations between two compared strings seqm is a difflib.
    SequenceMatcher instance whose a & b are strings
    """
    seqm = difflib.SequenceMatcher(None, text, n_text)
    output= []
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1])
        elif opcode == 'insert':
            output.append('<ins>' + seqm.b[b0:b1] + "</ins>")
        elif opcode == 'delete':
            output.append('<del>' + seqm.a[a0:a1] + "</del>")
        elif opcode == 'replace':
            # seqm.a[a0:a1] -> seqm.b[b0:b1]
            output.append("<del>" + seqm.b[b0:b1] + "</del><ins>" +
                          seqm.a[a0:a1] + "</ins>")
        else:
            raise RuntimeError("unexpected opcode")
    return Markup(''.join(output))


jinja2env.filters["diff"]=show_diff

if __name__=="__main__" :
    for pairs in [ ("Hallo","Hello"),
                   ("Die beste Wahl","Die einfachste Wahl") ] :
        print(show_diff(*pairs))

