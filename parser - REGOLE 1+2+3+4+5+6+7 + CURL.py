import string
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef
from rdflib.namespace import DC, FOAF
from subprocess import check_output

disableInput = False
if(not disableInput):
	frase = input("Inserisci la frase:")
	# ottengo rdf da fred tramite curl
	curlString = "curl -G -X GET -H \"Accept: application/rdf+xml\" --data-urlencode text=\""+ frase +"\" http://etna.istc.cnr.it/stlab-tools/fred/demo"
	toParse = check_output(curlString, shell=True).decode()
	toParse = toParse[:-1]

	#salvo il tutto in un file temporaneo
	out_file = open("TEMP.rdf","w")
	out_file.write(toParse)
	out_file.close()

g = Graph()
#g.parse("boat.rdf")
g.parse("TEMP.rdf")

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
	var = nome[0].lower()
	insert = True
	omonimia = False
	nomeTrovato = False
	
	for (v,n) in amrVarList:
		if(nome == n):
			if(var == v):
				insert = False
			else:
				var = v
	
	if(not nomeTrovato):
		for (v,n) in amrVarList:
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
	
def printAMR(verbo, listaArgomenti, indiceArgomenti, chiusura, soloArgomenti, soloVerbo, argomentoVerbo, tabdeep, amrVarList, polarityFlag, possType):
	
	stringa = ""
	if(not soloArgomenti):
		amrVarList = updateAmrVarList(str(verbo), amrVarList)
		stringa = "\n("+getPrintableAmrName(str(verbo), amrVarList)
		tabs = "\n\t"
		if(possType == -1):
			amrVarList = updateAmrVarList("he", amrVarList)
			stringa = stringa + tabs + ":poss (" + getPrintableAmrName("he", amrVarList) + ")"
		elif(possType == -2):
			amrVarList = updateAmrVarList("she", amrVarList)
			stringa = stringa + tabs + ":poss (" + getPrintableAmrName("she", amrVarList) + ")"
		elif(possType == -3):
			amrVarList = updateAmrVarList("it", amrVarList)
			stringa = stringa + tabs + ":poss (" + getPrintableAmrName("it", amrVarList) + ")"
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
		if(polarityFlag):
			stringa = stringa + tabs + ":polarity -"
	if(chiusura):
		stringa = stringa + ")"
	print(stringa)
	return amrVarList

def recArgs(m, args, counter, bkp, mlist, firstPrint, mchecklist, tabs, amrVarList, polarityQres):
	a = []
	polarityFlag = False
	if(firstPrint):
		if(len(args) == 0):
			amrVarList = printAMR(m, args, counter, True, False, True, False, 0, amrVarList, polarityFlag, mchecklist[mlist.index(str(m))])
		else:
			amrVarList = printAMR(m, args, counter, False, False, True, False, 0, amrVarList, polarityFlag, mchecklist[mlist.index(str(m))])
	for x in args:
		if(str(x) != "None"):
			a.append(x)
			if(str(x) in mlist and (mchecklist[mlist.index(str(x))] <= 0)):
				amrVarList = printAMR(m, a, counter, False, True, False, True, tabs, amrVarList, polarityFlag, mchecklist[mlist.index(str(x))])
				counter = len(a)
				a = []
				for (bm,bargs) in bkp:
					if(str(bm) == mlist[mlist.index(str(x))]):
						mchecklist[mlist.index(str(x))] = 1
						recArgs(bm, bargs, 0, bkp, mlist, False, mchecklist, tabs+1, amrVarList, polarityQres)
						
	if(len(args) != 0):
		for (x,y) in qres4:
			if(m == x):
				truthValue = getName(y)
				if(truthValue == "False"):
					polarityFlag = True
		amrVarList = printAMR(m, a, counter, True, True, False, False, tabs, amrVarList, polarityFlag, mchecklist[mlist.index(str(m))])
	return mchecklist
	
#ricerco i mainverb ed i loro argomenti (rule1 + rule2)
qres = g.query(
	"""SELECT DISTINCT ?mainverb ?j_1 ?j_2 ?j_3 ?that
		WHERE {
		  ?mainverb a ?verb . 
		  ?verb rdfs:subClassOf <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Event> .
		  OPTIONAL{?mainverb j.0:Theme ?j_1} .
		  OPTIONAL{?mainverb j.0:Agent ?j_2} .
		  OPTIONAL{?mainverb j.0:Experiencer ?j_3} .
		  OPTIONAL{?mainverb j.4:that ?that}
		}""")

