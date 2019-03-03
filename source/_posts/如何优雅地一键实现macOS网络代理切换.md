---
title: 如何优雅地一键实现 macOS 网络代理切换
permalink: post/switch-macOS-web-proxy-in-elegant-way
date: 2016/11/24
categories:
  - 效率工具
tags:
  - proxy
  - Shuttle
  - mitmproxy
  - Locust
---

在`macOS`中配置Web代理时，通常的做法是在控制面板中进行操作，`System Preferences` -> `Network` -> `Advanced` -> `Proxies`.

![macOS-Web-Proxy-Setting](/images/macOS-Web-Proxy-Setting.jpg)

这种配置方式虽然可以实现需求，但缺点在于操作比较繁琐，特别是在需要频繁切换的情况下，效率极其低下。

基于该痛点，我们希望能避免重复操作，实现快速切换配置。

## Terminal中实现网络代理配置

要避免在GUI进行重复的配置操作，比较好的简化方式是在Terminal中通过命令实现同样的功能。事实上，在macOS系统中的确是存在配置网络代理的命令，该命令即是`networksetup`。

### 获取系统已有的网络服务

首先需要明确的是，macOS系统中针对不同网络服务（`networkservice`）的配置是独立的，因此在配置Web代理时需要进行指定。

而要获取系统中存在哪些网络服务，可以通过如下命令查看：

```bash
$ networksetup -listallnetworkservices
An asterisk (*) denotes that a network service is disabled.

Wi-Fi
iPhone USB
Bluetooth PAN
Thunderbolt Bridge
```

如果计算机是通过`Wi-Fi`上网的，那么我们设置网络代理时就需要对`Wi-Fi`进行设置。

### 开启Web代理

通过`networksetup`命令对`HTTP`接口设置代理时，可以采用如下命令：

```bash
$ sudo networksetup -setwebproxy <networkservice> <domain> <port number> <authenticated> <username> <password>
# e.g. sudo networksetup -setwebproxy "Wi-Fi" 127.0.0.1 8080
```

执行该命令时，会开启系统的Web HTTP Proxy，并将Proxy设置为`127.0.0.1:8080`。

如果是对`HTTPS`接口设置代理时，命令为：

```bash
$ networksetup -setsecurewebproxy <networkservice> <domain> <port number> <authenticated> <username> <password>
# e.g. sudo networksetup -setsecurewebproxy "Wi-Fi" 127.0.0.1 8080
```

### 关闭Web代理

对应地，关闭`HTTP`和`HTTPS`代理的命令为：

```bash
$ sudo networksetup -setwebproxystate <networkservice> <on off>
# e.g. sudo networksetup -setwebproxystate "Wi-Fi" off

$ networksetup -setsecurewebproxystate <networkservice> <on off>
# e.g. sudo networksetup -setsecurewebproxystate "Wi-Fi" off
```

## 结合Shuttle实现一键配置

现在我们已经知道如何通过`networksetup`命令在Terminal中进行Web代理切换了，但如果每次都要重新输入命令和密码，还是会很麻烦，并没有真正地解决我们的痛点。

而且在实际场景中，我们通常需要同时开启或关闭HTTP、HTTPS两种协议的网络代理，这类操作如此高频，要是还能通过点击一个按钮就实现切换，那就优雅多了。

幸运的是，这种优雅的方式还真能实现，只需要结合使用`Shuttle`这么一款小工具。

[`Shuttle`](http://fitztrev.github.io/shuttle/)，简而言之，它可以将一串命令映射到macOS顶部菜单栏的快捷方式。我们要做的很简单，只需要将要实现的任务拼接成一条串行的命令即可，然后就可以在系统菜单栏中点击按钮运行整条命令。

例如，在Terminal中，要想在不手动输入`sudo`密码的情况下实现同时关闭HTTP和HTTPS的网络代理，就可以通过如下串行命令实现。

```bash
$ echo <password> | sudo -S networksetup -setwebproxystate 'Wi-Fi' off && sudo networksetup -setsecurewebproxystate 'Wi-Fi' off
```

类似地，我们还可以实现同时开启HTTP和HTTPS网络代理，更有甚者，我们还可以实现在同时开启HTTP和HTTPS网络代理后，启动`mitmproxy`抓包工具。

这一切配置都可以在Shuttle的配置文件`~/.shuttle.json`中完成。

```json
"hosts": [
  {
    "mitmproxy": [
      {
        "name": "Open mitmproxy",
        "cmd": "echo <password> | sudo -S networksetup -setwebproxy 'Wi-Fi' 127.0.0.1 8080 && sudo networksetup -setsecurewebproxy 'Wi-Fi' 127.0.0.1 8080 && workon mitmproxy && mitmproxy -p 8080"
      }
    ],
    "HTTP(S) Proxy": [
      {
        "name": "Turn on HTTP(S) Proxy",
        "cmd": "echo <password> | sudo -S networksetup -setwebproxy 'Wi-Fi' 127.0.0.1 8080 && sudo networksetup -setsecurewebproxy 'Wi-Fi' 127.0.0.1 8080"
      },
      {
        "name": "Turn off HTTP(S) Proxy",
        "cmd": "echo <password> | sudo -S networksetup -setwebproxystate 'Wi-Fi' off && sudo networksetup -setsecurewebproxystate 'Wi-Fi' off"
      },

    ],
  },
]
```

配置十分简洁清晰，不用解释也能看懂。完成配置后，在`macOS`顶部菜单栏中就会出现如下效果的快捷方式。

![macOS-Web-Proxy-Setting](/images/shuttle-preview.png)

后续，我们就可以通过快捷方式实现一键切换HTTP(S)代理配置、一键启动`mitmproxy`抓包工具了。

说到[`mitmproxy`](https://github.com/mitmproxy/mitmproxy)这款开源的抓包工具，只能说相见恨晚，第一次使用它时就被惊艳到了，情不自禁地想给它点个赞！自从使用了`mitmproxy`，我现在基本上就不再使用`Fiddler`和`Charles`了，日常工作中HTTP(S)抓包任务全靠它搞定。

哦对了，`mitmproxy`不仅可以实现抓包任务，还可以跟[`locust`](https://github.com/locustio/locust)性能测试工具紧密结合，直接将抓取的数据包生成`locust`脚本啊！

`mitmproxy`如此强大，本文就不再多说了，后续必须得写一篇博客单独对其详细介绍。
