import string
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF

g = Graph()
g.parse("theboy3.rdf")


import pprint
#for stmt in g:
#	pprint.pprint(stmt)
#ns1 = Namespace('http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Event')
#g.bind("dul", ns1)

def getName(strg):
	name = strg.split("#")[-1]
	return name

def updateAmrVarList(strg, amrVarList):
	nome = getName(strg)
	var = nome[0]
	insert = True
	omonimia = False
	for (v,n) in amrVarList:
		if(v == var and n == nome):
			insert = False
		if(v == var and n != nome):
			omonimia = True
		
	if(insert):
		if(omonimia):
			i = 2
			while((var+str(i),nome) in amrVarList):
				i = i+1
			var = var+str(i)
		amrVarList.append((var, nome))
	return amrVarList
	
def getPrintableAmrName(strg, amrVarList):
	nome = getName(strg)
	printableName = "None"
	for (v,n) in amrVarList:
		if(n == nome):
			printableName = v + " / " + nome
	return printableName

def printAMR(verbo, listaArgomenti, indiceArgomenti, chiusura, soloArgomenti, soloVerbo, argomentoVerbo, tabdeep, amrVarList):

	stringa = ""
	if(not soloArgomenti):
		amrVarList = updateAmrVarList(str(verbo), amrVarList)
		stringa = "\n("+getPrintableAmrName(str(verbo), amrVarList)
	if(not soloVerbo):
		i = indiceArgomenti
		tabs = "\n\t"
		for tab in range(tabdeep):
			tabs = tabs + "\t" 
		for arg in listaArgomenti:
			amrVarList = updateAmrVarList(str(arg), amrVarList)
			stringa = stringa + tabs + ":ARG" + str(i) + "(" + getPrintableAmrName(str(arg), amrVarList) + ")"
			i = i+1
		if(argomentoVerbo):
			stringa = stringa[:-1] #rimuovo l'ultima parentesi
	if(chiusura):
		stringa = stringa + ")"
	print(stringa)
	return amrVarList

def recArgs(m, args, counter, bkp, mlist, firstPrint, mchecklist, tabs, amrVarList):
	a = []
	if(firstPrint):
		amrVarList = printAMR(m, args, counter, False, False, True, False, 0, amrVarList)
	for x in args:
		if(str(x) != "None"):
			a.append(x)
			if(str(x) in mlist and (not mchecklist[mlist.index(str(x))])):
				amrVarList = printAMR(m, a, counter, False, True, False, True, tabs, amrVarList)
				counter = len(a)
				a = []
				for (bm,bargs) in bkp:
					if(str(bm) == mlist[mlist.index(str(x))]):
						mchecklist[mlist.index(str(x))] = True
						recArgs(bm, bargs, 0, bkp, mlist, False, mchecklist, tabs+1, amrVarList)
						
	if(len(args) != 0):
		amrVarList = printAMR(m, a, counter, True, True, False, False, tabs, amrVarList)
	return mchecklist
		
#for mainverb in mainverbList:
qres = g.query(
	"""SELECT DISTINCT ?mainverb ?j_1 ?j_2 ?j_3
		WHERE {
		  ?mainverb a ?verb . 
		  ?verb rdfs:subClassOf <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Event> .
		  OPTIONAL{?mainverb j.0:Theme ?j_1} .
		  OPTIONAL{?mainverb j.0:Agent ?j_2} .
		  OPTIONAL{?mainverb j.0:Experiencer ?j_3}
		}""")
mlist = []
bkp = []
mchecklist = []

#guardo se ci sono delle coref
qres2 = g.query(
	"""SELECT DISTINCT ?x ?y
		WHERE {
		  ?x j.1:other_coref ?y
		}""")

#guardo se ci sono delle modality
qres3 = g.query(
	"""SELECT DISTINCT ?x ?y
		WHERE {
		  ?x j.2:hasModality ?y
		}""")
		
for (m, t, a, e) in qres : 
		for (x,y) in qres3:
			if(m == x):
				modality = getName(y)
				if(modality == "Necessary"):
					mlist.append("O#obligate_1")
					bkp.append(("O#obligate_1", [m]))
					mchecklist.append(False)
				if(modality == "Possible"):
					mlist.append("P#permit_1")
					bkp.append(("P#permit_1", [m]))
					mchecklist.append(False)
		mlist.append(str(m))
		args = []
		for x in [t, a, e]:
			if(str(x) != "None"):
				#se e' presente una coref		
				for (xx, yy) in qres2:
					if(x == yy):
						x = xx		
				args.append(x)
		bkp.append((m,args))
		mchecklist.append(False)

counter = 0
for ((m, args)) in bkp : 
		#print("MAINVERB:%s\nTHEME:%s\nAGENT:%s\nEXPERIENCER:%s" %(m, t, a, e))
		
		if(not mchecklist[counter]): #se non e' ancora stata fatta
			mchecklist = recArgs(m, args, 0, bkp, mlist, True, mchecklist, 0, [])
		mchecklist[counter] = True
		counter = counter + 1