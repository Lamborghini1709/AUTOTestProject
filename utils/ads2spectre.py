# coding=utf-8

from dataclasses import replace
from distutils.log import debug, info
from hashlib import new
from lib2to3.pgen2.literals import simple_escapes
from math import floor
import os
import logging
from pyexpat import model
from tokenize import Double

logging.basicConfig(level=logging.DEBUG, 
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
filename="./ads2spectre.log",
filemode='w+',
encoding='utf-8')
logger = logging.getLogger('Arc')# 创建logger对象
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()# 创建 console handler 并设置级别为debug
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')# 创建输出格式
handler.setFormatter(formatter)# 为handler添加fromatter
logger.addHandler(handler)# 将handler添加到 logger

gl_line_number = 0
param_list = {}
model_list = []


def get_file_name(test_dir):
    file_list = []
    for filepath, dirnames, filenames in os.walk(test_dir, topdown=False):
        for filename in filenames:
            if filename.endswith(".ads"):
                pictrue_path = filepath + "\\" + filename
                file_list.append(pictrue_path)
    return file_list


def ads2spectre(netlist, output_name=""):
    logger.info("{1}开始转换ads网表：{0}{1}".format(netlist, "*"*20))
    if output_name=="":
        output_name = netlist+".spec"
    f = file_deal(netlist)
    content = f.readlines()
    data_init(content)
    w = open(output_name, "w", encoding='utf-8')
    for l in content:
        new_line = element2spec(l).strip()
        new_line = deals(new_line)
        if new_line.endswith("\n"):
            w.write(new_line)
        else:
            w.write(new_line + "\n")
    f.close()
    w.close()

def file_deal(fp):
    f = open(fp, "r", encoding='utf-8')
    w = open("./utils/tmp/tmp.scs", "w", encoding='utf-8')
    content = f.read()
    content = content.replace("\\\n", "")
    content = content.replace("\t", "")
    w.write(content)
    f.close()
    w.close()
    nf = open("./utils/tmp/tmp.scs", "r", encoding='utf-8')
    return nf


def data_init(content):
    global param_list, model_list
    for line in content:
        data = line.split(" ")
        data = remove_null(data)
        if (len(data)==1) or ("tune" in line):
            if data[0]=='\n':
                pass
            else:
                key_word = data[0].replace("\n", "").split("=")
                param_list[key_word[0]] = key_word[1]
        elif line.startswith("model"):
            model_list.append(data[1])
        else:
            pass 


def element2spec(line):
    global model_list
    line = deals(line)
    b = line.split(" ")
    b = remove_null(b)
    nl =""
    if (len(b)==1) or ("tune" in line):
      nl = parameters(b)
    elif line.startswith("R:"):
        nl = r_conversion(b)
    elif line.startswith("Short:"):
        nl = short_conversion(b)
    elif line.startswith("L:") or line.startswith("INDQ_Z:"):
        nl = l_conversion(b)
    elif line.startswith("C:") or line.startswith("CAPQ:"):
        nl = c_conversion(b)
    elif line.startswith("I_Source:"):
        nl = i_conversion(b)
    elif line.startswith("V_Source:"):
        nl = v_conversion(b)
    elif line.startswith("Port:"):
        nl = port_conversion(b)
    elif line.startswith("OutputPlan:"):
        nl = output_deal(b)
    elif line.startswith(";"):
        nl = other_deal(b)
    elif line.startswith("AC:") or line.startswith("HB:") or line.startswith("TRAN:") or line.startswith("Component:") or line.startswith("SweepPlan:"):
        nl = sim_deal(line)
    elif line.startswith("Options"):
        nl = option_deal(b)
    elif line.startswith("model") or line.startswith("\""):
        nl = mdoel_deal(b)
        # for m in model_list:
        #     if m in line:
        #         nl = mdoel_deal(b)
    else:
        logger.warning(f"line: {line}, 未做转换")

    return nl
  

def r_conversion(b):
    a1 = name_d(b[0])
    a2 = b[3].lower()
    a2 = value_deal(a2)
    a3 = b[4].replace("Ohm", "")
    ll = []
    for i in range(5,len(b)):
        if b[i].startswith("Noise="):
            ll.append(b[i].replace("Noise=", "isnoisy="))
        else:
            logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    new_line = f"{a1} ( {b[1]} {b[2]} ) resistor {a2}{a3} {a4}"
    return new_line

def short_conversion(b):
    n = b[0].split(":")[1].lower()
    a1 = f"R{n}"
    new_line = f"{a1} ( {b[1]} {b[2]} ) resistor r=0"
    return new_line

