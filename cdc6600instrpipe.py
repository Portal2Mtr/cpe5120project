# Functions representing instruction pipe computations

def createDesc(self, instr):
    if (instr.category == "FETCH"):
        instr.catDesc = "Fetch"
        instr.instrDesc = instr.catDesc + " " + instr.varName
    elif instr.category == "STORE":
        instr.catDesc = "Store"
        instr.instrDesc = instr.catDesc + " " + instr.varName
    else:
        instr.catDesc = instr.category
        instr.instrDesc = instr.catDesc + " " + instr.instrRegs['leftOp'] + " " + instr.instrRegs['rightOp']

def getTimeFromOp(self, category):

    try:
        return category, self.funcUnits[category]
    except(KeyError):
        if (category == "FETCH") or (category == "STORE"):
            return self.getCurrIncr(), self.funcUnits[self.getCurrIncr()]
        elif (category == "MULTIPLY"):
            return category, self.funcUnits["MULTIPLY1"]  # Doesn't matter for func unit execution
        else:
            return "NONE", 0

def checkDataDepend(self, instr):

    if instr.operator is not None:
        currStartTime = instr.timeDict['startTime']
        oldStartTime = currStartTime
        currLeftInstr = self.instrList[instr.leftOpIdx]
        currRightInstr = self.instrList[instr.rightOpIdx]
        currStartTime = max(currLeftInstr.timeDict['resultTime'], currRightInstr.timeDict['resultTime'],
                            oldStartTime,currLeftInstr.busyUntil,currRightInstr.busyUntil)

        if currStartTime != oldStartTime:
            instrIdx = self.instrList.index(instr)
            print("Data dependancy at instr idx %s!" % instrIdx)
            self.dataDeps.append(instrIdx)

        return currStartTime - oldStartTime

    elif instr.category == "STORE":
        hasLogged = False
        oldStartTime = instr.timeDict['startTime']
        currStartTime = oldStartTime
        for line in self.instrList:
            if line.operator is not None:
                if line.timeDict['resultTime'] > currStartTime:  # TODO Temporary, won't work with vector loops
                    currStartTime = line.timeDict['resultTime']
                    if not hasLogged:
                        hasLogged = True
                        instrIdx = self.instrList.index(instr)
                        print("Data dependancy at instr idx %s!" % instrIdx)
                        self.dataDeps.append(instrIdx)

        return currStartTime - oldStartTime

    return 0

def performArithmetic(self, instr):
    # TODO Change to using instruction managers

    # Sum all operator instructions
    outputVal = 0
    instrDict = {}
    varDict = {}
    btwnInstr = {} # TODO Only supports addition, will need to parse other operators from equation
    alreadyCalc = []
    for idx, entry in enumerate(self.instrList):
        if entry.operator is None:
            varDict[entry.varName] = entry.value
            if entry.varName == 'X':
                varDict['oldX'] = entry.value
            # outputVal = self.ops[entry.operator](outputVal, self.instrList[entry.rightOpIdx].value)
        else:
            instrDict[entry.varName] = [entry.operator, self.instrList[entry.leftOpIdx].varName,
                                        self.instrList[entry.rightOpIdx].varName]

    # TODO Setup splitting of X calculations between original and squared X versions

    varDict['Y'] = 0
    for key,values in instrDict.items():
        if key == "+":
            continue # Already summing Y
        leftOp =varDict[values[1]]
        rightOp = varDict[values[2]]
        if key[-1] == "2": # Calculating BX
            outputVal = self.ops[values[0]](leftOp, varDict['oldX'])
        else:
            outputVal = self.ops[values[0]](leftOp, rightOp)
        if values[1] == values[2]: # Squaring
            varDict[values[1]] = outputVal
        else:
            varDict['Y'] += outputVal
            alreadyCalc.append(values[1])
            alreadyCalc.append(values[2])

    instr.value = varDict['Y']

def generateTimes(self, instr):

    instrIdx = self.genTimeIdx
    self.genTimeIdx += 1
    if instrIdx == 0:
        instr.timeDict['issueTime'] = 1
        self.currWordTimes[instr.currWord] = 1
    else:
        # Check for next word
        if self.instrList[instrIdx - 1].currWord == instr.currWord:
            prevType = self.instrList[instrIdx - 1].instrType
            if prevType == "LONG":
                instr.timeDict['issueTime'] = self.longWait + self.instrList[instrIdx - 1].timeDict['issueTime']
            else:
                instr.timeDict['issueTime'] = self.shortWait + self.instrList[instrIdx - 1].timeDict['issueTime']
        else:
            instr.timeDict['issueTime'] = self.wordWait + self.currWordTimes[self.instrList[instrIdx - 1].currWord]
            self.currWordTimes[instr.currWord] = instr.timeDict['issueTime']

        # TODO fillout conditions

    # Get timing offset for managing resource conflicts
    instr.timeDict['startTime'] = instr.timeDict['issueTime'] + \
                                  self.checkResourceConflict(instr)
    # Update Variable and make sure its not being used by another instruction

    # Check if we need to wait for data dependancy
    instr.timeDict['startTime'] = instr.timeDict['startTime'] + self.checkDataDepend(instr)

    # 'Execute' the functional unit for output
    if instr.category == "STORE":
        self.performArithmetic(instr)

    funcName, funcTime = self.getTimeFromOp(instr.category)
    instr.timeDict['resultTime'] = instr.timeDict['startTime'] + funcTime
    instr.funcUnit = funcName
    if instr.operator is not None:
        self.instrList[instr.leftOpIdx].busyUntil = instr.timeDict['resultTime']
        self.instrList[instr.rightOpIdx].busyUntil = instr.timeDict['resultTime']


    instr.timeDict['unitReadyTime'] = instr.timeDict['resultTime'] + self.unitReadyWait
    if instr.category == "FETCH":
        instr.timeDict['fetchTime'] = instr.timeDict['unitReadyTime'] + self.fetchStoreWait
    elif instr.category == "STORE":
        instr.timeDict['storeTime'] = instr.timeDict['unitReadyTime'] + self.fetchStoreWait

    # Done processing instructions and generating times!

def cleanUpTimes(self, instr):
    # Replace empty times with a dash for better visualization
    for key, value in instr.timeDict.items():
        if value == 0:
            instr.timeDict[key] = '-'