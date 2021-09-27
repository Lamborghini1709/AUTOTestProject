搜索文件中是否出现关键字；
参数说明：
--open_dir  # 要搜索的文件夹路径
--key_str  # 要搜索的关键字
--suffix  # 文件类型后缀（现支持单一后缀）

example：
python3 search_str.py --open_dir "/mnt/case/test-examples-linux/" --key_str "The license runs for successful" --suffix ".log"
