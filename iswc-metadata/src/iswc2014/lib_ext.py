# -*- coding: utf-8 -*-
import unicodedata
import urllib
import re

LATEX_ACCENT_X = [
      [ u"à", "`a" ], # Grave accent
      [ u"è", "`e" ],
      [ u"ì", "`i" ],
      [ u"ò", "`o" ],
      [ u"ù", "`u" ],
      [ u"ỳ", "`y" ],
      [ u"À", "`A" ],
      [ u"È", "`E" ],
      [ u"Ì", "`I" ],
      [ u"Ò", "`O" ],
      [ u"Ù", "`U" ],
      [ u"Ỳ", "`Y" ],
      [ u"á", "'a" ], # Acute accent
      [ u"é", "'e" ],
      [ u"í", "'i" ],
      [ u"ó", "'o" ],
      [ u"ú", "'u" ],
      [ u"ý", "'y" ],
      [ u"Á", "'A" ],
      [ u"É", "'E" ],
      [ u"Í", "'I" ],
      [ u"Ó", "'O" ],
      [ u"Ú", "'U" ],
      [ u"Ý", "'Y" ],
      [ u"â", "\\^a" ], # Circumflex
      [ u"ê", "\\^e" ],
      [ u"î", "\\^i" ],
      [ u"ô", "\\^o" ],
      [ u"û", "\\^u" ],
      [ u"ŷ", "\\^y" ],
      [ u"Â", "\\^A" ],
      [ u"Ê", "\\^E" ],
      [ u"Î", "\\^I" ],
      [ u"Ô", "\\^O" ],
      [ u"Û", "\\^U" ],
      [ u"Ŷ", "\\^Y" ],
      [ u"ä", "\"a" ],    # Umlaut or dieresis
      [ u"ë", "\"e" ],
      [ u"ï", "\"i" ],
      [ u"ö", "\"o" ],
      [ u"ü", "\"u" ],
      [ u"ÿ", "\"y" ],
      [ u"Ä", "\"A" ],
      [ u"Ë", "\"E" ],
      [ u"Ï", "\"I" ],
      [ u"Ö", "\"O" ],
      [ u"Ü", "\"U" ],
      [ u"Ÿ", "\"Y" ],
  ]

LATEX_ACCENT = [
      [ u"à", "\\`a" ], # Grave accent
      [ u"è", "\\`e" ],
      [ u"ì", "\\`\\i" ],
      [ u"ò", "\\`o" ],
      [ u"ù", "\\`u" ],
      [ u"ỳ", "\\`y" ],
      [ u"À", "\\`A" ],
      [ u"È", "\\`E" ],
      [ u"Ì", "\\`\\I" ],
      [ u"Ò", "\\`O" ],
      [ u"Ù", "\\`U" ],
      [ u"Ỳ", "\\`Y" ],
      [ u"á", "\\'a" ], # Acute accent
      [ u"é", "\\'e" ],
      [ u"í", "\\'\\i" ],
      [ u"ó", "\\'o" ],
      [ u"ú", "\\'u" ],
      [ u"ý", "\\'y" ],
      [ u"Á", "\\'A" ],
      [ u"É", "\\'E" ],
      [ u"Í", "\\'\\I" ],
      [ u"Ó", "\\'O" ],
      [ u"Ú", "\\'U" ],
      [ u"Ý", "\\'Y" ],
      [ u"â", "\\^a" ], # Circumflex
      [ u"ê", "\\^e" ],
      [ u"î", "\\^\\i" ],
      [ u"ô", "\\^o" ],
      [ u"û", "\\^u" ],
      [ u"ŷ", "\\^y" ],
      [ u"Â", "\\^A" ],
      [ u"Ê", "\\^E" ],
      [ u"Î", "\\^\\I" ],
      [ u"Ô", "\\^O" ],
      [ u"Û", "\\^U" ],
      [ u"Ŷ", "\\^Y" ],
      [ u"ä", "\\\"a" ],    # Umlaut or dieresis
      [ u"ë", "\\\"e" ],
      [ u"ï", "\\\"\\i" ],
      [ u"ö", "\\\"o" ],
      [ u"ü", "\\\"u" ],
      [ u"ÿ", "\\\"y" ],
      [ u"Ä", "\\\"A" ],
      [ u"Ë", "\\\"E" ],
      [ u"Ï", "\\\"\\I" ],
      [ u"Ö", "\\\"O" ],
      [ u"Ü", "\\\"U" ],
      [ u"Ÿ", "\\\"Y" ],
      [ u"ç", "\\c{c}" ],   # Cedilla
      [ u"Ç", "\\c{C}" ],
      [ u"œ", "{\\oe}" ],   # Ligatures
      [ u"Œ", "{\\OE}" ],
      [ u"æ", "{\\ae}" ],
      [ u"Æ", "{\\AE}" ],
      [ u"å", "{\\aa}" ],
      [ u"Å", "{\\AA}" ],
      [ u"ø", "{\\o}" ],    # Misc latin-1 letters
      [ u"Ø", "{\\O}" ],
      [ u"ß", "{\\ss}" ],
      [ u"¡", "{!`}" ],
      [ u"¿", "{?`}" ],
      [ u"≥", "$\\ge$" ],   # Math operators
      [ u"≤", "$\\le$" ],
      [ u"≠", "$\\neq$" ],
      [ u"©", "\copyright" ], # Misc
      [ u"ı", "{\\i}" ],
      [ u"µ", "$\\mu$" ],
      [ u"°", "$\\deg$" ],
#      [ u"\\", "\\\\" ],    # Characters that should be quoted
      [ u"~", "\\~" ],
      [ u"&", "\\&" ],
      [ u"$", "\\$" ],
      [ u"{", "\\{" ],
      [ u"}", "\\}" ],
      [ u"%", "\\%" ],
      [ u"#", "\\#" ],
      [ u"_", "\\_" ],
      [ u"–", "--" ],   # Dashes
      [ u"—", "---" ],
      [ u"‘", "`" ],    #Quotes
      [ u"’", "'" ],
      [ u"“", "``" ],
      [ u"”", "''" ],
      [ u"‚", "," ],
      [ u"„", ",," ],
    ]
