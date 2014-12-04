# This Python file uses the following encoding: utf-8
# also see http://www.python.org/dev/peps/pep-0263/

import unittest
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 
from lib_unicode import *
from lib_format import *
import simplejson as json

class lib_unicode_test(unittest.TestCase):
    def test_csv2json(self): 
        dir_me = os.path.dirname(os.path.abspath(__file__))
        filename_csv = os.path.join(dir_me, "lib_unicode_test1_input.csv")
        filename_json_expected = os.path.join(dir_me, "lib_unicode_test1_expected.json")

        json_actual = UtilCsv.csv2json(filename_csv)

        with open (filename_json_expected) as f:
            json_expect = json.load(f)

        actual = json.dumps(json_actual, indent=4, sort_keys=True)
        #print actual
        expected = json.dumps(json_expect, indent=4, sort_keys=True)

        self.assertEqual(actual,expected)

if __name__ == "__main__":
    unittest.main()