# coding=utf-8
#!/usr/bin/env python

def change_suffix(file, suffix):
    if file.endswith('.sp'):
        file = file.replace('.sp', suffix)
    elif file.endswith('.cir'):
        file = file.replace('.cir', suffix)
    elif file.endswith('.scs'):
        file = file.replace('.scs', suffix)
    else:
        pass
    return file