import pickle
import redis
import time

class BigDataRedis:
    #虚拟机上的redis
    redis_cli = redis.Redis(host='192.168.232.134', port=6379)

    def save_database(self, data, site):
        # 可以二进制存储
        try:
            s = pickle.dumps(data)
            # 同一坐标下的保存在同一个列表里
            self.redis_cli.rpush(site, s)
        except Exception as e:
            time.sleep(10)
            print('服务器已关，请重启')

        # 把data转换成能序列化的字典
        # step = {}
        # for key, value in data.items():
        #     one_step={}
        #     one_step.update(value)
        #     for key1, value1 in value.items():
        #         #foods里的值都是对象,需要转化成字典
        #         if key1 == 'foods':
        #             an_value = {}
        #             for key2, value2 in value1.items():
        #                 s = self.json_serialize(value2, key2)
        #                 an_value.update(s)
        #                 #所以的对象转化成字典后，赋值
        #             one_step[key1] = an_value
        #     #店铺已转换成字典类型，对id对应
        #     step[key]=one_step
        # #最终全转换成str
        # step = json.dumps(step, ensure_ascii=False)
        # with open('a.json', 'w', encoding='utf-8') as file:
        #     file.write(step)

    def json_serialize(self, obj, key):
        obj_dic = self.class2dic(obj, key)
        return obj_dic

    def class2dic(self, obj, org_key):
        obj_dic = obj.__dict__
        anobj_dic = {}
        for key in obj_dic.keys():
            value = obj_dic[key]
            obj_dic[key] = self.value2py_data(value)
        anobj_dic[org_key] = obj_dic['_values']
        return anobj_dic

    def value2py_data(self, value):
        if str(type(value)).__contains__('.'):
            # value 为自定义类
            value = self.class2dic(value)
        elif str(type(value)) == "<class 'list'>":
            # value 为列表
            for index in range(0, value.__len__()):
                value[index] = self.value2py_data(value[index])
        return value

