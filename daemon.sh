nohup python3 /home/ideaman_crawler/arxiv.py >/home/ideaman_crawler/download_his_log.log 2>&1 &
nohup coscmd upload -rs /home/ideaman-data/thumbs thumbs/ >/home/ideaman-data/coscmd.log 2>&1 &

