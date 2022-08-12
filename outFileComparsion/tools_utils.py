#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/8/12 11:10
# @Author  : wayne
# @File    : tools_utils.py
# @Software: PyCharm
import collections
import numpy as np
import math
import matplotlib.pyplot as plt

def get_mse(records_real, records_predict):
    """
    均方误差 估计值与真值 偏差
    """
    if len(records_real) == len(records_predict):
        return sum([(x - y) ** 2 for x, y in zip(records_real, records_predict)]) / len(records_real)
    else:
        return None


def get_rmse(records_real, records_predict):
    """
    均方根误差：是均方误差的算术平方根
    """
    mse = get_mse(records_real, records_predict)
    if mse or mse == 0:
        return math.sqrt(mse)
    else:
        return None


def get_ae(records_real, records_predict):
    if len(records_real) == len(records_predict):
        return sum([np.abs(x - y) for x, y in zip(records_real, records_predict)]) / len(records_real)
    else:
        return None


def get_mape(records_real, records_predict):
    """
    平均绝对百分比误差：mean(abs((YReal - YPred)./YReal))
    """
    error = np.array(records_real) - np.array(records_predict)

    pe = [error / real for real in np.array(records_real) if real != 0]
    return np.mean(np.abs(pe))


def AlignDataLen(outdata_df, refdata_df):
    """
    三次样条插值
    """
    outdata_df.drop_duplicates(subset=['time'], inplace=True)
    refdata_df.drop_duplicates(subset=['time'], inplace=True)
    outtime = outdata_df['time']
    outdata = outdata_df['srcvalue']
    reftime = refdata_df['time']
    refdata = refdata_df['dstvalue']
    kind = "cubic"  # 插值方式
    from scipy import interpolate
    if len(outdata) > len(refdata):
        x = reftime
        y = refdata
        x_new = outtime
        f = interpolate.interp1d(x, y, kind=kind)
        outdata_cubic = f(x_new)
        newrefdata = outdata_cubic
        newoutdata = outdata
    else:
        x = outtime
        y = outdata
        x_new = reftime
        f = interpolate.interp1d(x, y, kind=kind)
        outdata_cubic = f(x_new)
        newrefdata = refdata
        newoutdata = outdata_cubic

    return x_new, newoutdata, newrefdata


def outfile_parser(file_name):
    fo = open(file_name, "r", encoding='latin-1')
    # def a list with nodes startwith "Title"
    nodelists = []
    # def a list with single node
    nodelist = []
    output_file = fo.readlines()
    notenum = 1
    plotname_arr = []

    for i, line in enumerate(output_file):
        if i != 0 and line.startswith('Title'):
            nodelists.append(nodelist)
            # print(nodelists)
            notenum += 1
            nodelist = []
            nodelist.append(line)
        elif line.startswith('#') or line.startswith(' \n'):
            pass
        else:
            nodelist.append(line)

    nodelists.append(nodelist)
    # print(nodelists)
    assert len(nodelists) == notenum
    nodelistsresult = collections.OrderedDict()
    # read the number of variables and number of points
    for titles in nodelists:
        number_of_variables = int(titles[4].split(':', 1)[1])
        plotname = titles[2].split(': ')[-1].split('\n')[0]
        plotname_arr.append(plotname)
        # multi_plotname_result = list()
        if plotname not in nodelistsresult.keys():
            #     mark = True
            #     # print("aaaaa" + str(mark))
            #     # print(nodelistsresult[plotname])
            #     multi_plotname_result.append(nodelistsresult[plotname])
            # else:
            nodelistsresult[plotname] = list()
            # print("bbbb")

        # read the names of the variables
        variable_name_unit = []
        for variable in titles[8:8 + number_of_variables]:
            # 取节点名
            var_name = variable.split('\t', -1)[2]
            # # 取节点单位
            # var_unit = variable.split('\t', -1)[3].split('\n')[0]
            # # 节点名和单位之间用----拼接，赋给variable_name_unit
            # var_name_unit = var_name + "----" + var_unit
            # variable_name_unit.append(var_name_unit)
            variable_name_unit.append(var_name)

        # print(variable_name_unit)

        # read the values of the variables
        results = collections.OrderedDict()
        variable_index = 0
        for variable in variable_name_unit:
            results[variable] = []


        for value in titles[8 + number_of_variables + 1:]:
            if variable_index != number_of_variables - 1:
                # print(variable_index)
                # print(variable_name[variable_index])
                st = value.split('\t', -1)[-1]
                if st.startswith("FAIL"):
                    st = "0"
                vlu = eval(st)
                # 如果是虚数，out文件中会有两个值，我们只取实部
                if type(vlu) == tuple:
                    results[variable_name_unit[variable_index]].append(vlu[0])
                else:
                    results[variable_name_unit[variable_index]].append(vlu)
                variable_index += 1
            else:
                st = value.split('\t', -1)[-1].split('\n')[0]

                # 如果out文件中出现Fail字符串，将其转换成0
                if st.startswith("FAIL"):
                    st = "0"
                vlu = eval(st)
                if type(vlu) == tuple:
                    results[variable_name_unit[variable_index]].append(vlu[0])
                else:
                    results[variable_name_unit[variable_index]].append(vlu)
                variable_index = 0
        # multi_plotname_result.append(results)
        nodelistsresult[plotname].append(results)
        # nodelistsresult[plotname] = results
        # print("FINAL result: {}".format(nodelistsresult))
    # close the output_file
    fo.close()

    assert len(nodelistsresult) > 0
    return nodelistsresult, plotname_arr

def calc_error(benchout_dict, compout_dict, config):
    comp_result = {}
    comparelist = []
    check_nodes = config['compnodes']
    for plotname_node in check_nodes:
        plotn = plotname_node.split('--')[0]
        noden = plotname_node.split('--')[1]
        benchdata = benchout_dict[plotn][0][noden]
        compdata = compout_dict[plotn][0][noden]
        benchx = next(iter(benchout_dict[plotn][0].values()))
        compx = next(iter(compout_dict[plotn][0].values()))


        # 对齐数据
        if len(benchdata) != len(compdata):
            x_value, outdata, refdata = AlignDataLen(benchx, compx, benchdata, compdata)

        assert len(benchdata) == len(compdata)

        # 评估指标
        if config['metric'] == "RMSE":
            error_rate = get_rmse(benchdata, compdata)
        else:
            error_rate = get_mape(benchdata, compdata)
        comp_value = config['threshold']
        compareflag = True if error_rate <= comp_value else False
        comparelist.append(compareflag)
        comp_result[plotname_node] = str((error_rate, compareflag))
    compare = False if False in comparelist else True

    return compare, str(comp_result)

