
class instrManager():

    def __init__(self,compInstr,manageType):
        temp = 0
        # types=["SCALAR","SQUARE","CONSTANT","OUTPUT","OPERATIONS"]
        self.manageType = manageType
        self.compInstr = compInstr

        # Dict of managment instructions objects, assign1 is variable
        self.instrDict = {'assign1':None,'assign2':None,'scalMult':None,'square':None,'output':None}
        # Dict of managment instructions list indices for cdc6600system instrList
        self.instrDictIdxs = {'assign1':None,'assign2':None,'scalMult':None,'square':None,'output':None}
        self.instrInOthers = {'assign1':False,'assign2':False,'scalMult':False,'square':False,'output':False}
        self.opDict = {}
        self.opDictIdx = {}
        self.mangOps = {}
        self.calcVal = 0

    def getOutputIdx(self):
        if self.manageType == "SCALAR":
            return self.instrDict['scalMult']
        elif self.manageType == "SQUARE":
            return self.instrDict['scalMult']
        elif self.manageType == 'OUTPUT':
            return self.instrDict['output']
        else:
            return self.instrDict['assign1']

    def addInstr(self,instr,key):
        self.instrDict[key] = instr

    def assignIdx(self,instr,idx):
        for key,value in self.instrDict.items():
            if value == instr:
                self.instrDictIdxs[key] = idx
                return

    def getInstrOrder(self):
        returnList = []
        for key,value in self.instrDict.values():
            if value is not None:
                returnList.append(value)

        return returnList

    def __str__(self):
        return self.manageType

    def computeCalc(self):
        if self.manageType == "SCALAR":
            return self.instrDict['assign1'].value * self.instrDict['scalMult'].value
        elif self.manageType == "SQUARE":
            return self.instrDict['assign1'].value * self.instrDict['assign1'].value * self.instrDict['assign2'].value
        elif self.manageType == 'OUTPUT':
            return self.instrDict['output'].value
        else:
            return self.instrDict['assign1'].value

    def calcOutput(self,outputVal):
        self.instrDict['output'].value = outputVal

    def getOutputVal(self):
        return self.instrDict['output'].value

    # Add managers for conducting operations between
    def addOps(self,manage1,manage2):
        temp = 0 # TODO
        print("TODO")

    # Get all operation instructions associated with manager
    def getOps(self):
        if self.manageType != "OPERATIONS":
            retList = []
            opsList = ['square','scalMult']
            for entry in opsList:
                if self.instrDict[entry] is not None:
                    retList.append(self.instrDict[entry])

            return retList
        else:
            retList = []
            for key,val in self.opDict.items():
                for instr in val:
                    retList.append(instr)

            return retList

    def getOuputReg(self):
        temp = 0
        print("TODO")
        # TODO

    def __add__(self, other):
        return self.computeCalc() + other.computeCalc()

    def __sub__(self, other):
        return self.computeCalc() - other.computeCalc()
