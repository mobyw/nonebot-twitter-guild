<!-- markdownlint-disable MD033 MD041-->
<p align="center">
  <img src="https://cdn.jsdelivr.net/gh/mobyw/images@main/Comics/Himesaka.png" width="200" height="200"/>
</p>

<div align="center">

# HimesakaBot(Twitter频道插件)
<!-- markdownlint-disable-next-line MD036 -->
_✨ 由HanayoriBot修改的基于NoneBot2的Twitter频道推送插件，可接入百度翻译 ✨_

</div>

## 简介

本插件由[HanayoriBot](https://github.com/kanomahoro/nonebot-twitter)修改而来，基于[NoneBot2](https://github.com/nonebot/nonebot2)与[go-cqhttp](https://github.com/Mrs4s/go-cqhttp)，可以及时将Twitter用户的最新推文推送至子频道，并且自带基于百度翻译的推文翻译接口，及时跟进所关注的账号的推文，增加频道活跃度。

注意：本插件目前只支持频道内使用，且不能与HanayoriBot共同使用。频道相关功能通过[nonebot2频道适配补丁](https://gist.github.com/mnixry/57033047be55956e2168284bcf0bd4b6)实现，并增加了部分代码。

## 特色

1. **轻依赖**：本插件在编写时尽量避免了采用使用第三方包，以减少依赖项；
2. **轻量化**：本插件经由4个文件构成，可以快速集成至任何已有的机器人框架；
3. **支持aarch64架构**：本插件在树莓派4B上能够正常运行，并且支持安卓平台的termux环境；
4. **强权限管理**：本插件在编写时采用了强权限的设计，仅可由超级用户进行操作；
5. **隔离关注列表**：各子频道拥有独立的关注列表，互不干扰。

## 安装步骤

### 安装NoneBot2

完整文档可以在 [这里](https://v2.nonebot.dev/) 查看。

懒得看文档？下面是快速安装指南：

1. (可选)使用你喜欢的 Python 环境管理工具创建新的虚拟环境。

2. 使用 `pip` (或其他) 安装 NoneBot 脚手架。

   ```bash
   pip install nb-cli
   ```

3. 使用脚手架创建项目。

   ```bash
   nb create
   ```

4. 请在创建项目时选用cqhttp适配器，并且按照文档完成最小实例的创建。
   
### 配置文件示例

1. .env
   ```yml
   ENVIRONMENT=prod
   ```

2. .env.prod
   ```yml
   HOST=127.0.0.1
   PORT=8080
   SECRET=
   ACCESS_TOKEN=
   SUPERUSERS=[管理员账户(18位频道QQ号，不是QQ号，可@后在go-cqhttp控制台获得)]
   COMMAND_START=["","/"]
   NICKNAME=["","/"]
   COMMAND_SEP=["."]
   ```

3. 请务必安装以上示例配置你的Bot；go-cqhttp请自行参照官方文档配置

### 安装HimesakaBot(Twitter频道插件)

   将本项目`\src\plugins`文件夹下的内容复制到项目的插件目录`\plugins`中。

### 安装phantomjs

本项目依赖于[phantomjs](https://github.com/ariya/phantomjs)，请将下载解压后的二进制文件放入Bot的根目录。由于经测试Linux下直接放二进制文件到项目根目录而不添加到路径可能无法打开，故已注释掉检查文件存在的语句，请确保按以下步骤配置好phantomjs。

phantomjs:[下载页面](https://phantomjs.org/download.html)

1. 对于Windows用户：
   请直接下载[压缩包](https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-windows.zip)，解压后将phantomjs.exe放入Bot根目录。

2. 对于Linux用户：
   对32位系统：
   ```bash
   cd /usr/local/share
   sudo wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-i686.tar.bz2
   sudo tar xjf phantomjs-2.1.1-linux-i686.tar.bz2
   sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-i686/bin/phantomjs /usr/local/share/phantomjs
   sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-i686/bin/phantomjs /usr/local/bin/phantomjs
   sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-i686/bin/phantomjs /usr/bin/phantomjs
   ```
   对64位系统：
   ```bash
   cd /usr/local/share
   sudo wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
   sudo tar xjf phantomjs-2.1.1-linux-x86_64.tar.bz2
   sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/share/phantomjs
   sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs
   sudo ln -s /usr/local/share/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/bin/phantomjs
   ```

3. 对于树莓派(Raspberry Pi)或其它ARM设备的用户：

   1. 感谢fg2it大佬的[phantomjs-on-raspberry](https://github.com/fg2it/phantomjs-on-raspberry)项目；

   2. Raspberry Pi(1b,2 and 3)：[下载页面](https://github.com/fg2it/phantomjs-on-raspberry/releases/tag/v2.1.1-wheezy-jessie-armv6)；

   3. Raspberry Pi(4 and later) and arm64：[下载页面](https://github.com/fg2it/phantomjs-on-raspberry/releases/tag/v2.1.1-jessie-stretch-arm64)；

   4. 直接下载 phantomjs 可执行文件；
   
   5. 确保 phantomjs 能正常运行 切换至 phantomjs 可执行文件所在目录执行：
   ```bash
   chmod 777 phantomjs  
   ./phantomjs --version
   ```
   如果能显示版本号，则能够正常运行，再将phantomjs复制到Bot根目录。

### 配置HimesakaBot(Twitter频道插件)

如果您的服务器位于境外，请忽略以下内容中的(1-4)

1. 首先确保你的代理软件支持http代理模式，并且已经开启，不推荐启用全局代理模式

2. 明确你的代理端口号，请咨询你的代理服务提供商

3. 根据平台不同，请按照以下方式分别设置代理：

   1. Windows平台 cmd环境
   ```bash
   set http_proxy=http://127.0.0.1:端口号  
   set https_proxy=http://127.0.0.1:端口号  
   ```

   2. windows平台 PowerShell环境
   ```bash
   $env:HTTP_PROXY="127.0.0.1:端口号"  
   $env:HTTPS_PROXY="127.0.0.1:端口号" 
   ```

   3. Linux平台 Bash环境
   ```bash
   export http_proxy=http://127.0.0.1:端口号 
   export https_proxy=http://127.0.0.1:端口号 
   ```

4. 在按照3设置代理后，请不要关闭终端，在当前终端执行nb run才能使机器人连上代理（请提前运行go-cqhttp）
   **注意**：go-cqhttp也必须运行于代理环境中，保证能连接外网，否则无法发送图片！！！

5. 在机器人成功运行后，会在机器人根目录会生成baidu_translate.json文件，若你不需要推文翻译功能，请忽略下一步

6. 用文本编辑器打开baidu_translate.json
   ```bash
   {"appid": "填入你申请的百度翻译API的appid", "baidu_token": "填入你申请的百度翻译API的密钥"}
   ```
   按以上要求填写，在[百度翻译开放平台](https://api.fanyi.baidu.com/)申请普通版通用翻译API即可，免费使用但是有限制调用频率。

### 指令说明

以下所以指令在子频道中只允许超级用户进行操作

**使用格式**：指令 推特ID(如果指令要求的话) 

**推特ID**：在Twitter的用户主页，@后面的部分；或者‘https://twitter.com/xxxxx’ 用户主页链接中的xxxxx

**所有指令如下：**

1. **推特关注 推特ID**
   添加新用户

2. **推特取关 推特ID**
   取关用户

3. **推特列表**
   显示当前关注列表

4. **开启翻译 推特ID**
   开启推文翻译

5. **关闭翻译 推特ID**
   关闭推文翻译

6.  **推特帮助**
   顾名思义

### 遇到问题？

你可以直接提交issue，或者发送邮件到：mobyw66@gmail.com

### 效果展示

![效果1](https://cdn.jsdelivr.net/gh/mobyw/images@main/Screenshots/Screenshot_0.jpg)

![效果2](https://cdn.jsdelivr.net/gh/mobyw/images@main/Screenshots/Screenshot_1.jpg)
