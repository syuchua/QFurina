# QFurina - QQ机器人项目

欢迎来到MY_QBOT项目！这是一个基于Python的QQ机器人后端服务,提供了一系列自动化和交互功能。

## QFurina功能列表
  1. AI聊天,角色扮演
  2. 群聊管理
  3. 从pixiv获取并发送图片
  4. 指定关键词发送或者随机图片
  5. AI绘画
  6. AI生成语音
  7. 天气查询
  8. 联网搜索
  9. 定时开关机

## 支持的消息平台
目前主要在Windows端Llonebot上测试,理论上所有支持onebot v11协议的消息平台都可以使用。HTTP对接配置可能需要额外设置。

## 部署指南

### Docker部署 (已集成[napcat](https://github.com/NapNeko/NapCatQQ)和mongodb数据库)

1. 克隆项目并进入目录:
   ```
   git clone -b dev https://github.com/syuchua/QFurina.git
   cd QFurina && mkdir data && cd data && mkdir music && cd ../
   ```

2. 编辑配置文件:
   ```
   nano config/config.json
   ```
   根据需要修改配置文件内容。
  如果需要配置gpt以外的模型，可以修改model.json，其中vision项表示模型是否支持识图

3. 启动服务:
   ```
   docker-compose up -d
   ```

4. 查看日志:
   ```
   docker-compose logs -f
   ```

### 本地部署

1. 克隆项目:
   ```
   git clone -b dev https://github.com/syuchua/QFurina.git
   cd Qfurina && mkdir data && cd data && mkdir music && cd ../
   ```

2. 创建虚拟环境 (可选):
   ```
   python -m venv venv
   source venv/bin/activate  # Windows使用: venv\Scripts\activate
   ```

3. 安装依赖:
   ```
   pip install -r requirements.txt
   ```

4. 配置:

- `openai_api_key`: OpenAI API密钥
- `model`: 使用的模型 (默认: gpt-3.5-turbo)
- `self_id`: 机器人QQ号
- `admin_id`: 管理员QQ号
- `nicknames`: 机器人昵称列表
- `system_message`: 系统消息配置,包括 `character` (机器人人格)
- `connection_type`: 连接类型 (http 或 ws_reverse)
- `proxy_api_base`: API请求地址
- `reply_probability`: 无昵称时的回复频率
- `r18`: R18内容设置 (0关闭, 1开启, 2随机)

完整配置选项请参考 `example.json.txt`。

5. 安装并配置 MongoDB:
   a. 下载 MongoDB Community Server: https://www.mongodb.com/try/download/community

   b. 安装 MongoDB:
      - Windows: 运行下载的安装程序，按照向导完成安装。
      - Linux: 根据您的发行版，使用包管理器安装。例如，Ubuntu:
        ```
        sudo apt update
        sudo apt install mongodb
        ```

   c. 启动 MongoDB 服务:
      - Windows:
        - 如果您将 MongoDB 安装为服务，它应该已经自动启动。
        - 否则，在mongod.exe所在目录下打开命令提示符并运行:
          ```
           mongod --dbpath D:\MongoDB\data --logpath D:\MongoDB\log\mongodb.log --logappend
          ```
        （请将对应目录替换为你自己的）

      - Linux:
        ```
        sudo systemctl start mongodb
        ```
        如果使用较旧的系统或 MongoDB 版本:
        ```
        sudo service mongodb start

6. 运行:
   ```
   python main.py
   ```

## 命令功能

机器人支持以下命令：

- `/help`：显示帮助信息。
- `/reset`：重置当前会话。
- `/character`：输出`config.json`中的`character`值，也即当前的人设。
- `/history`: 输出之前的条消息记录，默认十条，也可以接空格+数字指定。
- `/clear`:清除消息记录，默认十条，可接空格+数字指定。
- `/music_list`: 获取歌曲列表
- `/r18 [0, 1, 2]`切换涩图接口r18模式，0为关闭，1为开启，2随机
- `/model [new_model]`切换模型，新模型需先在model.json中配置好
- `/shutdown`关机
- `/restart`重启


## 插件系统

QFurina 采用了灵活的插件系统，允许开发者轻松扩展和定制机器人的功能。

### 插件结构

每个插件都应该是一个独立的 Python 模块，位于 `plugins` 目录下。一个典型的插件结构如下：

```
plugins/
└── ExamplePlugin/
    ├── __init__.py
    └── example_plugin.py
```

### 创建插件

要创建一个新插件，您需要：

1. 在 `plugins` 目录下创建一个新的文件夹。
2. 在该文件夹中创建一个主 Python 文件（如 `example_plugin.py`）。
3. 在主文件中定义一个继承自 `PluginBase` 的类。
4. 使用 `@PluginBase.register` 装饰器注册您的插件。

示例插件代码：

```python
from app.plugin.plugin_base import PluginBase

@PluginBase.register("example")
class ExamplePlugin(PluginBase):
    def __init__(self):
        super().__init__()
        self.name = "Example Plugin"
        self.version = "1.0.0"
        self.description = "This is an example plugin"

    async def on_message(self, message):
        # 处理消息的逻辑
        pass

    async def on_file_upload(self, file_path):
        # 处理文件上传的逻辑
        pass
```

### 插件生命周期

插件有以下生命周期方法：

- `on_load()`: 插件加载时调用
- `on_enable()`: 插件启用时调用
- `on_disable()`: 插件禁用时调用
- `on_unload()`: 插件卸载时调用

### 插件配置

插件可以在 `config/config.json` 文件中进行配置。您可以在插件的 `on_load()` 方法中读取配置。

### 启用和禁用插件

您可以通过修改 `config/config.json` 文件中的 `ENABLED_PLUGINS` 列表来启用或禁用插件。

### 插件命令

插件可以注册自定义命令，这些命令可以通过聊天消息触发。

### 文件处理

插件可以实现 `on_file_upload()` 方法来处理文件上传事件。

更多详细信息和高级用法，请参考我们的插件开发文档（即将推出）。

## 贡献

欢迎提交 Pull Requests 或创建 Issues 来改进项目。您的贡献将帮助 MY_QBOT 变得更好!

## 许可

本项目采用[MIT许可](LICENSE)。

## [附上一个自己的api中转站，支持各种主流模型，有需要的可以看看](https://api.yuchu.me)

## [gpt_sovits整合包](https://cloud.yuchu.me/s/J2um)

### [一些AI翻唱资源](https://cloud.yuchu.me/s/KRCv)

### 获取bing的cookie用于非gpt系列的AI绘图(疑似失效，推荐cloudflare workers ai)

[如果视频无法渲染可以点击链接下载](https://cloud.yuchu.me/f/qxjsX/2024-08-05%2021-41-49.mp4)

<div class="onebox video-onebox" dir="auto">
            <video width="100%" height="100%" controls="" __idm_id__="8195">
              <source src="https://cloud.yuchu.me/f/qxjsX/2024-08-05%2021-41-49.mp4">
              <a href="https://cloud.yuchu.me/f/qxjsX/2024-08-05%2021-41-49.mp4" rel="noopener nofollow ugc">
                "https://cloud.yuchu.me/f/qxjsX/2024-08-05%2021-41-49.mp4"
              </a>
            </video>
</div>

### 一些跟芙芙聊天的日常
【谁家傻芙芙连9.8和9.11哪个大都分不清】 https://www.bilibili.com/video/BV1TivWeFEot/?share_source=copy_web&vd_source=6f08734cb3a294b6a1e634a3e5b481ca
