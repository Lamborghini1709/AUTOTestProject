import os
import datetime
import subprocess
import sys
import argparse




file_Num = 0

is_netlist = lambda x:any(x.endswith(extension)
    for extension in ['.sp','.cir', 'scs'])
netlist_list = []

def sim_folder(opt):
    test_dir = opt.test_path
    if isinstance(test_dir,str):
        for filepath,dirnames,filenames in os.walk(test_dir, topdown=False):
            for filename in filenames:
                if is_netlist(filename):
                    spfile = os.path.join(filepath,filename)
                    netlist_list.append(spfile)
                    print("Find %s \n" % (spfile))
                    global file_Num
                    file_Num += 1
                    if not_simulated(spfile) and not opt.update:
            # RunCmd = ['simulator',spfile]
                        RunCmd = "simulator {} >> {}.log".format(spfile, spfile)
            # os.system(' '.join(RunCmd))
                        os.system(RunCmd)

                        print("rcmd:", RunCmd)

    else:
        print("Please specify the test folder in string format.")

def not_simulated(file):
    if file.endswith('.sp'):
        out_file = file.replace('.sp', '.out');
    elif file.endswith('.cir'):
        out_file = file.replace('.cir', '.out');


    out_file = file.replace('.sp','.out');
    out_file = out_file.replace('.cir','.out');

    if os.path.exists(out_file):
        return 0
    else:
        return 1

def global_out_check():
    print("Check output....")
    logfile = open("autoRun.log", "a")
    now = datetime.datetime.now()
    logfile.write(now.strftime("%Y-%m-%d %H:%M:%S \n"))
    for file in netlist_list:
        out_file = file.replace('.sp','.out');
        out_file = out_file.replace('.cir','.out');

        if os.path.exists(out_file):
            out_file_size = os.path.getsize(out_file)
            if out_file_size == 0:
                logfile.write(' '.join([file,'NO [ZERO OUT]','\n']))
            else:
                logfile.write(' '.join([file,'YES','\n']))
        else:
            logfile.write(' '.join([file,'NO','\n']))
        #print out_file;
    print("output check is OK.")
    print("The result is in autoRun.log.")





def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test_path", type=str, default="./", help="path to test")
    parser.add_argument("--update", type=int, default=0, help="update out file")
    opt = parser.parse_args()
    print(opt)
    print("Start AutoSim...")
    test_dir = '.'
    sim_folder(opt)
    print("Total: %d files (.sp or .cir)\n" % (file_Num));
    #print netlist_list
    global_out_check()

if __name__ == '__main__':
    main()

