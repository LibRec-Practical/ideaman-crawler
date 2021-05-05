import datetime
import pymysql
import util
from util.db import *


class Paper:
    def __init__(self, published, user_id, version, link, title, updated, description, authors, tags, pdf_link):
        self.published = published
        self.user_id = user_id,
        self.version = version
        self.link = link
        self.title = title
        self.updated = updated
        self.description = description
        self.authors = authors
        self.tags = tags
        self.pdf_link = pdf_link
        self.add_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def generate_SQL(self):
        sql = "REPLACE INTO `paper`( `user_id`, `authors`, `type`,  `tags`,   `version`, `link`, `title`, `updated`, `published`, `pdf_link`, `description`,`add_time`) " \
              "VALUES (\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\" ,\"%s\",str_to_date('%s','%%Y-%%m-%%d %%H:%%i:%%S'));" % (
                  self.user_id[0], self.authors, "1", self.tags, self.version, self.link, self.title, str(self.updated),
                  str(self.published), self.pdf_link, self.description, self.add_time)
        return sql

    @staticmethod
    def update_SQL(col_name, col_value, arxiv_id):
        sql = "UPDATE paper SET `%s`='%s' WHERE user_id like '%%%s%%'" % (
            col_name, pymysql.escape_string(col_value), arxiv_id)
        # 插入到数据库
        # 执行sql语句
        util.db.cur.execute(sql)
        # 提交到数据库执行
        util.db.conn.commit()

