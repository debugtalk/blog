---
title: 使用SIPp对基于SIP协议的IP电话通信服务器进行性能测试
permalink: post/SIPp-IP-Telephone-Server-Performance-Testing
date: 2014/05/11
categories:
  - Testing
  - 性能测试
tags:
  - SIP
---

## 背景知识介绍

### IP电话
IP电话是指在IP网络上打电话。所谓“IP网络”就是“使用IP协议的分组交换网”的简称。
常见的IP电话有VoIP（Voice over IP），Internet Telephony 和 VON（Voice over Net）。

### IP电话网关
IP电话网关（IP Telepathy Gateway），是公用电话网（即公用电路交换电话网，又称传统电话网或电信网）与IP网络的接口设备，其作用包含两个方面：

- 在电话呼叫阶段和呼叫释放阶段进行电话信令的转换
- 在通话期间进行话音编码的转换

IP电话网关的出现，实现了PC机用户之间的IP电话通话（无需经过IP电话网关），PC机用户与固定电话用户的IP电话通话（仅需经过IP电话网关1次），以及固定电话用户之间的IP电话通话（需要经过IP电话网关2次）。

### IP电话所需要的几种应用协议
在IP电话的通信中，至少需要两种应用协议，即信令协议和传送协议。
其中，**信令协议**的作用是帮助主叫者在因特网上找到被叫用户。在公用电话网中，电话交换机根据用户所拨打的号码就能够通过合适的路由找到被叫用户，并在主叫和被叫之间建立一条电路连接。这些都是依靠电话信令（Signaling）实现的。我们听到的振铃音、忙音或一些录音提示，以及打完电话挂机释放连接，都是由电话信令来处理的。现在电话网使用的信令是7号信令SS7。利用IP网络打电话同样也需要IP网络能够识别某种信令。但由于IP电话往往要经过已有的公用电话网，因此IP电话的信令必须在功能上与原有的7号信令相兼容，这样才能使IP网络和公用电话网上的两种信令能够互相转换，从而做到互操作。现有的与信令有关的协议为H.323和SIP，本文只介绍SIP协议。
话音分组的**传送协议**，其作用是使用来进行电话通信的话音数据能够以时延敏感属性在因特网中传送。常见的传送协议为RTP。

### SIP协议
SIP协议，即会话发起协议（Session Initiation Protocol），是使用文本方式的客户服务器协议。
SIP系统只有两种构件，即用户代理（user agent）和网络服务器（network server）。
用户代理包含两个程序，即用户代理客户端UAC（User Agent Client）和用户代理服务器UAS（User Agent Server）；前者用来发起呼叫，后者用来接受呼叫。
网络服务器分为代理服务器（proxy server）和重定向服务器（redirect server）。代理服务器接受来自主叫用户的呼叫请求（实际上是来自用户代理客户端UAC的呼叫请求），并将其转发给被叫用户或下一跳代理服务器；若转发给下一跳代理服务器，则下一跳代理服务器再把呼叫请求转发给被叫用户（实际上是转发给用户代理服务器UAS）。重定向服务器不接受呼叫，它通过响应告诉客户下一跳代理服务器的地址，由客户按此地址向下一跳代理服务器重新发送呼叫请求。
SIP的会话共有三个阶段：建立会话、通信和终止会话。图1给出了一个简单的SIP会话的例子。其中建立会话阶段和终止会话阶段都是使用SIP协议，而中间的通信阶段是使用如RTP这样的传送实时话音分组的协议。

{: .center}
![SIP_Simple_Session](/images/20140511201122_SIP_Simple_Session.png)
图1 SIP的简单会话过程

在图1中，主叫方（Tesla）先向被叫方（Marconi）发出INVITE报文，这个报文中含有双方的地址信息以及一些其它信息（如通话时话音编码方式等）；被叫方收到请求后，会返回180 Ringing的状态码，并处于振铃状态；若被叫方接受呼叫请求，则返回200 OK的状态码；主叫方再发送ACK报文作为确认（类似于TCP建立连接时的三次握手），然后双方便完成连接，可以进行通话了；通话过程中，双方中的任何一方都可以发送BYE报文以终止会话。如上便是SIP会话的全过程。

## SIPp工具介绍

