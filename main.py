from prettytable import PrettyTable
from cdc6600system import CDC6600System
from cdc7600system import CDC7600System

"""
    This is the CDC 6600/7600 simulation project for Anh Nguyen and Charles Rawlins.
    This code takes a given input string and generates two tables to stdout showing
    the execution timing for a given equation broken down into instructions. 
    Unfortunately, due to time restrains, this simulation does not support vector 
    operations, so only the two scalar input test equations are implemented.
    The program takes an input selection from the user for which equation to conduct
    tests with. 
"""

def getInputEqn():
    """
        Creates a dialogue with the user to generate the input equation for simulation

        :return: xinput (Value for x variable), selEqn (Equation selected from list)
    """
    eqns = ["Y = AX^2 + BX","Y = AX^2 + BX + C"]

    print("Select equation to test:")
    for idx, entry in enumerate(eqns):
        print(str(idx+1) +": " +entry)

    eqnSel = int(input("Selection:"))
    eqnIdx = eqnSel - 1
    selEqn = eqns[eqnIdx]

    selEqn = selEqn.replace("^2","S")
    xinput = int(input("Enter value for X:"))

    return xinput,selEqn


if __name__ == "__main__":
    """
        Main function for conducting simulation. Input equations were tested using
        Python 3.8.
    """
    print("Welcome! This program simulates the timing diagrams for\n"
          "the CDC6600/7600 systems! Please select your input equation.\n"
          "NOTE: Vectors are not supported for this version of the project.")

    # Generate System object for generating timing diagram
    xinput,selEqn= getInputEqn()

    # Constant values for equation calculations can be manipulated here.
    scalarValues = {"A": 1, "B": 2, "C": 3}

    # Colors for prettytable
    R = "\033[0;31;40m"  # RED
    G = "\033[0;32;40m"  # GREEN
    B = "\033[0;34;40m"  # Blue
    N = "\033[0m"  # Reset
    # 1 = unitbusy, 2 = register reuse,3 = data dependancy (RAW)
    conflictInds ={'1':R,'2':G,'3':B}

    print('######################################################################################')
    print('                                      CDC 6600                                        ')
    print('######################################################################################')
    cdc6600 = CDC6600System()

    # Get input and parse instuctions
    print("---------------------------------------------------")
    print("Parsing input and setting up CDC 6600 system...")

    # Parse input and create ordered instruction list
    instrList = cdc6600.creatInstrList(command=selEqn,
                                       values=scalarValues,
                                       varInput=xinput)

    # 'Run' instructions and generate timing output
    print("Computing instructions for CDC 6600...")
    print("---------------------------------------------------")
    for idx,instr in enumerate(instrList):
        cdc6600.compute(instr)
        print('Processed: %s' % instr.equation)

    print("---------------------------------------------------")
    # Create table based on in-class examples
    print("Creating table for CDC 6600...")
    print("KEY:" + R + " Unit Busy " + N + G + " Register Reuse " + N + B + " Data Dependancy " + N)
    x = PrettyTable()
    x.field_names = ["Instr. #", "Word","Eqn.","Desc.", "Instr. Type","Issue","Start",
                     "Result","Unit Ready","Fetch","Store","Func. Unit","Registers"]
    descOffset = 5
    for instr in instrList:
        workDesc = instr.getDesc()
        for idx,(key,val) in enumerate(instr.conflictInd.items()):
            if str(val) in conflictInds.keys():
                workDesc[idx + descOffset] = conflictInds[str(val)] + workDesc[idx + descOffset] + N
        x.add_row(workDesc)
    print(x.get_string())

    # Print out equation output values
    print("---------------------------------------------------")
    outputInstr = instrList[-1]
    print("Equation Result: " +outputInstr.varName + " = " + str(outputInstr.value))

    # Print out performance analysis with resource conflicts
    print("---------------------------------------------------")
    if len(cdc6600.hardDeps) > 0:
        print("Hardware resource conflicts at line(s):")
        print(str(cdc6600.hardDeps))
    else:
        print("No detected hardware conflicts!")
    if len(cdc6600.dataDeps) > 0:
        print("Data resource conflicts at line(s):")
        print(str(cdc6600.dataDeps))
    else:
        print("No detected data dependencies!")
    print("---------------------------------------------------")

    # print('######################################################################################')
    # print('                                      CDC 7600                                        ')
    # print('######################################################################################')
    #
    # cdc7600 = CDC7600System()
    #
    # # Get input and parse instuctions
    # print("---------------------------------------------------")
    # print("Parsing input and setting up CDC 7600 system...")
    #
    # # Parse input and create ordered instruction list
    # instrList = cdc7600.creatInstrList(command=selEqn,
    #                                    values=scalarValues,
    #                                    varInput=xinput)
    #
    # # 'Run' instructions and generate timing output
    # print("Computing instructions for CDC 7600...")
    # print("---------------------------------------------------")
    # for idx, instr in enumerate(instrList):
    #     cdc7600.compute(instr)
    #     print('Processed: %s' % instr.equation)
    #
    # print("---------------------------------------------------")
    # # Create table based on in-class examples
    # print("Creating table for CDC 7600...")
    # x = PrettyTable()
    # x.field_names = ["Instr. #", "Word", "Eqn.", "Desc.", "Instr. Type", "Issue", "Start",
    #                  "Result", "Unit Ready", "Fetch", "Store", "Func. Unit", "Registers"]
    # for instr in instrList:
    #     x.add_row(instr.getDesc())
    # print(x.get_string())
    #
    # # Print out equation output values
    # print("---------------------------------------------------")
    # outputInstr = instrList[-1]
    # print("Equation Result: " + outputInstr.varName + " = " + str(outputInstr.value))
    #
    # # Print out performance analysis with resource conflicts
    # print("---------------------------------------------------")
    # if len(cdc7600.hardDeps) > 0:
    #     print("Hardware resource conflicts at line(s):")
    #     print(str(cdc7600.hardDeps))
    # else:
    #     print("No detected hardware conflicts!")
    # if len(cdc7600.dataDeps) > 0:
    #     print("Data resource conflicts at line(s):")
    #     print(str(cdc7600.dataDeps))
    # else:
    #     print("No detected data dependencies!")
    # print("---------------------------------------------------")