def l_conversion(b):
    a1 = name_d(b[0], "L")
    a2 = b[3].lower()
    a2 = value_deal(a2)
    a3 = b[4].replace("H", "")
    ll = []
    for i in range(5,len(b)):
        if b[i].startswith("Q="):
            ll.append(b[i].lower())
        elif b[i].startswith("F="):
            d1 = b[i].replace("F=", "fq=")
            d2 = b[i+1].replace("Hz", "")
            ll.append(d1+d2)
        elif b[i].startswith("Mode="):
            ll.append(b[i].lower())
        elif b[i].startswith("Rdc="):
            e1 = b[i].lower()
            e2 = b[i+1].replace("Hz", "")
            ll.append(e1+e2)
        elif b[i].startswith("Noise="):
            ll.append(b[i].replace("Noise=", "isnoisy="))
        else:
            logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    new_line = f"{a1} ( {b[1]} {b[2]} ) inductor {a2}{a3} {a4}"
    return new_line

def c_conversion(b):
    line = " ".join(b)
    a1 = name_d(b[0])
    a2 = b[3].lower()
    a2 = value_deal(a2)
    a3 = b[4].replace("F", "")
    ll = []
    for i in range(5,len(b)):
        if b[i].startswith("Q="):
            ll.append(b[i].lower())
        elif b[i].startswith("F="):
            d1 = b[i].replace("F=", "fq=")
            d2 = b[i+1].replace("Hz", "")
            ll.append(d1+d2)
        elif b[i].startswith("Mode="):
            ll.append(b[i].lower())
        else:
            logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    t = "capq" if line.startswith("CAPQ:") else "capacitor"
    new_line = f"{a1} ( {b[1]} {b[2]} ) {t} {a2}{a3} {a4}"
    return new_line

def i_conversion(b):
    a1 = name_d(b[0])
    ll = []
    for i in range(3,len(b)):
        if b[i].startswith("Type="):
            if "I_1Tone" in b[i]:
                ll.append("type=sine")
            else:
                logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
        else:
            logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    new_line = f"{a1} ( {b[1]} {b[2]} ) isource {a4}"

    return new_line

def v_conversion(b):
    a1 = name_d(b[0])
    ll = []
    for i in range(3,len(b)):
        if b[i].startswith("Type="):
            if "V_DC" in b[i]:
                ll.append("type=dc")
            else:
                logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
        elif b[i].startswith("Vdc="):
            a2 = value_deal(b[i])
            d1 = a2.replace("Vdc=", "v=")
            d2 = b[i+1].replace("V", "")
            ll.append(d1+d2)
        else:
            logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    new_line = f"{a1} ( {b[1]} {b[2]} ) vsource {a4}"

    return new_line

def port_conversion(b):
    a1 = name_d(b[0])
    a2 = b[4].lower()
    a2 = value_deal(a2)
    a2 = a2.replace("z", "r")
    a3 = b[5].replace("Ohm", "")
    new_line = f"{a1} ( {b[1]} {b[2]} ) port {a2}{a3}"
    if len(b) > 5:
        infos = " ".join(b[5:-1])
        logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{infos}")
    return new_line

def sim_deal(line):
    new_line = f"//{line}"
    return new_line

def mdoel_deal(b):
    if b[0] == "model":
        new_line = "//" + " ".join(b[0:3])
    else:
        n = b[0].split(":")
        a1 = n[1]
        a2 = n[0].replace("\"", "")
        ll = []
        for x in range(5, len(b)):
            if b[x].startswith("Noise="):
                d1 = b[x].replace("Noise=", "isnoisy=")
                ll.append(d1)
            else:
                logger.warning(f"line: {b[0]}, 暂未支持该语法转换：{b[x]}")
        a3 = " ".join(ll)
        new_line = f"{a1} ( {b[1]} {b[2]} {b[3]} ) {a2} {a3} temp=25 tnom=25"
    return new_line

def option_deal(b):
    new_line = "// Options"
    return new_line

def output_deal(b):
    new_line = "// OutputPlan"
    return new_line

def other_deal(b):
    line = " ".join(b)
    new_line = f"//{line[1:]} "
    return new_line

def parameters(data):
    if data[0]=='\n':
        return data[0]
    else:
        return "parameters " + data[0]

def remove_null(l):
    while "" in l:
        l.remove("")
    return l

def value_deal(key8value):
    global param_list
    a = key8value.split("=")
    param_value = a[1]
    try:
        b = f"{a[0]}=" + str(float(param_value))
    except:
        b = f"{a[0]}=" + param_list[param_value]
    return b

def deals(line):
    new_line = line.replace("\n", "")
    new_line = new_line.replace("\r", "")
    return new_line

def name_d(n, u=""):
    n1 = n.split(":")
    n2 = ""
    if u=="":
        n2 = n1[0][0].upper() + n1[1].lower()
    else:
        n2 = u.upper() + n1[1].lower()
    return n2


if __name__=="__main__":
    # 批量转换
    # file_list = get_file_name(r"F:\工作文件\ADS网表\ads_netlist")
    # for file_path in file_list:
    #     ads2spectre(file_path)

    # 单个转换
    ads2spectre(r"./utils/demo.ads", 
                output_name=r"./utils/demo.spec")