### SIPp软件简介
如下是SIPp官方网站上关于SIPp的介绍。

> SIPp is a free Open Source test tool / traffic generator for the SIP protocol. It includes a few basic SipStone user agent scenarios (UAC and UAS) and establishes and releases multiple calls with the INVITE and BYE methods. It can also reads custom XML scenario files describing from very simple to complex call flows. It features the dynamic display of statistics about running tests (call rate, round trip delay, and message statistics), periodic CSV statistics dumps, TCP and UDP over multiple sockets or multiplexed with retransmission management and dynamically adjustable call rates.
SIPp can be used to test various real SIP equipment like SIP proxies, B2BUAs, SIP media servers, SIP/x gateways, SIP PBX, ... It is also very useful to emulate thousands of user agents calling your SIP system.

### SIPp的安装（Windows）
SIPp几乎可以运行在所有UNIX平台上，HPUX、Tru64、Linux (RedHat, Debian, FreeBSD)和Solaris/SunOS。并且，SIPp已被移植到Windows平台。

- 在Linux/Unix平台上，SIPp采用源代码的形式进行提供，需要通过编译源代码的方式进行安装。
- 在Windows平台上，SIPp提供了预编译的可执行文件，可以直接进行安装；也可以通过在Windows系统中安装CYGWIN模拟Linux环境，然后通过编译源代码的方式进行安装。

通常情况下，在Windows平台中通过预编译可执行文件可以快速完成安装，操作简单且成功率高，但该种方式存在局限性，主要有如下几点：

- Windows预编译版本的功能存在删减，不支持PCAP（语音）和密码验证功能；
- Windows的预编译版本较为滞后，例如当前SIPp的最新版本为3.4，而Windows的最新预编译版本为3.2；
- 相比于Linux/Unix平台，SIPp在Windows平台上运行不够稳定，特别是并发量较大时可能会出现问题，因此不适宜进行压力测试。

### SIPp的工作原理
对于电话而言，每台电话机既是客户端（可拨打电话）也是服务端（可接听电话）。同理，SIPp模拟用户代理，也有两种工作模式：UAC和UAS。

SIPp中具有场景（scenario）的概念，它是一个XML格式的文件，其作用是用来描述SIP协议通讯过程。具体地，UAC和UAS分别对应一个场景文件：uac.xml用于描述客户端的呼叫，uas.xml用于描述服务端的响应。在SIPp工具中，已经内置了许多场景文件，可直接使用；测试人员也可参照场景文件的格式要求，自定义编写场景文件。

另外，SIPp采用了数据与场景分离的设计，从而使工具的使用更加灵活。其中，数据包括IP地址、端口号、电话号码、用户名等内容。通常，测试数据保存在CSV文件中，如data.csv。

SIPp是通过命令行的方式操作调用的。例如，在利用SIPp模拟UAC发起呼叫时，可在cmd窗口中运行如下命令：
```shell
sipp -sn uac 172.31.89.4:5060 -r 1 -rp 3000 -inf data.csv -p 7098 -i 172.31.89.242 -s 8001 -sf uac_onecall.xml –m 1000 –l 900
```

可以看出，如果每次都在命令行中输入命令进行运行，效率将十分低下；因此，可以将配置好的命令保存在bat批处理文件中，方便测试时直接调用。

### SIPp的常用工作模式
SIPp具有三种常用工作模式：

- 当SIPp作为UAC时，可向已有电话终端（电话机或运行在电脑上的虚拟终端）发起呼叫；
- 当SIPp作为UAS时，可接收到现有电话终端（电话机或运行在电脑上的虚拟终端）发起的呼叫；
- SIPp还可同时作为UAC和UAS，并使用UAC向UAS发起呼叫，以此来对代理服务器进行测试。

图2是对第三种模式的描述。

{: .center}
![SIPp_Operating_Principle](/images/20140511201122_SIPp_Operating_Principle.jpg)
图2 SIPp工作原理

在该种模式下，需先运行服务端UAS，然后再运行客户端UAC。接下来，UAC便参照uac.xml场景文件的描述，发起呼叫；而UAS则参照uas.xml场景文件的描述，对呼叫进行响应；整个通讯过程遵循SIP协议，在本文的1.4节已经进行了介绍。


