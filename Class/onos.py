from deploytarget import DeployTarget

class Onos(DeployTarget):

    def __init__(self):
        super().__init__()

    # overriding abstract method
    def compile(self):
        print("ok")