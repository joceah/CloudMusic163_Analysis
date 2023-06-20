from jinja2 import Environment, FileSystemLoader

# 参考学习了文章https://blog.csdn.net/xuezhangjun0121/article/details/128497276


def html_generator(tag_list, artist_list, artist_img, comment_list, play_count, album_img, recommended_songs, age, city, pref):
    # 创建Jinja2环境
    env = Environment(loader=FileSystemLoader('.'))

    # 定义数据
    data = dict()
    data['age'] = age
    data['city'] = city
    data['pref'] = pref
    data['play_count'] = play_count
    data['album_img'] = album_img
    data['rec_songs'] = recommended_songs
    index = 1
    for i in tag_list:
        data['tag{}'.format(index)] = i
        index += 1

    index = 1
    for i in artist_list:
        data['artist{}'.format(index)] = i
        index += 1

    index = 1
    for i in comment_list:
        data['comment{}'.format(index)] = i
        index += 1

    index = 1
    for i in artist_img:
        data['img{}'.format(index)] = i
        index += 1
    # 加载HTML模板
    template = env.get_template('new_template.html')

    # 渲染模板并传递数据
    output = template.render(data=data)

    # 将渲染后的内容保存到HTML文件
    with open('output.html', 'w', encoding='utf-8') as file:
        file.write(output)
