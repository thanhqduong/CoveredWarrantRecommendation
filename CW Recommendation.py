import math
from scipy.stats import norm
import scipy.stats as stats
import datetime
import statistics
from selenium import webdriver
import pandas as pd
import numpy as np 
import pytz
from Newton_Raphson import *
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager

driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

driver.get('https://24hmoney.vn/covered-warrant/')
d = driver.find_elements('class name', 'app-link') 
d = list(set(d))
count = 0
links = [e.get_attribute('href') for e in d]
links = list(set(links))

totalret = []
d = driver.find_elements('class name', 'app-link')
d = list(set(d))
count = 0
for link in links:
    if not link.startswith('https://24hmoney.vn/covered-warrant/'):
        continue
    # print(link)
    name = link.split('/')[-1]
    driver.get(link)
    dd = driver.find_elements('class name', 'content')
    ddd = dd[1]
    s = ddd.text
    idx = s.index('Khối lượng Niêm yết')
    s = s[:idx]
    s = s.split('\n')
    find = ['CK cơ sở', 'Tổ chức phát hành CW', 'Thời hạn', 'Ngày phát hành', 'Ngày đáo hạn', 'Giá phát hành', 'Giá thực hiện']
    tl = 'Tỷ lệ chuyển đổi'
    if 'Tỷ lệ chuyển điểu chỉnh' in s:
        tl = 'Tỷ lệ chuyển điểu chỉnh'
    find.append(tl)
    ret = [name]
    for f in find:
        idx = s.index(f) + 1
        ret.append(s[idx])
    ret[2] = ret[2].split()[-1][1:-1]
    ret[3] = float(ret[3].split()[0])/12
    ret[4] = datetime.datetime.strptime(ret[4],'%d/%m/%Y')
    ret[5] = datetime.datetime.strptime(ret[5],'%d/%m/%Y')
    ret[6] = float(ret[6]) * 1000
    ret[7] = float(ret[7]) * 1000
    ret[8] = float( ret[8].split(':')[0] )
    totalret.append(ret)

or_data = pd.DataFrame(totalret, columns = ['Name', 'CKCS', 'CTCK', 'Time', 'From', 'To', 'Call', 'Strike', 'ConvertRate'])

driver.get('https://24hmoney.vn/covered-warrant/')
d = driver.find_element('class name', 'list-related-covered-warrant') 

ldata = d.text.split('\n')

jump = 4
idx = 0
total_data = []
while idx < len(ldata[9:]):
    row = ldata[9:][idx:idx + jump]
    ret = row[:3]
    rest = row[3].split()
    ret.extend(rest)
    idx += jump
    total_data.append(ret)

df = pd.DataFrame(total_data, columns = ['Mã', 'Giá', 'Tăng/ Giảm', 'Volume', 'Giá CK cơ sở', 'S-X', 'Hòa vốn', 'Tổ chức phát hành', 'Số ngày đến hạn'])

def to_num_vol(v):
    v = v.replace(',', '')
    if v == '--':
        return 0
    return int(v)
df['Volume'] = [to_num_vol(x) for x in df['Volume']]

df_later = df[['Mã', 'Volume']]

median_vol = max(statistics.median(list(df['Volume'])), 1000)
mean_vol = max(1/4 * sum(df['Volume']) / len(df), 1000)
vol_benchmark = min(median_vol, mean_vol)
df = df[df['Volume'] >= vol_benchmark]
df = df.drop('Volume', axis = 1)

temp = df[['Mã', 'Giá', 'Giá CK cơ sở',  'Số ngày đến hạn']].merge(or_data[['Name', 'CKCS', 'CTCK', 'ConvertRate', 'Strike']], left_on = 'Mã', right_on = 'Name' )

total = []
for index, row in temp.iterrows():
    C = float(row['Giá']) * 1000
    S = float(row['Giá CK cơ sở']) * 1000
    X = float(row['Strike'])
    T = int(row['Số ngày đến hạn']) / 365
    ratio = float(row['ConvertRate'])
    volatility = find_volatility(C, S, X, T, ratio)
    # print((C, S, X, T, ratio))
    ret = [ row['Name'], row['CKCS'], row['CTCK'], C, S, X, ratio, volatility ]
    total.append(ret)

tz = pytz.timezone("Asia/Ho_Chi_Minh") 
timeInVN = datetime.datetime.now(tz)
currentTimeInVN = timeInVN.strftime("%Y-%m-%d %H:%M")

check = pd.DataFrame(total, columns = ['Name', 'CKCS', 'CTCK', 'Call Price', 'Stock', 'Strike', 'ConversionRatio (x:1)', 'Volatility'])

t = check.merge(temp[['Name', 'Số ngày đến hạn']], on = 'Name')

t['days'] = [int(x) for x in t['Số ngày đến hạn']]
t = t.drop('Số ngày đến hạn', axis = 1)
t = t[['Name', 'CKCS', 'CTCK', 'Call Price', 'Stock', 'Strike', 'ConversionRatio (x:1)', 'days', 'Volatility']]
t.columns = ['Name', 'CKCS', 'CTCK', 'CurrentCallPrice', 'Stock', 'Strike', 'ConversionRatio (x:1)', 'DaysTillExpiry', 'Volatility']

ret = []
for index, row in t.iterrows():
    ret.append(black_scholes_call_option(row['Stock'], row['Strike'], row['DaysTillExpiry'] / 365, 0.02, row['Volatility']))

t['EstPrice'] = ret
t['EstCPrice'] = t['EstPrice'] / t['ConversionRatio (x:1)']
t['HoaVon'] = t['CurrentCallPrice'] * t['ConversionRatio (x:1)'] + t['Strike']

def check_delta_price(a,b):
    return abs(a-b)/a < 0.0025

t['Check'] = [check_delta_price(a,b) for a,b in zip(t['CurrentCallPrice'], t['EstCPrice'])]
t = t[t['Check'] == True]
t = t.drop('Check', axis = 1)

def z_score(cw_name):
    v = sum(t[t['Name'] == cw_name]['Volatility'])
    underlying = cw_name[1:4]
    l = list(t[t['CKCS'] == underlying]['Volatility'])
    idx = l.index(v)
    return stats.zscore(l)[idx]

t['z_score'] = [z_score(x) for x in t['Name']]
t = t.sort_values(['z_score', 'DaysTillExpiry'], ascending = [True, False])
t = t.merge(df_later, how = 'left', left_on = 'Name', right_on = 'Mã').drop('Mã', axis = 1)

l = list(t.head(3)['Name'])
print('Current time: '+ currentTimeInVN)
print('My recommendation: ' + ', '.join(l))