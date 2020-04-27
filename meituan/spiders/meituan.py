import requests
import json
import time
from selenuim_chrome.selenuim_chrome import UtilSelenuim
from parse_font.parse_font import ParseFont
import re
import traceback
from database.redis import BigDataRedis
import database.logger as loggers


class meituan_spider:
    big_data = []
    headers = {

        'Accept': 'application/json',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36'
    }
    site = ''
    # 使用模拟获取cookie
    utilSelenuim = UtilSelenuim()
    # 解析文件
    parseFont = ParseFont()
    # 保存到redis
    bigdata_redis = BigDataRedis()
    #保存所有店铺id
    shop_id=set()
    # cookie
    # cookies = dict()
    cookies = {}
    # 代理ip
    ip = ''
    # 计数
    count = 0

    def get_cookie(self):
        cookies_ip = self.utilSelenuim.get_cookie()
        self.cookies = cookies_ip[0]
        print(self.cookies)
        self.ip = cookies_ip[1]

    def main(self):
        url = 'http://i.waimai.meituan.com/openh5/homepage/poilist?_='

        # 得到cookies和ip
        self.get_cookie()

        # 深圳处于东经113°46'～114°37'，北纬22°27'～22°52'。东经转化为度为：113.766666~114.616666,北纬转化成度为：22.45~22.866666
        # 东莞处于东经113°31′-114°15′,北纬22°39′-23°09 东经转为度为：113.516666~114.25,北纬转化为度为：22.65~23.15
        # 2分约等于3.7千米左右
        #114.191666 22.658333
        interval = 0.033333
        latitude = 22.65
        try:
            #深圳12
            #东莞15
            for i in range(15):
                longitude = 113.516666
                # 深圳大约可以增加25次左右
                #东莞大约可以增加22次左右
                for j in range(22):
                    print(f'{latitude}和{longitude}')
                    # 美团经纬度全是正整数
                    lat = round(latitude * 1000000)
                    long = round(longitude * 1000000)
                    self.site = f'{long},{lat}'
                    self.get_shopid(url, lat, long)
                    longitude = longitude + interval
                latitude = latitude + interval
        except Exception as e:
            print(e)
            traceback.print_exc()
            # 记录
            # loggers.logger_city.error(e)

    def get_shopid(self, url, lat, long):
        # 获取cookies
        poiHasNextPage = True
        # 判断
        mark = 1
        # post的数据
        form_data = {
            # 根据startIndex相当于下拉加载
            "startIndex": "{}".format(-1),
            "wm_actual_latitude": "{}".format(lat),
            "wm_actual_longitude": "{}".format(long),
        }
        while poiHasNextPage:
            try:
                self.big_data=[]
                # 每个网页后面跟着时间戳
                times = round(time.time() * 1000)
                url_time = url + str(time)
                form_data['startIndex'] = str(int(form_data['startIndex']) + 1)
                resp = requests.post(url_time, data=form_data, headers=self.headers, cookies=self.cookies,
                                     proxies=self.ip)
                # resp = requests.post(url_time, data=form_data, headers=self.headers, cookies=self.cookies)
                resp.encoding = resp.apparent_encoding
                text = json.loads(resp.text)
                if text['msg'] != '成功':
                    break
                print(f"{lat}和{long}的{form_data['startIndex']}成功")
                # 判断是否还有下一次加载
                poiHasNextPage = text['data']['poiHasNextPage']
                # 得到各家店铺的列表
                text = text['data']['shopList']
                # 保存各家店铺的id
                id_list = list()
                # 各家地址
                shop_address = list()
                # 各家评分
                shop_score = list()
                # 获取到各家的id、地址和评分
                for i in range(len(text)):
                    #排除相同的店铺
                    if text[i]['mtWmPoiId'] not in self.shop_id:
                        self.shop_id.add(text[i]['mtWmPoiId'])
                        id_list.append(text[i]['mtWmPoiId'])
                        shop_address.append(text[i]['address'])
                        shop_score.append(text[i]['wmPoiScore'])
                # 通过id得到店铺的数据
                self.get_shop_by_id(id_list, shop_address, shop_score)
                # 存储到数据库
                self.bigdata_redis.save_database(self.big_data, self.site)
            except Exception as e:
                traceback.print_exc()
                s = str(e)[-22:-6]
                if s == '由于目标计算机积极拒绝，无法连接':
                    self.get_cookie()
                elif mark == 2:  # 2次不管什么原因换ip
                    self.get_cookie()
                    mark = 1
                else:
                    mark = mark + 1

                form_data['startIndex'] = str(int(form_data['startIndex']) - 1)

    def get_shop_by_id(self, id_list, shop_address, shop_score):
        # 店铺地址
        url = 'http://i.waimai.meituan.com/openh5/poi/food'
        # post数据
        data = {
            "geoType": 2,
            "mtWmPoiId": '',
            "dpShopId": -1,
            "source": "shoplist",
            "platform": 3,
            "partner": 4,
            "riskLevel": 71,
            "optimusCode": 10,
        }
        for i in range(len(id_list)):
            # 根据id确定哪家店铺
            data['mtWmPoiId'] = id_list[i]
            shop = dict()
            mark = True
            number = 0
            while mark:
                try:
                    mark = False
                    # 获取到店铺的数据
                    time.sleep(0.5)
                    resp = requests.post(url, data=data, cookies=self.cookies, proxies=self.ip)
                    # resp = requests.post(url, data=data, cookies=self.cookies)
                    # resp.encoding = resp.apparent_encoding
                    # 转化为字典
                    text = json.loads(resp.text)
                    if text['msg'] != '成功':
                        break
                    # 获取店铺信息
                    shop = self.get_shop_info(text['data'])
                    # 店铺id
                    shop['mtWmPoiId'] = id_list[i]
                    # 店铺地址
                    shop['address'] = shop_address[i]
                    # 评分
                    shop['score'] = shop_score[i]
                    # 保存
                    self.big_data.append(shop)
                except Exception as e:
                    traceback.print_exc()
                    base_10=str(e).split(":")
                    if base_10[0]=='invalid literal for int() with base 10':
                        print("解析一半，重析获取")
                        self.get_cookie()
                        mark = True
                        continue
                    if str(e) == 'spuList':
                        break
                    if str(e) == '解析不了，重新获取' and number != 3:
                        number = number + 1
                        mark = True
                    else:
                        print("error: "+str(e)+str(number))
                        number=number+1
                        if number>=2:
                            break
                        self.get_cookie()
                        mark = True

    def get_shop_info(self, data):
        # # 得到解密字体所需要的文件路径
        # url_woff = self.utilSelenuim.get_woff(data['mtWmPoiId'])
        # # 下载解密文件且得到路径
        # path_name = self.down_woff(url_woff)
        # if path_name == None:
        #     return;
        #每周会变化
        path_names = ['3c2e9aa4.woff','a4b11683.woff','61b89466.woff','4e4c232c.woff','3c2e9aa4.woff','d1b1c800.woff']
        for path_name in path_names:
            path_name = 'E:\\woff\\' + path_name
            # 映射字典
            parse_dict = self.parseFont.parseWoff(path_name)
            shopInfo = data['shopInfo']
            shop = dict()
            # 配送时间
            shop['deliverTime'] = self.parseFont.parseString(shopInfo['deliveryTimeDecoded'], parse_dict)
            if shop['deliverTime'] == shopInfo['deliveryTimeDecoded']:
                if path_name != 'E:\\woff\\d1b1c800.woff':
                    continue
                else:
                    raise Exception('解析不了，重新获取')
            #防止只有一部分解析成功
            int(shop['deliverTime'])
            print("映射成功")
            # 店名
            shop['shopName'] = shopInfo['shopName']
            # 配送费
            shop['deliveryFee'] = shopInfo['deliveryFee']
            # 起送费用
            shop['minFee'] = shopInfo['minFee']
            # 月售,先设为0
            shop['monthSale'] = 0
            # 满减活动
            shop['activity'] = data['shoppingCart']['promptText']
            # 食品
            shop['foods'] = self.get_shop_food(data['categoryList'], parse_dict, shop)
            return shop

    def get_shop_food(self, categoryList, parse_dict, shop):
        shop_foods = []
        monthsale = 0
        for category_tag in categoryList:
            spuList = category_tag['spuList']
            if type(spuList) is list:
                for food in spuList:
                    shop_food = {}
                    # 食物名字
                    shop_food['spuName'] = food['spuName']
                    # 食物id
                    shop_food['spuId'] = food['spuId']
                    # 销售量
                    shop_food['sale'] = self.parseFont.parseString(food['saleVolumeDecoded'], parse_dict)
                    if shop_food['sale'] != food['saleVolumeDecoded']:
                        # 计算总销售量
                        monthsale = monthsale + int(shop_food['sale'])
                    # 原始价格
                    shop_food['originPrice'] = food['originPrice']
                    # 最终价格
                    shop_food['currentPrice'] = food['currentPrice']
                    # 计算满减优惠
                    if shop_food['originPrice'] == shop_food['currentPrice']:
                        shop_food['currentPrice'] = self.calculate_price(shop_food['originPrice'], shop['activity'])
                    shop_foods.append(shop_food)
        # 获取总销售额
        shop['monthSale'] = monthsale
        return shop_foods

    def calculate_price(self, price, description):
        res = re.compile('满\d+元减\d+元')
        # 判断是否是满减活动，不是则返回
        if not res.search(description):
            return price
        else:
            price = float(price)
            result = re.compile('\d+')
            # 根据正则取出所有的数字
            array = result.findall(description)
            # 计算个数 [28,15,30,28]
            length = len(array)
            for i in range(0, length, 2):
                # 与价格进行比较，超出则减，从最大的优惠算起 例 price>=30 大于则减price=price-18
                if price >= float(array[length - i - 2]):
                    price = round(price - float(array[length - i - 1]), 2)
                    break;
            return price

    def down_woff(self, url):
        try:
            # 获取到woff文件
            # resp = requests.get(url, headers=self.headers, proxies=self.ip)
            resp = requests.get(url, headers=self.headers)
            strs = url.split('/')
            # 取文件名字
            path_name = 'E:\\woff\\' + strs[len(strs) - 1]
            # 把数据保存起来
            with open(path_name, 'wb') as file:
                file.write(resp.content)
            return path_name
        except Exception as e:
            self.get_cookie()
            self.count = self.count + 1
            if self.count != 2:
                return self.down_woff(url)
            loggers.logger_city.error(e)
        return None
