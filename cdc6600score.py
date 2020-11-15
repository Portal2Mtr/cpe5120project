from cdc6600instr import *
from instrManager6600 import instrManager

"""
Functions for the CDC 6600 representing 
Scoreboard computations 
(parsing data and managing 
instruction meta generation).
"""

def parseAndSort(self, command="Y = AXS + BX + C",
                 values={"A": 1, "B": 2, "C": 3},
                 varInput=0):
    """
    Creates instruction objects based on input equation,
     no calculations or generating new data,
    which is handled in the 'compute' function.
    :param self: CDC6600System
    :param command: Input equation
    :param values: Constant values
    :param varInput: variable input value
    :return: Generated list of instructions
    """

    # Organize/sort instructions from given input string
    brokenInput = command.split(' ')
    outputVar = brokenInput[0]
    sepIdx = brokenInput.index("=")
    inputs = brokenInput[(sepIdx + 1):]
    inputVars = [c for c in inputs if c.isalpha()]
    specials = [c for c in inputs if not c.isalpha()]
    print("Setting up instructions...")
    # Setup instruction list
    # Sort separated inputs based on type and
    # create managers for handling instruction output order.
    for entry in inputVars:
        if len(entry) == 1:
            self.compDict['CON'] = \
                instrManager(compInstr=entry,
                             manageType='CONSTANT',
                             system=self)
        if len(entry) == 2:
            self.compDict['SCA'] = \
                instrManager(compInstr=entry,
                             manageType='SCALAR',
                             system=self)
        if len(entry) == 3:
            self.compDict['SQU'] = \
                instrManager(compInstr=entry,
                             manageType='SQUARE',
                             system=self)

    # Make output manager
    self.compDict['OUT'] =\
        instrManager(compInstr=outputVar,
                     manageType='OUTPUT',
                     system=self)

    for idx, entry in enumerate(inputVars):
        # Setup Assignment and operator
        # instructions for instruction managers
        if self.inputVar in entry:
            # Check if variable is in a given string input
            varEntry = inputVars[idx]
            if len(varEntry) == 3: #AXS Form
                # Setup instructions for
                # instruction manager and parse variables
                workMan = self.compDict['SQU']
                multScal = varEntry[0]
                var = varEntry[1]

                # Setup Fetches
                # assign1 in variable
                workMan.instrDict['assign1'] = CDC6600Instr(varName=var,
                                                  category="FETCH",
                                                  system=self,
                                                  value=varInput,
                                                  instrManager=workMan)
                workMan.instrDict['assign2'] = CDC6600Instr(varName=multScal,
                                                  category="FETCH",
                                                  system=self,
                                                  value=values[multScal],
                                                  instrManager=workMan)
                # Setup Operators
                workMan.instrDict['square'] = CDC6600Instr(varName='*s',
                                                 category="",
                                                 system=self,
                                                 operator='*',
                                                 instrManager=workMan)

                workMan.instrDict['scalMult'] = CDC6600Instr(varName='*',
                                                 category="",
                                                 system=self,
                                                 operator='*',
                                                 instrManager=workMan)

            elif len(varEntry) == 2:  # BX form
                # Setup instructions for instruction manager and parse variables
                workMan = self.compDict['SCA']
                multScal = varEntry[0]
                var = varEntry[1]
                # Setup Fetches
                # assign1 in variable
                workMan.instrDict['assign1'] = \
                    CDC6600Instr(varName=var,
                                 category="FETCH",
                                 system=self,
                                 value=varInput,
                                 instrManager=workMan)
                workMan.instrDict['assign2'] =\
                    CDC6600Instr(varName=multScal,
                                 category="FETCH",
                                 system=self,
                                 value=values[multScal],
                                 instrManager=workMan)
                # Setup Operators
                workMan.instrDict['scalMult'] = \
                    CDC6600Instr(varName='*',
                                 category="",
                                 system=self,
                                 operator='*',
                                 instrManager=workMan)
        else:
            # No variable, constant
            workMan = self.compDict['CON']
            # Setup Fetches
            workMan.instrDict['assign1'] = \
                CDC6600Instr(varName=entry,
                             category="FETCH",
                             system=self,
                             value=varInput,
                             instrManager=workMan)

    # Setup operators for between instruction managers
    # based on broken input equation
    self.compDict['OPS'] = instrManager("OPS","OPERATIONS",self)
    for entry in set(specials):
        # Iterate through btwn manager operations (pluses)
        entIdx = [idx for idx,val in
                  enumerate(brokenInput) if val == entry]
        allOpArray = []
        for occur in entIdx:
            leftVar = brokenInput[occur-1]
            rightVar = brokenInput[occur + 1]
            opArray = [None,None] # Two entries
            # for left and right operation variables
            # Get complex instructions to do operations on
            for key,value in self.compDict.items():
                if value is not None: # Handle for no constant case
                    inVar = value.compInstr
                    if inVar == leftVar:
                        opArray[0] = leftVar
                    elif inVar == rightVar:
                        opArray[1] = rightVar
            allOpArray.append(opArray)
            # Store btwn instr manager operations in order
        self.compDict['OPS'].mangOps[entry] = allOpArray
        storeOpArray = []
        storeOpArrayIdx = []
        for calc in allOpArray:
            storeOpArray.append(
                CDC6600Instr(varName=entry,
                             category="",
                             system=self,
                             instrManager=self.compDict['OPS'],
                             operator=entry))
            storeOpArrayIdx.append(None)
        self.compDict['OPS'].opDict[entry] = storeOpArray
        self.compDict['OPS'].opDictIdx[entry] = storeOpArrayIdx

    # Setup output for instruction managers
    outputInstr = CDC6600Instr(varName=outputVar,
                                  category="STORE",
                                  system=self,
                                  instrManager=self.compDict["OUT"])

    self.compDict['OUT'].addInstr(outputInstr,'output')

    # Reorder instructions and update indices
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
    # Simple alpha sorting, too lazy to do it properly
    corrOrder = ['X', 'A', 'B', 'C']
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
    if len(inputVars) == 2:
        # No Constant
        preferredOrder = ["SQU","SCA","OPS"]
        for entry in preferredOrder:
            workMan = self.compDict[entry]
            opInstrs = workMan.getOps()
            for instr in opInstrs:
                instrList.append(instr)

    elif len(inputVars) == 3:
        # Have equation with constant
        preferredOrder = ["SQU", "SCA", "CON","OPS"]
        for entry in preferredOrder:
            workMan = self.compDict[entry]
            opInstrs = workMan.getOps()
            for instr in opInstrs:
                instrList.append(instr)

    for key,val in self.compDict.items():
        # Append output instruction (should be only one)
        if val is not None: # Handle if no constant
            if val.instrDict['output'] is not None:
                instrList.append(val.instrDict['output'])

    # Conduct final sorting, get more optimized output
    # table and determine equation mode (constant or not)
    instrList = optimizeList(instrList,inputVars)

    # Add indices to managers, instruction list
    # should be complete and ordered!
    for key,man in self.compDict.items():
        if man is not None:
            man.updateIdxs(instrList)

    # Update indices for operation managers
    compOpList = []
    for instr in instrList:
        if instr.operator is not None and \
                instr.instrManager.manageType != "OPERATIONS":
            instr.instrManager.linkInstr(instr)
        elif instr.operator is not None and \
                instr.instrManager.manageType == "OPERATIONS":
            # Get all comp operations
            compOpList.append(instr)

    self.compDict['OPS'].updateCompOpIdxs(compOpList)

    #Update indices for output instruction
    self.compDict['OUT'].getLastCalcOut(instrList)

    # Assign words to instructions
    byteCnt = 0
    currWord = 1
    for instr in instrList:
        if instr.instrType == "LONG":
            byteCnt += 2
        else:
            byteCnt += 1

        instr.currWord = "N" + str(currWord)

        if byteCnt >= 4:
            currWord += 1
            byteCnt = 0

    self.instrList = instrList

    return instrList


