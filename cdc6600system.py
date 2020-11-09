from cdc6600instr import CDC6600Instr
import operator


# TODO Create subclasses for better organization?
# Class for handling keeping track of each component's timing in the CDC 6600 system
class CDC6600System():

    def __init__(self,inputVar="X",showLoops=False,inputMode="SCALAR"):

        numAddr = 8
        numOp = 8
        numMem = 8
        self.addrRegs = {}
        self.opRegs = {}
        self.memRegs ={}
        for i in range(numAddr):
            self.addrRegs["A" + str(i)] = None

        for i in range(numOp):
            self.opRegs["X" + str(i)] = None

        for i in range(numMem):
            self.memRegs["K" + str(i)] = None

        # Define 6600 wait and Func. Unit Calc times
        self.wordSize = 4 # Bytes
        self.shortWait = 1
        self.longWait = 2
        self.wordWait = 8
        self.unitReadyWait = 1
        self.fetchStoreWait = 4
        self.opMap = {
            "+":"FLADD",
            "-":"FLADD",
            "*":"MULTIPLY"
        }
        self.funcUnits = {
            "FLADD":3,
            "MULTIPLY1":10,
            "MULTIPLY2":10,
            "DIVIDE":29,
            "FIXADD":3,
            "INCR1":3,
            "INCR2":3,
            "BOOLEAN":3,
            "SHIFT":3, # TODO: Special case for FP
            "BRANCH":0 # TODO: Depends on input
        }
        self.busyUntil = {
            "FLADD": 0,
            "MULTIPLY1": 0,
            "MULTIPLY2": 0,
            "DIVIDE": 0,
            "FIXADD": 0,
            "INCR1": 0,
            "INCR2": 0,
            "BOOLEAN": 0,
            "SHIFT": 0,
            "BRANCH": 0
        }
        self.instrList = []
        self.opMRU = None # Set most recently used op address for calculations

        # Setup simulation vars
        self.currWordTimes = {}
        self.ops = {"+": operator.add,
               "-": operator.sub,
               "*":operator.mul}  # etc.

        self.showLoops = showLoops
        self.inputVar = inputVar

        self.dataDeps = []
        self.hardDeps = []

    # Move functions to separate files for cleaner editing
    from cdc6600score import parseAndSort,eqnAndRegisters
    from cdc6600instrpipe import performArithmetic,generateTimes,\
        cleanUpTimes,checkDataDepend,getTimeFromOp,createDesc

    def getEmptyAddr(self):
        for i in self.addrRegs.keys():
            if i != "A0":
                if self.addrRegs[i] is None:
                    return i

    # Sets addr register to instruction number from instrList
    def setAddrByIdx(self,register,idx):
        self.addrRegs[register] = idx

    def setMemByIdx(self,register,idx):
        self.memRegs[register] = idx

    def getEmptyOp(self):
        for i in self.opRegs.keys():
            if self.opRegs[i] is None:
                return i

    def getEmptyMem(self):
        for i in self.memRegs.keys():
            if i != "K0":
                if self.memRegs[i] is None:
                    return i

    def checkBusy(self,funcUnit,currTime):
        waitVal = self.busyUntil[funcUnit]
        return (waitVal > currTime)

    def getFuncFromOp(self,operator):
        return self.opMap[operator]

    def creatInstrList(self,command, values, varInput, system):
        # Move parseandsort to make editing easer
        instrList = self.parseAndSort(command=command, values=values, varInput=varInput, system=system)
        return instrList

    def checkResourceConflict(self,instr):
        category = instr.category
        timing = instr.timeDict['issueTime']

        if (category == "FETCH") or (category == "STORE"):
            category = self.getAvailIncr()
        elif ("MULTIPLY" in category):
            category = self.getAvailMult()

        if(self.busyUntil[category] > timing):
            instrIdx = self.instrList.index(instr)
            print("Hardware Resource dependancy at instr idx %s!" % instrIdx)
            self.hardDeps.append(instrIdx)
            return self.busyUntil[category] - timing
        else:
            self.busyUntil[category] = self.funcUnits[category] + timing + self.unitReadyWait
            return 0

    def getCurrIncr(self):
        if self.busyUntil['INCR1'] > self.busyUntil['INCR2']:
            return 'INCR1'
        else:
            return 'INCR2'

    def getAvailIncr(self):
        if self.busyUntil['INCR1'] <= self.busyUntil['INCR2']:
            return 'INCR1'
        else:
            return 'INCR2'

    def getAvailMult(self):
        if self.busyUntil['MULTIPLY1'] <= self.busyUntil['MULTIPLY2']:
            return 'MULTIPLY1'
        else:
            return 'MULTIPLY2'


    def compute(self, instr):
        # Generate instruction equation and description from
        self.eqnAndRegisters(instr)
        self.createDesc(instr)
        self.generateTimes(instr)
        self.cleanUpTimes(instr)