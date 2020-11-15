# Functions representing instruction pipe computations
from itertools import compress

"""
    Functions for CDC6600System that are normally handled by the instruction pipe. 
"""

def createDesc(self, instr):
    """
    Creates the time table description for a given instruction.
    :param self: CDC6600System
    :param instr: Instruction for description generation
    """
    if (instr.category == "FETCH"):
        instr.catDesc = "Fetch"
        instr.instrDesc = instr.catDesc + " " + instr.varName
    elif instr.category == "STORE":
        instr.catDesc = "Store"
        instr.instrDesc = instr.catDesc + " " + instr.varName
    else:
        instr.catDesc = instr.category # Use fuunctional unit for description
        instr.instrDesc = instr.catDesc + " " + instr.instrRegs['leftOp'] + " " + instr.instrRegs['rightOp']

def getTimeFromOp(self, category):
    """
    Gets the time from the given functional unit
    :param self: CDC6600System object
    :param category: Functional unit to get time for.
    :return: Functional unit, time adjustment
    """

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
    """
    Checks for data dependencies for a given instructions time table generations.
    :param self: CDC6600System
    :param instr: Instruction for dependency checking
    :return: Time adjustment to wait for data to be processed.
    """

    if instr.operator is not None:
        # If operation instruction, check each instruction involved to make sure times are correct.
        currStartTime = instr.timeDict['startTime']
        oldStartTime = currStartTime
        currLeftInstr = self.instrList[instr.leftOpIdx]
        currRightInstr = self.instrList[instr.rightOpIdx]
        currStartTime = max(currLeftInstr.timeDict['resultTime'], currRightInstr.timeDict['resultTime'],
                            oldStartTime,currLeftInstr.busyUntil,currRightInstr.busyUntil)

        if currStartTime != oldStartTime:
            # Log data dependancy
            instrIdx = self.instrList.index(instr)
            print("Data dependancy at instruction line %s!" % (instrIdx+1))
            if (instrIdx + 1) not in self.dataDeps:
                self.dataDeps.append(instrIdx + 1)

        # Return time adjustment
        return currStartTime - oldStartTime

    elif instr.category == "STORE":
        # Log final data dependancy
        hasLogged = False
        oldStartTime = instr.timeDict['startTime']
        currStartTime = oldStartTime
        for line in self.instrList:
            if line.operator is not None:
                if line.timeDict['resultTime'] > currStartTime:
                    currStartTime = line.timeDict['resultTime']
                    if not hasLogged:
                        hasLogged = True
                        instrIdx = self.instrList.index(instr)
                        print("Data dependancy at instruction line %s!" % (instrIdx+1))
                        if (instrIdx+1) not in self.dataDeps:
                            self.dataDeps.append(instrIdx+1)

        # Update time adjustment
        return currStartTime - oldStartTime

    # No adjustment
    return 0

def performArithmetic(self, instr):
    """
    Calculates the equation output from each of the instruction managers in the final output instruction.
    :param self: CDC6600System
    :param instr: Output instruction.
    """

    # Sum all operator instructions
    compOps = self.compDict['OPS'].mangOps
    alreadyCalc = []
    allComps = []
    allCompsOps = []
    runningVal = 0

    for key,val in self.compDict.items():
        # Get comp instrs
        if val is not None:
            if val.manageType != "OPERATIONS" and val.compInstr != 'Y':
                allComps.append(val)
                allCompsOps.append(val.compInstr)

    for key,op in self.compDict['OPS'].mangOps.items():
        # Get operators from operations manager and compute
        for jdx,compute in enumerate(op):
            compIdxs = []
            for compName in compute:
                compIdxs.append(allCompsOps.index(compName))

            workComps = [allComps[i] for i in compIdxs]

            # Check if already calculated, if so use runningVal
            calcCheck = []
            for entry in compute:
                calcCheck.append(entry in alreadyCalc)

            if True in calcCheck:
                # Get index of already calculated
                alreadyVal = list(compress(compute,calcCheck))[0]
                opIdx = compute.index(alreadyVal)
                if opIdx == 0:
                    runningVal = self.ops[key](workComps[1],runningVal)
                else:
                    runningVal = self.ops[key](workComps[0], runningVal)
            else:
                # Get manager by var
                runningVal += self.ops[key](workComps[0],workComps[1])
                alreadyCalc.extend(compute)

    instr.value = runningVal

def generateTimes(self, instr):
    """
    Generate the time values for the output table. Main checker for updating calculation times
    :param self: CDC6600System
    :param instr: Instruction for calculating time values.
    """

    # Index by separate counter, instruction list indexes comp operations incorrectly for some reason
    instrIdx = self.genTimeIdx
    self.genTimeIdx += 1
    if instrIdx == 0:
        instr.timeDict['issueTime'] = 1
        self.currWordTimes[instr.currWord] = 1
    else:
        # Check for next word
        if self.instrList[instrIdx - 1].currWord == instr.currWord:
            # Word is not changed, update issue time normally based on instruction type
            prevType = self.instrList[instrIdx - 1].instrType
            if prevType == "LONG":
                # Adjust time for previous long instruction.
                instr.timeDict['issueTime'] = self.longWait + self.instrList[instrIdx - 1].timeDict['issueTime']
            else:
                # Adjust time for previous short instruction
                instr.timeDict['issueTime'] = self.shortWait + self.instrList[instrIdx - 1].timeDict['issueTime']

            if instr.operator is not None and instr.instrManager.manageType == "SCALAR":
                # Check if this is the scalar reuse instruction, if so then wait until complete execution of
                # constant fetching
                instr.timeDict['issueTime'] = instr.instrManager.instrDict['assign2'].timeDict['fetchTime'] + 1

        else:
            # Word has changed, adjust accordingly
            instr.timeDict['issueTime'] = self.wordWait + self.currWordTimes[self.instrList[instrIdx - 1].currWord]
            self.currWordTimes[instr.currWord] = instr.timeDict['issueTime']

        if instr.operator is not None:
            if not self.checkFuncUnit(instr):
                # Check if functional unit is fully clear, if not then get fetchTime of last instruction
                instrIdx = self.instrList.index(instr)
                print("Hardware esource dependancy at instruction line %s!" % (instrIdx + 1))
                self.hardDeps.append(instrIdx+1)
                lastInstr = self.getLastInstrFunc(instr.category)
                instr.timeDict['issueTime'] = lastInstr.timeDict['unitReadyTime']

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
    """
    Replace empty times with a dash for better visualization
    :param self: CDC6600System
    :param instr: Instruction to clean up.
    """

    for key, value in instr.timeDict.items():
        if value == 0:
            instr.timeDict[key] = '-'