## SIPp的使用

### SIPp的配置文件
通过本文2.3节的介绍可知，使用SIPp时会涉及到5个文件：uac.xml, uas.xml, data.csv, uac.bat, uas.bat。

其用途简要说明如下：

- uac.xml：用于描述客户端UAC的SIP信号流程；
- uas.xml：用于描述服务端UAS的SIP信号流程；
- data.csv：存储数据的文件，方便在uac.xml和uas.xml中引入的相应数据；
- uac.bat：存储SIPp命令及参数，便于执行时直接调用，模拟UAC的呼叫；
- uas.bat：存储SIPp命令及参数，便于执行时直接调用，模拟UAS的响应。

由于uac.xml和uas.xml类似，uac.bat和uas.bat类似，本文只对uac.xml、uac.bat和data.csv三个文件进行讲解。

### uac.xml
SIPp默认自带的uac.xml内容如下：

```xml
<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE scenario SYSTEM "sipp.dtd">

<scenario name="Basic Sipstone UAC">
  <!-- In client mode (sipp placing calls), the Call-ID MUST be         -->
  <!-- generated by sipp. To do so, use [call_id] keyword.              -->
  <send retrans="500">
    <![CDATA[

      INVITE sip:[service]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: sipp <sip:sipp@[local_ip]:[local_port]>;tag=[call_number]
      To: sut <sip:[service]@[remote_ip]:[remote_port]>
      Call-ID: [call_id]
      CSeq: 1 INVITE
      Contact: sip:sipp@[local_ip]:[local_port]
      Max-Forwards: 70
      Subject: Performance Test
      Content-Type: application/sdp
      Content-Length: [len]

      v=0
      o=user1 53655765 2353687637 IN IP[local_ip_type] [local_ip]
      s=-
      c=IN IP[media_ip_type] [media_ip]
      t=0 0
      m=audio [media_port] RTP/AVP 0
      a=rtpmap:0 PCMU/8000

    ]]>
  </send>

  <recv response="100" optional="true">
  </recv>

  <recv response="180" optional="true">
  </recv>

  <!-- By adding rrs="true" (Record Route Sets), the route sets         -->
  <!-- are saved and used for following messages sent. Useful to test   -->
  <!-- against stateful SIP proxies/B2BUAs.                             -->
  <recv response="200" rtd="true">
  </recv>

  <!-- Packet lost can be simulated in any send/recv message by         -->
  <!-- by adding the 'lost = "10"'. Value can be [1-100] percent.       -->
  <send>
    <![CDATA[

      ACK sip:[service]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: sipp <sip:sipp@[local_ip]:[local_port]>;tag=[call_number]
      To: sut <sip:[service]@[remote_ip]:[remote_port]>[peer_tag_param]
      Call-ID: [call_id]
      CSeq: 1 ACK
      Contact: sip:sipp@[local_ip]:[local_port]
      Max-Forwards: 70
      Subject: Performance Test
      Content-Length: 0

    ]]>
  </send>

  <!-- This delay can be customized by the -d command-line option       -->
  <!-- or by adding a 'milliseconds = "value"' option here.             -->
  <pause/>

  <!-- The 'crlf' option inserts a blank line in the statistics report. -->
  <send retrans="500">
    <![CDATA[

      BYE sip:[service]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: sipp <sip:sipp@[local_ip]:[local_port]>;tag=[call_number]
      To: sut <sip:[service]@[remote_ip]:[remote_port]>[peer_tag_param]
      Call-ID: [call_id]
      CSeq: 2 BYE
      Contact: sip:sipp@[local_ip]:[local_port]
      Max-Forwards: 70
      Subject: Performance Test
      Content-Length: 0

    ]]>
  </send>

  <recv response="200" crlf="true">
  </recv>

  <!-- definition of the response time repartition table (unit is ms)   -->
  <ResponseTimeRepartition value="10, 20, 30, 40, 50, 100, 150, 200"/>

  <!-- definition of the call length repartition table (unit is ms)     -->
  <CallLengthRepartition value="10, 50, 100, 500, 1000, 5000, 10000"/>

</scenario>
```

