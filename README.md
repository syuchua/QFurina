# MY_QBOT - QQ机器人项目

欢迎来到MY_QBOT项目！这是一个基于Python的QQ机器人后端服务，提供了一系列自动化和交互功能。

## MY_QBOT都能做什么
  1. AI聊天，角色扮演
  2. 群聊
  3. 从pixiv获取并发送涩图()
  4. 指定关键词发送或者随机涩图
  5. AI绘画
  6. AI生成语音
  7. 天气查询
  8. 联网搜索
  9. 定时开关机

## 当前支持的消息平台：
目前仅在Windows端Llonebot上测试过，理论上所有支持oneonev11协议的消息平台都可以用，不过http对接配置可能要麻烦一点

## 部署指南
  - ### docker部署(还未测试过)
    先运行如下命令建立相关目录与文件：
    ```
    mkdir bot && cd bot
    mkdir config && cd config
    vim config.json
    ```
    打开config.json文件，按i进入输入模式，按需填入以下配置：
      ```
      {
        "openai_api_key": "",#你的apikey
        "model": "gpt-3.5-turbo",#默认3.5
        "nicknames": [""],#当消息中出现nickname时自动触发对话
        "self_id": 123,#修改为机器人QQ号
        "admin_id": 456,#修改为管理员QQ号
        "block_id": 789, #修改为要屏蔽的QQ号
        "report_secret": "123456",#http上报密钥，见下文Llonebot配置，如果选择反向ws连接则可不填。
        "connection_type": 连接类型，可选`http`和`ws_reverse`，具体见下文。
        "proxy_api_base": "https://api.openai.com/v1",#api请求地址,默认为官方
        "system_message": {
            "character": ""#机器人人设
        },
        "reply_probability": 0.5 #群聊中没有nickname时触发主动聊天的概率
        "r18": 0为关闭r18，1开启r18，2为随机发送(慎选)
        "audio_save_path": 语音文件保存位置
        "voice_service_url": 语音接口地址
        "cha_name"：语音接口指定角色
      }
      ```
    填完后按下esc退出输入，再输入`:wq`回车保存
    回到上一级目录
    ```
    vim docker-compose.yaml
    ```
    新建docker-compose.yaml文件，将项目内的复制过去，或者直接下载项目内的，copy到服务器上，执行
    ```
    docker-compose up -d
    ```
    即可，记得放行3001端口，用于跟QQ通信
    
  - ### 本地部署
    
    - **安装Python环境**：确保您的系统上安装了Python 3.11或更高版本(低版本还没有测试过)。
    - **克隆本项目**
    ```
    git clone -b dev https://github.com/syuchua/MY_QBOT.git
    ```

    - **进入项目目录**
    ```
    cd MY_QBOT
    ```
    - **创建虚拟环境**（可选）：
    
    ```
    python -m venv venv
    source venv/bin/activate  # 对于Windows使用 venv\Scripts\activate
    ```
    - **安装依赖**：
    ```
    pip install -r requirements.txt
    ```

  ## 配置

  在`config.json`文件中配置机器人的设置，包括但不限于：
  - `openai_api_key`: 你的openai_api_key
  - `model`: 使用的模型，默认为gpt-3.5-turbo
  - `self_id`：机器人的QQ号。
  - `admin_id`：管理员的QQ号。
  - `block_id`: 要屏蔽的QQ号。
  - `nicknames`：机器人的昵称列表。
  - `system_message`：系统消息配置，最重要的是`character`，相当于机器人的人格。
  - `connection_type`: 连接类型，可选http或ws_reverse
  - `report_secret`: http事件上传密钥。
  - `enable_time`: 每天自动开始回复时间，如08:00
  - `disable_time`: 自动停止回复时间如02:00
  - `proxy_api_base`: openai_api_key请求地址，默认为https://api.openai.com/v1
  - `reply_probability`: 当收到的消息中没有nickname时的回复频率，1为每一条都回复，0为仅回复带有nickname的消息，默认0.5
  - `r18`: 0为关闭r18，1开启r18，2为随机发送(慎选)
  - `audio_save_path`: 语音文件保存位置
  - `voice_service_url`: 语音接口地址
  - `cha_name`：语音接口指定角色


 - ### 部署Llonebot:
    [建议查看官方文档](https://llonebot.github.io/zh-CN/)

   
  ### 一个api中转站点(如果有需求的话可以看看，支持各种主流模型)
  [点我跳转](https://ngedlktfticp.cloud.sealos.io/register?aff=DEAp)
  
  ### 个人搭建的claude-3.5sonnet中转站：
  [claude3.5中转](https://gcp.yuchu.me)

  ### 配置Llonebot: 如图
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240615234833.png)

  若使用反向ws连接则仅需这样配置：
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240720181142.png)

## 数据库

本项目使用 MongoDB 作为数据库。MongoDB 是一个文档导向的 NoSQL 数据库，具有高性能、高可用性和易扩展性的特点。

### MongoDB vs SQLite

虽然 SQLite 是一个轻量级的选择，但 MongoDB 在以下方面具有优势：

1. 可扩展性：MongoDB 可以轻松处理大量数据和高并发访问。
2. 灵活性：MongoDB 的文档模型允许存储复杂的数据结构，无需预定义模式。
3. 查询能力：MongoDB 提供强大的查询语言，支持复杂的数据分析。
4. 分布式：MongoDB 支持分片，可以在多台服务器上分布数据。

### 安装和配置 MongoDB

1. 下载 MongoDB：
   访问 [MongoDB 下载页面](https://www.mongodb.com/try/download/community) 并下载适合你操作系统的版本。

2. 安装 MongoDB：
   按照官方文档的指引进行安装。

3. 启动 MongoDB 服务：
   - Windows: 
     进入 MongoDB 安装目录，运行以下命令（请根据实际情况修改路径）：
     ```
     mongod --dbpath D:\MongoDB\data --logpath D:\MongoDB\log\mongodb.log --logappend
     ```
     注意：请确保指定的数据和日志目录已经存在。
   - macOS/Linux: 运行 `sudo systemctl start mongod`

4. 注意：确保在启动机器人之前，MongoDB 服务已经正常运行。

### 数据库操作

本项目使用 `app/database.py` 文件管理数据库操作。主要功能包括：

- 存储用户信息
- 记录聊天历史
- 管理会话上下文

数据库的具体配置和操作已在 `database.py` 中实现，无需额外配置。


## 运行机器人

在终端中执行以下命令启动机器人：
```
python main.py
```

## 食用方法：
  - 直接对话即可
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616001408.png)
  - 发送`发一张`，`来一张`+关键词即可自定义发送涩图，比方说`发一张卡芙卡`
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616001141.png)
  - 发送`来份涩图`，`来份色图`，`再来一张` 即可发送随机涩图
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616001208.png)
  - 发送`画一张`，`生成一张` 即可发送AI绘画（目前默认使用dalle进行AI绘画，若需使用AI绘画功能，模型必须为gpt系列）
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616001253.png)
  - 发送`语音说`，``语音回复` +`要用语音说的话`让机器人发送语音，或者再提示词里提示机器人通过把`#voice`标签放在回复的开头，实现更生动地语音回复。
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240720233521.png)
  - 发送`点歌`+歌曲名进行点歌，支持模糊匹配。
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240805154117.png)
  - R-18?
  该接口的涩图数量足有十几万，其中r18占27.8%，建议公共场合尽量设置为0，2的话，还是不要太相信自己的运气了(问就是惨痛的教训)
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616002550.png)

