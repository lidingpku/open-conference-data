import rdflib
from rdflib import Namespace

'''
sparql query was not properly executed in rdflib,
'''

def run_test(graph, query):
	print query
	qres = g.query(query)
	count = 0
	for row in qres:
		if count<3:
			print "row ", count, ":", row
		count +=1			

	print "total rows: ", count


# load graph
g=rdflib.Graph()
url ="http://liding.org/foaf.rdf"
g.load(url)

total =0
for s, p, o in g:
	total +=1
	
print "loaded {0} triples from {1}".format(total, url)


print "=================================="
print "Test 1: result is correct"
query =	""" 	select ?domain ?p ?range (count(*) as ?cnt) 
		where {
		?s ?p ?o .
		?s a ?domain .
		}
		group by ?domain ?p 
		order by ?domain ?p
		"""
run_test(g, query)


print "=================================="
print "Test 2: result is incorrect, group is not working properly on None column"

query =	""" 	select ?domain ?p ?range (count(*) as ?cnt) 
		where {
		?s ?p ?o .
		?s a ?domain .
		OPTIONAL {?o a ?range} 
		}
		group by ?domain ?p ?range
		order by ?domain ?p ?range
		"""
run_test(g, query)
