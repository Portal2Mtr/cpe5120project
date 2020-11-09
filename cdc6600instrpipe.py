from cdc6600system import CDC6600System

class CDC6600InstrPipe(CDC6600System):
    def __init__(self,inputMode):
        # Selector for input instruction types (easier to manage)
        self.inputMode = inputMode
