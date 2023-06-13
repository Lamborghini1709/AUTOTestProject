# coding=utf-8

from parent import father
import time

class sonA(father):
    def __init__(self, name):
       super(sonA, self).__init__(name)
       time.sleep(5)
       self.fix1()
    
    def fix1(self):
        self.name += "sonA "
        return self.name
        