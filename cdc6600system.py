from cdc6600instr import CDC6600Instr

class CDC6600System():

    """
        The main CDC 6600 simulation object. This
        object uses the CDC6600Instr objects to
        generate a timing diagram for the CDC 6600.
    """

    def __init__(self,inputVar="X"):
        """
        Constructor for CDC6600System,
        :param inputVar: Variable string to alter what
        variable to look for in input equation.
        """

    def __init__(self):
        numAddr = 8
        numOp = 8
        numMem = 8
        self.addrRegs = {}
        self.opRegs = {}
        self.memRegs ={}
        for i in range(numAddr):
            self.addrRegs["A" + str(i)] = None

        for i in range(numOp):
            self.opRegs["X" + str(i)] = None

        for i in range(numMem):
            self.memRegs["K" + str(i)] = None

        # Define 6600 wait and Func. Unit Calc times
        self.wordSize = 4 # Bytes
        self.shortWait = 1
        self.longWait = 2
        self.wordWait = 8
        self.unitReadyWait = 1
        self.fetchStoreWait = 4
        self.opMap = {
            "+":"FPADD"
        }
        self.funcUnits = {
            "FPADD":3,
            "MULTIPLY1":10,
            "MULTIPLY2":10,
            "DIVIDE":29,
            "FIXADD":3,
            "INCR1":3,
            "INCR2":3,
            "BOOLEAN":3,
            "SHIFT":3, # TODO: Special case for FP
            "BRANCH":0 # TODO: Depends on input
        }
        self.busyUntil = {
            "FPADD": 0,
            "MULTIPLY1": 0,
            "MULTIPLY2": 0,
            "DIVIDE": 0,
            "FIXADD": 0,
            "INCR1": 0,
            "INCR2": 0,
            "BOOLEAN": 0,
            "SHIFT": 0,
            "BRANCH": 0
        }
        self.instrList = []
        self.opMRU = None # Set most recently used op address for calculations

        # Setup simulation vars TODO
        self.currWordTimes = {}

        self.ops = {"+": operator.add,
               "-": operator.sub,
               "*":operator.mul}  # etc.

        self.inputVar = inputVar

        self.dataDeps = []
        self.hardDeps = []

        # Used for keeping track of complex instruction objects
        self.compDict = {'SQU':None,'SCA':None,
                         'CON':None,'OPS':None,'OUT':None}

        self.genTimeIdx = 0

    # Move functions to separate files for cleaner editing
    from cdc6600score import parseAndSort,eqnAndRegisters
    from cdc6600instrpipe import performArithmetic,generateTimes,\
        cleanUpTimes,checkDataDepend,getTimeFromOp,createDesc


    def getEmptyAddr(self):
        for i in self.addrRegs.keys():
            if i != "A0":
                if self.addrRegs[i] is None:
                    return i

    # Sets addr register to instruction number from instrList
    def setAddrByIdx(self,register,idx):
        self.addrRegs[register] = idx

    def setMemByIdx(self,register,idx):
        self.memRegs[register] = idx

    def getEmptyOp(self):
        for i in self.opRegs.keys():
            if self.opRegs[i] is None:
                return i

    def getEmptyMem(self):
        for i in self.memRegs.keys():
            if i != "K0":
                if self.memRegs[i] is None:
                    return i

    def checkBusy(self,funcUnit,currTime):

        """
        Checks if a given functional unit is busy.
        :param funcUnit: Functional unit to check.
        :param currTime: Given time to compare to functional unit.
        :return: Bool if currTime is greater
        than the time a functional unit is busy.
        """

        waitVal = self.busyUntil[funcUnit]
        return (waitVal > currTime)

    def getFuncFromOp(self,operator):
        return self.opMap[operator]

    def creatInstrList(self,command, values, varInput):
        """
        Creates the global instruction list for
        generating the timing table.
        :param command: Input equation.
        :param values: Constant values
        :param varInput: X Variable input value.
        :return: Created instruction list.
        """
        # Move parseandsort to make editing easer
        instrList = self.parseAndSort(command=command,
                                      values=values,
                                      varInput=varInput)
        return instrList

    def 
    Conflict(self,instr):
        """
        Checks for hardware resource conflicts
        with a given instruction.
        :param instr: Input instruction.
        :return:
        """
        category = instr.category
        timing = instr.timeDict['issueTime']

        if (category == "FETCH") or (category == "STORE"):
            category = self.getAvailIncr()

        if(self.busyUntil[category] > timing):

            instrIdx = self.instrList.index(instr)
            print("Hardware resource dependancy at "
                  "instr line %s!" % (instrIdx + 1))
            lastInstr = self.getLastInstrFunc(instr.category)
            lastInstr.conflictInd['unitReadyTime'] = 1
            instr.conflictInd['startTime'] = 1
            self.hardDeps.append(instrIdx+1)
            return self.busyUntil[category] - timing
        else:
            self.busyUntil[category] = self.funcUnits[category] \
                                       + timing + self.unitReadyWait
            return 0

    def checkFuncUnit(self,instr):
        """
        Checks if an instructions functional unit is available.
        :param instr: Instruction to check functional unit for.
        :return: Boolean on whether functional unit is availible.
        """
        unitReady = False
        timing = instr.timeDict['issueTime']
        if instr.operator is not None:
            if "MULTIPLY" != instr.category or \
                    instr.category.find("INCR") != -1:
                if self.busyUntil[instr.category] < timing:
                    unitReady = True
            else:
                unitReady = True # For CDC6600,
                # only nonmultiply and nonadd units are an issue.


        return unitReady

    def getLastInstrFunc(self,category):
        """
        Returns the last instruction executed by a functional unit.
        :param category: Functional unit to check
        :return: Instruction that was last executed by functional unit.
        """
        if "MULTIPLY" in category:
            for key,manage in self.compDict.items():
                # Check comp operations for conflicting functional unit times
                for key2,instr in manage.instrDict.items():
                    if instr is not None:
                        if instr.category == category:
                            return instr
        else:
            for key,manage in self.compDict.items():
                # Check comp operations for conflicting functional unit times
                for key2,instrList in manage.opDict.items():
                    for instr in instrList:
                        if instr is not None:
                            if instr.category == category:
                                return instr
        return None

    def getCurrIncr(self):
        if self.busyUntil['INCR1'] > self.busyUntil['INCR2']:
            return 'INCR1'
        else:
            return 'INCR2'

    def getAvailIncr(self):
        if self.busyUntil['INCR1'] <= self.busyUntil['INCR2']:
            return 'INCR1'
        else:
            return 'INCR2'


    def createDesc(self,instr):

        if (instr.category == "FETCH"):
            instr.catDesc = "Fetch"
            instr.instrDesc = instr.catDesc + " " + instr.varName
        elif instr.category == "STORE":
            instr.catDesc = "Store"
            instr.instrDesc = instr.catDesc + " " + instr.varName
        else:
            instr.catDesc = instr.category
            instr.instrDesc = instr.catDesc + " " + instr.instrRegs['leftOp'] + " "+ instr.instrRegs['rightOp']


    def getTimeFromOp(self,category):

        try:
            return self.funcUnits[category]
        except(KeyError):
            if (category == "FETCH") or (category == "STORE"):
                return self.funcUnits[self.getCurrIncr()]
            else:
                return 0


    def generateTimes(self,instr):
        # TODO compute output times based on instruction category
        # TODO Main simulation loop will go here!
        instrIdx = self.instrList.index(instr)
        if instrIdx == 0:
            instr.timeDict['issueTime'] = 1
            self.currWordTimes[instr.currWord] = 1
        else:
            # Check for next word
            if self.instrList[instrIdx-1].currWord == instr.currWord:
                prevType = self.instrList[instrIdx - 1].instrType
                if prevType == "LONG":
                    instr.timeDict['issueTime'] = self.longWait + self.instrList[instrIdx - 1].timeDict['issueTime']
                else:
                    instr.timeDict['issueTime'] = self.shortWait + self.instrList[instrIdx - 1].timeDict['issueTime']
            else:
                instr.timeDict['issueTime'] = self.wordWait + self.currWordTimes[self.instrList[instrIdx-1].currWord]
                self.currWordTimes[instr.currWord] = instr.timeDict['issueTime']


            # TODO fillout conditions

        # Check for timing of start execution
        if False: # TODO Check for data-dependant hazard
            temp = 0
        else:
            # Get timing offset for managing resource conflicts
            instr.timeDict['startTime'] = instr.timeDict['issueTime'] + \
                                          self.checkResourceConflict(instr.category,instr.timeDict['issueTime'])

        instr.timeDict['resultTime'] = instr.timeDict['startTime'] + self.getTimeFromOp(instr.category)
        instr.timeDict['unitReadyTime'] = instr.timeDict['resultTime'] + self.unitReadyWait
        if instr.category == "FETCH":
            instr.timeDict['fetchTime'] = instr.timeDict['unitReadyTime'] + self.fetchStoreWait
        elif instr.category == "STORE":
            instr.timeDict['storeTime'] = instr.timeDict['unitReadyTime'] + self.fetchStoreWait

        # Done processing instructions and generating times!


    def cleanUpTimes(self,instr):
        # Replace empty times with a dash for better visualization
        for key,value in instr.timeDict.items():
            if value == 0:
                instr.timeDict[key] = '-'

    def compute(self, instr):

        # Generate instruction equation and description
        self.eqnAndRegisters(instr) # TODO may move to parseandstore and check for conflicts
        self.createDesc(instr)
        self.generateTimes(instr)
        self.cleanUpTimes(instr)




