# coding=utf-8

from son1 import sonA

class sonB(sonA):
    def __init__(self, name):
       super(sonB, self).__init__(name)
    
    def fix2(self):
        self.name += "sonB "
        return self.name

