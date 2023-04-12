#!/usr/bin/env python
import math
import numpy as np

def check_duplicate(x, y):
    xnew = []
    ynew = []
    for i,j in enumerate(x):
        if j not in xnew:
            xnew.append(j)
            ynew.append(y[i])
    return xnew, ynew

def check_duplicate_o(num_list):
    xnew = []
    tag = 0
    for i in num_list:
        if i in xnew:
            # ns = list(str(i))
            # ns.insert(-4, "1")
            # s = "".join(ns)
            # xnew.append(float(s))
            s = i + 1e-15
            tag += 1
            xnew.append(s)
        else:
            xnew.append(i)
    if tag == 0:
        return xnew
    else:
        return check_duplicate(xnew)

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
    # print(records_real)
    # print(records_predict)
    error = (np.array(records_real) - np.array(records_predict)).tolist()
    pe = []
    if np.array(records_predict).any():
        for i, predict in enumerate(records_predict):
            if predict != 0:
                pe.append(error[i] / predict)
        # pe = [error / real for real in np.array(records_real) if real != 0]
        m = math.ceil(0.9*len(pe))
        pe =sorted(np.abs(pe), key=lambda x:x)[:m]
        return np.mean(np.abs(pe))
    else:
        return np.mean(np.array(records_real))

def max_diff(outdata, refdata):
    error = np.abs((np.array(outdata) - np.array(refdata))).tolist()
    l = sorted(error, key=lambda x:x)
    return l[-1]

def AlignDataLen(outx, refx, outdata, refdata):
    """
    三次样条插值
    """
    outx, outdata = check_duplicate(outx, outdata)
    refx, refdata = check_duplicate(refx, refdata)
    kind = "cubic"  # 插值方式
    from scipy import interpolate

    if len(outdata) > len(refdata):
        f = interpolate.interp1d(outx, outdata, kind=kind)
        outdata = f(refx)
        return refx, outdata, refdata
    else:
        f = interpolate.interp1d(refx, refdata, kind=kind)
        refdata = f(outx)

        return outx, outdata, refdata
    

if __name__ == '__main__':
    a = [0.015, 0.027, 0.049, 0.087, 0.154, 0.269, 0.446]
    b = [0.01540899, 0.02740073, 0.04872154, 0.086608, 0.1536845, 0.2886208, 0.338304]
    #print(get_mape(a, b))
    #print(get_rmse(a, b))
    # print(int(1.9))
