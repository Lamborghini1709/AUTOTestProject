# coding=utf-8 

import argparse
from queue import Queue
import pandas as pd
import numpy as np
import multiprocessing as mp
import os
import time
import threading
import datetime
import openpyxl

def error_diff():
    file_name = r"D:\Ubuntu_IC618\share\eehemt\HBcase3\result\case3_pin10"
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

paths = r"D:\Ubuntu_IC618\share\pin-current-unit\spectre\bsimbulk_107_0\dc\case_8.scs"
n_path = r"D:\Ubuntu_IC618\share\pin-current-unit\spectre\bsimbulk_107_0\dc\case1\case_1.scs"
case_dir = r"D:\Ubuntu_IC618\share\pin-current-unit"
# 批量修改文件内容
# for filepath, dirnames, filenames in os.walk(case_dir, topdown=False):
#     if "dc=1.8" in filepath:
#         if ("model" in filepath):
#             pass
#         else:
#             for filename in filenames:
#                 tag_path = os.path.join(filepath, filename)
#                 if tag_path.endswith(".scs") | tag_path.endswith(".sp"):
#                     print(tag_path)
#                     f = open(tag_path, "r")
#                     content = f.read()
#                     new_con = content.replace("dc=1", "dc=1.8")
#                     f.close()
#                     w = open(tag_path, "w")
#                     w.write(new_con)
#                     w.close()
#                 else:
#                     pass

#     else:
#         pass

# 批量处理spectre网表，放入对应文件夹下
# model_type = "bsimcmg_110_0"
# analysis = "dc"
# tag_path = os.path.join(case_dir, model_type, analysis)
# for filepath, dirnames, filenames in os.walk(tag_path, topdown=False):
#     for filename in filenames:
#         if filename.endswith(".raw"):
#             tag_name = filename.split(".")[0]
#             os.system(rf"del {filepath}\{filename}")

# for filepath, dirnames, filenames in os.walk(tag_path, topdown=False):
#     for i in range(len(filenames)):
#         filename = filenames[i]
#         source_path = os.path.join(filepath, filename)
#         if source_path.endswith(".scs"):
#             print(source_path)
#             t_path = os.path.join(filepath, f"case{i+1}")
#             mv_cmd = rf"move {filepath}\case_{i+1}.scs {t_path}\{tag_name}.scs"
#             os.mkdir(t_path)
#             os.system(mv_cmd)
            # print(mv_cmd)


# 批量仿真
btd_path = r"/home/xubj006/pin-current-unit/btdsim"

# for filepath, dirnames, filenames in os.walk(btd_path, topdown=False):
#     if "model" in filepath:
#         pass
#     else:
#         for filename in filenames:
#             tag_name = filename.split(".")[0]
#             netlist = os.path.join(filepath, tag_name)
#             print(netlist)
#             outfile = os.path.join(filepath, tag_name)
#             logfile = os.path.join(filepath, tag_name)
#             sim_cmd = f"btdsim {netlist}.sp -o {outfile}.out > {logfile}.log &"
#             os.system(sim_cmd)

spec_path = r"/home/xubj006/pin-current-unit/spectre"

# for filepath, dirnames, filenames in os.walk(spec_path, topdown=False):
#     if "model" in filepath:
#         pass
#     else:
#         for filename in filenames:
#             tag_name = filename.split(".")[0]
#             netlist = os.path.join(filepath, tag_name)
#             print(netlist)
#             outfile = os.path.join(filepath, tag_name)
#             logfile = os.path.join(filepath, tag_name)
#             sim_cmd = f"spectre {netlist}.scs -f psfbin -raw {outfile}_psfbin.raw > {logfile}.log &"
#             os.system(sim_cmd)

def dataframe_to_log(data_frame, file_path=r'./tmp.log', file_object=None, isclose=True):
    data = data_frame.to_dict(orient='dict')
    d_keys = data.keys()
    key_len = {}
    for a in d_keys:
        key_len[a] = len(a)
        dvalue = data[a]
        for b in dvalue.keys():
            if len(str(dvalue[b])) > key_len[a]:
                key_len[a] = len(str(dvalue[b]))
    if file_object is None:
        f = open(file_path, 'a+')
    else:
        f = file_object
    for c in d_keys:
        dvalue = str(c).ljust(key_len[c]+2, ' ')
        f.write(dvalue)
    f.write("\n")
    for d in data_frame.index:
        for e in d_keys:
            value = data[e][d]
            fvalue = str(value).ljust(key_len[e]+2, ' ')
            f.write(fvalue)
        f.write("\n")
    if isclose==False:
        pass
    else:
        f.close()


