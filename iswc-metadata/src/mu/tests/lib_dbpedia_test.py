    import unittest
import os
import sys
parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir) 
from lib_dbpedia import DbpediaApi
import simplejson as json

class TestDbpediaApi(unittest.TestCase):
    """Test DbpediaApi functions"""
    def test_process_name(self): 
        dir_me = os.path.dirname(os.path.abspath(__file__))
        dir_data = os.path.join(dir_me, "dbpedia_entity")


        dbpedia_api = DbpediaApi(dir_data, DbpediaApi.ENTITY_TYPE_ORGANIZATION)

        self.assertEqual(len(dbpedia_api.map_name),1)
        print dbpedia_api.map_name

        #indexed
        ret = dbpedia_api.find_cached_name("MIT")
        print ret
        self.assertTrue(None!=ret)
        self.assertEquals(ret[u"title"],"Massachusetts Institute of Technology")

        ret = dbpedia_api.process_one_name("MIT")
        self.assertEqual(len(dbpedia_api.map_name),1)
        print ret
        self.assertTrue(None!=ret)
        self.assertEquals(ret[u"title"],"Massachusetts Institute of Technology")

        #not indexed
        ret = dbpedia_api.process_names("UMBC")
        self.assertEqual(len(dbpedia_api.map_name),2)
        self.assertTrue(None==ret)

        dbpedia_api.write_new_data()
        self.assertEqual(len(dbpedia_api.list_new_entity),1)


    def testSearchWikipedia(self): 
        name = "MIT"
        ret = DbpediaApi.search_wikipedia(name)
        print ret
        self.assertEqual(ret['title'],u'Massachusetts Institute of Technology')

    def testSearchDbpedia(self): 
        # usually the first result is what we want
        name = "MIT"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.search_dbpedia(name, entity_type)
        print ret

        self.assertEqual(ret['label'],u'Massachusetts Institute of Technology')

        # sometimes the first result may be wrong
        # while the second result is correct
        name = "University of Maryland, Baltimore"
        ret = DbpediaApi.search_dbpedia(name, entity_type)
        print ret
        self.assertEqual(ret['label'],u'University of Maryland, Baltimore')

        #TODO expect the "new" file contains one entry

    def testLinkDbpedia(self): 
        name = "CNR"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertTrue('uri' in ret)
        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/French_National_Centre_for_Scientific_Research")

        name = "DERI galway"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/Digital_Enterprise_Research_Institute")



        name = "Linkoping University"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/Link%C3%B6ping_University")



        name = "MIT CSAIL"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/MIT_Computer_Science_and_Artificial_Intelligence_Laboratory")



        name = "University Maryland"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/University_of_Maryland,_College_Park")

        name = "University Maryland, Baltimore"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/University_of_Maryland,_Baltimore")



        name = "Apple"
        entity_type = DbpediaApi.ENTITY_TYPE_ORGANIZATION
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/Apple_Inc.")
    
        name = "Jim Hendler"
        entity_type = DbpediaApi.ENTITY_TYPE_PERSON
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertEqual(ret['uri'],"http://dbpedia.org/resource/James_Hendler")

        name = "Li Ding"
        entity_type = DbpediaApi.ENTITY_TYPE_PERSON
        ret = DbpediaApi.link_dbpedia(name, entity_type)
        print json.dumps(ret, indent=4)

        self.assertTrue('uri' not in ret)

if __name__ == "__main__":
    unittest.main()