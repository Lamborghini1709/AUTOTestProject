# coding=utf-8
#!/usr/bin/env python

from result_stat import ResultStat
import argparse
import sys

parser = argparse.ArgumentParser(
    prog='AutoTest V5',
    usage='%(prog)s [options]', prefix_chars='-+', 
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='''\
       * Description ---------------------------------------------- * 
       *                                                            *
       *    各测试集代号(用法:'-t 代号')                             *
       * --------------------------------                           *
       *     代号 | 测试集名称                                      *
       * --------------------------------                           *
       *     all  | All_regress_Cases,                              *
       *     hisi | hisiCaseAll,                                    *
       *     huali| regress_Cases_all-cmg-bulk_20230307-1400,       *
       *     hbt  | hbt_regression,                                 *
       *     K3   | K3_regression,                                  *
       *     XVA  | XVA_pin_current_regression                      *
       * ---------------------------------------------------------- *
       ''',
    epilog='''\
  脚本执行命令示例: 
        python main_args.py -o ./testtmp/ -e btdsimP -t huali -c case21 -b plus

  note: 将回归集regress_Cases_all-cmg-bulk_20230307-1400（-t huali）
        保存到./testtmp/（-o ./testtmp/）目录下,
        使用btdsimP（-e btdsimP）仿真该回归测试集的case21（-c case21）,
        （-b plus）表示本次使用的执行文件btdsimP是plus版本\n''')

parser.add_argument("-o", "--outputpath", type=str, default="./", help="输出结果的存放路径")
parser.add_argument("-e", "--execufilename", type=str, default='btdsim', help="btdsim执行文件的名字")
parser.add_argument("-notsavesimcsv", "--savesimcsv", action="store_false", default=True, help="是否保存仿真结果到csv,如果不保存则在命令中添加参数 -notsavesimcsv")
parser.add_argument("-notsavediffcsv", "--savediffcsv", action="store_false", default=True, help="是否保存对比结果到csv,如果不保存则在命令中添加参数 -notsavediffcsv")
parser.add_argument("--savefig", action="store_true", default=False, help="是否画图,默认不画图,需要画图则在命令中添加参数 --savefig")
parser.add_argument("--metric", choices=["MAPE", "RMSE"], type=str, default="MAPE", help="选择误差对比方式, i.e. RMSE or MAPE")
parser.add_argument("-notdel", "--isdelold", action="store_false", default=True, help="是否删除原有的测试集,默认删除,如果不删除则在命令中添加参数 -notdel")
parser.add_argument("-notcp", "--iscpset", action="store_false", default=True, help="是否从远端拷贝测试集过来，默认拷贝,如果不需要拷贝则在命令中添加参数 -notcp")
parser.add_argument("-t", "--testset", nargs='+',  type=str, help="""测试集代码,详情见Description:各测试集代码""")
parser.add_argument("-c", "--casename", nargs='+',type=str, default="", help="指定某一个case,默认为该测试集下所有case")
parser.add_argument("-b", "--btdversion", choices=["base", "plus", "rf"], type=str, default="rf", help="btdsim 版本,每个大版本下会分出三个版本: base、plus、rf")
parser.add_argument("--ccost", type=str, default=0, help="Simulatorcost Compare")
parser.add_argument("--logtime", type=int, default=0, help="Whether to compare the cputime and walltime")
parser.add_argument("-v", "--version", action="version", version='%(prog)s')
opt = parser.parse_args()
print(opt)
print("-"*100)

# output = ResultStat(opt)
# ret = output.outputTerm()
# if(ret >=1):
#     print("ERROR Count: ")
#     print(ret)
#     sys.exit(1)
# else:
#     print("INFO: Regression test passed")
#     sys.exit(0)

