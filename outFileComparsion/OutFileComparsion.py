#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2022/8/12 11:00
# @Author  : wayne
# @File    : OutFileComparsion.py
# @Software: PyCharm

import yaml
from tools_utils import outfile_parser, calc_error


if __name__ == '__main__':
    # 1、读取配置文件
    config = yaml.load(open('config.yaml', 'r', encoding='utf-8'), Loader=yaml.FullLoader)
    # 2、加载benchoutfile并解析文件得到字典数据
    benchoutpath = config['benchoutpath']
    benchout_dict, benchout_plotnames = outfile_parser(benchoutpath)
    # {plotname: [OrderedDict]}
    # {'nodename----unit': [valuelist]}
    # 3、加载compoutfile并解析文件得到字典数据
    compoutpath = config['compoutpath']
    compout_dict, compout_plotnames = outfile_parser(compoutpath)
    # print(compout_plotnames)
    # 4、根据配置文件对比数据,计算误差
    compare, com_result_dict = calc_error(benchout_dict, compout_dict, config)
    print(com_result_dict)
    print(compare)

    # 6、 如果参数指定了保存图片，则开始画图
    # //TODO

