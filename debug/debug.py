# coding=utf-8 

import math
import pandas as pd
import numpy as np

file_name = "./debug/case8_-0.out"
f = open(file_name)
content = f.readlines()
data_list = []

for line in content:
    if line.startswith("COL_HEADERS"):
        pass
    else:
        data = line.replace("\n", '')
        data = data.split(' ')
        
        data_list.append(data)
# print(data_list)
print("*"*20 + f"{file_name}" + "*"*20)
for d in data_list:
    btd = abs(eval(d[1]))
    ads = abs(eval(d[3]))
    spec = abs(eval(d[5]))
    try:
        btd_ads = abs((btd - ads)/ads)*100
        ads_spec = abs((ads - spec)/ads)*100
    except:
        btd_ads = 0
        ads_spec = 0
    print(f"Rfreq={d[0]}")
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

