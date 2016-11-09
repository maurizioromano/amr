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
g2 = Graph()
#g.parse("boat.rdf")
g.parse("TEMP.rdf")
g2.parse("TEMP.rdf")

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
	
def printAMR(verbo, listaArgomenti, indiceArgomenti, chiusura, soloArgomenti, soloVerbo, argomentoVerbo, tabdeep, amrVarList, polarityFlag, possType, argOf, numberArgOF, escludiArgomenti):
	
	stringa = ""
	vbTabs = "\n"
	if(argOf):
		for tab in range(tabdeep):
			vbTabs = vbTabs + "\t"
	if(not soloArgomenti):
		amrVarList = updateAmrVarList(str(verbo), amrVarList)
		if(argOf):
			stringa = vbTabs+":ARG"+str(numberArgOF)+"-of ("+getPrintableAmrName(str(verbo), amrVarList)
		else:
			stringa = "\n("+getPrintableAmrName(str(verbo), amrVarList)
		tabs = "\n\t"

		if(possType != "0" and possType != "1"):
			if(possType == "-1"):
				amrVarList = updateAmrVarList("he", amrVarList)
				stringa = stringa + tabs + ":poss (" + getPrintableAmrName("he", amrVarList) + ")"
			elif(possType == "-2"):
				amrVarList = updateAmrVarList("she", amrVarList)
				stringa = stringa + tabs + ":poss (" + getPrintableAmrName("she", amrVarList) + ")"
			elif(possType == "-3"):
				amrVarList = updateAmrVarList("it", amrVarList)
				stringa = stringa + tabs + ":poss (" + getPrintableAmrName("it", amrVarList) + ")"
			else:
				amrVarList = updateAmrVarList(possType, amrVarList)
				stringa = stringa + tabs + ":poss (" + getPrintableAmrName(possType, amrVarList) + ")"
	if(not soloVerbo):
		i = indiceArgomenti
		tabs = "\n\t"
		for tab in range(tabdeep):
			tabs = tabs + "\t" 
		

		for arg in listaArgomenti:
			if(arg not in escludiArgomenti):
				amrVarList = updateAmrVarList(str(arg), amrVarList)
				stringa = stringa + tabs + ":ARG" + str(i) + "(" + getPrintableAmrName(str(arg), amrVarList) + ")"
			i = i+1
		if(argomentoVerbo):
			stringa = stringa[:-1] #rimuovo l'ultima parentesi
		if(polarityFlag):
			stringa = stringa + tabs + ":polarity -"
	if(chiusura):
		tabs = "\n"
		for tab in range(tabdeep):
			tabs = tabs + "\t" 
		stringa = stringa + tabs + ")"
	print(stringa)
	return amrVarList

def recArgs(m, args, argsCheckList, counter, bkp, mlist, firstPrint, mchecklist, tabs, amrVarList, polarityQres):
	a = []
	countArgs = 0
	for (x,argsOfOthersM) in args:
		countArgs = countArgs + 1
	polarityFlag = False
	if(firstPrint):
		if(countArgs == 0):
			amrVarList = printAMR(m, None, counter, True, False, True, False, 0, amrVarList, polarityFlag, mchecklist[mlist.index(str(m))], False, 0, [])
		else:
			amrVarList = printAMR(m, args[0], counter, False, False, True, False, 0, amrVarList, polarityFlag, mchecklist[mlist.index(str(m))], False, 0, [])
	i = 0
	for (x,argsOfOthersM) in args:

		if(str(x) != "None" and (not argsCheckList[i])):
			a.append(x)

			if(str(x) in mlist):
				amrVarList = printAMR(m, a, counter, False, True, False, True, tabs, amrVarList, polarityFlag, mchecklist[mlist.index(str(x))], False, 0, [])
			else:
				amrVarList = printAMR(m, a, counter, False, True, False, False, tabs, amrVarList, polarityFlag, "0", False, 0, [])
			counter = len(a)
			a = []
			escludiVerbi = []
			if(str(x) in mlist and (mchecklist[mlist.index(str(x))] != "1")):
				for (bm,bargs,bargsCheckList) in bkp:	
					if(str(bm) == mlist[mlist.index(str(x))]):
						mchecklist[mlist.index(str(x))] = "1"
						escludiVerbi.append(bm)

						mchecklist = recArgs(bm, bargs, bargsCheckList, 0, bkp, mlist, False, mchecklist, tabs+1, amrVarList, polarityQres)
			
			#se ci sono degli argomenti in comune con altri verbi
			
			
			for xxx in argsOfOthersM:
				numberXXX = xxx[-1:]
				xxx = xxx[:-1]
				
				(bm,bargs,bargsCheckList) = bkp[mlist.index(str(xxx))]
				if(mchecklist[mlist.index(str(bm))] == "0"):
					if(bm not in escludiVerbi):
						argomentiDaStampare = []
						argomentiDaEscludere = []
						for (argomento, arOfOthrs) in bargs:
							if(str(argomento) in mlist):
								argomentiDaEscludere.append(argomento)
							argomentiDaStampare.append(argomento)
						argomentiDaEscludere.append(argomentiDaStampare[int(numberXXX)])
						amrVarList = printAMR(bm, argomentiDaStampare, 0, True, False, False, False, tabs+2, amrVarList, polarityFlag, mchecklist[mlist.index(str(bm))], True, int(numberXXX), argomentiDaEscludere)
						mchecklist[mlist.index(str(xxx))] = "1"
			

		i = i+1				
	
	if(countArgs != 0):
		for (x,y) in qres4:
			if(m == x):
				truthValue = getName(y)
				if(truthValue == "False"):
					polarityFlag = True
		amrVarList = printAMR(m, a, counter, True, True, False, False, tabs, amrVarList, polarityFlag, mchecklist[mlist.index(str(m))], False, 0, [])
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

