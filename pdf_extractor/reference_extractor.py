import re

# 判断邮件地址的正则表达式
email_str = r'([\w-]+(\.[\w-]+)*@[\w-]+(\.[\w-]+)+)'
email_reg = re.compile(email_str)

# 定位参考文献位置的正则表达式
reg_strs = [
    '(?i)\nreferences', '\nReferences', 'References*', 'References', 'References\n\s',
    '(?i)\n\d+\.\s*References', '(?i)\n\d+\s*References',
    '(?i)\d+\.\s*References', '(?i)\d+\s*References',
    '(?i)REFERˆENCIAS', '(?i)REFERÊNCIAS', '(?i)Список литературы', '(?i)KAYNAKÇA','REFERENCES','(?i)\nREFEREMCES'
]

def split_authors(authors_str, domain):
    """
    将论文中形如 [author|author2] @ domain.com 的表达重组为邮件地址
    :param authors_str: 待分割的文本
    :param domain: 邮件地址域名
    :return: 重组后邮件地址的list
    """
    authors_str = authors_str.replace(' ', '').replace('\n', '')
    a_list = authors_str.split(',')
    if len(a_list) == 1:
        a_list = authors_str.split('|')
    return [a + '@' + domain for a in a_list]


class text_info_extractor(object):
    """
    引用提取器,注意到有时pdf即使成功提取出文本，也会有无意义的内容
    todo: 将传入构造函数参数变为文件对象
    """

    def __init__(self, text_str):
        """
        构造器
        字段：
            text：暂存待提取引用的论文
            ref_sections：中间变量，通过正则表达式分割的原论文，如果len为2，说明单引用的论文分割成功，取后半即可
            ref_part:定位到的reference部分，之后可用于APA、MLA等格式的正则提取详细各条的引用
        """
        # 文本
        self.text = text_str
        # 可能的参考文献位置组成的list
        self.ref_sections = []
        # 定位的参考文献部分
        self.ref_part = ''
        # 类似上面
        self.email_sections = []
        self.email_part = ''

    def extract_email(self):
        emails = email_reg.findall(self.text)
        email_list = []
        # 返回含单个元组的list
        if emails:
            # re.search（）作为条件过滤含@纯数字的误匹配项
            email_list = [email for email in [result[0] for result in emails] if not re.search('@[\d.]+', email)]
        else:
            left = r'[\[\{]'
            right = r'[\]\}]'
            authors_reg_str = r'([\w\|.,\s]*)'
            domain = r'@([\w-]+(\.[\w-]+)+)+'
            candidate = re.findall(r'(' + left + authors_reg_str + right + domain + ')', self.text)
            if candidate:
                print()
                rs = candidate[0]
                email_list = split_authors(rs[1], rs[2])
        return email_list

    def probe_by_reg(self, reg):
        temp_sections = reg.split(self.text)
        if len(self.ref_sections) != 2:
            if len(temp_sections) == 2:
                self.ref_sections = temp_sections
            if len(temp_sections) > len(self.ref_sections):
                self.ref_sections = temp_sections

    def get_reference_part(self):
        for i in reg_strs:
            start = self.text.find(i)
            if start > 0:
                self.ref_part = self.text[start+len(i):]
                end = self.ref_part.find("\t")
                self.ref_part = self.ref_part[:end]
                break
        return self.ref_part