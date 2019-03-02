---
title: 基 HTTP 的 WebService 测试方法
permalink: post/WebService-Test-Based-On-HTTP
date: 2015/02/13
categories:
  - Testing
  - 性能测试
tags:
  - LoadRunner
  - WebService
  - HTTP(S)
---

在《基于WSDL或SOAP的WebService测试方法--对原理的思考》一文中写道：

> 从通讯协议层面上来看，SOAP报文只是对传输的内容进行了格式封装，具体传输实现还是依赖于其它应用层协议（如HTTP）。因此我们在测试WebService时，完全可以抛开WSDL和SOAP，直接从HTTP协议层面获取请求和响应的内容，然后采用测试工具构造HTTP请求，实现对WebService的调用。

在本篇文章中，`52test.org`仍将在测试案例[天气预报WebService服务](
http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx)的基础上，详细介绍如何通过HTTP协议测试WebService。

## 获取HTTP请求

在`天气预报WebService服务`的各个接口介绍页面中，均包含一个测试工具，可对接口进行调用测试。

例如，接口getWeatherbyCityName的测试工具如下图所示。在theCityName参数框内输入城市的名称，点击【调用】按钮，即可实现对getWeatherbyCityName接口的调用，并获得返回结果。

![](/images/150213_01.png)

在WebService的调用过程中，我们无需关注它具体是采用什么样的通讯协议，因为不管是何种通讯协议，具体传输实现还是会依赖于HTTP。因此，我们可以通过HTTP抓包工具对WebService调用过程中的通讯交互数据包进行捕捉。

在这里我们采用Fiddler Web Debugger进行演示。在浏览器中调用接口getWeatherbyCityName的测试工具时，在Fiddler中抓取到对应的HTTP请求，如下图所示。

![](/images/150213_02.png)

从该HTTP请求可以获得如下关键信息：

- HTTP请求类型为POST，HTTP版本为1.1
- 请求的URL为：http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx/getWeatherbyCityName
- POST的数据包为：theCityName=%E5%B9%BF%E5%B7%9E；POST数据包中对中文进行了URL转码

使用获取到的HTTP信息，可构造HTTP请求，从HTTP协议层面对WebService进行调用。

## 在Fiddler中构造HTTP请求

在Fiddler中，可使用Composer对HTTP请求进行构造，如下图所示。

![](/images/150213_03.png)

在Request Body中，修改请求参数theCityName为不同的城市（例如，重庆），Execute请求，查看返回结果。

![](/images/150213_04.png)

## 在LoadRunner中构造HTTP请求

若要进行性能测试，则需在性能测试工具中构造HTTP请求，再通过多进程或多线程机制实现并发压力测试。

在LoadRunner中，可在Web(HTTP/HTML)虚拟用户协议中，采用web_custom_request函数来构造HTTP请求。

具体的代码实现及回放结果如下图所示。

![](/images/150213_05.png)

虽然在LoadRunner中返回的中文显示为乱码，但是从城市编码（57516）可以看出，脚本执行后返回了正确的结果。

## 写在后面

通过这篇文章可以看出，在通讯协议层面上对应用服务进行测试时，可以采用更底层的协议。当然，由于HTTP协议是基于Socket的，在测试WebService时也可以从Socket协议层面进行测试，但估计没人会那么去做。

至此，我们已经对主流的WebService测试方法完成了总结，相关的文章如下：

- [测试工程师的自我修养--理解WebService]({% post_url 2013-08-05-测试工程师的自我修养--理解WebService %})
- [LoadRunner基于WSDL的WebService测试方法]({% post_url 2013-08-02-LoadRunner基于WSDL的WebService测试方法 %})
- [LoadRunner基于SOAP的WebService测试方法]({% post_url 2013-08-06-LoadRunner基于SOAP的WebService测试方法 %})
- [基于WSDL或SOAP的WebService测试方法--对原理的思考]({% post_url 2015-02-12-基于WSDL或SOAP的WebService测试方法--对原理的思考 %})
- [基于HTTP的WebService测试方法]({% post_url 2015-02-13-基于HTTP的WebService测试方法 %})
