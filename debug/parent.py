# coding=utf-8

class father():
    def __init__(self, name):
       self.name = name
       self.fix()
    
    def fix(self):
        self.name += "father "
        return self.name

if __name__=="__main__":
    titles = "Plotname: S-Parameter Analysis `sp1': freq = (1.3e+09 -> 1.5e+09)"
    plotname = titles.split(': ', 1)[-1].split('\n')[0]
    print(plotname)