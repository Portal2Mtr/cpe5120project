import operator

# Class for handling keeping track of
# each component's timing in the CDC 7600 system
class CDC7600System():
    """
        The main CDC 7600 simulation object.
         This object uses the CDC7600Instr objects to
        generate a timing diagram for the CDC 7600.
    """

    def __init__(self,inputVar="X"):
        """
        Constructor for CDC7600System,
        :param inputVar: Variable string to
        alter what variable to look for in input equation.
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
        self.wordWait = 6
        self.unitReadyWait = 1
        self.fetchStoreWait = 4
        self.opMap = {
            "+":"FLADD",
            "-":"FLADD",
            "*":"MULTIPLY"
        }
        self.funcUnits = {
            "FLADD":4,
            "MULTIPLY":5,
            "DIVIDE":20,
            "FIXADD":2,
            "INCR":2,
            "BOOLEAN":2,
            "SHIFT":2,
            "BRANCH":0 # Depends on input type, not used
        }
        # Setment times for functional units
        self.segTime = {
            "FLADD": 1,
            "MULTIPLY": 2,
            "DIVIDE": 18,
            "FIXADD": 1,
            "INCR": 1,
            "BOOLEAN": 1,
            "SHIFT": 1,  # Special case for Fixed point, not used
            "BRANCH": 0  # Depends on input type, not used
        }

        # Indicators for how long unitl func unit can be used again.
        self.busyUntil = {
            "FLADD": 0,
            "MULTIPLY": 0,
            "DIVIDE": 0,
            "FIXADD": 0,
            "INCR": 0,
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
        self.compDict = {'SQU':None,
                         'SCA':None,
                         'CON':None,
                         'OPS':None,
                         'OUT':None}

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

    def setAddrByIdx(self,register,idx):
        """
        Sets addr register to
        instruction index number from instrList.
        :param register: Register string for indexing.
        :param idx: index to set address register to.
        """
        self.addrRegs[register] = idx

    def setMemByIdx(self,register,idx):
        """
        Sets memory register to
         instruction index number from instrList.
        :param register: Register string for indexing.
        :param idx: Index to set memory address to.
        """
        self.memRegs[register] = idx

    def getEmptyOp(self):
        """
        Gets an empty operator
        register from opRegs dict.
        :return: Key of empty operator register.
        """
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
        :return: Bool if currTime
        is greater than the time a functional unit is busy.
        """
        waitVal = self.busyUntil[funcUnit]
        return (waitVal > currTime)

    def getFuncFromOp(self,operator):
        return self.opMap[operator]

    def creatInstrList(self,command, values, varInput):
        """
        Creates the global instruction
        list for generating the timing table.
        :param command: Input equation.
        :param values: Constant values
        :param varInput: X Variable input value.
        :return: Created instruction list.
        """
        # Move parseandsort to make editing easer
        instrList = \
            self.parseAndSort(command=command,
                              values=values,
                              varInput=varInput)
        return instrList

    def checkResourceConflict(self,instr):
        """
        Checks for hardware resource
        conflicts with a given instruction.
        :param instr: Input instruction.
        :return:
        """
        category = instr.category
        timing = instr.timeDict['issueTime']

        if (category == "FETCH") or (category == "STORE"):
            category = 'INCR'
        elif ("MULTIPLY" in category):
            category = 'MULTIPLY'

        if(self.busyUntil[category] > timing):
            instrIdx = self.instrList.index(instr)
            print("Hardware Resource "
                  "dependancy at instr line %s!" % (instrIdx + 1))
            lastInstr = self.getLastInstrFunc(instr)
            lastInstr.conflictInd['unitReadyTime'] = 1
            instr.conflictInd['issueTime'] = 1
            self.hardDeps.append(instrIdx+1)
            return self.busyUntil[category] - timing
        else:
            # Moving busyuntil to another function
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
                unitReady = True
                # For CDC7600, only nonmultiply and nonadd units are an issue.


        return unitReady

    def getLastInstrFunc(self, currInstr):
        """
        Returns the last instruction
        executed by a functional unit.
        :param category: Functional unit to check
        :return: Instruction that
         was last executed by functional unit.
        """
        category = currInstr.category
        if "MULTIPLY" in category:
            for key, manage in self.compDict.items():
                # Check comp operations for
                # conflicting functional unit times
                for key2, instr in manage.instrDict.items():
                    if instr is not None:
                        if instr.category == category and instr != currInstr:
                            return instr
        else:
            for key, manage in self.compDict.items():
                # Check comp operations for
                # conflicting functional unit times
                for key2, instrList in manage.opDict.items():
                    for instr in instrList:
                        if instr is not None:
                            if instr.category == category:
                                return instr
        return None

    def updateBusyUntil(self,instr):
        """
        Updates the busyUntil dict which
         manages when functional units can be used again.
        :param instr: Instruction for timing reference.
        """
        category = instr.category

        if (category == "FETCH") or (category == "STORE"):
            category = 'INCR'
        elif ("MULTIPLY" in category):
            category = 'MULTIPLY'
        self.busyUntil[category] =\
            instr.timeDict['startTime'] + \
            self.segTime[category]

    def compute(self, instr):
        """
        Wrapper for creating timing table with other subfunctions.
        :param instr: Input instruction.
        """
        self.eqnAndRegisters(instr)
        self.createDesc(instr)
        self.generateTimes(instr)
        self.cleanUpTimes(instr)