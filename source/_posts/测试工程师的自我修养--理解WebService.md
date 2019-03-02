---
title: 测试工程师的自我修养--理解WebService
permalink: post/concept-about-webservice
date: 2013/08/05
categories:
  - Testing
  - 性能测试
tags:
  - WebService
  - WSDL
  - SOAP
---

随着WebService技术的广泛应用，项目中对WebService进行测试的需求越来越多，而对WebService的性能测试更是重中之重。

作为测试人员，虽然不需要参与WebService的编码实现，但是对WebService相关概念的掌握仍然必不可少，只有这样，才能在测试工作中游刃有余。

本文将对WebService的概念及其相关名词进行阐述，后续将在此基础上，对如何采用LoadRunner测试WebService进行详细介绍。

## 什么是WebService

WebService，顾名思义就是基于Web的服务。WebService是一种构建应用程序的普遍模型，可以在任何支持网络通信的操作系统中实施运行，并作为应用组件，采用Web的方式接收和响应外部系统的请求，逻辑性地为其它应用程序提供数据与服务。

无论是简单还是复杂的业务处理，都可以将其封装为WebService，部署成功以后，其它应用程序就可以发现并调用部署的服务。而且，应用程序并不需要关注WebService是基于什么样的系统平台和架构开发实现的，它只需要通过通用的网络协议（如Http）和标准的数据格式（如XML、Soap）来访问WebService，即可通过WebService内部执行得到所需结果。

在实际应用场景中，很多企业用户经过多年的积累，已经部署了很多应用系统，这些应用系统在企业运营中分担着不同的功能或任务。随着企业的发展壮大，由于种种原因，这些企业用户逐渐开始考虑如何对原有的这些旧系统进行整合。使用WebService方式将这些旧的应用系统整合起来，对外部提供一致的接口，不仅可以达到整合已有旧系统的目的，还可以避开因为完全构建一个新系统而产生的风险，这样就大大降低了项目的成本和风险。这也是SOA得以被客户广泛采纳的主要原因。

## WebService的相关名词解释：WSDL和SOAP

在对WebService进行测试时，接触到最多的两个名词就是WSDL和SOAP。测试人员在跟开发人员沟通时，可能常常会听到开发人员说：

- “WebService已经部署好了，详细的服务描述你可以参照WSDL”
- “SOAP报文我已经准备好了，你帮我测下这几个接口的性能吧”

对于不了解WebService的测试人员，可能刚开始的时候会一头雾水，不明白WSDL和SOAP的含义，对于WebService测试任务如何开展就更是不知所措了。

经过在网上一番搜索，看见好多帖子都说使用LoadRunner测试WebService可以采用基于WSDL的【Add Service Call】和基于SOAP的【Import SOAP】的方法。看到这里，新手可能会感到更加迷惑了，WSDL和SOAP到底有啥关联，这两种测试方法到底有啥区别？

实际上，WSDL与SOAP只是WebService的两大标准，它们之间并没有必然的联系。我们可以先比较一下较为官方的名词解释。

如下是[W3C](http://www.w3.org/TR/wsdl)上关于WSDL的解释。

> WSDL is an XML format for describing network services as a set of endpoints operating on messages containing either document-oriented or procedure-oriented information. The operations and messages are described abstractly, and then bound to a concrete network protocol and message format to define an endpoint. Related concrete endpoints are combined into abstract endpoints (services). WSDL is extensible to allow description of endpoints and their messages regardless of what message formats or network protocols are used to communicate.

如下是[wikipedia](http://en.wikipedia.org/wiki/SOAP)上关于SOAP的解释。

> SOAP, originally defined as Simple Object Access Protocol, is a protocol specification for exchanging structured information in the implementation of Web Services in computer networks. It relies on XML Information Set for its message format, and usually relies on other Application Layer protocols, most notably Hypertext Transfer Protocol (HTTP) or Simple Mail Transfer Protocol (SMTP), for message negotiation and transmission.

对比两者的详细解释，可以得出：

- WSDL描述的是服务本身，它以machine-readable的形式对外界描述了该Web Service提供的服务接口，包括Service的名称，调用Service时需要传入的参数类型和格式，以及返回的数据结构。另外，它还以message formats和network protocols无关的形式对网络传输进行了描述。
- SOAP本身就是一种通信协议，利用它以WSDL定义的形式对Service的调用方式进行描述，包括调用的具体Service名称、参数名称和参数数值。
- 对于WebService来说，WSDL是必须的，而SOAP只是通信协议中较为常用的一种，可以用其它通信协议代替；例如可以直接采用HTTP GET/POST的形式对WebService进行调用。

## 演示案例

为了便于直观理解，本文选取互联网上常用的[天气预报WebService服务](http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx)作为案例进行讲解。

从介绍页面可知，该WeatherWebService一共提供了5项服务：getSupportCity、getSupportDataSet、getSupportProvince、getWeatherbyCityName和getWeatherbyCityNamePro。

对于该WeatherWebService，服务提供商通过[WSDL](
http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx?WSDL)对服务进行了完整的定义，大家可通过这个链接了解一下WSDL文档的结构。

对于每一项服务，服务商提供了4种调用方式：SOAP 1.1、SOAP 1.2、HTTP GET、HTTP POST，并对每一种调用方式都给出了请求和响应示例。

不管是有了WSDL，还是有了SOAP或HTTP的请求和响应示例，就可以对WebService开展测试工作了。而且，这三者分别对应了3种不同的测试方法，可在项目中根据实际情况进行选择。

后续，[52test.org](http://52test.org)将基于WeatherWebService天气服务，分3篇文章分别对采用LoadRunner测试WebService的方法进行详细介绍，并进行案例演示。

- 《LoadRunner基于WSDL的WebService测试方法》
- 《LoadRunner基于SOAP的WebService测试方法》
- 《LoadRunner基于HTTP的WebService测试方法》

敬请期待！
