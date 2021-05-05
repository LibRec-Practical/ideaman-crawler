# -*-coding:utf-8-*-
'''
从pdf中获取文本与缩略图
'''
import time
from util.Paper import Paper
from .reference_extractor import *
from tika import parser
from pdf2image import convert_from_path
from .pdf_info_extractor import *
from PIL import Image
import logging as logger

logger.basicConfig(filename='./logs/%s.txt' % time.strftime("%Y-%m-%d", time.localtime()),
                   level=logger.DEBUG,
                   format='[%(asctime)s] - [%(levelname)s] - [PID:%(process)d] - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S'  # 注意月份和天数不要搞乱了，这里的格式化符与time模块相同
                   )

# 检测pdf文本提取是否成功的正则,出现如下字段说明源pdf未准备好
not_available_reg = re.compile(r"Link back to: arXiv, form interface, contact.")
# 如果返回None，说明源pdf有效
def is_invalid(text):
    return not_available_reg.search(text)

def get_pdf_id_ver(file_name):
    """
        从pdf文件名获取arxiv id和版本
        :param file_name pdf文件名
        :return 字典，值含有id与版本，通过key:'id','ver'提取
    """
    key = ['id', 'ver']
    info = file_name.split('.pdf')[0].split(r'/')[-1].split('v')
    return dict(zip(key, info))

def get_preview(im):
    '''
    读取配置中要求的宽度（目前为850），保持比例进行缩放
    :param im: pillow的图片对象
    :return: 处理后的图片
    '''
    # 原图的尺寸
    origin_width, origin_height = im.size
    # 原图的高宽比
    ratio = origin_height / origin_width
    # 对原图进行缩放
    output = im.resize((preview_width, int(preview_width * ratio)), Image.ANTIALIAS)
    return output

# 提取pdf信息的内部类
class PdfExtractor(object):

    def __init__(self, pdf_file):
        """
            构造函数，传入pdf文件对象，构造pdf内容提取器
            :param pdf_file 使用open(pdf_path,'rb')打开的pdf文件对象
        """
        # 文件对象
        self.pdf = pdf_file
        # 文件所在绝对路径
        self.abs_path = pdf_file.name
        # Arxiv id 与版本
        id_and_ver = get_pdf_id_ver(self.abs_path)
        self.id = id_and_ver['id']
        self.ver = id_and_ver['ver']
        # id与版本的结合
        self.idvv = self.id+'v'+self.ver

        # 提取工作的成功状态
        self.status = 'fin_'
        # # 各种路径
        # self.paper_info_path = os.path.join(papers_info_dir_path, self.idvv)

        self.txt_path = os.path.join(papers_text_dir_path,self.idvv+"_text.txt")
        self.thumbs_path = os.path.join(papers_thumbs_dir_path,self.idvv)
        # 论文文本
        self.content = ""

    def extract_text(self):
        """
        提取pdf的文本到text.txt，tika实现
        :return: 文本提取的结果
        """
        # 尝试传入file对象作为输入，之前使用绝对路径
        # 提取失败的体现:返回状态非200 / content中包含："Link back to: arXiv, form interface, contact."
        result = parser.from_file(self.abs_path)
        content = ''
        isSuccess = False
        if result['status'] == 200:
            content = result['content']
            if not is_invalid(content):
                with open(self.txt_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                isSuccess = True
                self.content = content
        if not isSuccess:
            self.status = Fail_type.tf.value
            # raise 下方不能执行任何语句
            raise Exception('pdf格式有误')
        return self



    def extract_preview(self):
        """
        提取pdf的缩略图，pdf2image实现,提取成webp
        :return:
        """
        if self.status == 'fin_':
            count = 0
            # 按照配置要求提取前x页的缩略图
            images = convert_from_path(self.abs_path)[:preview_pages]
            # 创建文件夹
            if not os.path.isdir(self.thumbs_path):
                os.makedirs(self.thumbs_path)
            # 保存每一页的WebP缩略图
            for im in images:
                output = get_preview(im)
                # 按照preview_序号（从0开始）.webp 进行保存
                preview_webp_path = os.path.join(self.thumbs_path, "preview_{seq}.webp".format(seq=count))
                # 保存为WebP，75%质量
                output.save(preview_webp_path,'WebP', quality=75)
                count += 1
        else:
            pass
        return self

    def check_finish(self):
        '''
        检查内容提取是否完全完成,是则生成完成标记
        :return: 是否成功提取的Boolean
        '''
        # 如果该文件名不在出错的并集内，说明成功提取所有内容
        if self.status == '_fin':
            # 创建完成内容提取的标记文件
            with open(os.path.join(self.paper_info_path, 'content_finish'), 'wb') as fin:
                pass
            return True
        else:
            return False
    def extract_references(self):
        """
        提取论文references
        :return:
        """
        tie = text_info_extractor(self.content)
        Paper.update_SQL('references',tie.get_reference_part(),self.idvv)

    def extract(self):
        '''
        提取论文对象信息的主程序,进行链式调用，提取文本、preview，中途出错则分拣到相应的list处理
        :return: 提取是否成功的Boolean
        '''
        return self.extract_text().extract_preview().extract_references()

    def update_name(self):
        '''
        对完成提取的pdf添加前缀，标记状态（成功/提取文本或缩略图失败）
        :return:
        '''
        #pass
        new_name = os.path.join(pdfs_dir_path,self.status + self.pdf_name)
        os.renames(self.abs_path,new_name)

def extract_from_a_pdf(path):
    # 指定pdf路径，使用本类进行提取
    start = time.time()
    with open(path,'r',encoding='utf-8') as pdf:
        pe = PdfExtractor(pdf)
        pe.extract()
    pe.update_name()

if __name__=='__main__':
    # 测试：
    #   文本提取
    #   preview提取
    #   log记录
    #   重命名
    # recover_name()
    # C:\Users\Jackson Ma\Documents\GitHub\recsys\data\error_pdfs\text_fail_1712.02183v5.pdf
    # C:\Users\Jackson Ma\Documents\GitHub\recsys\data\error_pdfs\preview_fail_1709.02673v3.pdf
    # extract_from_a_pdf(r'C:\Users\Jackson Ma\Documents\GitHub\recsys\data\error_pdfs\preview_fail_1709.02673v3.pdf')
    print('请使用contnet_extraction_launcher进行操作')