import highLevelParsing #This imports prototypes,utility, and cleaning too
import prototypes       #But just to make the code nice, import them again
import pickle           #Pickle module for saving

class DCECContainer:
    def __init__(self):
        self.namespace = prototypes.NAMESPACE()
        self.statements = []
        self.checkMap = {}
        
    def save(self,filename):
        namespaceOut = open(filename+".namespace","w")
        statementsOut = open(filename+".statements","w")
        pickle.dump(self.namespace,namespaceOut)
        pickle.dump(self.checkMap,statementsOut)
    
    def load(self,filename):
        nameIn = open(filename+".namespace","r")
        stateIn = open(filename+".statements","r")
        namespaceIn = pickle.load(nameIn)
        statementsIn = pickle.load(stateIn)
        if isinstance(namespaceIn,prototypes.NAMESPACE):
            self.namespace = namespaceIn
        else:
            return False
        if isinstance(statementsIn,dict):
            self.statements = statementsIn.keys()
            self.checkMap = statementsIn
    
    def printStatement(self,statement,expressionType = "S"):
        if isinstance(statement,str):
            print statement
        quantifiernames = ["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
        quantifiervars = []
        place = 0
        if expressionType == "S":
            temp = statement.createSExpression()
        elif expressionType == "F":
            temp = statement.createFExpression()
        else:
            print "ERROR: invalid notation type"
            return False
        while place != -1:
            place = temp.find("QUANTIFIER")
            if place == -1:
                break
            temp2 = temp[place:place+20]
            for potential in quantifiernames:
                if potential in quantifiervars or potential in self.namespace.atomics.keys():
                    continue
                else:
                    quantifiervars.append(potential)
                    temp = temp.replace(temp2,potential)
                    break
        return temp
    
    def addStatement(self,statement):
        addAtomics = {}
        addFunctions = {}
        addee = statement
        if isinstance(addee,str):
            addee,addAtomics,addFunctions = highLevelParsing.tokenizeRandomDCEC(addee,self.namespace)
            if isinstance(addee,bool) and not addee:
                print "ERROR: the statement "+str(statement)+" was not correctly formed."
                return False
        elif isinstance(addee,highLevelParsing.Token):
            pass
        else:
            print "ERROR: the input "+str(statement)+" was not of the correct type."
            return False
        for atomic in addAtomics.keys():
            if isinstance(atomic,highLevelParsing.Token): continue #Tokens are not currently stored
            for potentialtype in range(0,len(addAtomics[atomic])):
                if not self.namespace.noConflict(addAtomics[atomic][0],addAtomics[atomic][potentialtype]):
                    print "ERROR: The atomic "+atomic+" cannot be both "+addAtomics[atomic][potentialtype]+" and "+addAtomics[atomic][0]+". (This is caused by assigning different sorts to two atomics inline. Did you rely on the parser for sorting?)"
                    return False
        for function in addFunctions.keys():
            for item in addFunctions[function]:
                if item[0] == "?":
                    print "ERROR: please define the returntype of the inline function "+function
                    return False
                else:
                    self.namespace.addCodeFunction(function,item[0],item[1])         
        for atomic in addAtomics.keys():
            if isinstance(atomic,highLevelParsing.Token): continue #Tokens are not currently stored
            elif atomic in self.namespace.atomics.keys():
                if not addAtomics[atomic][0] == self.namespace.atomics[atomic]:
                    print "ERROR: The atomic "+atomic+" cannot be both "+addAtomics[atomic][0]+" and "+self.namespace.atomics[atomic]+"."
                    return False
            else:
                self.namespace.addCodeAtomic(atomic,addAtomics[atomic][0])
            
        self.statements.append(addee)
        self.checkMap[addee.createSExpression()] = addee  
        return True


    def sortOf(self,statement):
        if isinstance(statement,str):
            return self.namespace.atomics.get(statement)
        if statement == None:
            return None
        if not statement.funcName in self.namespace.functions.keys():           
            return None
        tmpFunc = statement.funcName
        tmpArgs = statement.args
        tmpTypes = []
        for arg in tmpArgs:
            tmpTypes.append(self.sortOf(arg))
        for x in self.namespace.functions[tmpFunc]:
            if len(x[1]) != len(tmpTypes): continue
            else:
                returner = True
                for r in range(0,len(x[1])):
                    if not tmpTypes[r] == None and self.namespace.noConflict(tmpTypes[r],x[1][r],):
                        continue
                    else:
                        returner = False
                        break
                if returner:
                    return x[0]
                else:
                    continue
        return None

    def sortsOfParams(self,statement):
        sorts=[]
        if isinstance(statement,str):
            return sorts
        if statement == None:
            return None
        if not statement.funcName in self.namespace.functions.keys():
            return None
        tmpFunc = statement.funcName
        tmpArgs = statement.args
        tmpTypes = []
        for arg in tmpArgs:
            tmpTypes.append(self.sortOf(arg))
        for x in self.namespace.functions[tmpFunc]:
            if len(x[1]) != len(tmpTypes): continue
            else:
                returner = True
                for r in range(0,len(x[1])):
                    if not tmpTypes[r] == None and self.namespace.noConflict(tmpTypes[r],x[1][r],):
                        continue
                    else:
                        returner = False
                        break
                if returner:
                    return x[1]
                else:
                    continue
        return None

    
    def stupidSortDefine(self,sort,oldContainer):
        if sort in self.namespace.sorts.keys():
            return
        else:
            for x in oldContainer.namespace.sorts[sort]:
                self.stupidSortDefine(x,oldContainer)
            self.namespace.addCodeSort(sort,oldContainer.namespace.sorts[sort])
    
    #TODO replace with iterator
    def stupidLoop(self,token,functions,atomics,oldContainer):
        if isinstance(token,str):
            if oldContainer.sortOf(token)==None:
                self.stupidSortDefine(atomics[token][0],oldContainer)
                self.namespace.addCodeAtomic(token,atomics[token][0])
            else:
                self.stupidSortDefine(oldContainer.sortOf(token),oldContainer)
                self.namespace.addCodeAtomic(token,oldContainer.sortOf(token))
        else:
            if token.funcName in ["forAll","exists"]:
                pass
            elif oldContainer.sortOf(token)==None:
                argTypes = []
                for arg in token.args:
                    argTypes.append(atomics[arg][0])
                if token in atomics.keys():
                    self.stupidSortDefine(atomics[token][0],oldContainer)
                    for arg in argTypes:
                        self.stupidSortDefine(arg,oldContainer)
                    self.namespace.addCodeFunction(token.funcName,atomics[token][0],argTypes)
                else:
                    for x in functions[token.funcName]:
                        self.stupidSortDefine(x[0],oldContainer)
                        for y in x[1]:
                            self.stupidSortDefine(y,oldContainer)
                        self.namespace.addCodeFunction(token.funcName,x[0],x[1])
            else:
                self.stupidSortDefine(oldContainer.sortOf(token),oldContainer)
                for x in oldContainer.sortsOfParams(token):
                    self.stupidSortDefine(x,oldContainer)
                self.namespace.addCodeFunction(token.funcName,oldContainer.sortOf(token),oldContainer.sortsOfParams(token))
            for arg in token.args:
                self.stupidLoop(arg,functions,atomics,oldContainer)


    def tokenize(self,statement):
        if not isinstance(statement,str):
            return False
        dcecContainer=DCECContainer()
        stuff=highLevelParsing.tokenizeRandomDCEC(statement,self.namespace)
        if isinstance(stuff,bool) and not stuff:
            return False
        dcecContainer.stupidLoop(stuff[0],stuff[2],stuff[1],self)
        dcecContainer.addStatement(statement)
        return dcecContainer

if __name__ == "__main__":
    test = DCECContainer()
    test.namespace.addBasicDCEC()
    test.namespace.addBasicLogic()
    #test.namespace.addTextFunction("Boolean hello Agent Moment")
    #test.namespace.addTextFunction("Boolean hello Boolean")
    #test.namespace.addTextAtomic("Boolean earth")
    #test.namespace.addTextSort(raw_input("Enter a sort: "))
    #test.namespace.addTextSort(raw_input("Enter a sort: "))
    #test.namespace.addTextSort(raw_input("Enter a sort: "))
    test.tokenize(raw_input("Enter an expression: "))
    test.addStatement(raw_input("Enter an expression: "))
    test.addStatement(raw_input("Enter an expression: "))
    test.save("TEST")
    new = DCECContainer()
    new.load("TEST")
    for x in test.statements:
        x.printTree()
    print test.namespace.atomics
    print test.namespace.functions
    print test.namespace.sorts
    print test.sortsOfParams(test.statements[0])
    print test.sortOf(test.statements[0])