fakeMlist = []
for (m, t, a, e, that) in qres : 
	fakeMlist.append(m)
	

for (m, t, a, e, that) in qres : 
		for (x,y) in qres3:
			if(m == x):
				modality = getName(y)
				if(modality == "Necessary"):
					mlist.append("O#obligate_1")
					bkp.append(("O#obligate_1", [(m, [])], [False]))
					mchecklist.append("0")
				if(modality == "Possible"):
					mlist.append("P#permit_1")
					bkp.append(("P#permit_1", [(m, [])], [False]))
					mchecklist.append("0")
		args = []
		argsCheckList = []
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
				args.append((x, []))
				argsCheckList.append(False)
				
		#verifico se il verbo ha argomenti in comune con altri verbi
		for (bkpm, bkpargs, bkpargsCheckList) in bkp:
			for (arg, argOfOthersM) in bkpargs:
				i = 0
				#j = 0
				for (x, lll) in args:
					if(bkpm != m and (x not in fakeMlist)):
						if(x == arg and (str(m)+str(i) not in argOfOthersM)):
							argOfOthersM.append(str(m)+str(i))
							argsCheckList[i] = True
							#bkpargs[j] = (arg, argOfOthersM)

					i = i+1
					
				#j = j+1
				bkp[mlist.index(str(bkpm))] = (bkpm, bkpargs, bkpargsCheckList)
		
		mlist.append(str(m))			
		bkp.append((m,args,argsCheckList))
		mchecklist.append("0")

		
for (m, arg) in qres5:

	if(getName(str(m)) == "Topic"):
		lll = m
		m = arg
		bkp.append((m, [], []))
	else:
		bkp.append((m, [(arg, [])], [False]))
	mlist.append(str(m))

	name = getName(str(m))
	if(name[-2:-1] == "_"):
		realName = name[:-2]
	else:
		realName = name
	
	qres7 = g2.query(
	"""SELECT DISTINCT ?x ?y ?z ?others ?k
		WHERE {
		  OPTIONAL{?x j.3:""" + realName + """Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#male_1>} .
		  OPTIONAL{?y j.3:""" + realName + """Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#female_1>} .
		  OPTIONAL{?z j.3:""" + realName + """Of <http://www.ontologydesignpatterns.org/ont/fred/domain.owl#neuter_1>} .
		  OPTIONAL{?others j.2:""" + realName + """Of ?k}
		}""")
	
	possType = "0"
	for (xx, yy, zz, others, k) in qres7:
		if(str(xx) == str(m)):
			possType = "-1"
		elif(str(yy) == str(m)):
			possType = "-2"
		elif(str(zz) == str(m)):
			possType = "-3"
		elif(str(others) == str(m)):
			possType = str(k)
	if(possType != "0"):
		mchecklist.append(possType)
	else:
		mchecklist.append("0")

counter = 0


for (m, args, argsCheckList) in bkp : 
		#print("MAINVERB:%s\nTHEME:%s\nAGENT:%s\nEXPERIENCER:%s" %(m, t, a, e))

		if(mchecklist[counter] != "1"): #se non e' ancora stata fatta
			mchecklist = recArgs(m, args, argsCheckList, 0, bkp, mlist, True, mchecklist, 0, [], qres4)
		mchecklist[counter] = "1"
		counter = counter + 1

if(len(bkp) == 0):
	print("\nATTENZIONE: questa versione del parser non consente di tradurre in AMR la frase scelta!")
