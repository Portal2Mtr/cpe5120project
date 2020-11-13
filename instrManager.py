
class instrManager():

    def __init__(self,compInstr,manageType,system):
        temp = 0
        # types=["SCALAR","SQUARE","CONSTANT","OUTPUT","OPERATIONS"]
        self.manageType = manageType
        self.compInstr = compInstr
        self.system = system

        # Dict of managment instructions objects, assign1 is variable
        self.instrDict = {'assign1':None,'assign2':None,'scalMult':None,'square':None,'output':None}
        # Dict of managment instructions list indices for cdc6600system instrList
        self.instrDictIdxs = {'assign1':None,'assign2':None,'scalMult':None,'square':None,'output':None}
        self.instrInOthers = {'assign1':False,'assign2':False,'scalMult':False,'square':False,'output':False}
        self.opDict = {}
        self.opDictIdx = {}
        self.mangOps = {}
        self.calcVal = 0

    def getOutputIdx(self,opCalc=None):
        if self.manageType == "SCALAR":
            return self.instrDictIdxs['scalMult']
        elif self.manageType == "SQUARE":
            return self.instrDictIdxs['scalMult']
        elif self.manageType == 'OUTPUT':
            return self.instrDictIdxs['output']
        elif self.manageType == "OPERATIONS":
            print("TODO")
            return self.opDictIdx
        else: # Constant
            return self.instrDictIdxs['assign1']

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

    def getOutputReg(self):
        temp = 0
        print("TODO")
        # TODO

    def genOpEqn(self,instr):

        for key,val in self.instrDict.items():
            if val is not None:
                if val == instr:
                    workInstr = instr
                    break

        self.system.opRegIdx += 1
        if instr.operator == '+': # Check if last addition, if so output to X7 if x6 is full
            if self.system.instrList.index(instr) + 1 == (len(self.system.instrList) - 1):
                # Last addition
                if self.system.opRegIdx > 1: # Assignment for x6 has passed
                    opAddr = 'X7'

            else:
                opAddr = self.system.opRegsList[self.system.opRegIdx]
        else:
            opAddr = self.system.opRegsList[self.system.opRegIdx]
        opAddrIdx = int(opAddr[-1])
        instr.outputAddrIdx = opAddrIdx
        instr.instrRegs['result'] = opAddr

        self.system.opRegs[opAddr] = self.instrDictIdxs[key]

        leftAddr = self.system.instrList[instr.leftOpIdx].instrRegs['result']
        rightAddr = self.system.instrList[instr.rightOpIdx].instrRegs['result']

        if 'A' in leftAddr:
            leftAddr = leftAddr.replace('A','X')
        if 'A' in rightAddr:
            rightAddr = rightAddr.replace('A','X')

        instr.instrRegs['leftOp'] = leftAddr
        instr.instrRegs['rightOp'] = rightAddr
        instr.instrRegs['operand'] = instr.operator


    # Generate left/right idxs from instruction list for equation generation from within manager
    def linkInstr(self,instr):

        for key,val in self.instrDict.items():
            if val is not None:
                if val.varName == instr.varName: # Instr may belong to other manager
                    workInstr = val
                    workKey = key
                    break

        # Get instruction indices in instruction list from managers
        leftOpIdx = 0
        rightOpIdx = 0
        if workKey == 'square':
            leftOpIdx = self.instrDictIdxs['assign1']
            rightOpIdx = leftOpIdx
            workInstr.assignOpVarIdx(leftOpIdx,rightOpIdx)
        elif workKey == 'scalMult' and self.manageType == 'SQUARE': # Link scalar multiply to output of square register
            leftOpIdx = self.instrDictIdxs['square']
            rightOpIdx = self.instrDictIdxs['assign2']
            workInstr.assignOpVarIdx(leftOpIdx, rightOpIdx)
        elif workKey == 'scalMult':
            leftOpIdx = self.instrDictIdxs['assign1']
            rightOpIdx = self.instrDictIdxs['assign2']
            workInstr.assignOpVarIdx(leftOpIdx, rightOpIdx)


    def updateIdxs(self,instrList):

        if self.manageType != "OPERATIONS":
            for key,instr in self.instrDict.items():
                if instr is not None:
                    for idx,entry in enumerate(instrList):
                        # Catch for getting X in both managers
                        if entry == instr or (instr.varName == entry.varName and entry.instrManager.instrInOthers[key]):
                            self.instrDictIdxs[key] = idx
        else:
            for key, group in self.opDict.items():
                instr = group[0] # TODO Temp
                idxs = [idx for idx,entry in enumerate(instrList) if entry == instr]
                self.opDictIdx[key] = idxs

    def getLastCalcOut(self,instrList):
        for idx,instr in enumerate(instrList):
            if instr == self.instrDict['output']:
                lastCalcIdx = idx -1
                instr.leftOpIdx = lastCalcIdx
        instr.rightOpIdx = int(self.system.getEmptyMem()[-1])

    def updateCompOpIdxs(self,compOpList):
        workOps = self.mangOps[compOpList[0].varName]
        mangDict = self.system.compDict
        alreadyCalc = []
        for idx,compOp in enumerate(compOpList):
            currWorkOps = workOps[idx]
            opLens = [len(i) for i in currWorkOps]

            if 1 not in opLens: # Check if working with constant
                currWorkInstr = compOpList[idx]
                alreadyCalc.extend(currWorkOps)
                leftMang = [val for key,val in mangDict.items() if val.compInstr == currWorkOps[0]]
                leftIdx = leftMang[0].getOutputIdx()
                rightMang = [val for key, val in mangDict.items() if val.compInstr == currWorkOps[1]]
                rightIdx = rightMang[0].getOutputIdx()
                currWorkInstr.assignOpVarIdx(leftIdx,rightIdx)
            else:
                # Get output of first comp instr instead of manager
                for jdx,compInstr in enumerate(currWorkOps):
                    if compInstr in alreadyCalc:
                        workIdx = jdx

                if workIdx == 0: # leftopidx is from previous comp calc
                    currWorkInstr = compOpList[idx]
                    leftIdx = self.opDictIdx[compOpList[0].varName][0]
                    rightMang = [val for key, val in mangDict.items() if val.compInstr == currWorkOps[1]]
                    rightIdx = rightMang[0].getOutputIdx()
                    currWorkInstr.assignOpVarIdx(leftIdx, rightIdx)
                else: # rightopidx is from previous comp calc
                    # TODO Does this work?
                    currWorkInstr = compOpList[idx]
                    leftIdx = leftMang[0].getOutputIdx()
                    rightMang = [val for key, val in mangDict.items() if val.compInstr == currWorkOps[1]]
                    rightIdx = self.opDictIdx[compOpList[0].varName][0]
                    currWorkInstr.assignOpVarIdx(leftIdx, rightIdx)


    def __add__(self, other):
        return self.computeCalc() + other.computeCalc()

    def __sub__(self, other):
        return self.computeCalc() - other.computeCalc()