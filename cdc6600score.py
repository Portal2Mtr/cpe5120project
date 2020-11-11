# Functions representing Scoreboard computations (parsing data and managing instruction meta generation)
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
    compEnums = [(i + 1) for i in range(len(compInstr))]
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

    temp = set(operators)
    # Handle for multiple operators
    # TODO Just do multiple additions
    plusOps =[i for i in operators if i == "+"]
    if len(set(plusOps)) < len(plusOps): # TODO Fix
        # TODO add support for multiple variable equation parts
        for entry in set(operators):
            idxs = [idx for idx, val in enumerate(operators) if val == entry]
            eqnidxs = [idx for idx, val in enumerate(brokenInput) if val == entry]
            if len(eqnidxs) == 0: # Handle for if operators are in variables
                eqnidxs = [idx for idx, val in enumerate(brokenInput) if len(val) > 1]
            enums = [str(i + 1) for i in idxs]
            for jdx, val in enumerate(idxs):
                operators[val] = operators[val] + enums[jdx]
                brokenInput[eqnidxs[jdx]] = operators[val]

    # Label multplication operations for multiple complex operations
    if len(compInstr) > 0:
        # Setup for multiple multiplication operations
        multOps = [i for i in operators if i == "*"]
        # Match operations with complex instructions
        idxs = [idx for idx, val in enumerate(operators) if val == "*"]
        for jdx, val in enumerate(idxs):
            operators[val] = operators[val] + str(compEnums[jdx])

    ############# Organize instructions
    print("Setting up instructions...")
    instrList = []

    # Add fetch objs first
    for idx, entry in enumerate(set(inputVars)):
        if entry in values.keys():
            value = values[entry]
        else:
            value = varInput
        newFetch = CDC6600Instr(entry, "FETCH", system, value=value)
        instrList.append(newFetch)

    # Sort inputs by putting X first then go by alphabet
    corrOrder = ['X','A','B','C'] # Simple alpha sorting, too lazy to do it properly
    corrIdx = []
    tempList = [str(i) for i in instrList]
    for entry in corrOrder:
        if entry in tempList:
            corrIdx.append(tempList.index(entry))

    instrList = [instrList[i] for i in corrIdx]

    # TODO Vector support
    # Add operation instructions
    for entry in operators:
        newOp = CDC6600Instr(entry, "", system=system, operator=entry[0])  # Works for duplicates
        instrList.append(newOp)

    # Add storing instructions, only have one
    instrList.append(CDC6600Instr(outputVar, "STORE", system=system))

    # Get linked instruction variables from input equation
    opIter = iter(operators)
    compIdx = 0
    for idx,entry in enumerate(opIter):
        # Get linked variables from sorted input for operator
        try:  # Check if operator is in basic equation, otherwise it is in variable operation
            opIdx = brokenInput.index(entry)
            rightVar = brokenInput[opIdx + 1]
            leftVar = brokenInput[opIdx - 1]
        except (ValueError):  # Operator is in variable input
            # TODO Add support for additional x var operations?
            if "s" not in entry:
                if entry[-1].isnumeric():
                    # TODO is divided between mutliple comp units
                    workInstr = compInstr[compIdx]
                    scalar = workInstr[0]
                    compIdx += 1
                    variable = workInstr[1]
                    leftVar = scalar
                    rightVar = variable

                else:
                    workInstr = compInstr[compIdx]
                    scalar = workInstr[0]
                    variable = workInstr[1]
                    leftVar = scalar
                    rightVar = variable
            else:  # x^2
                workInstr = compInstr[compIdx]
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
                instrList[leftIdx].eqnOutputIdx = outputIdx # TODO Does this work with multiple X queries?
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
            # instr.instrRegs['result'] = memAddr
            instr.instrRegs['leftOp'] = memAddr
            self.setAddrByIdx(memAddr, self.instrList.index(instr))
    else:
        # For operations, use priority list
        if instr.operator == '+':
            # Check if last addition
            selfIdx = self.instrList.index(instr)
            lastPlus = True
            for i in range(selfIdx+1,len(self.instrList)):
                if self.instrList[i].getVar == "+":
                    lastPlus = False

            if lastPlus: # Output to 7
                temp = 0
                opAddr = self.opRegsList[-1]
                opAddrIdx = int(opAddr[-1])
                instr.outputAddrIdx = opAddrIdx
                instr.instrRegs['result'] = opAddr
                self.opRegs[opAddr] = self.instrList.index(instr)

            else: # Regular output
                self.opRegIdx += 1
                opAddr = self.opRegsList[self.opRegIdx]
                opAddrIdx = int(opAddr[-1])
                instr.outputAddrIdx = opAddrIdx
                instr.instrRegs['result'] = opAddr
                self.opRegs[opAddr] = self.instrList.index(instr)
        else:
            self.opRegIdx += 1
            opAddr = self.opRegsList[self.opRegIdx]
            opAddrIdx = int(opAddr[-1])
            instr.outputAddrIdx = opAddrIdx
            instr.instrRegs['result'] = opAddr
            self.opRegs[opAddr] = self.instrList.index(instr)



    # Setup FETCH Idxs (simplest)
    if instr.category == "FETCH":
        currIdx = instr.outputAddrIdx
        instr.instrRegs['rightOp'] = "K" + str(currIdx)
        instr.instrRegs['operand'] = "+"
        instr.genEqn()
        instr.descRegisters = instr.instrRegs['result'] + ",X" + instr.instrRegs['result'][-1]
        instr.removeDescDuplicates()
        return

    # TODO after instructions for nonmem operators, set as A6 or A7 (from wikipedia), A7 if A6 used
    if instr.category == "STORE":
        # TODO Different for vector operations
        # Get most recently used operator and its output

        recentOp = self.instrList[self.instrList.index(instr) - 1]
        opResult = recentOp.instrRegs['result']

        emptyMem = self.getEmptyMem()
        instr.instrRegs['rightOp'] = emptyMem
        instr.instrRegs['leftOp'] = 'A' + opResult[-1]
        instr.instrRegs['operand'] = "+"
        self.memRegs[emptyMem] = self.instrList.index(instr)
        #Update output register and check if x6 is used
        if self.opRegs['X6'] is not None:
            instr.instrRegs['result'] = 'A7'
        else:
            instr.instrRegs['result'] = 'A6'
        instr.genEqn()
        instr.descRegisters = instr.instrRegs['result'] + ",X" + instr.instrRegs['result'][-1] + "," + opResult
        instr.removeDescDuplicates()

        return

    # Operation Insruction
    # TODO May not work for vector operations
    leftAddr = self.instrList[instr.leftOpIdx].instrRegs['result']
    rightAddr = self.instrList[instr.rightOpIdx].instrRegs['result']
    # Update instruction list entry with previously computed indicator to manage dependancies registers
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

    if "X" in [self.instrList[instr.leftOpIdx].getVar(),self.instrList[instr.rightOpIdx].getVar()]:
        xinstr = [i for i in self.instrList if i.getVar() == "X"][0] # Only one register, wont work for vectors
        if xinstr.mruIdx is not None:
            # X has been used in previous calculation, use that register as input for this calculation
            if "X" == self.instrList[instr.leftOpIdx].getVar():
                leftAddr = self.instrList[xinstr.mruIdx].instrRegs['result']
            else:
                # Check if in squared form, if not then use original x value
                if instr.varName[-1] == '2':
                    # Not in squared form, use original x register
                    rightAddr = xinstr.instrRegs['result']
                else:
                    rightAddr = self.instrList[xinstr.mruIdx].instrRegs['result']
        else:
            xinstr.mruIdx = self.instrList.index(instr)

    # leftOutput = self.instrList[instr.leftOpIdx].eqnOutputIdx
    # rightOutput = self.instrList[instr.rightOpIdx].eqnOutputIdx
    # Check for previous computation

    if "+" in instr.varName:

        instr.instrRegs['leftOp'] = 'X' + self.opRegsList[self.opRegIdx -1][-1]
        instr.instrRegs['rightOp'] = 'X' + self.opRegsList[self.opRegIdx - 2][-1]

        # TODO Manage +2
    else:
        instr.instrRegs['leftOp'] = "X" + leftAddr[-1]
        instr.instrRegs['rightOp'] = "X" + rightAddr[-1]
    instr.instrRegs['operand'] = instr.operator
    instr.genEqn()
    instr.descRegisters = instr.instrRegs['leftOp'] + "," + instr.instrRegs['rightOp'] \
                          + "," + instr.instrRegs['result']
    instr.removeDescDuplicates()

    return