mlist = []
bkp = []
bkpqres6 = []
mlistqres6 = []
mchecklist = []

#guardo se ci sono delle coref
qres2 = g.query(
	"""SELECT DISTINCT ?x ?y
		WHERE {
		  ?x j.1:other_coref ?y
		}""")

#guardo se ci sono delle modality (rule 3)
qres3 = g.query(
	"""SELECT DISTINCT ?x ?y
		WHERE {
		  ?x j.2:hasModality ?y
		}""")

#guardo se ci sono dei TruthValue (rule 4)
qres4 = g.query(
	"""SELECT DISTINCT ?x ?y
		WHERE {
		  ?x j.2:hasTruthValue ?y
		}""")
		
#guardo il focus (rule 5)
qres5 = g.query(
	"""SELECT DISTINCT ?m ?arg
		WHERE {
		  ?arg <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasQuality> ?m
		}""")

qres6 = g.query(
	"""SELECT DISTINCT ?mainverb ?situationChild
		WHERE {
		  ?mainverb a ?verb . 
		  ?verb rdfs:subClassOf <http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#Event> .
		  OPTIONAL{
		  ?mainverb j.4:that ?that .
		  ?that j.3:involves ?situationChild}
		}""")
	

for (m, situationChild) in qres6 :
	if(m in mlistqres6):
		(bm, bChildsList) = bkpqres6[mlistqres6.index(m)]
		bChildsList.append(situationChild)
		bkpqres6[mlistqres6.index(m)] = (bm, bChildsList)
	else:
		mlistqres6.append(m)
		bkpqres6.append((m, [situationChild]))
	

for (m, t, a, e, that) in qres : 
		for (x,y) in qres3:
			if(m == x):
				modality = getName(y)
				if(modality == "Necessary"):
					mlist.append("O#obligate_1")
					bkp.append(("O#obligate_1", [m]))
					mchecklist.append(0)
				if(modality == "Possible"):
					mlist.append("P#permit_1")
					bkp.append(("P#permit_1", [m]))
					mchecklist.append(0)
		args = []
		for x in [t, a, e]:
			if(str(x) != "None"):
				#se e' presente una coref		
				for (xx, yy) in qres2:
					if(x == yy):
						x = xx	
				if(getName(str(x)) == "thing_1" and str(that) != "None"):
					(bm, bChildsList) = bkpqres6[mlistqres6.index(m)]
					inqres5 = False
					for situationChild in bChildsList:
						for (m5, arg5) in qres5:
							if(situationChild == m5):
								x = m5
								inqres5 = True
							if(situationChild == arg5):
								inqres5 = True
						if(not inqres5):
							x = situationChild
				args.append(x)
				
		mlist.append(str(m))			
		bkp.append((m,args))
		mchecklist.append(0)

posslist = []		
for (m, arg) in qres5:
#fare il check per il poss (rule 7) "?x j.3:" . m . "Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#male_1>"
#dopodiche' salvare il risultato come arg, aggiungere una lista per indicare la presenza di flag
	if(getName(str(m)) == "Topic"):
		lll = m
		m = arg
		bkp.append((m, []))
	else:
		bkp.append((m, [arg]))
	mlist.append(str(m))
	
	name = getName(str(m))
	if(name[-2:-1] == "_"):
		realName = name[:-2]
	else:
		realName = name
	
	qres7 = g.query(
	"""SELECT DISTINCT ?x ?y ?z
		WHERE {
		  OPTIONAL{?x j.3:""" + realName + """Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#male_1>} .
		  OPTIONAL{?y j.3:""" + realName + """Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#female_1>} .
		  OPTIONAL{?z j.3:""" + realName + """Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#neuter_1>}
		}""")
	possType = 0
	for (xx, yy, zz) in qres7:
		if(str(xx) == str(m)):
			possType = -1
		elif(str(xx) == str(m)):
			possType = -2
		elif(str(xx) == str(m)):
			possType = -3
	if(possType != 0):
		mchecklist.append(possType)
	else:
		mchecklist.append(0)

counter = 0
for ((m, args)) in bkp : 
		#print("MAINVERB:%s\nTHEME:%s\nAGENT:%s\nEXPERIENCER:%s" %(m, t, a, e))
		
		if(mchecklist[counter] <= 0): #se non e' ancora stata fatta
			mchecklist = recArgs(m, args, 0, bkp, mlist, True, mchecklist, 0, [], qres4)
		mchecklist[counter] = 1
		counter = counter + 1

if(len(bkp) == 0):
	print("\nATTENZIONE: questa versione del parser non consente di tradurre in AMR la frase scelta!")
