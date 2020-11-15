import operator

# Class for handling keeping track of each component's timing in the CDC 7600 system
class CDC7600System():
    """
        The main CDC 7600 simulation object. This object uses the CDC7600Instr objects to
        generate a timing diagram for the CDC 7600.
    """

    def __init__(self,inputVar="X"):
        """
        Constructor for CDC7600System,
        :param inputVar: Variable string to alter what variable to look for in input equation.
        """

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

        # Define 7600 wait and Func. Unit Calc times
        self.wordSize = 4 # Bytes
        self.shortWait = 1
        self.longWait = 2
        self.wordWait = 8
        self.unitReadyWait = 1
        self.fetchStoreWait = 4
        self.opMap = {
            "+":"FLADD",
            "-":"FLADD",
            "*":"MULTIPLY"
        }
        self.funcUnits = {
            "FLADD":4,
            "MULTIPLY1":10,
            "MULTIPLY2":10,
            "DIVIDE":29,
            "FIXADD":3,
            "INCR1":3,
            "INCR2":3,
            "BOOLEAN":3,
            "SHIFT":3, # Special case for Fixed point, not used
            "BRANCH":0 # Depends on input type, not used
        }

        # Indicators for how long unitl func unit can be used again.
        self.busyUntil = {
            "FLADD": 0,
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
        self.opRegsList = ['X0','X6','X0','X5','X7']
        self.opRegIdx = -1

        # Setup simulation vars
        self.currWordTimes = {}
        self.ops = {"+": operator.add,
               "-": operator.sub,
               "*":operator.mul}  # etc.

        self.inputVar = inputVar

        self.dataDeps = []
        self.hardDeps = []

        # Used for keeping track of complex instruction objects
        self.compDict = {'SQU':None,'SCA':None,'CON':None,'OPS':None,'OUT':None}

        self.genTimeIdx = 0

    # Move functions to separate files for cleaner editing
    from cdc7600score import parseAndSort,eqnAndRegisters
    from cdc7600instrpipe import performArithmetic,generateTimes,\
        cleanUpTimes,checkDataDepend,getTimeFromOp,createDesc

    def getEmptyAddr(self):
        """
        Gets an empty register from the system.
        :return: Returns string address of empty register.
        """
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
        """
        Returns an empty memory register.
        :return: Empty memory register.
        """
        for i in self.memRegs.keys():
            if i != "K0":
                if self.memRegs[i] is None:
                    return i

    def checkBusy(self,funcUnit,currTime):
        """
        Checks if a given functional unit is busy.
        :param funcUnit: Functional unit to check.
        :param currTime: Given time to compare to functional unit.
        :return: Bool if currTime is greater than the time a functional unit is busy.
        """
        waitVal = self.busyUntil[funcUnit]
        return (waitVal > currTime)

    def getFuncFromOp(self,operator):
        return self.opMap[operator]

    def creatInstrList(self,command, values, varInput):
        """
        Creates the global instruction list for generating the timing table.
        :param command: Input equation.
        :param values: Constant values
        :param varInput: X Variable input value.
        :return: Created instruction list.
        """
        # Move parseandsort to make editing easer
        instrList = self.parseAndSort(command=command, values=values, varInput=varInput)
        return instrList

    def checkResourceConflict(self,instr):
        """
        Checks for hardware resource conflicts with a given instruction.
        :param instr: Input instruction.
        :return:
        """
        category = instr.category
        timing = instr.timeDict['issueTime']

        if (category == "FETCH") or (category == "STORE"):
            category = self.getAvailIncr()
        elif ("MULTIPLY" in category):
            category = self.getAvailMult()

        if(self.busyUntil[category] > timing):
            instrIdx = self.instrList.index(instr)
            print("Hardware Resource dependancy at instr line %s!" % (instrIdx + 1))
            self.hardDeps.append(instrIdx+1)
            return self.busyUntil[category] - timing
        else:
            self.busyUntil[category] = self.funcUnits[category] + timing + self.unitReadyWait
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
            if "MULTIPLY" != instr.category or instr.category.find("INCR") != -1:
                if self.busyUntil[instr.category] < timing:
                    unitReady = True
            else:
                unitReady = True # For CDC7600, only nonmultiply and nonadd units are an issue.


        return unitReady

    def getLastInstrFunc(self,category):
        """
        Returns the last instruction executed by a functional unit.
        :param category: Functional unit to check
        :return: Instruction that was last executed by functional unit.
        """
        for key,manage in self.compDict.items():
            # Check comp operations for conflicting functional unit times
            for key2,instrList in manage.opDict.items():
                for instr in instrList:
                    if instr is not None:
                        if instr.category == category:
                            return instr
        return None

    def getCurrIncr(self):
        """
        Gets the current increment unit that is availible.
        :return: Increment unit string.
        """
        if self.busyUntil['INCR1'] > self.busyUntil['INCR2']:
            return 'INCR1'
        else:
            return 'INCR2'

    def getAvailIncr(self):
        """
        Returns the availible increment unit that is not busy.
        :return:
        """
        if self.busyUntil['INCR1'] <= self.busyUntil['INCR2']:
            return 'INCR1'
        else:
            return 'INCR2'

    def getAvailMult(self):
        """
        Returns the avialible multiply unit that is not busy.
        :return: Multiply unit string.
        """
        if self.busyUntil['MULTIPLY1'] <= self.busyUntil['MULTIPLY2']:
            return 'MULTIPLY1'
        else:
            return 'MULTIPLY2'


    def compute(self, instr):
        """
        Wrapper for creating timing table with other subfunctions.
        :param instr: Input instruction.
        """
        self.eqnAndRegisters(instr)
        self.createDesc(instr)
        self.generateTimes(instr)
        self.cleanUpTimes(instr)