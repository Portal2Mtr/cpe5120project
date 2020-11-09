# Functions representing Scoreboard computations
from cdc6600instr import *

# Creates instruction objects based on input equation, no calculations or generating new data, thats for compute
def parseAndSort(self, command="Y = A + B + C", values={"A": 1, "B": 2, "C": 3}, varInput=0, system=None):
    brokenInput = command.split(' ')
    # Organize/sort instructions
    outputVar = brokenInput[0]
    sepIdx = brokenInput.index("=")
    inputs = brokenInput[(sepIdx + 1):]  # TODO add other special operators as inputs
    inputVars = [c for c in inputs if c.isalpha()]
    specials = [c for c in inputs if not c.isalpha()]
    compInstr = [c for c in inputs if len(c) > 1]
    operators = []
    # TODO Assumed all nonalphabet characters are operators, look for squares, separate coefficients from linear vars
    for idx, entry in enumerate(inputVars):
        if self.inputVar in entry:
            varEntry = inputVars.pop(idx)
            if len(varEntry) == 2:  # BX form
                multScal = varEntry[0]
                var = varEntry[1]
                inputVars.insert(0, multScal)
                inputVars.insert(0, var)
                operators.append("*")
            elif "S" in varEntry:  # AX^Squared form
                multScal = varEntry[0]
                var = varEntry[1]
                inputVars.insert(0, multScal)
                inputVars.insert(0, var)
                operators.append('*s')
                operators.append("*")

            if not isinstance(varInput, list):  # TODO Move to vector parseandsort
                self.compMode = "SCALAR"
            else:
                self.compMode = "VECTOR"

    for entry in specials:
        operators.append(entry)

    # Handle for multiple operators
    if len(set(operators)) < len(operators):
        # TODO add support for multiple variable equation parts
        for entry in set(operators):
            idxs = [idx for idx, val in enumerate(operators) if val == entry]
            eqnidxs = [idx for idx, val in enumerate(brokenInput) if val == entry]
            enums = [str(i + 1) for i in idxs]
            for jdx, val in enumerate(idxs):
                operators[val] = operators[val] + enums[jdx]
                brokenInput[eqnidxs[jdx]] = operators[val]

    ############# Organize instructions
    print("Setting up instructions...")
    instrList = []

    # Add fetch objs first
    for idx, entry in enumerate(inputVars):
        if entry in values.keys():
            value = values[entry]
        else:
            value = varInput
        newFetch = CDC6600Instr(entry, "FETCH", system, value=value)
        instrList.append(newFetch)

    # TODO More complicated commands, Sort based on priority in use (vectors load before scalars, put longer instr executions first)
    # Add operation instructions
    for entry in operators:
        newOp = CDC6600Instr(entry, "", system=system, operator=entry[0])  # Works for duplicates
        instrList.append(newOp)

    # Add storing instructions, only have one
    instrList.append(CDC6600Instr(outputVar, "STORE", system=system))

    # Get linked instruction variables from input equation
    for entry in operators:
        # Get linked variables from sorted input for operator
        try:  # Check if operator is in basic equation, otherwise it is in variable operation
            opIdx = brokenInput.index(entry)
            rightVar = brokenInput[opIdx + 1]
            leftVar = brokenInput[opIdx - 1]
        except (ValueError):  # Operator is in variable input
            # TODO find bx if x2 also in equation
            if entry == "*":
                workInstr = compInstr[0]  # TODO Temp for single variable in eqn
                scalar = workInstr[0]
                variable = workInstr[1]
                leftVar = scalar
                rightVar = variable
            else:  # x^2
                workInstr = compInstr[0]  # TODO Temp for single variable in eqn
                variable = workInstr[1]
                leftVar = variable
                rightVar = variable

        leftIdx = 0
        rightIdx = 0
        for idx, instr in enumerate(instrList):  # Won't work for multiple vars with same name
            if rightVar is instr.getVar():
                rightIdx = idx

            if leftVar is instr.getVar():
                leftIdx = idx

        for instr in instrList:
            if entry is instr.getVar():
                instr.assignOpVarIdx(leftIdx, rightIdx)
                outputIdx = instrList.index(instr)
                instrList[leftIdx].eqnOutputIdx = outputIdx
                instrList[rightIdx].eqnOutputIdx = outputIdx
                break

    # Assign words to instructions
    byteCnt = 0
    currWord = 1
    for instr in instrList:
        if instr.instrType == "LONG":
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
        instr.descRegisters = instr.instrRegs['result'] + ",X" + instr.instrRegs['result'][-1]
        return

    # TODO after instructions for nonmem operators, set as A6 or A7 (from wikipedia), A7 if A6 used
    if instr.category == "STORE":
        # TODO Different for vector operations
        # Get most recently used operator and its output
        recentOpIdx = self.opRegs['X' + str(self.opMRU)]
        opResult = self.instrList[recentOpIdx].instrRegs['result']
        emptyMem = self.getEmptyMem()
        instr.instrRegs['rightOp'] = emptyMem
        instr.instrRegs['leftOp'] = opResult
        instr.instrRegs['operand'] = "+"
        self.memRegs[emptyMem] = self.instrList.index(instr)
        instr.genEqn()
        instr.descRegisters = instr.instrRegs['result'] + ",X" + instr.instrRegs['result'][-1] + "," + opResult
        return

    # Operation Insruction
    # TODO May not work for vector operations
    leftAddr = self.instrList[instr.leftOpIdx].instrRegs['result']
    rightAddr = self.instrList[instr.rightOpIdx].instrRegs['result']
    if self.instrList[instr.leftOpIdx].eqnOutputIdx != self.instrList[instr.rightOpIdx].eqnOutputIdx:
        if self.instrList[instr.leftOpIdx].eqnOutputIdx > self.instrList[instr.rightOpIdx].eqnOutputIdx:
            self.instrList[instr.leftOpIdx].hadComp = True
            self.instrList[instr.leftOpIdx].prevCompIdxs.append(self.instrList.index(instr))
        else:
            self.instrList[instr.rightOpIdx].hadComp = True
            self.instrList[instr.rightOpIdx].prevCompIdxs.append(self.instrList.index(instr))
    else:
        if self.instrList[instr.leftOpIdx].hadComp:
            prevCompIdx = self.instrList[instr.leftOpIdx].prevCompIdxs[0] # TODO Will not work for multiple adds
            leftAddr = self.instrList[prevCompIdx].instrRegs["result"]

        if self.instrList[instr.rightOpIdx].hadComp:
            prevCompIdx = self.instrList[instr.rightOpIdx].prevCompIdxs[0]  # TODO Will not work for multiple adds
            leftAddr = self.instrList[prevCompIdx].instrRegs["result"]



    leftOutput = self.instrList[instr.leftOpIdx].eqnOutputIdx
    rightOutput = self.instrList[instr.rightOpIdx].eqnOutputIdx
    # Check for previous computation

    instr.instrRegs['leftOp'] = "X" + leftAddr[-1]
    instr.instrRegs['rightOp'] = "X" + rightAddr[-1]
    instr.instrRegs['operand'] = instr.operator
    instr.genEqn()
    instr.descRegisters = instr.instrRegs['leftOp'] + "," + instr.instrRegs['rightOp'] \
                          + "," + instr.instrRegs['result']
    return