def eqnAndRegisters(self,instr):
    """
    Generates equations for each input instruction
    :param self: CDC6600System
    :param instr: Instruction to generate equation for
    :return:
    """

    memCats = ["FETCH","STORE"]

    if instr.category == "FETCH":
        # Initialize output address as the lowest index that is empty
        emptyMemIdx = self.getEmptyMem()
        memAddr = "A" + emptyMemIdx[-1]
        memAddrIdx = int(memAddr[-1])
        instr.outputAddrIdx = memAddrIdx
        instr.instrRegs['result'] = memAddr
        instr.instrRegs['leftOp'] = memAddr
        self.setMemByIdx(emptyMemIdx, self.instrList.index(instr))
        self.setAddrByIdx(memAddr, self.instrList.index(instr))
        currIdx = instr.outputAddrIdx
        instr.instrRegs['rightOp'] = "K" + str(currIdx)
        instr.instrRegs['operand'] = "+"
        instr.genEqn()
        instr.descRegisters = instr.instrRegs['result']\
                              + ",X" + instr.instrRegs['result'][-1]
        instr.removeDescDuplicates()
        return

    if instr.category == "STORE":
        # Handle final storing instruction
        memAddr = self.getEmptyAddr()
        memAddrIdx = int(memAddr[-1])
        instr.outputAddrIdx = memAddrIdx
        # instr.instrRegs['result'] = memAddr
        instr.instrRegs['leftOp'] = memAddr
        self.setAddrByIdx(memAddr, self.instrList.index(instr))
        # Get most recently used operator and its output

        recentOp = self.instrList[self.instrList.index(instr) - 1]
        opResult = recentOp.instrRegs['result']

        emptyMem = self.getEmptyMem()
        instr.instrRegs['rightOp'] = emptyMem
        instr.instrRegs['leftOp'] = 'A' + opResult[-1]
        instr.instrRegs['operand'] = "+"
        self.memRegs[emptyMem] = self.instrList.index(instr)
        # Update output register and check if x6 is used
        # After instructions for nonmem operators,
        # set as A6 or A7 (from wikipedia), A7 if A6 used
        if self.opRegs['X6'] is not None:
            instr.instrRegs['result'] = 'A7'
        else:
            instr.instrRegs['result'] = 'A6'
        instr.genEqn()
        instr.descRegisters = instr.instrRegs['result'] \
            + ",X" + instr.instrRegs['result'][-1] + "," + opResult
        instr.removeDescDuplicates()
        return

    #Operation instructions
    instr.instrManager.genOpEqn(instr)
    instr.genEqn()
    instr.descRegisters = instr.instrRegs['leftOp'] \
        + "," + instr.instrRegs['rightOp'] \
         + "," + instr.instrRegs['result']
    instr.removeDescDuplicates()


