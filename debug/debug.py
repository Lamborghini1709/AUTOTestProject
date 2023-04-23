# coding=utf-8 

import math
import pandas as pd
import numpy as np

file_name = "./debug/case11_-13.out"
f = open(file_name)
content = f.readlines()
btd_list = []
ads_list = []
spec_list = []

for line in content:
    if line.startswith("COL_HEADERS"):
        pass
    else:
        data = line.replace("\n", '')
        data = data.split(' ')
        btd_list.append([eval(data[0]), eval(data[1])])
        ads_list.append([eval(data[2]), eval(data[3])])
        spec_list.append([eval(data[4]), eval(data[5])])

print("*"*20 + f"{file_name}" + "*"*20)

new_btd = sorted(btd_list, key=lambda x:x[0])
new_ads = sorted(ads_list, key=lambda x:x[0])
new_spec = sorted(spec_list, key=lambda x:x[0])

for d in range(len(new_btd)):
    btd = abs(new_btd[d][1])
    ads = abs(new_ads[d][1])
    spec = abs(new_spec[d][1])
    try:
        btd_ads = abs((btd - ads)/ads)*100
        ads_spec = abs((ads - spec)/ads)*100
    except:
        btd_ads = 0
        ads_spec = 0
    print(f"freq={new_btd[d][0]}")
    print(f"btd & ads: ")
    print(f"ε1: {btd_ads}%")
    print(f"spec & ads: ")
    print(f"ε2: {ads_spec}%\n")

# d = ['0.000000e+000', '5.892651e-002+0.000000e+000j', '0.000000e+000', '5.892647e-002+0.000000e+000j', '0.000000e+000', '5.876020e-002+0.000000e+000j']
# btd = abs(eval(d[1]))
# ads = abs(eval(d[3]))
# spec = abs(eval(d[5]))
# btd_ads = abs((btd - ads)/btd)*100
# btd_spec = abs((btd - spec)/btd)*100
# # print(abs(btd))
# # print(abs(ads))
# # print(abs(btd - ads))
# # print((abs(btd)-abs(ads))/abs(btd))
# print(btd_ads)
# print(btd_spec)
# a ='%.6g' % btd_ads 
# print(a)

