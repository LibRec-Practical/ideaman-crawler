import util
from util.Paper import Paper
from util.db import *
from arxiv import get_one_page , crawler_arxiv_id_lists
from bs4 import BeautifulSoup
import time
import logging as logger

logger.basicConfig(filename="./logs/pwc.log",
                   level=logger.DEBUG,
                   format='[%(asctime)s] - [%(levelname)s] - [PID:%(process)d] - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S'  # 注意月份和天数不要搞乱了，这里的格式化符与time模块相同
                   )

def crawler_one_paper(url):
    html = get_one_page(url)
    soup = BeautifulSoup(html,features='html.parser')
    a = soup.find_all("a",class_="badge-light")
    if len(a) >= 1:
        href = a[1]['href']
        arxiv_id = href[href.rfind('/')+1:]
        crawler_arxiv_id_lists([arxiv_id],1,False)
        # tasks = []
        # for i in soup.find_all('span', class_="badge-primary"):
        #     task = i.text
        #     # task信息
        #     task_text = pymysql.escape_string(task)
        #     ignore_insert('pwc_tasks', 'PWC_task', task_text)
        #     task_id = get_id('pwc_tasks', 'PWC_task', task_text)
        #     tasks.append(str(task_id))
        # tasks = list(set(tasks))
        # task_str = ",".join(tasks)
        # print(task_str,arxiv_id)
        # Paper.update_SQL("pwc_tasks", task_str, arxiv_id)

def crawler_one_page(page):
    url = "https://www.paperswithcode.com/latest?page=%d"%page
    html = get_one_page(url)
    soup = BeautifulSoup(html,"html.parser")
    res = soup.find_all("div",class_="item-content")
    for item in res:
        a = item.find("a")['href']
        url = "https://www.paperswithcode.com"+a
        try:
        	crawler_one_paper(url)
        except:
        	pass
if __name__ == '__main__':
    page_nums = 1000000
    for page in range(page_nums):
        print(page)
        crawler_one_page(page)