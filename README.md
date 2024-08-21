# MY_QBOT - QQ机器人项目

欢迎来到MY_QBOT项目！这是一个基于Python的QQ机器人后端服务,提供了一系列自动化和交互功能。

## MY_QBOT功能列表
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

### Docker部署 (推荐)

1. 克隆项目并进入目录:
   ```
   git clone -b dev https://github.com/syuchua/MY_QBOT.git
   cd MY_QBOT
   ```

2. 创建并编辑配置文件:
   ```
   mkdir -p config
   cp example.json.txt config/config.json
   nano config/config.json
   ```
   根据需要修改配置文件内容。

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
   git clone -b dev https://github.com/syuchua/MY_QBOT.git
   cd MY_QBOT
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
   复制 `config.example.json` 到 `config/config.json` 并根据需要修改。

5. 运行:
   ```
   python main.py
   ```

## 配置说明

1. 在项目根目录下找到 `example.json.txt` 文件。
2. 将此文件复制并重命名为 `config/config.json`。
3. 使用文本编辑器打开 `config.json`。
4. 根据文件中的注释，替换所有需要自定义的值：
   - 务必替换 `api_key` 为您的实际 API 密钥。
   - 更新 `self_id` 和 `admin_id` 为实际的 QQ 号。
   - 根据需要调整其他设置，如昵称、启用时间、插件等。
5. 删除所有注释行（以 // 开头的行）。
6. 保存文件。

注意：
- `config.example.json.txt` 仅作为模板，请不要直接修改此文件。
- 确保您的 `config.json` 是有效的 JSON 格式。
- 如果不确定某项配置的作用，请参考项目文档或保持默认值。

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

完整配置选项请参考 `config.example.json`。

## 插件开发(插件系统待完善)

我们欢迎社区贡献新的插件来扩展 MY_QBOT 的功能!

### 如何开发插件(插件系统待完善)

1. 在 `plugins` 目录下创建新的 Python 文件。
2. 实现插件功能,使用装饰器注册命令或事件处理器。

插件示例:


### 插件开发指南（插件系统待完善）


我们期待看到您的创意插件!如有任何问题,请随时在 Issues 中提出。

## 贡献

欢迎提交 Pull Requests 或创建 Issues 来改进项目。您的贡献将帮助 MY_QBOT 变得更好!

## 许可

本项目采用[MIT许可](LICENSE)。
