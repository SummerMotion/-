import logging

logging.basicConfig(filename='error.log',format='%(asctime)s,%(msecs)d %(levelname)-8s %(name)s [%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S')
logging.getLogger().setLevel(logging.DEBUG)
logger_store = logging.getLogger("坐标")
logger_food=logging.getLogger("店铺")
logger_city=logging.getLogger("判断城市")


