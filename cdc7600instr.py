
class CDC7600Instr():
    """
    Instruction object for simulated CDC 7600
    """

    def __init__(self, varName=None,
                 category=None,
                 system=None,
                 instrManager=None,
                 value=None,
                 operator=None):
        """
        Constructor for instruction object.
        :param varName: Variable name
         to refer to the instruction by.
        :param category: Type of instruction
         (types=['FETCH','STORE',*insert func units*]
        :param system: CDC 6600/7600
        simulation system
        :param instrManager: Manager
        for handling interinstruction calculations
        :param value: Integer value
        for simulation calculations
        :param operator: Operator for
         calculating instruction, may be
         None for fetch instruction
        """

        # General instruction variables
        self.varName = varName
        self.value = value
        self.operator = operator
        self.system = system
        self.category = category
        self.catDesc = category
        self.currWord = ""
        self.equation = "TEMP"
        self.instrDesc = "TEMP"

        # Simulation variables
        self.outputAddrIdx = 0
        self.funcUnit = "N/A"
        self.descRegisters = "N/A"
        self.eqnOutputIdx = None
        self.busyUntil = 0
        self.instrManager = instrManager

        # Define category based on func unit of operator
        if self.operator is not None:
            self.category = system.getFuncFromOp(self.operator)

        # All nonfunctional unit
        # instructions are long, all functional units are short
        longCats = ["FETCH","STORE"]
        if self.category in longCats:
            self.instrType = "LONG"
        else:
            self.instrType = "SHORT"

        # Dict for handling simulation time table values
        self.timeDict = {
            "issueTime": 0,
            "startTime": 0,
            "resultTime": 0,
            "unitReadyTime": 0,
            "fetchTime": 0,
            "storeTime": 0
        }

        # Dict for handling
        # instruction simulation register values
        self.instrRegs = {
            "leftOp": "",
            "operand":"",
            "rightOp": "",
            "result": ""
        }

        # Color indicators for timing table (see main.py).
        self.conflictInd = {
            "issueTime": 0,
            "startTime": 0,
            "resultTime": 0,
            "unitReadyTime": 0,
            "fetchTime": 0,
            "storeTime": 0
        }

    def getDesc(self):
        """
        Generates a description about an
         instruction object for table generation.
        :return: List of instruction
        values for table generation.
        """
        outputArray = []
        outputArray.append(self.system.instrList.index(self) + 1)
        outputArray.append(self.currWord)
        outputArray.append(self.equation)
        outputArray.append(self.instrDesc)
        outputArray.append(self.instrType)
        for key, value in self.timeDict.items():
            outputArray.append(str(value))

        outputArray.append(self.funcUnit)
        outputArray.append(self.descRegisters)

        return outputArray

    def getVar(self):
        """
        Gets the current instructions variable name.
        :return: This instructions variable name.
        """
        return self.varName

    def genEqn(self):
        """
        Generates a string equation for a given
         instruction from self.instrRegs.
        """
        self.equation = self.instrRegs['result']+"=" \
                        + self.instrRegs['leftOp'] \
                        + self.instrRegs['operand']\
                        + self.instrRegs['rightOp']

    def assignOpVarIdx(self,leftIdx,rightIdx):
        """
        Assigns indices for operation left/right values.
        :param leftIdx: Left instruction
         index in self.system.instrList.
        :param rightIdx: Right instruction
        index in self.system.instrList.
        """
        self.leftOpIdx = leftIdx
        self.rightOpIdx = rightIdx

    def removeDescDuplicates(self):
        """
        Removes duplicate registers from self.descRegisters.
        """
        origDesc = self.descRegisters
        regs = origDesc.split(",")
        setRegs = list(set(regs)) # Remove all duplicate registers
        newDesc = ",".join(setRegs)
        self.descRegisters = newDesc

        # Remove current instruction from its manager
    def removeFromMan(self):
        """
        Removes this instruction (self) from its own manager. (unused)
        """
        for key, val in self.instrManager.instrDict.items():
            if val == self:
                self.instrManager.instrDict[key] = None

    def replaceInMan(self,newInstr):
        """
        Replaces self in self.instrManager
        with a different instruction. Used
        to remove duplicate X Fetch instructions.
        :param newInstr: New instruction to replace old one.
        """
        for key,val in self.instrManager.instrDict.items():
            if val is not None:
                if val == self:
                    self.instrManager.instrDict[key] = newInstr
                    self.instrManager.instrInOthers[key] = True

    def updateManIdx(self,idx):
        """
        Updates the given instruction's
        index in self.instrManager
        :param idx: New index for manager.
        """
        if self.instrManager.manageType != "OPERATIONS":
            # Update instrDict with new index
            for key, val in self.instrManager.instrDict.items():
                if val is not None:
                    if val.varName == self.varName:
                        self.instrManager.instrDictIdxs[key] = idx
        else:
            # Update index in opDict by getting instruction operator
            for key, val in self.instrManager.opDict.items():
                # Get operator occurances
                for idx,entry in enumerate(val):
                    if entry == self:
                        self.instrManager.opDictIdx[key][idx] = idx

    def __str__(self):
        return self.varName

    def __eq__(self, other):
        # Used in instruction manager to
        # ensure correct instruction object is chosen.
        return str(other.instrManager) == \
               str(self.instrManager) and\
               other.varName == self.varName and \
               other.currWord == self.currWord