def unicode2latex(str):
    for pattern in LATEX_ACCENT:
        #print pattern
        str = str.replace(pattern[0],pattern[1])
    return str

def latex2unicode(str):
    for pattern in LATEX_ACCENT_X:
        #print pattern
        str = str.replace(pattern[1],pattern[0])
    return str
    
def create_ascii_localname(name, escape=False):
    """
        escape=False
         e.g. http://data.semanticweb.org/person/juergen-umbrich/html
         e.g. http://data.semanticweb.org/person/jerome-euzenat/html
         input:  u"Klüft skräms inför på fédéral électoral große"
         output:  'klueft-skraems-infoer-pa-federal-electoral-groe'

        escape=True
         e.g.  http://dbpedia.org/resource/J%C3%BCrgen_Melzer

         input:  u"Klüft skräms inför på fédéral électoral große"
         output: 'Kl%C3%BCft_skr%C3%A4ms_inf%C3%B6r_p%C3%A5_f%C3%A9d%C3%A9ral_%C3%A9lectoral_gro%C3%9Fe'

       also see:http://stackoverflow.com/questions/2700859 
    """  
    if escape:
        
       name = name.encode("utf-8")
       name = urllib.quote(name,safe='=/ ')
       name = re.sub("[ ]+","_", name)
    else:
        
       name = unicodedata.normalize('NFKD', name)
       table = {}
       name = re.sub(u"\u0308","e",name)
       #print name
       name = name.encode('ascii','ignore')
       name = re.sub("[ ]+","-", name)
#       name = re.sub("`","'", name)
#       name = re.sub("[\.'\(\)\"]","", name)
       name = re.sub("[^-a-zA-Z0-9]","", name)
       name = re.sub("-+","-", name)
       name = name.lower()

    return name


class MyCounter(object):
    def __init__(self):
        self.data = {}
    
    def inc(self, key, cnt=1):
        if not key in self.data:
            self.data[key]=0
        self.data[key] += cnt

    def list(self, min_count=0):
        ret = {}
        for k,v in self.data:
            if v >= min_count:
                ret[k]=v
                
        return ret
"""
class MyCounterKeyValue(object):
    def __init__(self):
        self.data = {}
    
    def inc(self, key, value, ref):
        key = UtilSyntax.convert(key)
        value = UtilSyntax.convert(value)
        if not key in self.data:
            self.data[key]={}            
        if not value in self.data[key]:
            self.data[key][value]=set()
        self.data[key][value].add(ref)

    def show(self, min_value_count=0):
        total =0
        for k in self.data:
            v = self.data[k]
            if len(v) >= min_value_count:
                msg = ""
                for v in self.data[k]:
                    msg +="{0}={1},".format(v, len(self.data[k][v]))
                msg = "{0}--[{1}]--[{2}]".format(k, len(self.data[k]), msg)
                print msg
                total +=1
        print "total {0} item with >={1} values".format(total, min_value_count)
"""