# CloudMusic163_Analysis
网易云音乐歌曲偏好分析
# 网易云音乐听歌偏好可视化分析

## 功能介绍

1.对最爱的歌手、歌曲按出现次数和播放次数排名并可视化
2.对歌单歌曲的风格标签按出现次数进行可视化
3.对相关评论区出现的关键词按出现次数进行可视化
4.歌曲推荐：根据偏好歌手、风格、标签作相关歌曲推荐。
5.同好用户群像分析：爬取同好歌曲评论区用户数据，分析人群特点。

## 环境要求

需要 NodeJS 12+ 环境

所需库：

```py
# music_analysis.py

import jieba
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import sys
import webbrowser
import datetime
```

```py
# write_data.py
from jinja2 import Environment, FileSystemLoader
```


## 安装

```shell
$ git clone git@github.com:Binaryify/NeteaseCloudMusicApi.git
$ cd NeteaseCloudMusicApi
$ npm install
```

或者

```shell
$ git clone https://github.com/Binaryify/NeteaseCloudMusicApi.git
$ cd NeteaseCloudMusicApi
$ npm install
```


## 运行

先在终端定位路径：

```shell
$ cd .\NeteaseCloudMusicApi\
```

再输入：

```shell
$ node app.js
```

若首次使用，可能会报错。请根据报错提示安装api所需框架。(如安装失败，请尝试不同版本)


在所需框架全部安装完成后，api即可成功运行。在 music_analysis.py 中输入要爬取的歌单id，运行即可。


## 快捷指令

在music_analysis.py末尾可输入以下指令：

```py
# 输出歌单曲风组成
freq_sum = 0
for i in style_preference.values():
    freq_sum += i
print("\n\n您的歌单的曲风组成是：")
for i in sorted(style_preference.items(), key=lambda item: item[1], reverse=True):
    print((i[0]+": ").ljust(25), round(int(i[1])/freq_sum*100, 1), "%", sep="")
```

```py
# 输出最爱的三个歌手
print('\n你最喜欢的歌手是：')
for i in artist_list:
    print((i[0]).ljust(25), '收藏数：', i[1], sep="")
```

```py
# 输出最爱的三首歌曲
print('\n你最喜欢的歌曲是：')
for i in play_count:
    print((i[0]).ljust(25), '播放次数', i[1], sep="")
```