def optimizeList(instrList, inputVars):
    """
    Reorders instruction list based on equation variables.
    :param instrList: Instruction list to sort.
    :param inputVars: Number of complex inputs to check equation for.
    :return: Sorted instruction list.
    """
    if len(inputVars) == 2:
        preferredOrder = ['X', 'A',
            '*s', '*1', 'B', '*2', '+', 'Y']
        oldOrder = [i.varName for i in instrList]
        # Assign enum to multiply
        enum = 1
        for idx, entry in enumerate(oldOrder):
            if entry == "*":
                oldOrder[idx] = entry + str(enum)
                enum += 1
        oldIdxs = [i for i in range(len(oldOrder))]
        # Resort
        newIdxs = []
        for idx, entry in enumerate(preferredOrder):
            jdx = oldOrder.index(entry)
            newIdxs.append(oldIdxs[jdx])
        instrList = [instrList[i] for i in newIdxs]

    else:
        preferredOrder = ['X', 'A', '*s',
            '*1', 'B', 'C', '*2', '+1', '+2', 'Y']
        oldOrder = [i.varName for i in instrList]
        # Assign enum to multiply
        multenum = 1
        addenum = 1
        for idx, entry in enumerate(oldOrder):
            if entry == "*":
                oldOrder[idx] = entry + str(multenum)
                multenum += 1
            if entry == "+":
                oldOrder[idx] = entry + str(addenum)
                addenum += 1

        oldIdxs = [i for i in range(len(oldOrder))]
        # Resort
        newIdxs = []
        for idx, entry in enumerate(preferredOrder):
            jdx = oldOrder.index(entry)
            newIdxs.append(oldIdxs[jdx])
        instrList = [instrList[i] for i in newIdxs]

    return instrList




