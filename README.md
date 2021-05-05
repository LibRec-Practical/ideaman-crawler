# 爬虫系统设计

## 系统架构图
![](https://uploader.shimo.im/f/4t6lHyi3nWhb3f93.png)

1. Arxiv等数据源数据经过py爬虫的爬取，将数据同时写入到国内主机的MySQL
2. 将PDF文件下载到海外主机的文件系统中，使用coscmd同步到腾讯云对象存储中。定期清理pdf与thumbs文件（TODO）
3. 使用Sqoop,实现mysql到hive数据仓库的数据小时级别同步。
4. 使用Mysqldump，备份mysql数据库，将其同步云Mysql（TODO）

## 使用方法
进入到海外主机

``` cd /home && ./daemon.sh```
