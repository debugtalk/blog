---
title: Android App持续集成性能测试：启动流量（2）
permalink: post/Android-performance-test-start-traffic-tcpdump-wireshark
tags: [Android, 流量测试, tcpdump, wireshark]
---

在上一篇文章中，介绍了一种测试Android App启动流量的方法。当时也提到了，通过读取`/proc/uid_stat/<UID>/`目录下的`tcp_rcv`和`tcp_snd`文件，只能得到App的流量总值，无法得到更细化的数据。

例如，UC浏览器国际版在启动后，会和美国的服务器进行通讯交互，如果我们想测试浏览器在启动后与美国服务器的通讯流量，要怎么实现呢？。

本文便是针对这类场景的测试需求，讲解如何采用`tcpdump`测试得到更细化的流量数据。

## tcpdump

`tcpdump`，是一个在Unix-like系统中通用的网络抓包工具，当然，这个工具在Android系统中也是可以使用的。

对于工具本身，本文不做过多介绍。为了防止有读者之前完全没有`tcpdump`的使用经验，在这里我只简单地进行几点说明：

- 大多Android系统默认未集成tcpdump工具，我们需要事先将专门针对Android系统编译好的的tcpdump导入到Android系统，例如`/data/local/tmp/tcpdump`；当然，我们也不用自己编译，在[`androidtcpdump`](http://www.androidtcpdump.com)网站就可以下载到编译好的tcpdump二进制文件。
- 运行`tcpdump`工具时需要root权限。
- tcpdump命令支持许多参数，常见的有：
  - `-i`指定网卡（interface），`any`表示不限网卡；
  - `-c`指定接收的packets数量，接收完成后自动停止抓包；
  - `-w`指定输出文件，输出文件的格式为pcap；
  - `-s`(`--snapshot-length`)指定在每个packet中最多截取的字节数，设置为0时表示截取上限取默认值262144；
  - `-v`/`-vv`/`-vvv`，指定输出的详细程度，针对流量测试，我们不需要非常详尽的输出数据，取`-v`即可。


基于以上对`tcpdump`的介绍，我们要测试浏览器在启动后与美国服务器的通讯流量，就只需要先启动浏览器，然后在`adb shell`中执行以下命令即可。

~~~shell
1|shell@hammerhead:/ $ su -c /data/local/tmp/tcpdump -v -i any -s 0 -c 2000 -w /sdcard/us.pcap
tcpdump: listening on any, link-type LINUX_SLL (Linux cooked), capture size 262144 bytes
2000 packets captured
2024 packets received by filter
0 packets dropped by kernel
~~~

在这里之所有指定接收packets数为2000，是因为浏览器启动后并不是立即与美国服务器进行通讯。所以在这里设置了一个比较大的值，确保浏览器与美国服务器的异步通讯数据能包含在这2000packets之中。当然，这个2000只是一个工程实践得到的经验值，具体取多少还是要依赖于具体场景。

经过一段时间的抓包后，就生产了抓包结果，即`/sdcard/us.pcap`。

## 人工分析pcap文件

拿到pcap文件只是第一步，我们必须要对这个文件进行解析才能得到我们想要的结果。

那么，通过什么方法解析pcap文件呢？

先简单介绍下pcap。pcap，即`packet capture`的缩写，是一种通用的网络抓包数据存储格式。既然是通用，因此它除了可以被`tcpdump`解析外，还支持被多种网络工具解析，其中，就包括大家熟知的`wireshark`。

至于为什么有了`tcpdump`还要用`wireshark`来解析，这主要还是因为`wireshark`是图形界面，操作和使用上更友好一些。

在`wireshark`中分析pcap文件十分简单，只需要直接打开文件，就可以看到抓包过程中捕获的所有网络通讯数据。不过，由于我们抓包获得的数据是系统层面的，除了我们关注的与美国服务器的通讯交互外，还包含了非常多的其它通讯信息。

好在`wireshark`有非常强大的筛选功能。对于本案例，我们可以先确定出美国服务器的host或IP，例如host为`ucus.ucweb.com`，那么我们就可以在筛选器中通过`http.host == "ucus.ucweb.com"`语句，即可筛选出所有本地与美国服务器的通讯交互数据。

![](/images/wireshark_host_filter.png)

对于更丰富的筛选功能，大家可以根据实际需求查询`wireshark`的帮助文档，在此就不再进行展开。

从上图的筛选结果中可以看到，美国服务器的地址为`168.235.199.134`。那接下来如何查看通讯的流量大小呢？

首先，找出该次请求的`TCP Stream`。

![](/images/wireshark_tcp_stream_menu.png)

在筛选出的`TCP Stream`中，将各条记录的Length进行求和，即可得到总的大小。

![](/images/wireshark_tcp_stream_data.png)

例如，发送流量的总和，即`100.84.126.160`->`168.235.199.134`的总和，加和总值为3722bytes；接收流量的总和，即`168.235.199.134`->`100.84.126.160`的总和，加和总值为6300bytes。

当然，这里只是为了讲解计算流量的原理，实际上，我们并不需要去进行这个计算，可以直接读取得到总值。

【Statistics】->【Endpoints】

![](/images/wireshark_endpoints_menu.png)

在Endpoints界面中，选择`TCP` tab，勾选“Limit to display filter”，即可看到通讯流量汇总数据。

![](/images/wireshark_tcp_stream_data.png)

可以看出，这个的汇总数值与前面计算得到的数值完全相同。

## 自动化测试脚本

通过前面的人工分析，我们已经掌握了分析特定流量的一般性方法。然而，要想将此种场景的流量测试加入持续集成自动化测试系统，采用以上方法显然是不行的。

那么，要怎样才能在代码中完成对pcap文件的分析呢？

好在已经有前辈做了相应的工作，在GitHub上就找到了一个开源项目[`pcap2har`](https://github.com/andrewf/pcap2har)，可以实现对pcap文件的解析。

`pcap2har`项目的详细介绍请大家自行查看项目文档。

针对本文中的测试场景，解析pcap文件的代码实现如下。

~~~python
#!/usr/bin/env python
#coding=utf-8

import dpkt
from pcap2har import pcap
from pcap2har import http


def parsePcapFile(pcap_file, target_host):
    # parse pcap file
    dispatcher = pcap.EasyParsePcap(filename=pcap_file)

    traffic_total = 0
    traffic_receive_total = 0
    traffic_send_total = 0
    url_list = []

    # stream为tcp数据流，当为长链接时一个tcp流里面可以有多个http请求
    for stream in dispatcher.tcp.flows():
        # fwd为请求大小，如果小于200则肯定不是正常的HTTP请求，忽略
        if stream.fwd.caplen < 200:
            continue

        pointer = 0
        while pointer < len(stream.fwd.data):
            try:
                myrequest = http.Request(stream.fwd, pointer) #解析请求头
            except dpkt.Error as error:  # if the message failed
                break
            except:
                raise

            pointer += myrequest.data_consumed
            myhead = myrequest.msg.headers

            # 请求头大小<200时忽略
            if myrequest.data_consumed < 200:
                continue

            if myhead["host"] == target_host:
                traffic_receive_total += stream.rev.caplen
                traffic_send_total += stream.fwd.caplen
                traffic_total += stream.streamlen
                url_list.append(myrequest.fullurl)

    traffic_data = {
        'total': traffic_total,
        'tcp_snd': traffic_send_total,
        'tcp_rcv': traffic_receive_total,
        'url_list': url_list
    }
    return traffic_data


if __name__ == '__main__':
    pcap_file = ""
    target_host = "ucus.ucweb.com"
    print parsePcapFile(pcap_file, target_host)
    # output: {'url_list': ['http://ucus.ucweb.com/usquery.php'], 'total': 10022, 'tcp_rcv': 6300, 'tcp_snd': 3722}
~~~
