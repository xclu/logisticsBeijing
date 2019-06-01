#-*-coding:UTF-8-*-
import json
import requests  #导入requests库，这是一个第三方库，把网页上的内容爬下来用的
import time
from pathlib import Path

lat_min=39.690549    #高德五环：116.207687，39.757934；40.02306，116.54971  六环：116.090554，39.690549；116.710465，40.176729
lon_min=116.090554
lat_max=40.176729
lon_max=116.710465
width=0.1  #网格宽度
ak='d8d056db50d88dea8ac3d9ac175861c8'
url_file='快递网点_url.txt'
job_file='快递网点.csv'

urlset=[]
# 小区宿舍        keywords=住宅小区$宿舍楼&type=住宅区
# 公交站       types=公交车站
# 地铁站        types=地铁站
# 超市、便利店  types=超市|便利店
# ATM           keywords=ATM
# 餐厅酒店      keywords=餐厅|酒店|甜品店|咖啡厅|茶座|酒吧
#写字楼          keywords=商务写字楼&tag=商业
# 快递物流         keywords=快递网点&types=物流速递

#住宅区        typess=住宅区  （120300）
#购物            types=购物服务（060000）
#金融保险        types=金融保险（160000）
# 住宿服务      types=住宿服务 (包括酒店和旅馆)
# 餐饮服务      types=餐饮服务

basic_url='http://restapi.amap.com/v3/place/polygon?polygon={}，{}|{},{}&keywords=快递网点&types=物流速递&output=json&key={}&offset=25&page={}'


def freight_list_parse():
    lat_1=lat_2= lat_min
    # 用生成器将结果写入csv文件
    while lat_2 <lat_max:
        lon_1 = lon_2 = lon_min
        lat_2=lat_1+width
        file_handle2 = save_data(filename=url_file)
        # generator init
        file_handle2.send(None)  # 首次使用，发送None
        while lon_2 < lon_max:
            lon_2=lon_1+width
            url = basic_url.format(lon_1, lat_2, lon_2, lat_1,ak, '0')
            html = requests.get(url)  # 获取网页信息
            data = html.json()  # 获取网页信息的json格式数据
            while int(data['count'])>=1000:
                lon_2=(lon_2+lon_1)/2
                url = basic_url.format(lon_1,lat_2,lon_2,lat_1,ak,'0')
                html = requests.get(url)  # 获取网页信息
                data = html.json()  # 获取网页信息的json格式数据
            if url not in urlset:
                if data['status']=='1':
                    page_count=int(int(data['count'])/25)+1
                    for i in range(0,page_count):
                        #page_num=str(i)
                        url = basic_url.format(lon_1, lat_2, lon_2, lat_1, ak,i)
                        if url not in urlset:
                            urlset.append(url)
                            print(url)
                            file_handle2.send('{}\n'.format(url))
                            goods_detail_parse(url)
            lon_1=lon_2
        lat_1=lat_2

        #time.sleep(2)

def goods_detail_parse(url):
        html=requests.get(url)#获取网页信息
        data=html.json()#获取网页信息的json格式数据
        file_handle = save_data(filename=job_file)
        # generator init
        file_handle.send(None)  # 首次使用，发送None
        for item in data['pois']:
            jname=item['name'].replace(',','')
            jtype=item['type'].replace(',','')
            try:
                jadd = item['address'].replace(',', '')
            except:
                jadd=0

            try:
                jpro = item['pname']
            except:
                jpro=0
            try:
                jcity=item['cityname']
            except:
                jcity =0
            try:
                jarea=item['adname']
            except:
                jarea = 0
            jlng,jlat=item['location'].split(',')
            j_str = '{},{},{},{},{},{},{},{}\n'.format(jname,jadd, jpro, jcity, jarea, jlat, jlng,jtype)
            print(j_str)
            file_handle.send('{}'.format(j_str))
        file_handle.close()



def save_data(*args, filename):
    freight_text = ''
    with open(filename, 'a', encoding='gb18030') as f:
        while True:
            freight_text = yield f.write(freight_text)  # 生成器
    f.close()
    return


if __name__ == '__main__':
    if Path(url_file).exists():
        with open(url_file, 'r', encoding='gb18030') as f:
            url_list = f.readlines()
            for url in url_list:
                # 将 urlset_file 文件的数据增加到 urlset集合中，用于后面去重
                urlset.append(url.replace('\n', ''))
            f.close()

    freight_list_parse()
    print('完成')