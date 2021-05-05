import os
from enum import Enum
from util.config import *
# 存有失败原因的枚举类型
class Fail_type(Enum):
    # 内容提取失败的两种可能
    tf = 'text_fail_' # 文本提取失败
    pf = 'preview_fail_' # 预览图处理失败
# pdf存放位置
pdfs_dir_path = download_files_paths[0]
# pdf信息提取后的存放位置
papers_text_dir_path = download_files_paths[1]
# pdf缩略图的存放位置
papers_thumbs_dir_path = download_files_paths[2]


# 缩略图宽度
preview_width = 425
# 缩略图提取页数
preview_pages = 6

def recover_name():
    for file in os.listdir(pdfs_dir_path):
        print(file)
        origin = file.split('_')[-1]
        old = os.path.join(pdfs_dir_path,file)
        os.rename(old,os.path.join(pdfs_dir_path,origin))

