# Class for handling instruction computation for the simulated CDC6600 sytem

class CDC6600Instr():

    def __init__(self, varName, category, system, operator=None):
        # Category types:
        # *Insert functional units here*
        # "FETCH": Load var from core memory
        # "STORE": Store result in core memory
        self.varName = varName
        self.operator = operator
        self.operand = ""
        self.result = None
        self.system = system
        self.category = category
        self.currWord = ""
        self.equation = "TEMP"
        self.instDesc = "TEMP"

        # Define category based on func unit of operator
        # TODO
        if self.operator is not None:
            self.category = system.getFuncFromOp(self.operator)

        # All nonfunctional unit instructions are long, all functioinal units are short
        longCats = ["FETCH","STORE"]
        if self.category in longCats:
            self.instrtype = "LONG"
        else:
            self.instrtype = "SHORT"

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
        outputArray.append(self.instDesc)
        outputArray.append(self.instrtype)
        for key, value in self.timeDict.items():
            outputArray.append(str(value))

        return outputArray

    def genEqn(self):
        self.equation = self.instrRegs.result+"=" + self.instrRegs.operand + \
                        self.instrRegs.leftOp + self.instrRegs.rightOp

    def getVar(self):
        return self.varName

    def assignOpVarIdx(self,leftIdx,rightIdx):
        self.leftOpIdx = leftIdx
        self.rightOpIdx = rightIdx
