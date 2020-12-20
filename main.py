from prettytable import PrettyTable
from cdc6600system import CDC6600System
# from cdc7600instr import CDC7600Instr

if __name__ == "__main__":

    # Generate System object for generating timing diagram
    cdc6600 = CDC6600System()

    ########### Get input and parse instuctions
    print("Parsing input and setting up system...")
    # testInput = "Y = A + B" # Start small
    testInput = "Y = A + B + C + D + E"
    # TODO add vector support
    # testINput = "BX + C" # Verify these instructions work TODO
    # testInput = "AX^2 + BX + C" # TODO

    # Parse input and create ordered instruction list
    instrList = cdc6600.parseAndSort(testInput,cdc6600)

    # 'Run' instructions and generate timing output
    print("Computing instructions...")
    for idx,instr in enumerate(instrList):
        cdc6600.compute(instr)
        print('Processed: %s' % instr.equation)

    # Create table based on in-class examples
    print("Creating table...")
    x = PrettyTable()
    x.field_names = ["Word #","Eqn.","Desc.", "Instr. Type","Issue","Start","Result","Unit Ready","Fetch","Store"]
    for instr in instrList:
        x.add_row(instr.getDesc())
    print(x.get_string())