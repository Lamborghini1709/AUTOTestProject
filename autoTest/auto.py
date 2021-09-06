 # -*- coding: UTF-8 -*-
import os
import datetime
import subprocess
import sys
import re

file_Num = 0
UPDATE_TAG = 1

is_netlist = lambda x:any(x.endswith(extension)
    for extension in ['.sp', '.cir', 'scs'])
netlist_list = []
log_list = []
line_list = []

time_list = []
str_list = []

def sim_folder(test_dir, ref_filename):
    if isinstance(test_dir,str):
        for filepath,dirnames,filenames in os.walk(test_dir, topdown=False):
            for filename in filenames:
                if is_netlist(filename):
                    spfile = os.path.join(filepath,filename)
                    # changed 09/02
                    # print('filepath:', filepath)
                    ref_file = os.path.join(filepath,ref_filename)
                    ref_file = os.path.join(ref_file,filename)
                    # print("ref out file:", ref_file)
                    if ref_filename != 'None':
                        if not_simulated(ref_file):
                            # print()
                            msg =  'ref_file中没有对应的out文件，{}为被include的文件'.format(spfile)
                            print(msg)
                            print('或为ref_file不为默认值，请在ternimal中输入')
                            print('或没有Linux_Ref文件只能自己观察sp文件是否要被运行')
                        else:
                            run_simulation(spfile)
                    else:
                        # 没有Ref_linux文件只能自己观察sp文件是否要被运行（或之后程序改进为遍历sp寻找是否被include过）
                        run_simulation(spfile)

    else:
        print("Please specify the test folder in string format.")


def run_simulation(spfile):
    netlist_list.append(spfile)
    print("Find %s \n" % (spfile))
    global file_Num
    file_Num += 1
    if not_simulated(spfile) and not UPDATE_TAG:
        # RunCmd = ['simulator',spfile]
        logfile = change_suffix(spfile, '.log')
	# changed 0904 >> to >为了每次重新仿真得到的log不会记录之前的结果，
	# 否则autoRun.log的自动判断会出错
        RunCmd = "simulator {} > {}".format(spfile, logfile)
        log_list.append(logfile)
                    # os.system(' '.join(RunCmd))
        os.system(RunCmd)
        get_time(logfile)
        #print("rcmd:", RunCmd)

def change_suffix(file, suffix):
    file = file.replace('.sp', suffix)
    file = file.replace('.cir', suffix)
    file = file.replace('.scs', suffix)
    return file

def not_simulated(file):
    out_file = change_suffix(file, '.out')
    #print(out_file)
    if os.path.exists(out_file):
        return 0
    else:
        return 1
    

def global_out_check():
    print("Check output....")
    logfile = open("autoRun.log", "a")
    now = datetime.datetime.now()
    logfile.write(now.strftime("%Y-%m-%d %H:%M:%S \n"))
    for file in log_list:
        # changed 0902
        # out_file = file.replace('.sp','.out')
        # out_file = out_file.replace('.cir','.out')
        # if os.path.exists(out_file):
        #     out_file_size = os.path.getsize(out_file)
        #     if out_file_size == 0:
        #         logfile.write(' '.join([file,'NO [ZERO OUT]','\n']))
        #     else:
        #         logfile.write(' '.join([file,'YES','\n']))
        # else:
        #     logfile.write(' '.join([file,'NO','\n']))
        error = outfile_check(file)
        if error:
            logfile.write(' '.join([file,'NO','\n']))
        else:
            logfile.write(' '.join([file,'YES','\n']))
        #print out_file;
    print("output check is OK.")
    print("The result is in autoRun.log.")

# changed 0902
def outfile_check(file):
    with open(file) as f:
        if 'error' in f.read():
            if 'sucessfully' in f.read():
                return 0
            else:
                return 1
        else:
            return 0

# changed 0902
def get_time(file):
    with open(file) as f1:
        for line in f1.readlines():
            if line.find('wall-clock time')>-1:
                # print("time:", line)
                line_list.append(line)
    # print("line_list:", line_list)
    for line in line_list:
        line_list2 = line.split()
        time = line_list2[7]
        str_list.extend(time)

    # print("str_list:", str_list)
    length = len(str_list)
    x = 0
    while x < length:
        if str_list[x] == ":":
            # l.remove(l[x])
            del str_list[x]
            x -= 1
            length -= 1
        x += 1
    # print("str_list:", str_list)
    time_list = [int(i) for i in str_list]  

    time1 = (time_list[0] * 10 + time_list[1]) * 3600 + (time_list[2] * 10 + time_list[3]) * 60 + \
                                                                (time_list[4] * 10 + time_list[5])
    time2 = (time_list[6] * 10 + time_list[7]) * 3600 + (time_list[8] * 10 + time_list[9]) * 60 + \
                                                                (time_list[10] * 10 + time_list[11])
    rst = time2 - time1
    msg = "running time: {} s".format(rst)
    print(msg)    

def main():
    print("Start AutoSim...")
    test_dir = '.'
    # changed 09/02
    if len(sys.argv) == 2:
        ref_filename = sys.argv[1]
    else:
        print('未定义ref_filename，使用默认名称“Linux_Ref”')
        print('如想要定义ref_filename，请在运行时在ternimal中输入：python2 auto.py ref_filename')
        ref_filename = 'Linux_Ref'
        
    #print('ref_filename:', ref_filename)
    sim_folder(test_dir, ref_filename)
    print("Total: %d files (.sp or .cir)\n" % (file_Num))
    #print netlist_list
    global_out_check()

if __name__ == '__main__':
    main()
