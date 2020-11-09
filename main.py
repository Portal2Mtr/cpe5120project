from prettytable import PrettyTable
from cdc6600system import CDC6600System
# from cdc7600instr import CDC7600Instr



if __name__ == "__main__":

    # Generate System object for generating timing diagram
    # TODO Add equation selection
    xinput = 3 # TODO Add vector support for input var
    if xinput is None:
        print("Enter the variable (X) value:")
        xinput = input()
    cdc6600 = CDC6600System()

    ########### Get input and parse instuctions
    # TODO: Parse equation input
    print("Parsing input and setting up system...")
    # testInput = "Y = A + B" # Start small
    # testInput = "Y = A + B + C" # Order of operations doesn't work
    testInput = "Y = BX + C" # Verify these instructions work
    # testInput = "AX^2 + BX + C"
    scalarValues = {"A":1,"B":2,"C":3}
    # inputVector = [1,2,3,4,5] # TODO

    # Parse input and create ordered instruction list
    instrList = cdc6600.parseAndSort(command=testInput,values=scalarValues,varInput=xinput,system=cdc6600)

    # 'Run' instructions and generate timing output
    # TODO: Run instructions and generate timing output
    print("Computing instructions for CDC 6600...")
    for idx,instr in enumerate(instrList):
        cdc6600.compute(instr)
        print('Processed: %s' % instr.equation)

    # Create table based on in-class examples
    print("Creating table for CDC 6600...")
    x = PrettyTable()
    x.field_names = ["Word #","Eqn.","Desc.", "Instr. Type","Issue","Start",
                     "Result","Unit Ready","Fetch","Store","Func. Unit","Registers"]
    for instr in instrList:
        x.add_row(instr.getDesc())
    print(x.get_string())

    # Print out analysis and output values
    outputInstr = instrList[-1]
    print("Hardware Resource Conflicts:")
    print("TODO")
    print("Data Resource Conflicts:")
    print("TODO")
    print("Equation Result: " +outputInstr.varName + " = " + str(outputInstr.value))

    #TODO Add table generation for CDC 7600