如该文件所示，UAC首先发送INVITE请求，按照预期，UAC将依次接收100、180和200状态码，然后UAC再次发送ACK进行确认，从而完成通信连接的建立；最后，UAC发送BYE请求，结束通话，从而断开通信连接。

### data.csv
在data.csv文件中，第一行描述数据的读取方式，如顺序读取（SEQUENTIAL）、随机读取（RANDOM），或者自定义方式（USER）。
从第二行开始，每行描述一次呼叫时使用的数据；如果每次呼叫时调用的参数有多个，那么就可用分号（";"）进行分离，并可在XML文件中进行调用，每行的数据从左到右依次为[field0], [field1], ...。

csv文件的编写示例如下：

```csv
SEQUENTIAL
#注释将被忽略
Sarah;sipphone32
Bob;sipphone12
#This line too
Fred;sipphone94
```

XML调用CSV的具体方式如图3所示。

{: .center}
![XML_Invoke_CSV](/images/20140511201122_XML_Invoke_CSV.jpg)
图3 XML调用CSV的原理

### uac.bat
```shell
sipp -sn uac 172.31.89.4:5060 -r 1 -rp 3000 -inf data.csv -p 7098 -i 172.31.89.242 -s 8001 -sf uac_onecall.xml –m 1000 –l 900
```

各个参数说明：

- 172.31.89.4:5060：远端地址和端口（在xml脚本中用[remote_ip]，[remote_port]引用）
- -r 1 -rp 3000：每三秒钟（3000毫秒）发起一个呼叫
- -inf data.csv：引入数据配置文件
- -p 7098：本地端口（在xml脚本中用[local_port]引用）
- -i 172.31.89.242：本地地址（在xml脚本中用[local_ip]引用）
- -s 8001：被叫号码（在xml脚本中用[service]引用）
- -sf uac_onecall.xml：引用xml脚本文件，根据需要模拟的呼叫流程编写
- -sn uac :执行默认的uac流程，如需执行自己编写的流程文件，命令中应不含此参数
- -m 1000:发送1000次呼叫后停止并退出。
- -l 900 :最大同时保持呼叫量，默认值为3*caps值呼叫时长，当因种种原因导致现存呼叫总数达到此值时，SIPp将停止产生新的呼叫，等待现存呼叫总数低于此值时才继续产生呼叫。
- -trace_err跟踪所有错误消息，并把错误消息保存到文件场景文件描述的 {fileName}\_{pid}\_errors.log 文件中
- -trace_screen 当程序结束时候打印统计信息并弹出屏幕（如果在后台运行的话）


## 使用SIPp对基于SIP协议的网络电话进行性能测试

### 测试内容
- 测试某通信服务器在400组并发呼叫过程中的CPU负载峰值和内存占用率。

### 测试场景分析
呼叫发起端：湖北省公安厅的两台测试机，每台测试机模拟出等量的电话终端，向十堰市公安局的物理电话机发起呼叫。
电话接收端：十堰市公安局的400台物理电话机。
网络环境：湖北省公安信息网。

测试环境的网络拓扑图如图4所示。

{: .center}
![Network_Topology_Map](/images/20140511201122_Network_Topology_Map.gif)
图4 被测系统的网络拓扑图

### 测试方法
利用SIPp测试工具模拟电话终端，向物理电话机终端发起呼叫，保持呼叫16秒后，SIPp终止呼叫。
在测试过程中，通过命令的方式监控并记录通信服务器的CPU负载峰值和内存占用率。

### 测试步骤
（1）配置SIPp测试工具：在湖北省公安厅的两台测试机上分别配置SIPp的场景文件（uacTest.xml，详见附录），数据文件（CallNumber.csv，详见附录）和测试控制文件（test.bat，详见附录）。
（2）开启通信服务器的资源监控：远程登录至十堰市公安局网络电话通信服务器，执行资源监控命令，开启对通信服务器CPU负载和内存的监控。
（3）执行测试：在湖北省公安厅的两台测试机上同时执行SIPp控制文件（bat文件）。
（4）获取测试结果：测试完毕后，导出被测通信服务器的资源监控结果，提取出并发测试期间中的资源监控结果。

## 参考资料
- 电子工业出版社 计算机网络（第5版）谢希仁 编著。
- http://sipp.sourceforge.net/

## 附录

