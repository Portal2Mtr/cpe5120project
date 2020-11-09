from prettytable import PrettyTable
from cdc6600system import CDC6600System
# from cdc7600instr import CDC7600Instr

def getInputEqn():
    eqns = ["Y = A + B","Y = A + B + C","Y = BX + C","Y = AX^2 + BX + C","Y = AX^2 + BX","Y = AX^2 + BX + C",
            "Y = BX (Vector)","Y = AX^2 + BX (Vector)"]

    print("Select equation to test:")
    for idx, entry in enumerate(eqns):
        print(str(idx+1) +": " +entry)

    eqnSel = int(input())
    eqnIdx = eqnSel - 1
    selEqn = eqns[eqnIdx]
    inputMode = "SCALAR"
    if " (Vector)" in selEqn:
        selEqn = selEqn.replace(" (Vector)","")
        inputMode = "VECTOR"
        # TODO Add vector support

    print("Enter value for X:")
    xinput = int(input())
    return xinput,selEqn,inputMode



if __name__ == "__main__":

    # Generate System object for generating timing diagram
    xinput = 3
    # inputVector = [1,2,3,4,5] # TODO
    inputMode = "SCALAR"
    testInput = "Y = A + B + C" # TODO Fix order error, output should do last add
    # testInput = "Y = BX + C"  # Verify these instructions work
    # testInput = "AX^2 + BX + C"
    scalarValues = {"A": 1, "B": 2, "C": 3}
    selEqn = testInput
    # TODO Enable once project is done
    # xinput,selEqn,inputMode = getInputEqn()
    cdc6600 = CDC6600System(inputMode=inputMode)

    ########### Get input and parse instuctions
    print("-----------------------------")
    print("Parsing input and setting up system...")

    # Parse input and create ordered instruction list
    instrList = cdc6600.parseAndSort(command=selEqn,values=scalarValues,varInput=xinput,system=cdc6600)

    # 'Run' instructions and generate timing output
    print("Computing instructions for CDC 6600...")
    print("-----------------------------")
    for idx,instr in enumerate(instrList):
        cdc6600.compute(instr)
        print('Processed: %s' % instr.equation)

    print("-----------------------------")
    # Create table based on in-class examples
    print("Creating table for CDC 6600...")
    x = PrettyTable()
    x.field_names = ["Word #","Eqn.","Desc.", "Instr. Type","Issue","Start",
                     "Result","Unit Ready","Fetch","Store","Func. Unit","Registers"]
    for instr in instrList:
        x.add_row(instr.getDesc())
    print(x.get_string())

    # Print out equation output values
    print("-----------------------------")
    outputInstr = instrList[-1]
    print("Equation Result: " +outputInstr.varName + " = " + str(outputInstr.value))

    # Print out performance analysis
    print("-----------------------------")
    if len(cdc6600.hardDeps) > 0:
        print("Hardware Resource Conflicts Indices:")
        print(str(cdc6600.hardDeps))
    else:
        print("No detected hardware conflicts!")
    if len(cdc6600.dataDeps) > 0:
        print("Data Resource Conflicts Indices:")
        print(str(cdc6600.dataDeps))
    else:
        print("No detected data dependancies!")
    print("-----------------------------")

    #TODO Add table generation for CDC 7600