## 本地语音整合包

[GPT-SoVITS-Inference](https://cloud.yuchu.me/s/J2um)

## AI翻唱歌曲压缩包
[AI翻唱.zip](https://cloud.yuchu.me/s/KRCv)
解压后放到data/music目录下即可

## 命令功能

机器人支持以下命令：

- `/help`：显示帮助信息。
- `/reset`：重置当前会话。
- `/character`：输出`config.json`中的`character`值，也即当前的人设。
- `/history`: 输出之前的条消息记录，默认十条，也可以接空格+数字指定。
- `/clear`:清除消息记录，默认十条，可接空格+数字指定。
- `/music_list`: 获取歌曲列表
- `/r18 [0, 1, 2]`切换涩图接口r18模式，0为关闭，1为开启，2随机
- `/model [new_model]`切换模型，新模型需先在model.json中配置好。
- `/shutdown`睡眠。
- `/restart`解除睡眠。

## TODO
  - [x] 基本的消息接收和发送功能
  - [x] 命令交互
  - [x] 配置文件读取和解析
  - [x] 接入ChatGPT
  - [x] 接入DALLE
  - [x] 接入图片接口
  - [x] 自定义人格
  - [x] 新增支持反向ws连接
  - [x] 接入语音接口 #本地搭建参考b站箱庭xter的视频： https://b23.tv/9dOdMo6
  - [x] 接入其他大模型 #理论上只要符合openai api格式都可以，不过目前只涵盖了gemini,claude和kimi,其他的可以仿照`config/model.json`里的`models`配置自己写，记得下方model的值要在上方的`available_models`里。
  - [x] 新增图片识别功能，需要模型为`GPT4`系列或在`model.json`里设置`vision`为`true`
  - [x] 新增联网搜索和读取链接功能，且对GitHub链接读取做了优化
  - [x] 新增天气查询功能，需先前往[高德开放平台](https://console.amap.com/dev/key/app)获取密钥(选择web API即可)



## 贡献

如果您有任何建议或想要贡献代码，请提交Pull Request或创建Issue。

## 许可

本项目采用[MIT许可](LICENSE)。
