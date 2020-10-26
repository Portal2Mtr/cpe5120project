from prettytable import PrettyTable

from cdc6600instr import CDC6600Instr,CDC6600System
from cdc7600instr import CDC7600Instr

if __name__ == "__main__":

    ########### Get input and parse instuctions
    # TODO: Parse equation input
    print("Parsing input and setting up system...")
    testInput = "Y = A + B" # Start small
    # testINput = "BX + C"
    # testInput = "AX^2 + BX + C"

    brokenInput = testInput.split(' ')

    # Organize/sort instructions
    outputVar = brokenInput[0]
    sepIdx = brokenInput.index("=")
    inputs = brokenInput[(sepIdx+1):]
    inputVars = [c for c in inputs if c.isalpha()]
    specials = [c for c in inputs if not c.isalpha()]
    # TODO Assumed all nonalphabet characters are operators, look for squares, separate coefficients from linear vars
    operators = specials

    ############# Organize instructions
    print("Setting up instructions...")
    instrList = []
    cdc6600 = CDC6600System

    # Add fetch objs first
    for entry in inputVars:
        newFetch = CDC6600Instr(entry,"FETCH",cdc6600)
        instrList.append(newFetch)


    # TODO More complicated commands, (sort based on availibility?)

    # Add storing instructions
    instrList.append(CDC6600Instr(outputVar,"STORE",cdc6600))


    # TODO: Created object for handling system timing (e.g. waiting for func units to be availible, etc.), needs to be filled out

    # TODO: Run instructions and generate timing output
    print("Computing instructions...")
    for idx,instr in enumerate(instrList):
        instr.compute()
        print('Processed instr. (' + str((idx+1)) + '/' + str(len(instrList)) + ")")

    # TODO: Put timing output in pretty table
    # Example of Python table output we need to generate for the project.
    # TODO: Create output table that matches for CDC 6600/7600
    print("Creating table...")
    x = PrettyTable()
    x.field_names = ["City name", "Area", "Population", "Annual Rainfall"]
    x.add_row(["Adelaide",1295, 1158259, 600.5])
    x.add_row(["Brisbane",5905, 1857594, 1146.4])
    x.add_row(["Darwin", 112, 120900, 1714.7])
    x.add_row(["Hobart", 1357, 205556, 619.5])
    x.add_row(["Sydney", 2058, 4336374, 1214.8])
    x.add_row(["Melbourne", 1566, 3806092, 646.9])
    x.add_row(["Perth", 5386, 1554769, 869.4])

    print(x.get_string())