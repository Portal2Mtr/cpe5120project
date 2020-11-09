# Class for handling instruction computation for the simulated CDC6600 sytem

class CDC6600Instr():

    def __init__(self, varName, category, system, value=None,operator=None):
        # Category types:
        # *Insert functional units here*
        # "FETCH": Load var from core memory
        # "STORE": Store result in core memory
        self.varName = varName
        self.value = value
        if isinstance(value,int):
            self.datatype = "SCALAR"
        elif isinstance(value,list):
            self.datatype = "VECTOR"
        self.operator = operator
        self.operand = ""
        self.result = None
        self.system = system
        self.category = category
        self.catDesc = category # Change depending on instruction and contex
        self.currWord = ""
        self.equation = "TEMP"
        self.instrDesc = "TEMP"
        self.outputAddrIdx = 0
        self.funcUnit = "N/A"
        self.descRegisters = "N/A"
        self.eqnOutputIdx = None
        self.hadComp = False
        self.prevCompIdxs = []
        self.busyUntil = 0
        self.mruIdx = None

        # Define category based on func unit of operator
        # TODO
        if self.operator is not None:
            self.category = system.getFuncFromOp(self.operator)

        # All nonfunctional unit instructions are long, all functioinal units are short
        longCats = ["FETCH","STORE"]
        if self.category in longCats:
            self.instrType = "LONG"
        else:
            self.instrType = "SHORT"

        self.timeDict = {
            "issueTime": 0,
            "startTime": 0,
            "resultTime": 0,
            "unitReadyTime": 0,
            "fetchTime": 0,
            "storeTime": 0
        }

        self.instrRegs = {
            "leftOp": "",
            "operand":"",
            "rightOp": "",
            "result": ""
        }

    def getDesc(self):
        outputArray = []
        outputArray.append(self.currWord)
        outputArray.append(self.equation)
        outputArray.append(self.instrDesc)
        outputArray.append(self.instrType)
        for key, value in self.timeDict.items():
            outputArray.append(str(value))

        outputArray.append(self.funcUnit)
        outputArray.append(self.descRegisters)

        return outputArray

    def genEqn(self):
        self.equation = self.instrRegs['result']+"=" + self.instrRegs['leftOp'] + self.instrRegs['operand'] + self.instrRegs['rightOp']

    def getVar(self):
        return self.varName

    def assignOpVarIdx(self,leftIdx,rightIdx):
        self.leftOpIdx = leftIdx
        self.rightOpIdx = rightIdx

    def __str__(self):
        return self.varName

