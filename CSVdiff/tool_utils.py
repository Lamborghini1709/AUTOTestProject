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

def mean_absolute_percentage_error(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

def mape_vectorized_v2(a, b):
    mask = b != 0
    re = (np.fabs(np.abs(b) - np.abs(a))/np.fabs(b))[mask]
    ids = np.argmax(re)
    max_a = a[ids]
    max_b = b[ids]
    reval = sorted(re.values)
    outlines = reval[:int(0.75 * len(reval))]
    mape = np.mean(outlines)
    # mean = np.mean(reval)
    # std = np.std(reval)
    # relist = reval.tolist()
    # outline = [x for x in relist if (x > mean - 2 * std and x < mean + 2 * std)]
    # mape = np.mean(outline)
    # mape = np.percentile(re, 95, 0).mean()
    return mape



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

if __name__ == '__main__':
    a = [1,2,3,4]
    b = [1,2,4,5]
    print(get_mape(a, b))