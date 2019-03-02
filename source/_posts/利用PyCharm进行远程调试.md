---
title: 利用 PyCharm 进行 Python 远程调试
permalink: post/remote-debugging-with-pycharm
date: 2015/07/13
categories:
  - Development
tags:
  - Python
  - pycharm
---

## 背景描述

有时候Python应用的代码在本地开发环境运行十分正常，但是放到线上以后却出现了莫名其妙的异常，经过再三排查以后还是找不到问题原因，于是就在想，要是可以在服务器环境中进行单步跟踪调试就好了。

然而，在服务器系统上安装一个IDE肯定是不现实的；通过SSH远程到服务器端，采用`pdb`进行调试虽然可行，但是操作还是较为繁琐，而且也不够直观。

那么，是否可以将开发环境中的IDE与服务器环境相连，实现利用开发环境的IDE调试服务器环境中运行的程序呢？
答案是肯定的，这就是远程调试（Remote Debug）。

## 远程调试的工作原理

远程调试的功能在Eclipse、IntelliJ IDEA等大型IDE中均有支持，实现原理都基本相同，这里采用PyCharm进行说明。

在远程调试的模式下，PyCharm（IDE）扮演服务端（Server）的角色，而运行在远程计算机上的应用程序扮演客户端（Client）的角色。正因如此，进行远程调试时，需要先在本地开发环境中设定端口并启动IDE，IDE会对设定的端口开始监听，等待客户端的连接请求；那远程计算机中的应用程序又是怎样与IDE建立通讯连接的呢？

针对远程调试功能，PyCharm提供了`pydevd`模块，该模块以`pycharm-debug.egg`的形式存在于PyCharm的安装路径中。远程计算机安装该库文件后，然后就可以调用`pydevd.settrace`方法，该方法会指定IDE所在机器的IP地址和监听的端口号，用于与IDE建立连接；建立连接后，便可在IDE中对远程在远程计算机中的程序进行单步调试。

## 远程调试的配置方法

### 1、在远程计算机上安装`pydevd`模块

首先，在本地开发环境的PyCharm安装路径中找到`pycharm-debug.egg`文件（若远程计算机运行的是Python3，则需要`pycharm-debug-py3k.egg`）；

然后，将`pycharm-debug.egg`文件拷贝至远程计算机，在远程计算机中将`pycharm-debug.egg`添加至引用路径，可以采用多种方式：

- 采用`easy_install pycharm-debug.egg`命令进行安装（pip命令无法安装，只能使用easy_install）
- 将`pycharm-debug.egg`添加至`PYTHONPATH`或`sys.path`: `import sys; sys.path.append('/home/leo/app-dependancies/pycharm-debug.egg')`
- 解压`pycharm-debug.egg`，将其中的`pydev`文件夹拷贝至远程应用程序目录下

最后，在远程计算机的Python命令行中输入`import pydevd`，若没有报错则说明`pydevd`模块安装成功。

### 2、在本地开发环境的PyCharm中进行监听配置

在PyCharm中配置说明如下：

- 【Run】->【Edit Configurations】
- 【Add New Configuration】->【Python Remote Debug】
- 填写`Local host name`和`Port`，其中`Local host name`指的是本机开发环境的IP地址，而`Port`则随便填写一个10000以上的即可；需要注意的是，由于远程计算机需要连接至本地开发环境，因此本地IP地址应该保证远程可以访问得到
- 【Apply】and【OK】

### 3、在本地开发环境的PyCharm中配置Mapping映射

### 4、在远程计算机的应用程序中插入代码

将如下代码插入至远程计算机的应用程序中。

~~~python
import pydevd
pydevd.settrace('100.84.48.156', port=31235, stdoutToServer=True, stderrToServer=True)
~~~

其中，IP地址和端口号要与PyCharm中的监听配置保持一致。

### 5、在PyCharm中启动`Debug Server`

【Run】->【Debug...】，选择刚创建的远程调试配置项，在`Debug Console`中会显示如下信息：

~~~bash
Starting debug server at port 31235
Waiting for process connection...
Use the following code to connect to the debugger:
import pydevd
pydevd.settrace('100.84.48.156', port=31235, stdoutToServer=True, stderrToServer=True)
~~~

这说明`Debug Server`已经启动并处于监听状态。

### 6、在远程计算机中启动应用程序

在远程计算机中启动应用程序，当执行到`pydevd.settrace`语句时，便会与本地开发环境中的PyCharm建立通讯连接，接下来便可以在本地IDE中进行单步调试了。

需要注意的是，本地开发环境必须保证IP地址和端口号可从远程计算机访问得到，否则会无法建立连接。

~~~bash
$ telnet 100.84.48.156 31235
Trying 100.84.48.156...
telnet: Unable to connect to remote host: Connection refused

$ python devicedectector.py
Could not connect to 100.84.48.156: 31236
Traceback (most recent call last):
  File "/usr/local/lib/python2.7/dist-packages/pycharm-debug.egg/pydevd_comm.py", line 478, in StartClient
    s.connect((host, port))
  File "/usr/lib/python2.7/socket.py", line 224, in meth
    return getattr(self._sock,name)(*args)
error: [Errno 111] Connection refused
~~~

## 参考链接
http://stackoverflow.com/questions/6989965/how-do-i-start-up-remote-debugging-with-pycharm
https://www.jetbrains.com/pycharm/help/remote-debugging.html
