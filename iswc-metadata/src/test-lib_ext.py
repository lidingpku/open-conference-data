# -*- coding: utf-8 -*-
import unittest
from lib_ext import *

class TestLibExt(unittest.TestCase):

    def setUp(self):
    	# do nothing
    	print "setUp"

    def test_create_ascii_localname(self):

	    input = u'Jürgen Umbrich'
	    expect = 'juergen-umbrich'
	  #   for code in ["NFC","NFD", "NFKC", "NFKD"]:
			# actual = unicodedata.normalize(code, input)
			# print code, "---", actual.replace(u"\u0308","e")
	    actual = create_ascii_localname(input)
	    self.assertEquals(expect, actual)

	    input = u'Jérôme Euzenat'
	    expect = 'jerome-euzenat'
	    actual = create_ascii_localname(input)
	    self.assertEquals(expect, actual)


	    input = u"Klüft skräms inför på fédéral électoral große"
	    expect = 'klueft-skraems-infoer-pa-federal-electoral-groe'
	    actual = create_ascii_localname(input)
	    self.assertEquals(expect, actual)


	    input = u"Klüft skräms inför på fédéral électoral große"
	    expect = 'Kl%C3%BCft_skr%C3%A4ms_inf%C3%B6r_p%C3%A5_f%C3%A9d%C3%A9ral_%C3%A9lectoral_gro%C3%9Fe'
	    actual = create_ascii_localname(input, True)
	    self.assertEquals(expect, actual)


	    input = u'Jürgen Melzer'
	    expect = 'J%C3%BCrgen_Melzer'
	    actual = create_ascii_localname(input, True)
	    self.assertEquals(expect, actual)


if __name__ == '__main__':
    unittest.main()
