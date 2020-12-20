
class instrManager():
    """
    Manager object for handling interinstruction calculations. Greatly simplifies instrcution
    indexing and calculation handling.
    """

    def __init__(self,compInstr,manageType,system):
        """
        Constructor for instruction manager
        :param compInstr: Complex instruciton to refer to the manager by.
        :param manageType: Type of manager
        :param system: CDC 6600/7600 system.
        """
        # Manager types = ["SCALAR","SQUARE","CONSTANT","OUTPUT","OPERATIONS"]
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
        # Output calculation value
        self.calcVal = 0

    def getOutputIdx(self):
        """
        Gets the output register for a given type of input instruction.
        :return: Output register.
        """
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

    def assignIdx(self, instr, idx):
        for key, value in self.instrDict.items():
            if value == instr:
                self.instrDictIdxs[key] = idx
                return

    def addInstr(self,instr,key):
        """
        Add instruction to manager
        :param instr: Input instruction
        :param key: Key for instruction dictionary
        :return:
        """
        self.instrDict[key] = instr

    def getInstrOrder(self):
        """
        Returns a list of each instruction ordered in the manager's dictionary.
        :return: List of ordered instructions.
        """
        returnList = []
        for key,value in self.instrDict.values():
            if value is not None:
                returnList.append(value)

        return returnList

    def calcOutput(self,outputVal):
        """
        Set the output of the manager's instruction dictionary to a value.
        :param outputVal: Value for manager's dict value.
        :return:
        """
        self.instrDict['output'].value = outputVal

    def getOutputVal(self):
        """
        Get the output value of this manager's instruction dictionary.
        :return:
        """
        return self.instrDict['output'].value


    def assignIdx(self,instr,idx):
        """
        Assign an instruction in the manager a given index.
        :param instr: Input instruction
        :param idx: Input index.
        """
        for key,value in self.instrDict.items():
            if value == instr:
                self.instrDictIdxs[key] = idx
                return

    def computeCalc(self):
        """
        Computes the calculated value for the managers type.
        :return: Integer value with correct calculations.
        """
        # Perform all calculations here
        if self.manageType == "SCALAR":
            self.instrDict['scalMult'].value = self.instrDict['assign1'].value * self.instrDict['assign2'].value
            return self.instrDict['scalMult'].value
        elif self.manageType == "SQUARE":
            return self.instrDict['assign1'].value * self.instrDict['assign1'].value * self.instrDict['assign2'].value
        elif self.manageType == 'OUTPUT':
            return self.instrDict['output'].value
        else:
            return self.instrDict['assign1'].value

    def getOps(self):
        """
        Get all operation instructions associated with manager
        :return: Operation instruction list.
        """
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

    def genOpEqn(self,instr):
        """
        Generate operation equation from operation index.
        :param instr:
        :return:
        """

        for key,val in self.instrDict.items():
            if val is not None:
                if val == instr:
                    workInstr = instr
                    break

        self.system.opRegIdx += 1

        # Get instr object from manager
        if instr.operator == '+': # Check if last addition, if so output to X7 if x6 is full

            if self.system.instrList[-2] is instr:
                # Last addition
                if self.system.opRegIdx > 1: # Assignment for x6 has passed
                    opAddr = 'X7'

            else:
                opAddr = self.system.opRegsList[self.system.opRegIdx]
                # Reuse scalar assignment register
        else:
            # Check if this is scalar multiple, if so reuse assignment register
            if self.manageType == "SCALAR":
                reuseMem = 'X' + self.instrDict['assign2'].instrRegs['result'][-1]
                opAddr = reuseMem
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

    def linkInstr(self,instr):
        """
         Generate left/right idxs from instruction list for equation generation from within manager
        :param instr: Input instruction
        :return:
        """

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
        """
        Update the indices within the manager with those in the instruction list.
        :param instrList:
        :return:
        """

        if self.manageType != "OPERATIONS":
            for key,instr in self.instrDict.items():
                if instr is not None:
                    for idx,entry in enumerate(instrList):
                        # Catch for getting X in both managers
                        if entry == instr or (instr.varName == entry.varName and entry.instrManager.instrInOthers[key]):
                            self.instrDictIdxs[key] = idx
        else:
            for key, group in self.opDict.items():
                instr = group[0]
                idxs = [idx for idx,entry in enumerate(instrList) if entry == instr]
                self.opDictIdx[key] = idxs

    def getLastCalcOut(self,instrList):
        """
        Get the
        :param instrList:
        :return:
        """
        for idx,instr in enumerate(instrList):
            if instr == self.instrDict['output']:
                lastCalcIdx = idx -1
                instr.leftOpIdx = lastCalcIdx
                # Get empty memory register for output
        instr.rightOpIdx = int(self.system.getEmptyMem()[-1])

    def updateCompOpIdxs(self,compOpList):
        """
        For each complex operation instruction (addition), correctly gives the output
        instruction index in the instruction list for proper instruction equation
        generation.
        :param compOpList: List of operations using the complex instructions.
        """
        workOps = self.mangOps[compOpList[0].varName]
        mangDict = self.system.compDict
        alreadyCalc = []
        for idx,compOp in enumerate(compOpList):
            currWorkOps = workOps[idx]
            opLens = [len(i) for i in currWorkOps]

            if 1 not in opLens: # Check if working with constant
                currWorkInstr = compOpList[idx]
                alreadyCalc.extend(currWorkOps)
                leftMang = []
                rightMang = []
                for key,val in mangDict.items():
                    if val is not None:
                        if val.compInstr == currWorkOps[0]:
                            leftMang.append(val)
                for key,val in mangDict.items():
                    if val is not None:
                        if val.compInstr == currWorkOps[1]:
                            rightMang.append(val)
                leftIdx = leftMang[0].getOutputIdx()
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
                    currWorkInstr = compOpList[idx]
                    leftIdx = leftMang[0].getOutputIdx()
                    rightMang = [val for key, val in mangDict.items() if val.compInstr == currWorkOps[1]]
                    rightIdx = self.opDictIdx[compOpList[0].varName][0]
                    currWorkInstr.assignOpVarIdx(leftIdx, rightIdx)

    def __add__(self, other):
        if type(other) == instrManager:
            return self.computeCalc() + other.computeCalc()
        elif type(other) == int:
            return self.computeCalc() + other

    def __sub__(self, other):
        return self.computeCalc() - other.computeCalc()

    def __str__(self):
        return self.manageType

