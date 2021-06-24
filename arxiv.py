import os
import random
import time
from datetime import timedelta, datetime
from multiprocessing import Pool
import requests as r
import pymysql
from bs4 import BeautifulSoup
import re
from collections import defaultdict

import util
from pdf_extractor.content_extractor import PdfExtractor
from util.Paper import Paper
from util.config import *
import logging as logger
from urllib import parse

file_path = download_files_paths[0]  # pdf 存储路径
if not os.path.exists(file_path):
    os.makedirs(file_path)
have = set(os.listdir(file_path))
logger.basicConfig(filename='./logs/%s.txt' % time.strftime("%Y-%m-%d", time.localtime()),
                   filemode='w',
                   level=logger.DEBUG,
                   format='[%(asctime)s] - [%(levelname)s] - [PID:%(process)d] - [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S'  # 注意月份和天数不要搞乱了，这里的格式化符与time模块相同
                   )

ARXIV_BASE_URL = 'https://arxiv.org'


def get_header():
    """
    获取随机的headers,避免被PWC ban
    :return:
    """
    a = random.randint(12, 18)
    b = random.randint(0, 10)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_' + str(a) + '_' + str(
            b) + ') AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.108 Safari/537.36',
        'Referer': ARXIV_BASE_URL
    }
    return headers


def get_one_page(url):
    """
    获得一个页面的内容
    :param url:
    """
    num = 0
    time.sleep(2)
    while num < 10:  # 尝试十次
        try:
            response = r.get(url, headers=get_header())
            logger.info("访问" + url + "返回码:" + str(response.status_code))
            while response.status_code == 403:
                logger.error("访问" + url + "返回码:" + str(response.status_code), "访问错误")
                time.sleep(500 + random.uniform(0, 500))
                response = r.get(url, headers=get_header())
                logger.info("访问" + url + "返回码:" + str(response.status_code))
            if response.status_code == 200:
                return response.text
            return None
        except:
            logger.error("打开页面" + url + "失败,次数" + str(num))
            num += 1


def extractor_pdf(pdf_path):
    """
    提取pdf的文件的内容
    :param pdf_path:
    :return:
    """
    with open(pdf_path, 'r', encoding='utf-8') as pdf:
        pe = PdfExtractor(pdf)
        pe.extract_preview()


def download_pdf(arxiv_id):
    """
    从中国镜像下载pdf文件 注意可能会下载失败
    :param arxiv_id:
    :return:
     0: 下载失败
     1: 下载成功
     2： 文件已经存在
    """
    basename = arxiv_id[6:] + '.pdf'
    fname = os.path.join(file_path, basename)
    if os.path.isfile(fname):
        # 如果文件存在，跳过
        logger.info(fname + "文件存在,跳过该文件")
        return 2
    pdf_url = 'http://arxiv.org/pdf/' + basename
    logger.info("使用镜像1中" + pdf_url)
    try:
        res = r.get(pdf_url, headers=get_header())
        with open(fname, 'wb+') as f:
            f.write(res.content)
        fsize = os.path.getsize(fname)
        f_kb = fsize / float(1024)
        if f_kb <= 10:
            logger.error("下载文件过小")
            pdf_url = 'http://arxiv.org/ftp/arxiv/papers/' + basename[:4] + '/' + basename
            logger.error("使用镜像2" + pdf_url)
            res = r.get(pdf_url, headers=get_header())
            with open(fname, 'wb+') as f:
                f.write(res.content)
            return 0
        return 1
    except Exception as e:
        logger('error downloading: ' + pdf_url)
    return 0


