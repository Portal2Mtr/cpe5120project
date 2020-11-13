from prettytable import PrettyTable
from cdc6600system import CDC6600System
import sys

def getInputEqn():
    eqns = ["Y = AX^2 + BX","Y = AX^2 + BX + C","Y = AX^2 + BX (Vector)"]

    print("Select equation to test:")
    for idx, entry in enumerate(eqns):
        print(str(idx+1) +": " +entry)

    eqnSel = int(input("Selection:"))
    eqnIdx = eqnSel - 1
    selEqn = eqns[eqnIdx]
    inputMode = "SCALAR"
    if " (Vector)" in selEqn:
        print("Vector mode is not supported! Exiting!")
        sys.exit()

    selEqn = selEqn.replace("^2","S")
    xinput = int(input("Enter value for X:"))

    return xinput,selEqn,inputMode


if __name__ == "__main__":
    print("Welcome! This program simulates the timing diagrams for\n"
          "the CDC6600/7600 systems! Please select your input equation.")

    # Generate System object for generating timing diagram
    xinput,selEqn,inputMode = getInputEqn()

    # Can manipulate values here for calculations
    scalarValues = {"A": 1, "B": 2, "C": 3}
    cdc6600 = CDC6600System(inputMode=inputMode)

    ########### Get input and parse instuctions
    print("---------------------------------------------------")
    print("Parsing input and setting up CDC 6600 system...")

    # Parse input and create ordered instruction list
    instrList = cdc6600.creatInstrList(command=selEqn,
                                       values=scalarValues,
                                       varInput=xinput,
                                       system=cdc6600)

    # 'Run' instructions and generate timing output
    print("Computing instructions for CDC 6600...")
    print("---------------------------------------------------")
    for idx,instr in enumerate(instrList):
        cdc6600.compute(instr)
        print('Processed: %s' % instr.equation)

    print("---------------------------------------------------")
    # Create table based on in-class examples
    print("Creating table for CDC 6600...")
    x = PrettyTable()
    x.field_names = ["Word #","Eqn.","Desc.", "Instr. Type","Issue","Start",
                     "Result","Unit Ready","Fetch","Store","Func. Unit","Registers"]
    for instr in instrList:
        x.add_row(instr.getDesc())
    print(x.get_string())

    # Print out equation output values
    print("---------------------------------------------------")
    outputInstr = instrList[-1]
    print("Equation Result: " +outputInstr.varName + " = " + str(outputInstr.value))

    # Print out performance analysis
    print("---------------------------------------------------")
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
    print("---------------------------------------------------")

    #TODO Add table generation for CDC 7600