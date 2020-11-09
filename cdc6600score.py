from cdc6600system import *

class CDC6600Score(CDC6600System):
    def __init__(self,inputMode):
        # Selector for input instruction types (easier to manage)
        self.inputMode = inputMode