def crawler_arxiv_id_lists(list_ids, num_of_papers_today, flag=True):
    """
    根据arxiv_id的列表,通过api 下载论文相关信息
    :param list_ids:
    :param num_of_papers_today:
    :return:
    """
    if flag:
        for i in range(len(list_ids)):
            # 获取纯数字
            list_ids[i] = list_ids[i].text[6:]

    logger.info("通过页面获得论文数据ing")
    num = 0
    for tmp_id in list_ids:
        url = "https://arxiv.org/abs/" + tmp_id
        html = get_one_page("https://arxiv.org/abs/" + tmp_id)
        soup = BeautifulSoup(html, features='html.parser')
        title = soup.find('meta', attrs={"name": 'citation_title'})
        if title is None:
            continue
        title = title['content']
        updated = soup.find('meta', attrs={"name": 'citation_online_date'})['content']
        published = soup.find('meta', attrs={"name": 'citation_date'})['content']
        summary = soup.find('meta', attrs={"name": 'citation_abstract'})['content'].replace('\n', ' ').strip()
        d = {
            'id': 'arXiv:' + tmp_id,
            'url': url,
            'updated': updated,
            'published': published,
            'title': title,
            'summary': summary,
        }
        """
        # download_label = download_pdf(d['id'])
        # logger.info("论文" + d['id'] + "的pdf信息下载完成")
        # logger.info("论文" + d['id'] + "提取pdf信息")
        # extractor_pdf(file_path + d['id'][6:] + '.pdf')
        """

        # 判断论文是否已经存在
        if util.db.get_id("paper", "user_id", d['id']) is not None:
            # 下载PWC
            crawler_PWC(d['id'][6:], d['title'])
            logger.info("论文" + d['id'] + "的PWC信息下载完成")
            logger.info("论文" + tmp_id + "已经下载")
            num += 1
            logger.info("下载完成：" + d['id'] + "当前进度：" + str(float(num / num_of_papers_today) * 100) + "%")
            continue

        
        # 作者信息
        authors = []
        for author in soup.find_all('meta', attrs={"name": 'citation_author'}):
            author_text = author['content']
            author_text = pymysql.escape_string(author_text)
            util.db.ignore_insert('authors', 'author', author_text)
            author_id = util.db.get_id('authors', 'author', author_text)
            authors.append(str(author_id))
        logger.info("论文" + d['id'] + "作者信息下载完成")

        # 论文分类
        category_td = soup.find("td", class_='subjects')
        category_str = ""
        if category_td:
            category_str = category_td.text
        categories = []
        category_list = re.findall(r'[(](.*?)[)]', category_str)
        for category_text in category_list:
            category_text = pymysql.escape_string(category_text)
            util.db.ignore_insert('category', 'category_name', category_text)
            category_id = util.db.get_id('category', 'category_name', category_text)
            categories.append(str(category_id))
        logger.info("论文" + d['id'] + "标签信息下载完成")

        # 版本号
        v = ''
        if d['id'].find('v'):
            v = d['id'].split('v')[-1]
        else:
            v = 1

        p = Paper(
            published=int(datetime.strptime(d['published'], '%Y/%m/%d').timestamp() * 1000),
            user_id=d['id'],
            version=v,
            link=d['url'],
            title=pymysql.escape_string(d['title'].replace('\n', '')),
            updated=int(datetime.strptime(d['updated'], '%Y/%m/%d').timestamp() * 1000),
            description=pymysql.escape_string(d['summary']),
            authors=','.join(authors),
            tags=','.join(categories),
            pdf_link=file_path + d['id'][6:] + '.pdf'
        )

        # 执行sql语句
        util.db.cur.execute(p.generate_SQL())
        # 提交到数据库执行
        util.db.conn.commit()

        # 下载PWC
        crawler_PWC(d['id'][6:], d['title'])
        logger.info("论文" + d['id'] + "的PWC信息下载完成")
        logger.info("论文" + item + "已经下载")

        logger.info("下载完成：" + d['id'] + "当前进度：" + str(float(num / num_of_papers_today) * 100) + "%")
        num += 1


def get_url(query_start_date, query_end_date, query_size, query_start):
    url = ARXIV_BASE_URL + "/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=&terms-0-field=title&classification-computer_science=y&classification-physics_archives=all&classification-include_cross_list=include&date-year=&date-filter_by=date_range&date-from_date=" + query_start_date + "&date-to_date=" + query_end_date + "&date-date_type=submitted_date&abstracts=hide&size=" + str(
        query_size) + "&order=-announced_date_first&start=" + str(query_start)
    return url


