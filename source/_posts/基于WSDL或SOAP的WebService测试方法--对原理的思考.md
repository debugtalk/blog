---
title: 基于WSDL或SOAP的WebService测试方法--对原理的思考
permalink: post/Introspection-on-WebService-Test
date: 2015/02/12
categories:
  - Testing
  - 性能测试
tags:
  - LoadRunner
  - WebService
  - WSDL
  - SOAP
---

截止至今，我们已经总结了两种WebService测试方法，分别对应了两种应用场景：

- 在只获知WSDL的情况下，如何采用LoadRunner测试WebService
- 在具有SOAP报文的情况下，如何采用LoadRunner测试WebService

在文章《LoadRunner基于WSDL的WebService测试方法》和《LoadRunner基于SOAP的WebService测试方法》中，已经详细地描述了两种测试方法的具体实现方式，即使对于一个新接触WebService的测试人员，按照文章中的方法也基本都能完成测试任务。

但是，读到这里你是否会感到困惑：这两种测试方法之间的主要区别在哪儿？两者之间是否存在什么内在联系呢？

没错，虽然从LoadRunner的操作方式（导入WSDL和导入SOAP）与最终生成的封装函数（web_service_call和soap_request）来看，两者完全是两种不同的测试方法，但是从原理层面上讲，他们本质上都是一样的。

别惊讶，我们先来回顾一下WebService的概念。可参考《测试工程师的自我修养--理解WebService》。

在WebService中，涉及到的技术名词主要有包括WSDL和SOAP。其中，WSDL就如同WebService的规格说明书，它详细描述了WebService提供的服务接口，包括每个接口的方法名称、接受的参数类型，以及返回的数据结构。除此之外，WSDL还描述了网络传输协议，即WebService支持以什么协议进行通讯交互。而SOAP作为一种XML编码格式的通讯协议，在WebService中应用得最为广泛，基本上绝大多数WebService都支持SOAP协议，以至于谈到WebService时，会不由自主地联想到SOAP，甚至非常多的人混淆了WSDL和SOAP的概念，常在网上提问两者的区别。

事实上，对于WebService而言，SOAP并不是必须的，我们完全可以采用别的通讯协议来代替它。

现在再回到前面的问题。

在基于WSDL的WebService测试方法中：LoadRunner导入WSDL后，对WSDL进行解析，分析出里面包含的接口以及支持的通讯协议，并以友好的交互界面展示给测试人员。测试人员在界面中选择接口（Operation）和通讯协议（Port Name）后，LoadRunner进行封装，生成了web_service_call函数。

而在基于SOAP的WebService测试方法中：给定的SOAP报文已经限定了特定的接口和输入参数，当然，既然是SOAP报文，采用的通讯协议当然就是SOAP协议，并且在报文中指明了特定的SOAP版本。LoadRunner导入SOAP报文后，经过封装，生成了soap_request函数。

说到这里大家应该比较清楚了，不管是基于WSDL还是基于SOAP，最终无非都是指定WebService接口函数和通讯协议，然后，输入参数，获取响应结果。至于LoadRunner采用了什么样的封装函数，那也只是不同的表现形式而已。

其实，从通讯协议层面上来看，SOAP报文只是对传输的内容进行了格式封装，具体传输实现还是依赖于其它应用层协议（如HTTP）。因此我们在测试WebService时，完全可以抛开WSDL和SOAP，直接从HTTP协议层面获取请求和响应的内容，然后采用测试工具构造HTTP请求，实现对WebService的调用。

在下一篇文章中，`52test.org`将详细介绍如何通过HTTP协议测试WebService，敬请关注。
