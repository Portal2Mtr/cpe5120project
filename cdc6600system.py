from cdc6600instr import CDC6600Instr

# Class for handling keeping track of each component's timing in the CDC 6600 system
class CDC6600System():

    def __init__(self):
        numAddr = 8
        numOp = 8
        self.addrRegs = {}
        self.opRegs = {}
        for i in range(numAddr):
            self.addrRegs["A" + str(i)] = None

        for i in range(numOp):
            self.opRegs["X" + str(i)] = None

        # Define 6600 wait and Func. Unit Calc times
        self.wordSize = 4 # Bytes
        self.shortWait = 1
        self.longWait = 2
        self.wordWait = 8
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

        # Setup simulation vars TODO
        self.currTime = 0



    def getEmptyAddr(self):
        for i in self.addrRegs.keys():
            if self.addrRegs[i] is None:
                return i

    def getEmptyOp(self):
        for i in self.opRegs.keys():
            if self.opRegs[i] is None:
                return i

    def checkBusy(self,funcUnit):
        waitVal = self.busyUntil[funcUnit]
        return (waitVal > self.currTime)

    def getFuncFromOp(self,operator):
        return self.opMap[operator]

    # Creates instruction objects based on input equation, no calculations or generating new data, thats for compute
    def parseAndSort(self,command,system):

        brokenInput = command.split(' ')

        # Organize/sort instructions
        outputVar = brokenInput[0]
        sepIdx = brokenInput.index("=")
        inputs = brokenInput[(sepIdx + 1):] # TODO add other special operators as inputs
        inputVars = [c for c in inputs if c.isalpha()]
        specials = [c for c in inputs if not c.isalpha()]
        # TODO Assumed all nonalphabet characters are operators, look for squares, separate coefficients from linear vars
        operators = specials

        ############# Organize instructions
        print("Setting up instructions...")
        instrList = []

        # Add fetch objs first
        for entry in inputVars:
            newFetch = CDC6600Instr(entry, "FETCH", system)
            instrList.append(newFetch)

        # TODO More complicated commands, (sort based on availibility?)
        # Add operation instructions
        for entry in operators:
            newOp = CDC6600Instr("", "", system=system, operator=entry)
            instrList.append(newOp)

        # Add storing instructions, only have one
        instrList.append(CDC6600Instr(outputVar, "STORE", system=system))


        # Get linked instruction variables from input equation
        for entry in operators:
            # Get linked variables from sorted input for operator
            opIdx = brokenInput.index(entry)
            rightVar = brokenInput[opIdx + 1]
            leftVar = brokenInput[opIdx - 1]
            leftIdx = 0
            rightIdx = 0
            for idx, instr in enumerate(instrList): # Won't work for multiple vars with same name
                if rightVar is instr.getVar():
                    rightIdx = idx

                if leftVar is instr.getVar():
                    leftIdx = idx

            for instr in instrList:
                if entry is instr.getVar():
                    instr.assignOpVarIdx(leftIdx,rightIdx)
                    break

        # Assign words to instructions
        byteCnt = 0
        currWord = 1
        for instr in instrList:
            if instr.instrtype is "LONG":
                byteCnt += 2
            else:
                byteCnt += 1

            if byteCnt > 4:
                currWord += 1
                byteCnt = 0

            instr.currWord = "N" + str(currWord)

        self.instrList = instrList
        return instrList

    def preprocessing(self, instr):
        temp = 0

    def compute(self, instr):

        # Generate instruction equaiont and description
        self.preprocessing(instr)

        # TODO compute output times based on instruction category
        temp = 0

        # TODO Main simulation loop will go here!

