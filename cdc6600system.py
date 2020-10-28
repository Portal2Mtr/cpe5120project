from cdc6600instr import CDC6600Instr

# Class for handling keeping track of each component's timing in the CDC 6600 system
class CDC6600System():

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
        self.currTime = 0



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
            newOp = CDC6600Instr(entry, "", system=system, operator=entry)
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
            if instr.instrtype == "LONG":
                byteCnt += 2
            else:
                byteCnt += 1

            if byteCnt > 4:
                currWord += 1
                byteCnt = 0

            instr.currWord = "N" + str(currWord)

        self.instrList = instrList
        return instrList


    def eqnAndRegisters(self,instr):
        #TODO Move equation generation to parseandStore to check for conflicts?

        memCats = ["FETCH","STORE"]

        # Initialize output address as the lowest index that is empty
        if instr.category in memCats:
            if instr.category == "FETCH":
                emptyMemIdx = self.getEmptyMem()
                memAddr = "A" + emptyMemIdx[-1]
                memAddrIdx = int(memAddr[-1])
                instr.outputAddrIdx = memAddrIdx
                instr.instrRegs['result'] = memAddr
                instr.instrRegs['leftOp'] = memAddr
                self.setMemByIdx(emptyMemIdx, self.instrList.index(instr))
                self.setAddrByIdx(memAddr, self.instrList.index(instr))
            else:
                memAddr = self.getEmptyAddr()
                memAddrIdx = int(memAddr[-1])
                instr.outputAddrIdx = memAddrIdx
                instr.instrRegs['result'] = memAddr
                instr.instrRegs['leftOp'] = memAddr
                self.setAddrByIdx(memAddr, self.instrList.index(instr))



        else:
            # For operations, switch between x0 and x6 for output
            if (self.opMRU == None) or (self.opMRU == 6):
                self.opMRU = 0
                opAddr = 'X0'
                opAddrIdx = int(opAddr[-1])
                instr.outputAddrIdx = opAddrIdx
                instr.instrRegs['result'] = opAddr
                self.opRegs['X0'] = self.instrList.index(instr)

            else:
                self.opMRU = 6
                opAddr = 'X6'
                opAddrIdx = int(opAddr[-1])
                instr.outputAddrIdx = opAddrIdx
                instr.instrRegs['result'] = opAddr
                self.opRegs['X6'] = self.instrList.index(instr)


        # Setup FETCH Idxs (simplest)
        if instr.category == "FETCH":
            currIdx = instr.outputAddrIdx
            instr.instrRegs['rightOp'] = "K" + str(currIdx)
            instr.instrRegs['operand'] = "+"
            instr.genEqn()
            return

        # TODO after instructions for nonmem operators, set as A6 or A7 (from wikipedia), A7 if A6 used
        if instr.category == "STORE":
            # Get most recently used operator and its output
            recentOpIdx = self.opRegs['X' + str(self.opMRU)]
            opResult = self.instrList[recentOpIdx].instrRegs['result']
            emptyMem = self.getEmptyMem()
            instr.instrRegs['rightOp'] = emptyMem
            instr.instrRegs['leftOp'] = opResult
            instr.instrRegs['operand'] = "+"
            self.memRegs[emptyMem] = self.instrList.index(instr)
            instr.genEqn()
            return

        instr.instrRegs['leftOp'] = self.instrList[instr.leftOpIdx].instrRegs['result']
        instr.instrRegs['rightOp'] = self.instrList[instr.rightOpIdx].instrRegs['result']
        instr.instrRegs['operand'] = instr.operator
        instr.genEqn()


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



    def compute(self, instr):

        # Generate instruction equation and description
        self.eqnAndRegisters(instr)
        self.createDesc(instr)

        # TODO compute output times based on instruction category
        # TODO Main simulation loop will go here!

