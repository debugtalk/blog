---
title: Android App持续集成性能测试：启动流量（1）
permalink: post/Android-performance-test-start-traffic-uid-stat
tags: [Android, traffic]
---

本文对Android App的启动流量测试进行介绍。这里的启动流量指的是网络流量，即App在启动时发起网络请求和接收网络响应时传输的网络数据量。

说起流量，也许大家的第一反应就是tcpdump/wireshark这类网络抓包工具。的确，Android系统确实也支持`tcpdump`工具，通过`tcpdump`，我们可以实现非常精准的流量测试。但`tcpdump`也有个问题，就是它捕捉到的流量是系统层面的，我们很难区分捕捉得到的流量数据是否都是当前apk产生的。

其实，对于特定apk的整体流量数据，在Android系统中都会存储到对应文件中，我们完全可以通过读取对应文件来获得当前apk的流量信息。

## get app UID

与流量相关的状态数据存储在`/proc/uid_stat/<UID>/`目录下，其中，`<UID>`表示apk对应的UID。

关于UID，简单地进行下说明。在Linux系统中，UID表示的是User Identifier，主要用于表示是哪位用户运行了该程序。但在Android系统中，由于Android系统本身就为单用户系统，这时UID就被赋予了新的使命，主要用于实现数据共享。具体地，Android系统为每个应用都分配了一个UID，不同apk的UID几乎都是互不相同的，而对于不同UID的apk，不能共享数据资源。之所以用“几乎”，是因为有时候同一厂家会存在多个产品，并且希望能在多个apk之间实现数据共享，这个时候，便可通过在menifest配置文件中指定相同的sharedUserId，然后在Android系统中安装应用时便会分配相同的UID。

获取app UID的方式有多种，最简单的方式应该还是从`/data/system/packages.list`中读取，并通过apk的`<PKGNAME>`找到对应的UID。

~~~shell
root@hammerhead:/ # cat /data/system/packages.list | grep com.UCMobile.trunk
com.UCMobile.trunk 10084 0 /data/data/com.UCMobile.trunk default 3003,1028,1015
~~~

在这里，10084即是`com.UCMobile.trunk`的UID。

## 获取流量数据

流量数据分为接收流量（tcp_rcv）和发送流量（tcp_snd）两部分，这两个状态数值我们可以通过读取`/proc/uid_stat/<UID>`目录下的两个文件得到。

~~~shell
shell@hammerhead:/ $ cat /proc/uid_stat/10084/tcp_rcv
3446837
shell@hammerhead:/ $ cat /proc/uid_stat/10084/tcp_snd
134366
~~~

通过这种方式，我们就可以读取得到指定apk在当前时刻的累计流量数值。

## 获得启动流量数据

有了前面的基础，我们要测试启动流量就很好实现了。只需要在启动前采集下累计流量数值，然后启动应用，完成启动后再采集一次累计流量数值，前后两次累计数值的差值便是当次启动耗费的流量数。需要注意的是，由于很多时候apk在启动后，会在系统后台异步加载一些数据资源，因此为了保证我们采集到当次启动耗费的全部流量数值，我们在启动应用后最好能等待一段时间。

~~~shell
root@hammerhead:/ # cat /proc/uid_stat/10084/tcp_snd
15068
root@hammerhead:/ # cat /proc/uid_stat/10084/tcp_rcv
98021

# start app activity, sleep 10s

root@hammerhead:/ # cat /proc/uid_stat/10142/tcp_snd
23268
root@hammerhead:/ # cat /proc/uid_stat/10142/tcp_rcv
965651
~~~

采集到前后两次流量数值后，即可计算得到当次启动耗费的总流量。

~~~shell
当次启动总流量 = (23268 + 965651) - (15068 + 98021) = 875830 bytes
~~~

当然，这里的启动还分为好几种，包括首次安装启动、非首次安装启动、覆盖安装启动等。具体的启动方式可根据实际场景来定，但在统计流量的方法方面都是相同的。

## 总结

本文讲解了Android App启动流量测试的一种方法。然而，本次介绍的方法也存在一定局限性，因为`/proc/uid_stat/<UID>/`目录下的`tcp_rcv`和`tcp_snd`文件中都只记录了总值，如果我们只关注总体的流量数值还好，但要是我们希望能测试得到更细化的数据，该方法就没法满足我们的测试需求了。

举个例子，UC浏览器国际版在启动后，会和美国的服务器进行通讯交互。现在，我们想测试UC浏览器国际版在启动后与美国服务器的通讯流量。

显然，本文中介绍的方法是没法实现上述例子中的测试需求的。那例子中的场景要怎么测呢？这就还是得用到`tcpdump`，在下一篇文章中我会再详细进行介绍。
