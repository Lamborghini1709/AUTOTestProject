import math
import numpy as np


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


def AlignDataLen(outx, refx, outdata, refdata):
    """
    三次样条插值
    """
    kind = "cubic"  # 插值方式
    from scipy import interpolate
    if len(outdata) > len(refdata):
        x = refx
        y = refdata
        x_new = outx
        f = interpolate.interp1d(x, y, kind=kind)
        outdata_cubic = f(x_new)
        newrefdata = outdata_cubic
        newoutdata = outdata
    else:
        x = outx
        y = outdata
        x_new = refx
        f = interpolate.interp1d(x, y, kind=kind)
        outdata_cubic = f(x_new)
        newrefdata = refdata
        newoutdata = outdata_cubic

    return x_new, newoutdata, newrefdata

if __name__ == '__main__':
    a = [1,2,3,4]
    b = [1,2,4,5]
    print(get_mape(a, b))