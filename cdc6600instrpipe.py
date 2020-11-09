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
                            oldStartTime)

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

    if instr.category == "STORE":
        # Sum all operator instructions
        outputVal = 0
        for idx, entry in enumerate(self.instrList):
            if idx == 0:
                outputVal = entry.value
            if entry.operator is not None:
                outputVal = self.ops[entry.operator](outputVal, self.instrList[entry.rightOpIdx].value)
        instr.value = outputVal

def generateTimes(self, instr):
    # TODO compute output times based on instruction category
    # TODO Main simulation loop will go here!
    instrIdx = self.instrList.index(instr)
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
    # Check if we need to wait for data dependancy
    instr.timeDict['startTime'] = instr.timeDict['startTime'] + self.checkDataDepend(instr)

    # 'Execute' the functional unit for output
    self.performArithmetic(instr)

    funcName, funcTime = self.getTimeFromOp(instr.category)
    instr.timeDict['resultTime'] = instr.timeDict['startTime'] + funcTime
    instr.funcUnit = funcName
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