t = 22
f = 9
df = 5
dt = 17
c = 4
testset = "hisiCasesAll"
tmp_file = "./debug/demo.log"
rs = open(tmp_file, "a+", encoding="utf-8")

rs.write(f"""\n---------------------------------------------------------分隔符---------------------------------------------------------
# AutoTest V5 result statistics {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Test Set: {testset}
*********************************************************
*                     测试结果统计                      *
*********************************************************
    本次回归测试共执行{t+f}条case, 其中:
        仿真成功: {t} 条
            结果对比成功: {dt} 条
                仿真成功case中对比时间超过golden 20%的： {c} 条
            结果对比失败: {df} 条
        仿真失败: {f} 条

*********************************************************\n""")



data_df_diff = pd.read_excel("./AutoTestV4/data_df_diff_0606112354.xlsx")
data_df_diff = data_df_diff.set_index(['index'])
# print(data_df_diff.index)
df = data_df_diff
failed_df = df[(df['SimulatorStat'] == 0) | (df['outdiff'] == False) |  (df['time_div'] == 0) | (df['outdiff'].isna())]
# 可以在大数据量下，没有省略号
result_path = ""
if len(failed_df) > 0:
    print("INFO: 总计失败：" + str(len(failed_df)) + "个用例" + "\n")
    pd.set_option('display.max_columns', 20)
    pd.set_option('display.max_rows', 100)
    pd.set_option('display.max_colwidth', 500)
    pd.set_option('display.width', 1000000)
    # print(failed_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'cost_div', 'outdiff']])

    sim_fail_df = failed_df[failed_df['SimulatorStat'] == 0]
    print(f"\nWARNING 仿真失败: {len(sim_fail_df)}条")
    print(sim_fail_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'walltime_rate', 'outdiff']])
    rs.write(f"\nWARNING 仿真失败: {len(sim_fail_df)}条:\n")
    dataframe_to_log(sim_fail_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']] ,file_object=rs, isclose=False)
    # sim_fail_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']].to_csv(tmp_file, index=0, sep=',')

    diff_fail_df = failed_df[(failed_df['SimulatorStat'] == 1) & ((failed_df['outdiff'] == False) | (failed_df['outdiff'].isna()))]
    print(f"\nWARNING 结果对比失败: {len(diff_fail_df)}条")
    print(diff_fail_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'walltime_rate', 'outdiff']])
    rs.write(f"\nWARNING 结果对比失败: {len(diff_fail_df)}条:\n")
    dataframe_to_log(diff_fail_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']] ,file_object=rs, isclose=False)

    time_out_df = failed_df[(failed_df['SimulatorStat'] == 1) & (failed_df['time_div'] == 0) & (failed_df['outdiff'] == True)]
    print(f"\nWARNING 对比时间超过 golden 20%: {len(time_out_df)}条")
    print(time_out_df.loc[:, ['spFile', 'SimulatorStat', 'Simulatorcost', 'walltime_rate', 'outdiff']])
    rs.write(f"\nWARNING 对比时间超过 golden 20%: {len(time_out_df)}条:\n")
    dataframe_to_log(time_out_df.loc[:, ["spFile", "SimulatorStat", "Simulatorcost", 'walltime_rate', 'outdiff', 'outdiffdetail']] ,file_object=rs, isclose=False)
    rs.write(datetime.datetime.now().strftime("AutoTest End %Y-%m-%d %H:%M:%S \n"))
    rs.close()
else:
    print(f"\nINFO: 无失败案例,测试集case全部仿真成功,对比成功,仿真时间未超20%,回归测试通过")
    rs.write(datetime.datetime.now().strftime("AutoTest End %Y-%m-%d %H:%M:%S \n"))
    rs.close()

