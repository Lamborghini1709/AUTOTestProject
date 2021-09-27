import os, sys
import codecs
import argparse


def file_name(file_dir, file_types):
    path = []
    for root, dirs, files in os.walk(file_dir):
        for file in files:
            for file_type in file_types:
                if file.endswith(file_type):
                    path.append(os.path.join(root, file))
    return path


def search_str(files, keys):
    res_list = [{}]
    for file_path in files:
        FileObj = codecs.open(file_path, 'r', 'utf-8')
        line_temp = FileObj.readline()
        a = 0
        while line_temp:
            # print(LineTemp)
            # print(KeyStr)
            # zc = LineTemp.find(KeyStr)
            a = a + 1
            try:
                for key_str in keys:
                    if line_temp.find(key_str) >= 0:
                        FoundFlag = True
                        log_str = {file_path}
<<<<<<< HEAD
                        if log_str not in res_list:
                            print("file path is: " + file_path, "   " + key_str, " in the line number is: " + str(line_temp.find(key_str)))
                            # print(line_temp)
                            res_list.append(log_str)
=======
                        # if log_str not in res_list:
                        print("file path is: " + file_path, "   " + key_str, " in the line number is: " + str(a))
                        res_list.append(log_str)
>>>>>>> 440b606 (init code)
                    #       break

                line_temp = FileObj.readline()
            except Exception as e:
                break
        FileObj.close()

    if len(res_list) == 0:
        print("Not found the string!")
    return res_list


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('--open_dir', dest='open_dir', type=str, help='find folder')
    parser.add_argument('--key_str', dest='key_str', type=str, help='find search str')
    parser.add_argument('--suffix', dest='suffix', type=str, help='find file suffix')

    return parser.parse_args(argv)


if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])

    print('# --open_dir:{}'.format(args.open_dir))
    print('# --key_str:{}'.format(args.key_str))
    print('# --suffix:{}'.format(args.suffix))

    files_list = file_name(args.open_dir, args.suffix.split(','))
    res_list = search_str(files_list, args.key_str.split(','))

