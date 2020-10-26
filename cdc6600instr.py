
# Class for handling instruction computation for the simulated CDC6600 sytem
class CDC6600Instr():

    def __init__(self,varName,category,system,operator=None):

        # Category types:
        # "FETCH": Load var from core memory
        # "SET":
        # "COMPUTE": Compute operation on other instructions
        # "STORE": Store result in core memory
        self.varName = varName
        self.operator = operator
        self.result = None
        self.system = system
        self.category = category

        # Define 6600 wait and Func. Unit Calc times
        self.shortWait = 1
        self.longWait = 2
        self.wordWait = 8

        # Define Func Unit based on category
        # TODO

        # TODO Determine instruction type (long/short) based on category
        self.instrtype = "TEMP"

        self.timeDict = {
            "issueTime" : 0,
            "startTime" : 0,
            "resultTime": 0,
            "unitReadyTime": 0,
            "fetchTime": 0,
            "storeTime":0
        }

    def compute(self):
        # TODO compute output times based on instruction category
        print("Change me!")

    # Return array of times in string format for this instruction
    def outputTimes(self):
        outputArray = []
        for key,value in self.timeDict.items():
            outputArray.append(str(value))

        return outputArray

# Class for handling keeping track of each component's timing in the CDC 6600 system
class CDC6600System():
    def __init__(self):
        print("Temp")
