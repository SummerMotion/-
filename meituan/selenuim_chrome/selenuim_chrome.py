from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import re
import requests
import json
import time
class UtilSelenuim:
    mark=0
    count=0
    driver=''
    def get_driver(self):
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')  # 谷歌文档提到需要加上这个属性来规避bug
        chrome_options.add_argument('--hide-scrollbars')  # 隐藏滚动条, 应对一些特殊页面
        chrome_options.add_argument('blink-settings=imagesEnabled=false')  # 不加载图片, 提升速度
        chrome_options.add_argument('--headless')  # 浏览器不提供可视化页面. linux下如果系统不支持可视化不加这条会启动失败
        chrome_options.binary_location = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"  # 手动指定使用的浏览器位置

        #购买的ip获取地址
        p_url = 'xxxx'
        r = requests.get(p_url)
        html = json.loads(r.text)
        a = html['RESULT']['wanIp']
        b = html['RESULT']['proxyport']
        val = '--proxy-server=http://' + str(a) + ':' + str(b)
        val2 = 'http://' + str(a) + ':' + str(b)
        p = {'http': val2}
        print('获取IP：', p)
        chrome_options.add_argument(val)
        driver = webdriver.Chrome(chrome_options=chrome_options)  # executable_path驱动路径
        return (driver,p)
    def get_woff(self,id):
        url='http://h5.waimai.meituan.com/waimai/mindex/menu?mtShopId='+id
        #模拟打开页面
        woff=['','','']
        try:
            if self.mark==0:
                driver_ip=self.get_driver()
                self.driver=driver_ip[0]
                self.mark=1
            self.driver.get(url)
            time.sleep(0.5)
            #得到字体加密的正则表达式
            res = re.compile('<style type="text/css">@font-face{font-family: "mtsi-font";.*}')
            #得到字体加密的style
            result = res.search(self.driver.page_source)
            #得到.woff的正则表达式
            res = re.compile('//s3plus.meituan.net/v1/.*.woff')
            #得到style
            style = result.group()
            result = res.search(style)
            woff = result.group()
            woff = woff.split('url("')
            self.driver.close()
        except Exception as e:
            self.driver.quit()
            self.mark=0
            #重新获取
            self.count=self.count+1
            #避免陷入死循环
            if self.count!=2:
                return self.get_woff(id)
        self.count=0
        #例：//s3plus.meituan.net/v1/mss_73a511b8f91f43d0bdae92584ea6330b/font/6fb4b9b9.woff
        return 'http:'+woff[2]

    def get_cookie(self):
        mark = 0
        while mark == 0:
            driver_ip=self.get_driver()
            driver=driver_ip[0]
            driver.set_page_load_timeout(8)  # 设置超时
            driver.set_script_timeout(8)
            url = 'http://h5.waimai.meituan.com/waimai/mindex/home'  # 外卖页面
            try:
                now = time.time()
                driver.get(url)
                tt = time.time() - now
                print(tt)
                time.sleep(0.5)
                # ip速度测试，打开时间大于3S的NG
                if tt < 3:
                    c = driver.get_cookies()
                    driver.quit()
                    mark = 1
                    cookies = {}
                    for cookie in c:
                        cookies[cookie['name']] = cookie['value']
                    return (cookies,driver_ip[1])
                else:
                    print('超时')
                    driver.quit()
                    time.sleep(15)
            except:
                driver.quit()
                pass
# woff_set=set()
# u=UtilSelenuim()
# for i in range(20):
#     d = u.get_woff('1094981639681616')
#     if d not in woff_set:
#         woff_set.add(d)
#     d = u.get_woff('951860444496715')
#     if d not in woff_set:
#         woff_set.add(d)
#     d=u.get_woff('923346156615814')
#     if d not in woff_set:
#         woff_set.add(d)
# print(woff_set)
# u.get_cookie()