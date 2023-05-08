# coding=utf-8 

import argparse
import pandas as pd
import numpy as np



parser = argparse.ArgumentParser()
parser.add_argument("--tp", type=str, default="./", help="the save path to test case")
parser.add_argument("--sh", type=str, default='btdsim', help="choose simulator path")
parser.add_argument("--savesimcsv", type=bool, default=True, help="save final simulator csv file")
parser.add_argument("--savediffcsv", type=bool, default=True, help="save final diff csv file")
parser.add_argument("--savefig", type=bool, default=False, help="save final plot")
parser.add_argument("--metric", type=str, default="MAPE", help="select metrics for diff, i.e. RMSE or MAPE")
parser.add_argument("--isdelold", type=int, default=1, help="Whether to delete the old case dir")
parser.add_argument("--rp", type=str, default="all", help="""path to test case""")
parser.add_argument("--cn", type=str, default="", help="case name")
parser.add_argument("--si", type=str, default="all", help="execute case selector, all、hisi、huali")
parser.add_argument("-b", "--btdVersion", type=str, default="rf", help="btdsim version: base, plus, rf")
parser.add_argument("--ccost", type=str, default=1, help="Simulatorcost Compare")
opt = parser.parse_args()
print(opt)

print(opt.btdVersion)