test.bat
```shell
sipp -sf uac.xml -inf CallNumber.csv -i 10.XX.XX.151 -p 5061 -s 96018702 -m 1 -r 1 10.XX.XX.114:5060 -trace_err
```

uacTest.xml
```xml
<?xml version="1.0" encoding="ISO-8859-1" ?>
<!DOCTYPE scenario SYSTEM "sipp.dtd">

<scenario name="Basic Sipstone UAC">
  <!-- In client mode (sipp placing calls), the Call-ID MUST be         -->
  <!-- generated by sipp. To do so, use [call_id] keyword.              -->
  <send retrans="500">
    <![CDATA[

      INVITE sip:[field0]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: "[service]" <sip:[service]@[remote_ip]>;tag=[call_number]
      To: "[field0]" <sip:[field0]@[remote_ip]>
      Call-ID: [call_id]
      CSeq: 1 INVITE
      Contact: sip:[service]@[local_ip]:[local_port]
      Max-Forwards: 70
      Subject: Performance Test
      Content-Type: application/sdp
      Content-Length: [len]

      v=0
      o=- 1 2 IN IP[local_ip_type] [local_ip]
      s=-
      c=IN IP[media_ip_type] [media_ip]
      t=0 0
      m=audio [media_port] RTP/AVP 0 8 18 101
      a=rtpmap:18 G729/8000

    ]]>
  </send>

  <recv response="100" optional="true">
  </recv>

  <recv response="180">
  </recv>

  <!-- Set Ring Time   -->
  <pause milliseconds="8000"/>

  <!-- Abort Call   -->
  <send retrans="500">
    <![CDATA[

      CANCEL sip:[field0]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: "[service]" <sip:[service]@[remote_ip]>;tag=[call_number]
      To: "[field0]" <sip:[field0]@[remote_ip]>
      Call-ID: [call_id]
      CSeq: 1 CANCEL

    ]]>
  </send>

  <!-- By adding rrs="true" (Record Route Sets), the route sets         -->
  <!-- are saved and used for following messages sent. Useful to test   -->
  <!-- against stateful SIP proxies/B2BUAs.                             -->
  <recv response="200" rtd="true"></recv>

  <!-- Packet lost can be simulated in any send/recv message by         -->
  <!-- by adding the 'lost = "10"'. Value can be [1-100] percent.       -->
  <send>
    <![CDATA[

      ACK sip:[service]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: sipp <sip:sipp@[local_ip]:[local_port]>;tag=[call_number]
      To: sut <sip:[service]@[remote_ip]:[remote_port]>[peer_tag_param]
      Call-ID: [call_id]
      CSeq: 1 ACK
      Contact: sip:sipp@[local_ip]:[local_port]
      Max-Forwards: 70
      Subject: Performance Test
      Content-Length: 0

    ]]>
  </send>

  <!-- This delay can be customized by the -d command-line option       -->
  <!-- or by adding a 'milliseconds = "value"' option here.             -->
  <pause milliseconds="8000"/>

  <!-- The 'crlf' option inserts a blank line in the statistics report. -->
  <send retrans="500">
    <![CDATA[

      BYE sip:[service]@[remote_ip]:[remote_port] SIP/2.0
      Via: SIP/2.0/[transport] [local_ip]:[local_port];branch=[branch]
      From: sipp <sip:sipp@[local_ip]:[local_port]>;tag=[call_number]
      To: sut <sip:[service]@[remote_ip]:[remote_port]>[peer_tag_param]
      Call-ID: [call_id]
      CSeq: 2 BYE
      Contact: sip:sipp@[local_ip]:[local_port]
      Max-Forwards: 70
      Subject: Performance Test
      Content-Length: 0

    ]]>
  </send>

  <recv response="200" crlf="true">
  </recv>

  <!-- definition of the response time repartition table (unit is ms)   -->
  <ResponseTimeRepartition value="10, 20, 30, 40, 50, 100, 150, 200"/>

  <!-- definition of the call length repartition table (unit is ms)     -->
  <CallLengthRepartition value="10, 50, 100, 500, 1000, 5000, 10000"/>

</scenario>
```

CallNumber.csv
```csv
SEQUENTIAL
96038000;
96038001;
96038002;
......
```