def crawler_tmp_day(tmp_date):
    # 查询tmp_date该日期的论文数量
    query_start_date = tmp_date.strftime('%Y-%m-%d')  # 查询开始日期
    query_end_date = (tmp_date + timedelta(days=1)).strftime('%Y-%m-%d')  # 查询结束日期 = 查询开始日期 + 1
    query_size = 25  # 每页50个论文
    query_start = 0  # 最开始是从0开始的
    html = get_one_page(get_url(query_start_date, query_end_date, query_size, query_start))
    soup = BeautifulSoup(html, features='html.parser')
    logger.info("处理日期和今天的条目数")
    h3_title = soup.find('h1').text
    num_of_papers_today = eval(h3_title[h3_title.find('of ') + 3:h3_title.find(' results')])
    logger.info(query_start_date + "日共有论文" + str(num_of_papers_today) + "篇")

    # 获取tmp_date该日期的论文，将其的arxiv_id加入到list_ids中
    list_ids = []
    while query_start < num_of_papers_today:
        html = get_one_page(get_url(query_start_date, query_end_date, query_size, query_start))
        soup = BeautifulSoup(html, features='html.parser')
        res = soup.find_all('a')  # 获得当天的arxiv_id
        for i in res:
            if i.text.startswith("arXiv:"):
                list_ids.append(i)
        query_start += query_size

    # 爬取每篇论文，之后进行下一天
    crawler_arxiv_id_lists(list_ids, num_of_papers_today)
    logger.info("爬虫完成日期:" + query_start_date)
    time.sleep(35)



def crawler_history():
    print("#############################################################")
    print()
    print("                        开始历史爬虫:")
    print()
    print("#############################################################")

    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    tmp_date = start_date
    # process_pool = Pool(1)
    global error_dict

    error_dict = defaultdict(int)
    while tmp_date < end_date:
        crawler_tmp_day(tmp_date)
        # process_pool.apply_async(crawler_tmp_day, (tmp_date,))  # 维持执行的进程总数为processes，当一个进程执行完毕后会添加新的进程进去
        tmp_date += timedelta(days=1)
    # process_pool.close()
    # process_pool.join()
    logger.info("下载%s - %s 的论文完成！" % (start_date_str, end_date_str))
    logger.info("下载错误的有：%s", (error_dict,))


def crawler_PWC(arxiv_id, title):
    '''
    根据arxiv_id,通过PWC搜索，找到相关论文，然后下载该论文的Task以及分类信息
    :param arxiv_id:
    :return:
    '''
    html = get_one_page("https://www.paperswithcode.com/search?q_meta=&q=" + parse.quote(title))

    soup = BeautifulSoup(html, features='html.parser')
    tasks = []
    div = soup.select('div.col-lg-9.item-content')
    href = ""
    for div_itme in div:
        href = div_itme.find('a')['href']
        break
    if href == "":
        return
    else:
        html = get_one_page("https://www.paperswithcode.com" + href)
        soup = BeautifulSoup(html, features='html.parser')
        div = soup.find('div', class_='paper-tasks')
        for span in div.find_all('span', class_="badge-primary"):
            task = span.find('span')
            if task is None:
                continue

            # task信息
            task_text = task.text.replace("\n", "")
            # task_text = pymysql.escape_string(task.replace("\n", ""))
            # util.db.ignore_insert('pwc_tasks', 'PWC_task', task_text)
            # task_id = util.db.get_id('pwc_tasks', 'PWC_task', task_text)
            tasks.append(task_text)
        if len(tasks) == 0:
            return
        task_str = ",".join(tasks)
        logger.info("更新" + arxiv_id + "\r\r" + task_str)
        Paper.update_SQL("pwc_tasks", task_str, arxiv_id)


if __name__ == '__main__':
    crawler_history()
