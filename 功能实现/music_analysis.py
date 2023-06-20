import jieba
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import sys
import webbrowser
import datetime
from write_data import html_generator
from pylab import mpl
mpl.rcParams["font.sans-serif"] = ["SimHei"]   # 设置显示中文字体
mpl.rcParams["axes.unicode_minus"] = False     # 设置正常显示符号


playlist_id = 8888888                          # 设置歌单ID

########################  检测歌单id是否有效，获取歌单的歌曲数量(无需调用API)  ########################

try:
    driver = webdriver.PhantomJS(executable_path=r"D:\anaconda\Lib\site-packages\selenium\webdriver\phantomjs\bin\phantomjs.exe")
    driver.get("https://music.163.com/#/playlist?id={}".format(playlist_id))
    driver.switch_to.frame("g_iframe")  # 检查可知，要爬取的框架的id为g_iframe
    html = driver.page_source
    songs_quantity = BeautifulSoup(html, "lxml").find(id="playlist-track-count").text
except FileNotFoundError:
    print('无法找到PhantomJS驱动器！请检查路径是否正确后重试。')
    sys.exit()
except AttributeError:
    print('歌单id无效！请检查id是否正确或歌单为隐私歌单后重试。')
    sys.exit()
except:
    print('未知错误发生，请检查程序运行环境后重试。')
    sys.exit()
else:
    print("开始爬取歌单数据...请耐心等待...")

if songs_quantity == 0:
    print("歌单歌曲数量为0！请更换歌单后尝试。")
    sys.exit()

###############################################################################################

# 获取用户ID
user_id = str(BeautifulSoup(requests.get('http://localhost:3000/playlist/detail?id={}'.format(playlist_id)).text, 'html.parser')).split('"userId":')[1].split(',"')[0]

# 用字典来统计歌单中的曲风、歌手及评论关键词频次
style_preference = dict()
artist_preference = dict()
keyword_freq = dict()

# 列表存储常用中文停用词，用来剔除评论无效词
stop_words_list = []
with open('text_files/stop_words.txt', encoding='utf-8') as f:
    for word in f:
        stop_words_list.append(word.rstrip())

# 存储中国城市编码
city_code = dict()
with open('text_files/city_code.txt', encoding='utf-8') as f:
    for line in f:
        city_code[line.split()[0]] = line.split()[1]

# 存储评论区用户城市数据、歌曲偏好
user_city = dict()
user_pref = dict()

##############################################################################

# 用于计算评论区用户的平均年龄
counter = 0
total_age = 0

