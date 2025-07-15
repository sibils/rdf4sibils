import uuid
import urllib.parse
import unicodedata


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
def getBlankNode():
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    return "_:BN" + uuid.uuid4().hex


# - - - - - - - - - - - - - - - - - - - - - - - - - - 
def remove_accents(input_str):
# - - - - - - - - - - - - - - - - - - - - - - - - - - 
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])



#-------------------------------------------------
class TripleList:
#-------------------------------------------------
    def __init__(self):
        self.lines = list()
    def append(self, s, p, o, punctuation="."):
        line = " ".join([s,p,o, punctuation, "\n"])
        self.lines.append(line)
    def extend(self, triple_list):
        self.lines.extend(triple_list.lines)


