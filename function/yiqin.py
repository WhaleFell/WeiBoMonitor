'''
Author: whalefall
Date: 2021-05-31 15:37:14
LastEditTime: 2021-05-31 16:03:58
Description: http://wjj.foshan.gov.cn/zwgk/zwdt/yqxx/ 广东疫情情况
'''
import requests
from lxml import etree


class Yq(object):

    def __init__(self):
        self.url_index = "http://wjj.foshan.gov.cn/zwgk/zwdt/yqxx/"
        self.header = {
            "Referer": "http://wjj.foshan.gov.cn/zwgk/zwdt/yqxx/",
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36"
        }
        self.se = requests.session()

    def get_content_url(self):
        resp = self.se.get(self.url_index, headers=self.header).text
        html = etree.HTML(resp)
        # /html/body/div[4]/div[2]/div[1]/ul/li[1]/a
        try:
            url = html.xpath(
                "/html/body/div[4]/div[2]/div[1]/ul/li[1]/a/@href")[0]
        except Exception as e:
            print("获取最新疫情信息链接异常?", e)
            return False

        return url

    def index_content(self):
        url = self.get_content_url()

        if url:
            # print("scse", url)
            pass
        else:
            pass

        resp = self.se.get(url, headers=self.header).text
        print(resp)
        html = etree.HTML(resp)
        # /html/body/div[3]/div[2]/h3
        title = html.xpath(
            "/html/body/div[3]/div[2]/h3/text()")[0]

        # print(title)
        # /html/body/div[3]/div[2]/div[2]

        content = html.xpath(
            "/html/body/div[3]/div[2]/div[2]//text()")
        
        content=''.join(content).replace("\n", "").replace(" ", "")
        
        # print(content)
        return title,content

if __name__ == "__main__":
    Yq().index_content()