for i in range(int(songs_quantity)//1000+1):
    response = requests.get('http://localhost:3000/playlist/track/all?id={}&limit=1000&offset={}'.format(playlist_id, 1000*i))
    html = BeautifulSoup(response.text, 'html.parser')
    # 获得存储歌单歌曲信息的字典
    songs = eval(
        str(html).split(',"privileges":')[0].replace("null", "[]").replace("true", "[]").replace("false", "[]").strip(
            "\n")[9:])

    # 打印歌单中的歌曲及其歌手、专辑和曲风
    for song in songs:
        # 获得该单曲的音乐百科HTML内容
        ency_html = BeautifulSoup(requests.get('http://localhost:3000/song/wiki/summary?id={}'.format(song['id'])).text, 'html.parser')

        # 获取歌曲ID
        song_id = song['id']

        # 获得该单曲的评论HTML内容并解析存储为字典
        comment_html = BeautifulSoup(requests.get('http://localhost:3000/comment/music?id={}&limit=5000'.format(song['id'])).text, 'html.parser')
        comment_dic = eval(str(comment_html).replace('true', '[]').replace('false', '[]').replace('null', '[]').rsplit('}', 1)[0]+'}')

        # 设置每首歌爬取的评论数量
        comment_num = 3

        # 使用jieba库的精准分词来提取关键词
        if 'hotComments' in comment_dic:
            for comment in comment_dic['hotComments']:

                comment_num -= 1
                if comment_num == -1:
                    break

                # 此行代码参考了https://blog.csdn.net/qq_39236499/article/details/121956002?spm=1001.2014.3001.5502
                seg_list = jieba.cut(comment['content'], cut_all=False)

                # 获取评论区用户个人资料、偏好
                user_profile = eval(
                    str(BeautifulSoup(requests.get('http://localhost:3000/user/detail?uid={}'.format(comment['user']['userId'])).text,
                                      'html.parser')).replace('true', '[]').replace('false', '[]').replace('null', '[]').rsplit('}', 1)[0]+'}')

                user_preference = eval(str(BeautifulSoup(requests.get('http://localhost:3000/user/playlist?uid={}'.format(comment['user']['userId'])).text,
                                              'html.parser')).replace('true', '[]').replace('false', '[]').replace('null', '[]').rsplit('}', 1)[0]+'}')

                if 'profile' in user_profile:
                    if user_profile['profile']['birthday'] > 0:

                        # 获得用户的年龄
                        age = str((datetime.datetime.now() - datetime.datetime.fromtimestamp(
                            user_profile['profile']['birthday'] / 1000)) / 365).split()[0]
                        if age.isdigit():
                            total_age += int(age)
                            counter += 1

                    # 获取用户的城市
                    if str(user_profile['profile']['city']) in city_code:
                        if city_code[str(user_profile['profile']['city'])] not in user_city:
                            user_city[city_code[str(user_profile['profile']['city'])]] = 1
                        else:
                            user_city[city_code[str(user_profile['profile']['city'])]] += 1

                # 获取用户曲风偏好
                for p in user_preference['playlist']:
                    for t in p['tags']:
                        if t not in user_pref:
                            user_pref[t] = 1
                        else:
                            user_pref[t] += 1

                # 过滤无效词
                for keyword in seg_list:
                    if keyword not in stop_words_list and keyword not in keyword_freq and len(keyword) != 0 and keyword.isspace() == False and len(keyword) != 1:
                        keyword_freq[keyword] = 1
                    elif keyword not in stop_words_list and len(keyword) != 0 and keyword.isspace() == False and len(keyword) != 1:
                        keyword_freq[keyword] += 1

        # 有些歌曲比较冷门，网易云没有给其定义曲风
        if "曲风" not in str(ency_html):
            print((song['name'] + " - " + song['ar'][0]['name'] + " 《" + song['al']['name'] + "》").ljust(95), "曲风：未知")
            continue

        # 切片操作解析HTML内容，获取曲风
        if ("推荐标签" not in str(ency_html)) and ("语种" not in str(ency_html)):
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"暂无乐谱\"")[0].split("\"title\":")[1:]
        elif "推荐标签" not in str(ency_html):
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"语种\"")[0].split("\"title\":")[1:]
        else:
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"推荐标签\"")[0].split("\"title\":")[1:]

        song_tag = []
        for tag_temp in song_tag_temp:
            song_tag.append(tag_temp.split('\"')[1])

        for tag in song_tag:
            if tag not in style_preference:
                style_preference[tag] = 1
            else:
                style_preference[tag] += 1

        # 存储歌手出现频次以及歌手ID
        if song['ar'][0]['name'] not in artist_preference:
            artist_preference[song['ar'][0]['name']] = [1, song['ar'][0]['id']]
        else:
            artist_preference[song['ar'][0]['name']][0] += 1

        print((song['name'] + " - " + song['ar'][0]['name'] + " 《" + song['al']['name'] + "》").ljust(95), "曲风：", str(song_tag).strip('[').strip(']'))

average_age = str(int(total_age/counter))
most_city = sorted(user_city.items(), key=lambda item: item[1], reverse=True)[0][0]
pref = ''

if len(user_pref) >= 2:
    pref = sorted(user_pref.items(), key=lambda item: item[1], reverse=True)[0][0]+'、'+sorted(user_pref.items(), key=lambda item: item[1], reverse=True)[1][0]
elif len(user_pref) == 1:
    for i in user_pref.keys():
        pref = i
else:
    pref = '未知'

##################### 获得歌曲播放数据 #####################

html = BeautifulSoup(requests.get('http://localhost:3000/user/record?uid={}&type=0'.format(user_id)).text, 'html.parser')
play_data = eval(str(html).replace('true', '[]').replace('false', '[]').replace('null', '[]').rsplit('}', 1)[0]+'}')
play_count = []
counter = 0

# 所有歌曲总播放量
total_play = 0
for song in play_data["allData"]:
    total_play += song['playCount']

# 存储播放量前三的歌曲专辑封面url
album_img = []
for song in play_data["allData"]:
    play_count.append((song['song']['name'].replace('&amp;', '&'), song['playCount']))
    album_img.append(song['song']['al']['picUrl'])
    counter += 1
    if counter == 3:
        break

artists_sum = 0
for i in artist_preference.values():
    artists_sum += i[0]

freq_sum = 0
for i in style_preference.values():
    freq_sum += i

##################### 根据歌手及曲风偏好推荐歌曲 #####################

print("正在分析听歌数据中...请耐心等待...")

