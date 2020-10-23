from prettytable import PrettyTable


if __name__ == "__main__":

    # TODO: Parse equation input

    # TODO: Create intruction object for handling order? (Simulate scoreboard)

    # TODO: Organize/sort instructions

    # TODO: Run instructions and generate timing output

    # TODO: Put timing output in pretty table


    # Example of Python table output we need to generate for the project.
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