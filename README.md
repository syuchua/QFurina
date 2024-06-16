# MY_QBOT - QQ机器人项目

欢迎来到MY_QBOT项目！这是一个基于Python的QQ机器人后端服务，提供了一系列自动化和交互功能。

## MY_QBOT都能做什么
  1. AI聊天，角色扮演
  2. 群聊
  3. 从pixiv获取并发送涩图()
  4. 指定关键词发送或者随机涩图
  5. AI绘画

## 目录结构
```
.
├── MY_BOT/
│   ├── app/
│   │   ├── init.py
│   │   ├── command.py
│   │   ├── config.py
│   │   └── message.py
|   |── command/
|   |   |── init.py
|   |   |── help.py
|   |   |── reset.py
|   |   |── character.py
│   ├── main.py
│   ├── receive.py
│   ├── lolicon.py
│   ├── proxy_openai_api.py
│   ├── config.json
│   ├── requirements.txt
│   └── README.md
```
### 简单介绍下各目录及文件：
  - `app/`：一些配置和函数
  - `app/command.py`: 用于分发命令
  - `app/config.py`: 从config.json生成配置文件
  - `app/message.py`: 实现发送消息，包括图片的各个函数
  - `command/`: 一些命令有关的函数
  - `main.py`: 主程序
  - `receive.py`: 实现从QQ接收消息，需开放3001端口（跟Llonebot配置中对应）
  - `lolicon.py`: 涩图接口，你懂的
  - `proxy_openai_api.py`: 对接chatgpt用于聊天和dalle用于AI绘画，dalle默认dalle2,如果api支持，可选dalle3
  - `config.json`: 配置信息，必填

## 当前支持的消息平台：
目前仅在Windows端Llonebot上测试过，理论上所有支持oneonev11协议的消息平台都可以用，不过http对接配置可能要麻烦一点

## 安装指南

1. **安装Python环境**：确保您的系统上安装了Python 3.11或更高版本。
2. **创建虚拟环境**（可选）：

```
python -m venv venv
source venv/bin/activate  # 对于Windows使用 venv\Scripts\activate
```
3. **安装依赖**：
```
pip install -r requirements.txt
```
4. **安装Llonebot**:
[官方文档](https://llonebot.github.io/zh-CN/)

## 配置

  在`config.json`文件中配置机器人的设置，包括但不限于：
  - `openai_api_key`: 你的openai_api_key
  - `model`: 使用的模型，默认为gpt-3.5-turbo
  - `self_id`：机器人的QQ号。
  - `admin_id`：管理员的QQ号。
  - `nicknames`：机器人的昵称列表。
  - `system_message`：系统消息配置，最重要的是`character`，相当于机器人的人格。
  - `report_secret`: http事件上传密钥。
  - `proxy_api_base`: openai_api_key请求地址，默认为https://api.openai.com/v1
  - `reply_probability`: 当收到的消息中没有nickname时的回复频率，1为每一条都回复，0为仅回复带有nickname的消息，默认0.5

  配置Llonebot: 如图
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240615234833.png)
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
  - 发送`画一张`，`生成一张` 即可发送AI绘画
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616001253.png)
  - R-18?
  找到lolicon.py fetch_image函数的这一部分，修改r18的值，0为关闭r18，1开启r18，2为随机发送，该接口的涩图数量足有十几万，其中r18占27.8%，建议公共场合尽量设置为0，2的话，还是不要太相信自己的运气了(问就是惨痛的教训)
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616002550.png)
  ![](https://cdn.jsdelivr.net/gh/mazhijia/jsdeliver@main/img/20240616001941.png)


## 命令功能

机器人支持以下命令：

- `/help`：显示帮助信息。
- `/reset`：重置当前会话。
- `/character`：输出`config.json`中的`character`值，也即当前的人设。

## TODO
  - [x] 基本的消息接收和发送功能
  - [x] 命令交互
  - [x] 配置文件读取和解析
  - [x] 接入ChatGPT
  - [x] 接入DALLE
  - [x] 接入图片接口
  - [x] 自定义人格
  - [ ] 接入语音接口
  - [ ] 接入其他大模型

## 贡献

如果您有任何建议或想要贡献代码，请提交Pull Request或创建Issue。

## 许可

本项目采用[MIT许可](LICENSE)。