# 每个key对应的value为一个列表，列表的第一个元素为歌曲id，第二个元素为歌曲偏好分
songs_recommendation = dict()

# 根据歌单中播放量较高的歌曲，（为方便以下称为“母歌曲”）的相似歌曲（称为“子歌曲”）进行推荐，推荐分数由四部分组成：
# 1. 基础分：由母歌曲的播放次数决定；播放次数越高，则基础分越高
# 2. 歌手偏好分：若该子歌曲的歌手为偏好歌手，则根据对该歌手的喜好程度（量化为收藏数）赋分；喜好程度越高，则歌手偏好分越高
# 3. 曲风偏好分：若该子歌曲的曲风为偏好曲风，则根据对该曲风的喜好程度（量化为收藏数）赋分；喜好程度越高，则曲风偏好分越高
# 4. 多次推荐分：若该子单曲有多个母单曲（即与歌单中多个单曲相似），则有相应的额外加分
# 四项分值相加组成最终的推荐分数，推荐分数高的单曲将被推荐。

for song in play_data["allData"]:

    # 基础分
    recommend_score = song['playCount']/total_play*5

    similar_songs = eval(
        str(BeautifulSoup(requests.get('http://localhost:3000/simi/song?id={}'.format(song['song']['id'])).text, 'lxml').text).replace(
            "null", "[]").replace("true", "[]").replace("false", "[]").strip("\n"))

    for s in similar_songs['songs']:

    # 歌手偏好分
        for a in s['artists']:
            if a['name'] in artist_preference:
                recommend_score += artist_preference[a['name']][0]/artists_sum * 7

    # 曲风偏好分

        # 获得该单曲的音乐百科HTML内容
        ency_html = BeautifulSoup(requests.get('http://localhost:3000/song/wiki/summary?id={}'.format(s['id'])).text,
                                  'html.parser')

        # 有些歌曲比较冷门，网易云没有给其定义曲风
        if "曲风" not in str(ency_html):
            continue

        # 切片操作解析HTML内容，获取曲风
        if ("推荐标签" not in str(ency_html)) and ("语种" not in str(ency_html)):
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"暂无乐谱\"")[0].split("\"title\":")[1:]
        elif "推荐标签" not in str(ency_html):
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"语种\"")[0].split("\"title\":")[1:]
        else:
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"推荐标签\"")[0].split("\"title\":")[1:]

        song_tag = []
        for tag_temp in song_tag_temp:
            song_tag.append(tag_temp.split('\"')[1])

        for i in song_tag:
            if i in style_preference.keys():
                recommend_score += style_preference[i]/freq_sum*10

    # 多次推荐分
        if s['name'] not in songs_recommendation:
            songs_recommendation[s['name']+'-'+s['artists'][0]['name']] = [s['id'], recommend_score]
        else:
            songs_recommendation[s['name']+'-'+s['artists'][0]['name']][1] += 1

print(sorted(songs_recommendation.items(), key=lambda item: item[1][1], reverse=True))
if len(sorted(songs_recommendation.items(), key=lambda item: item[1][1], reverse=True)) >= 10:
    recommended_songs=sorted(songs_recommendation.items(), key=lambda item: item[1][1], reverse=True)[:10]
else:
    recommended_songs = sorted(songs_recommendation.items(), key=lambda item: item[1][1], reverse=True)
"""
freq_sum = 0
for i in style_preference.values():
    freq_sum += i
print("\n\n您的歌单的曲风组成是：")
for i in sorted(style_preference.items(), key=lambda item: item[1], reverse=True):
    print((i[0]+": ").ljust(25), round(int(i[1])/freq_sum*100, 1), "%", sep="")"""

"""
# 对获得的频次字典进行排序
sorted_style_preference = sorted(style_preference.items(), key=lambda item: item[1], reverse=True)
sorted_artist_preference = sorted(artist_preference.items(), key=lambda item: item[1], reverse=True)
data1, data2 = np.array([x[1] for x in sorted_style_preference]), np.array([x[1] for x in sorted_artist_preference])
style_name, artist_name = np.array([x[0] for x in sorted_style_preference]), np.array([x[0] for x in sorted_artist_preference])

# 绘制饼图
plt.pie(data1[:10], labels=style_name[:10], autopct='%3.1f%%')
plt.show()
plt.pie(data2[:10], labels=artist_name[:10], autopct='%3.1f%%')
plt.show()"""

##################### 整理排序风格偏好数据 #####################


