# coding=utf-8

from parent import father
from son1 import sonA
from son2 import sonB

# f = father("ff")
# f1 = f.fix()
# a = sonA("aa")
# a1 = a.fix1()
# b = sonB("bb ")
# b1 = b.fix2()

# print(f"f: {f1}")
# print(f"a: {a1}")
# print(f"b: {b1}")

import datetime
import os


# testset = "regress_Cases_all-cmg-bulk_20230307-1400"
# testset = "hisiCaseAll"
# testset = "K3_regression"
# cmd1 = f"find /home/mnt/BTD/{testset}/ -name '*.log' > logfile.txt"
# os.system(cmd1)

# f = open("logfile.txt", "r")
# content = f.readlines()
# for l in content:
#     l = l.replace("\n", "")
#     if "bench" in l:
#         r = open(l, "r")
#         content = r.readlines()

#     else:
#         ll = l.split("/")
#         p = "/".join(ll[1:-1])
#         tag_path = os.path.join("/home/mnt/BTD/", p, "bench", ll[-1])
#         cmd2 = f"cp {l} {tag_path}"
#         os.system(cmd2)

a = ".\\utils\\aaa\\bbb\\ccc"
b = a.split("\\")
print(b)
c = b[:0]
print("\\".join(b[:1]))
print("\\".join(b[:2]))
print("\\".join(b[:3]))
print("\\".join(b[:4]))
print("\\".join(b[:5]))

