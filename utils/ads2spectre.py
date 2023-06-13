# coding=utf-8

import os
import logging
import argparse
import sys

logging.basicConfig(level=logging.DEBUG, 
format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
filename="./ads2spectre.log",
filemode='a+',
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
                pictrue_path = os.path.join(filepath, filename)
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
    try:
        w = open("./tmp/tmp.scs", "w", encoding='utf-8')
    except:
        os.mkdir("./tmp")
        w = open("./tmp/tmp.scs", "w", encoding='utf-8')
    content = f.read()
    content = content.replace("\\\n", "")
    content = content.replace("\t", "")
    w.write(content)
    f.close()
    w.close()
    nf = open("./tmp/tmp.scs", "r", encoding='utf-8')
    return nf


def data_init(content):
    global param_list, model_list
    for line in content:
        data = line.split(" ")
        data = remove_null(data)
        if (len(data)==1) or ("tune" in line):
            if data[0]=='\n' or data[0].startswith(";"):
                pass
            else:
                key_word = data[0].replace("\n", "").split("=")
                param_list[key_word[0].lower()] = key_word[1]
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
        a = line.replace("\r", "")
        b = a.replace("\n", "")
        if b=="":
            pass
        elif b.startswith("#"):
            pass
        else:
            nl = "// " + line
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
            if b[i].endswith("Ohm"):
                pass
            else:
                logger.warning(f"line(R): {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    new_line = f"{a1} ( {b[1]} {b[2]} ) resistor {a2}{a3} {a4}"
    return new_line

def short_conversion(b):
    n = b[0].split(":")[1].lower()
    if "Mode=0" in b:
        a1 = f"R{n}"
        new_line = f"{a1} ( {b[1]} {b[2]} ) resistor r=0"
    elif "Mode=1" in b:
        a1 = f"C{n}"
        new_line = f"{a1} ( {b[1]} {b[2]} ) capacitor c=1u"
    elif "Mode=-1" in b:
        a1 = f"L{n}"
        new_line = f"{a1} ( {b[1]} {b[2]} ) inductor l=1u"
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
            e2 = b[i+1].replace("Ohm", "")
            ll.append(e1+e2)
        elif b[i].startswith("Noise="):
            ll.append(b[i].replace("Noise=", "isnoisy="))
        else:
            if b[i].endswith("Ohm") or b[i].endswith("Hz"):
                pass
            else:
                logger.warning(f"line(L): {b[0]}, 暂未支持该语法转换：{b[i]}")
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
            if b[i].endswith("Hz"):
                pass
            else:
                logger.warning(f"line(C): {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    t = "capq" if line.startswith("CAPQ:") else "capacitor"
    new_line = f"{a1} ( {b[1]} {b[2]} ) {t} {a2}{a3} {a4}"
    return new_line

def i_conversion(b):
    # a1 = name_d(b[0])
    # ll = []
    # for i in range(3,len(b)):
    #     if b[i].startswith("Type="):
    #         if "I_1Tone" in b[i]:
    #             ll.append("type=sine")
    #         else:
    #             logger.warning(f"line(I): {b[0]}, 暂未支持该语法转换：{b[i]}")
    #     else:
    #         if b[i].endswith("A"):
    #             pass
    #         else:
    #             logger.warning(f"line(I): {b[0]}, 暂未支持该语法转换：{b[i]}")
    # a4 = " ".join(ll)
    # new_line = f"{a1} ( {b[1]} {b[2]} ) isource {a4}"
    new_line = "// " + " ".join(b)
    logger.warning(f"line(Isource): 暂未支持 Isource 的转换：{b[0]}")
    return new_line

def v_conversion(b):
    a1 = name_d(b[0])
    ll = []
    for i in range(3,len(b)):
        if b[i].startswith("Type="):
            if "V_DC" in b[i]:
                ll.append("type=dc")
            else:
                logger.warning(f"line(Vsource): {b[0]}, 暂未支持该语法转换：{b[i]}")
        elif b[i].startswith("Vdc="):
            a2 = value_deal(b[i])
            d1 = a2.replace("Vdc=", "v=")
            try:
                if b[i+1].endswith("V"):
                    d2 = b[i+1].replace("V", "")
                else:
                    d2 = ""
            except:
                d2 = ""
            ll.append(d1+d2)
        else:
            if b[i].endswith("V"):
                pass
            else: 
                logger.warning(f"line(Vsource): {b[0]}, 暂未支持该语法转换：{b[i]}")
    a4 = " ".join(ll)
    new_line = f"{a1} ( {b[1]} {b[2]} ) vsource {a4}"

    return new_line

def port_conversion(b):
    # a1 = name_d(b[0])
    # a2 = b[4].lower()
    # a2 = value_deal(a2)
    # a2 = a2.replace("z", "r")
    # a3 = b[5].replace("Ohm", "")
    # new_line = f"{a1} ( {b[1]} {b[2]} ) port {a2}{a3}"
    # if len(b) > 5:
    #     infos = " ".join(b[5:-1])
    new_line = "// " + " ".join(b)
    logger.warning(f"line(PORT): 暂未支持 PORT 的转换: {b[0]}")
    return new_line

def sim_deal(line):
    new_line = f"//{line}"
    logger.warning(f"line(SIM): 暂未支持 仿真分析 的转换：{line}")
    return new_line

def mdoel_deal(b):
    if b[0] == "model":
        new_line = "//" + " ".join(b[0:3])
        logger.warning(f"line(MODEL): {b[2]}, 暂未支持该语法转换：{new_line}")
    else:
        n = b[0].split(":")
        a1 = n[1]
        a2 = n[0].replace("\"", "")
        if a2=="HBTM1":
            ll = []
            for x in range(5, len(b)):
                if b[x].startswith("Noise="):
                    d1 = b[x].replace("Noise=", "isnoisy=")
                    ll.append(d1)
                else:
                    logger.warning(f"line({a2}): {b[0]}, 暂未支持该语法转换：{b[x]}")
            a3 = " ".join(ll)
            new_line = f"{a1} ( {b[1]} {b[2]} {b[3]} ) {a2} {a3} temp=25 tnom=25"
        else:
            new_line = "// "+ " ".join(b)
            logger.warning(f"line({a2}): 暂未支持该 model 的转换：{b[0]}")
    return new_line

def option_deal(b):
    line = " ".join(b)
    new_line = f"// {line}"
    logger.warning(f"line(OPTION): 暂未支持 option 的转换：{b[0]}")
    return new_line

def output_deal(b):
    line = " ".join(b)
    new_line = f"// {line}"
    logger.warning(f"line(OUTPUT): 暂未支持 output 的转换：{b[0]}")
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
    param_value = a[1].lower()
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

def creat_dir(tag_path):
    new_path = tag_path.split("\\")
    for i in range(len(new_path)):
        n = "\\".join(new_path[:i+1])
        if os.path.exists(n):
            pass
        else:
            os.mkdir(n)

def change_suffix(file_name, suffix=".scs"):
    a = file_name.split(".")
    new_name = "".join(a[:-1])+suffix
    return new_name

if __name__=="__main__":
    parser = argparse.ArgumentParser(
    prog='ADS TO SPECTRE v1.0',
    usage='%(prog)s [options]', prefix_chars='-+', 
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='''\
       * Description ---------------------------------------- * 
       *                                                      *
       *        将ADS语法的网表转换成spectre语法的网表        *
       *                                                      *
       *----------------------------------------------------- *
       ''',
    epilog='''\
  脚本执行命令示例: 
        python ads2spectre.py -i ./testtmp/ -o ./result/ +b

  note: 批量转换./testtmp/目录下所有.ads结尾的文件
        转换结果保存到./result/目录下\n''')

    parser.add_argument("-i", "--input", type=str, required=True, help="需要转换的文件路径或者目录")
    parser.add_argument("-o", "--outputpath", type=str, default="./", help="指定输出目录")
    parser.add_argument("+b", "--batchProcessing", action='store_true', default=False, help="是否批量处理，后面不跟参数，默认不进行批量处理，命令中加入+b则开启批量处理模式")
    opt = parser.parse_args()
    print(opt)
    print("-"*100)

    if opt.batchProcessing == False:
        if os.path.isfile(opt.input):
            input_file = opt.input
            file_name = input_file.split("\\")[-1]
            file_name = change_suffix(file_name)
            if os.path.exists(opt.outputpath):
                outpu_file = os.path.join(opt.outputpath, file_name)
            else:
                creat_dir(opt.outputpath)
                outpu_file = os.path.join(opt.outputpath, file_name)
             
        else:
            print("ERROR: -i 参数请传入文件")
            sys.exit(1)
        # 单个转换
        ads2spectre(input_file, 
                    output_name=outpu_file)
    else:
        if os.path.isfile(opt.input):
            print("ERROR: -i 参数请传入文件目录")
            sys.exit(1)
        else:
        # 批量转换
            file_list = get_file_name(opt.input)
            for input_file in file_list:
                file_name = input_file.split("\\")[-1]
                file_name = change_suffix(file_name)
                if os.path.exists(opt.outputpath):
                    outpu_file = os.path.join(opt.outputpath, file_name)
                else:
                    creat_dir(opt.outputpath)
                    outpu_file = os.path.join(opt.outputpath, file_name)
                ads2spectre(input_file, 
                            output_name=outpu_file)


