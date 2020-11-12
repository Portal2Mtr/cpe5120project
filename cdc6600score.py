# Functions representing Scoreboard computations (parsing data and managing instruction meta generation)
from cdc6600instr import *
from instrManager import instrManager

# Creates instruction objects based on input equation, no calculations or generating new data, thats for compute
def parseAndSort(self, command="Y = A + B + C", values={"A": 1, "B": 2, "C": 3}, varInput=0, system=None):
    brokenInput = command.split(' ')
    # Organize/sort instructions
    outputVar = brokenInput[0]
    sepIdx = brokenInput.index("=")
    inputs = brokenInput[(sepIdx + 1):]  # TODO add other special operators as inputs
    inputVars = [c for c in inputs if c.isalpha()]
    specials = [c for c in inputs if not c.isalpha()]


    print("Setting up instructions...")
    # Setup instruction list


    # Sort separated inputs based on type and create managers for handling instruction output order.
    # TODO Add support for more?
    for entry in inputVars:
        if len(entry) == 1:
            self.compDict['CON'] = instrManager(compInstr=entry,manageType='CONSTANT')
        if len(entry) == 2:
            self.compDict['SCA'] = instrManager(compInstr=entry,manageType='SCALAR')
        if len(entry) == 3:
            self.compDict['SQU'] = instrManager(compInstr=entry,manageType='SQUARE')

    # Make output manager
    self.compDict['OUT'] = instrManager(compInstr=outputVar, manageType='OUTPUT')

    #Setup Assignment and operator instructions for instruction managers
    for idx, entry in enumerate(inputVars):
        if self.inputVar in entry:
            varEntry = inputVars[idx]
            if len(varEntry) == 3: #AXS Form
                # Setup instructions for instruction manager and parse variables
                workMan = self.compDict['SQU']
                multScal = varEntry[0]
                var = varEntry[1]

                # Setup Fetches
                # assign1 in variable
                workMan.instrDict['assign1'] = CDC6600Instr(varName=var,
                                                  category="FETCH",
                                                  system=system,
                                                  value=varInput,
                                                  instrManager=workMan)
                workMan.instrDict['assign2'] = CDC6600Instr(varName=multScal,
                                                  category="FETCH",
                                                  system=system,
                                                  value=values[multScal],
                                                  instrManager=workMan)
                # Setup Operators
                workMan.instrDict['square'] = CDC6600Instr(varName='*s',
                                                 category="",
                                                 system=system,
                                                 operator='*',
                                                 instrManager=workMan)

                workMan.instrDict['scalMult'] = CDC6600Instr(varName='*',
                                                 category="",
                                                 system=system,
                                                 operator='*',
                                                 instrManager=workMan)

            elif len(varEntry) == 2:  # BX form
                # Setup instructions for instruction manager and parse variables
                workMan = self.compDict['SCA']
                multScal = varEntry[0]
                var = varEntry[1]
                # Setup Fetches
                # assign1 in variable
                workMan.instrDict['assign1'] = CDC6600Instr(varName=var,
                                                            category="FETCH",
                                                            system=system,
                                                            value=varInput,
                                                            instrManager=workMan)
                workMan.instrDict['assign2'] = CDC6600Instr(varName=multScal,
                                                            category="FETCH",
                                                            system=system,
                                                            value=values[multScal],
                                                            instrManager=workMan)
                # Setup Operators
                workMan.instrDict['scalMult'] = CDC6600Instr(varName='*',
                                                             category="",
                                                             system=system,
                                                             operator='*',
                                                             instrManager=workMan)
            elif len(varEntry) == 1: # Constant
                workMan = self.compDict['CON']
                # Setup Fetches
                workMan.instrDict['assign1'] = CDC6600Instr(varName=varEntry,
                                                            category="FETCH",
                                                            system=system,
                                                            value=varInput,
                                                            instrManager=workMan)

    # Setup operators for between instruction managers based on broken input equation
    self.compDict['OPS'] = instrManager("OPS","OPERATIONS")
    for entry in set(specials):
        entIdx = [idx for idx,val in enumerate(brokenInput) if val == entry]
        allOpArray = []
        for occur in entIdx:
            leftVar = brokenInput[occur-1]
            rightVar = brokenInput[occur + 1]
            opArray = [None,None] # Two entries for left and right operation variables
            # Get complex instructions to do operations on
            for key,value in self.compDict.items():
                if value is not None: # Handle for no constant case
                    inVar = value.compInstr
                    if inVar == leftVar:
                        opArray[0] = leftVar
                    elif inVar == rightVar:
                        opArray[1] = rightVar
            allOpArray.append(opArray)
        self.compDict['OPS'].mangOps[entry] = allOpArray # Store btwn instr manager operations in order
        storeOpArray = []
        storeOpArrayIdx = []
        for calc in allOpArray:
            storeOpArray.append(CDC6600Instr(varName=entry,
                                                          category="",
                                                          system=system,
                                                          instrManager=self.compDict['OPS']))
            storeOpArrayIdx.append(None)
        self.compDict['OPS'].opDict[entry] = storeOpArray
        self.compDict['OPS'].opDictIdx[entry] = storeOpArrayIdx

    # Setup output for instruction managers
    outputInstr = CDC6600Instr(varName=outputVar,
                                  category="STORE",
                                  system=system,
                                  instrManager=self.compDict["OUT"])

    self.compDict['OUT'].addInstr(outputInstr,'output')

    ############## Reorder instructions and update indices TODO look at more optimized order in course slides
    instrList = []

    # Get all unique fetch instructions
    fetchList = []
    varList = []
    for key,val in self.compDict.items():
        if val is not None: # Handle for no constant case
            if val.instrDict['assign1'] is not None:
                fetchList.append(val.instrDict['assign1'])
                varList.append(val.instrDict['assign1'].varName)
            if val.instrDict['assign2'] is not None:
                fetchList.append(val.instrDict['assign2'])
                varList.append(val.instrDict['assign2'].varName)

    # Remove duplicate fetch instructions
    for entry in set(varList):
        occurs = [idx for idx,val in enumerate(varList) if val == entry]
        if len(occurs) > 1:
            # Have multiple occurances, remove from instruction managers
            toBeRem = occurs[1:]
            toBeRem = [fetchList[i] for i in toBeRem]
            for entry in toBeRem:
                entry.replaceInMan(fetchList[occurs[0]])
                fetchList.pop(occurs[0])

    # Sort on preferred order
    # Sort inputs by putting X first then go by alphabet
    corrOrder = ['X', 'A', 'B', 'C']  # Simple alpha sorting, too lazy to do it properly
    corrIdx = []
    tempList = [str(i) for i in fetchList]
    for entry in corrOrder:
        if entry in tempList:
            corrIdx.append(tempList.index(entry))
    fetchList = [fetchList[i] for i in corrIdx]

    # Add correctly sorted fetches to instruction list
    for entry in fetchList:
        instrList.append(entry)

    # Add operation instructions in preferred order
    if len(inputVars) == 2: # No Constant
        preferredOrder = ["SQU","SCA","OPS"]
        for entry in preferredOrder:
            workMan = self.compDict[entry]
            opInstrs = workMan.getOps()
            for instr in opInstrs:
                instrList.append(instr)

    elif len(inputVars) == 3:
        preferredOrder = ["SQU", "SCA", "CON","OPS"]
        for entry in preferredOrder:
            workMan = self.compDict[entry]
            opInstrs = workMan.getOps()
            for instr in opInstrs:
                instrList.append(instr)

    # Append output instruction (should be only one)
    for key,val in self.compDict.items():
        if val is not None: # Handle if no constant
            if val.instrDict['output'] is not None:
                instrList.append(val.instrDict['output'])

    # Add indices to managers, instruction list should be complete and ordered!
    for idx,instr in enumerate(instrList):
        instr.updateManIdx(idx=idx)


    # Assign instruction indices for operators

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
    ####################################












    # Get linked instruction variables from input equation
    opIter = iter(operators)
    compIdx = 0
    for idx,entry in enumerate(opIter):
        # Get linked variables from sorted input for operator
        try:  # Check if operator is in basic equation, otherwise it is in variable operation
            opIdx = brokenInput.index(entry[0]) # TODO Fix using brokeninput
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

            # if len(instr.getVar()) > 1:
            #     #Complex output

        for instr in instrList:
            if entry is instr.getVar():
                instr.assignOpVarIdx(leftIdx, rightIdx)
                outputIdx = instrList.index(instr)
                instrList[leftIdx].eqnOutputIdx = outputIdx # TODO Does this work with multiple X queries?
                instrList[rightIdx].eqnOutputIdx = outputIdx
                break




def eqnAndRegisters(self,instr):

    # TODO Incorporate instruction managers
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