if len(style_preference) >= 5:
    tag_list = [(x[0], str((int(x[1])/freq_sum)*100).split('.')[0]+'.'+str((int(x[1])/freq_sum)*100).split('.')[1][:1]+'%') for x in sorted(style_preference.items(), key=lambda item: item[1], reverse=True)[:5]]
else:
    tag_list = [(x[0], str((int(x[1])/freq_sum)*100).split('.')[0]+'.'+str((int(x[1])/freq_sum)*100).split('.')[1][:1]+'%') for x in sorted(style_preference.items(), key=lambda item: item[1], reverse=True)]

##################### 整理排序歌手偏好数据 #####################

artist_img = []

if len(artist_preference) >= 3:
    # x[0]是歌手名字，x[1][0]是播放该歌手歌曲的次数
    artist_list = [(x[0], x[1][0]) for x in sorted(artist_preference.items(), key=lambda item: item[1][0], reverse=True)[:3]]

    # 存储最喜欢的三个歌手的图片url
    for artist in sorted(artist_preference.items(), key=lambda item: item[1][0], reverse=True)[:3]:
        artist_html = BeautifulSoup(requests.get('http://localhost:3000/artist/detail?id={}'.format(artist[1][1])).text, 'html.parser')
        artist_img.append(str(artist_html).split('"avatar":"')[1].split('",')[0])
else:
    artist_list = [(x[0], x[1][0]) for x in sorted(artist_preference.items(), key=lambda item: item[1][0], reverse=True)]
    for artist in sorted(artist_preference.items(), key=lambda item: item[1][0], reverse=True):
        artist_html = BeautifulSoup(requests.get('http://localhost:3000/artist/detail?id={}'.format(artist[1][1])).text, 'html.parser')
        artist_img.append(str(artist_html).split('"avatar":"')[1].split('",')[0])

##################### 整理排序评论区关键词数据 #####################

comment_list = [x for x in sorted(keyword_freq.items(), key=lambda item: item[1], reverse=True)[:5]]

"""
for artist in artist_preference.values():

    driver.get('https://music.163.com/#/artist/album?id={}'.format(artist[1]))
    driver.switch_to.frame('g_iframe')
    html = driver.page_source
    similar_artists = BeautifulSoup(html, "lxml").find(id="rec-similar-artists").find_all('a')[::2]
    similar_artists_id = []

    for i in similar_artists:
        similar_artists_id.append(str(i).split('"/artist?id=')[1].split('"')[0])

    similar_songs_id = []
    for i in similar_artists_id:
        temp = eval(
            str(BeautifulSoup(requests.get('http://localhost:3000/artists?id={}'.format(i)).text, 'lxml').text).replace(
                "null", "[]").replace("true", "[]").replace("false", "[]").strip("\n"))
        for j in temp['hotSongs']:
            similar_songs_id.append(j['id'])

    print(1)
    recommend_score = artist[0]/freq_sum2 * 5
    for song in similar_songs_id:
        # 获得该单曲的音乐百科HTML内容
        ency_html = BeautifulSoup(requests.get('http://localhost:3000/song/wiki/summary?id={}'.format(song)).text,
                                  'html.parser')

        # 有些歌曲比较冷门，网易云没有给其定义曲风
        if "曲风" not in str(ency_html):
            continue

        # 切片操作解析HTML内容，获取曲风
        if ("推荐标签" not in str(ency_html)) and ("语种" not in str(ency_html)):
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"暂无乐谱\"")[0].split("\"title\":")[1:]
        elif "推荐标签" not in str(ency_html):
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"语种\"")[0].split("\"title\":")[1:]
        else:
            song_tag_temp = str(ency_html).split("曲风")[1].split("\"title\":\"推荐标签\"")[0].split("\"title\":")[1:]

        song_tag = []
        for tag_temp in song_tag_temp:
            song_tag.append(tag_temp.split('\"')[1])

        for i in song_tag:
            if i in style_preference.keys():
                recommend_score += style_preference[i]/freq_sum*10

        if song not in songs_recommendation:
            songs_recommendation[song] = recommend_score
        else:
            songs_recommendation[song] += 1"""


# 生成最终结果html
html_generator(tag_list, artist_list, artist_img, comment_list, play_count, album_img, recommended_songs, average_age, most_city, pref)

"""print('\n')
print('评论区关键词'.ljust(17), '出现次数')
for i in sorted(keyword_freq.items(), key=lambda item: item[1], reverse=True)[:15]:
    print(i[0].ljust(20), i[1])"""

print("爬取完成！正在跳转至结果网页...")
webbrowser.open('output.html')

