---
title: LoadRunner 基于 SOAP 的 WebService 测试方法
permalink: post/LoadRunner-SOAP-WebService
date: 2013/08/06
categories:
  - Testing
  - 性能测试
tags:
  - LoadRunner
  - WebService
  - SOAP
---

在《LoadRunner基于WSDL的WebService测试方法》一文中，`52test.org`基于案例[天气预报WebService服务](
http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx)，详细讲解了在只获悉WSDL的情况下，如何采用LoadRunner对WebService进行测试。

然而，在实际项目中基于WSDL来测试WebService的情况并不多，WSDL并不是WebService测试的最佳选择。

最主要的原因还是因为WSDL文档过于复杂。在案例（天气预报WebService服务）中，WeatherWebService虽然只包含5个接口，但是其WSDL对应的XML文档多达近500行；而实际项目中，被测系统往往包含上百个WebService接口，其WSDL文档的规模可想而知。

而且，WSDL文档包含的信息过于全面，其中大部分信息对于WebService测试是没有必要的。虽然采用LoadRunner导入WSDL后可以清晰地看见所有接口函数，但是每次都要在上百个接口中选择被测接口也是一件很麻烦的事情。特别是对WebService进行性能测试时，往往只需要选择少数典型的接口。

那么，除了WSDL，还有什么更好的方式呢？

答案就是SOAP。

SOAP是Simple Object Access Protocol的缩写，从字面上就可以知道它是一种通信协议。在这里我们不对SOAP进行详细讲解，大家有兴趣的话可以参看之前发布的《测试工程师的自我修养--理解WebService》一文。

采用SOAP对WebService进行测试时，大家只需要知道它以WSDL定义的形式对WebService的调用方式进行了具体描述，包括调用的具体WebService接口名称、参数名称和参数数值。每一个SOAP报文对应了一个WebService接口的调用方式，在其中包含相应的测试数据后，完全可以把它等同于WebService测试用例。

这对于测试人员来说真是再适合不过了。特别是对于新接触WebService的测试人员来说，对WebService的调用方式及其合法参数可能不是很清楚，这时如果能获取到被测接口的SOAP报文，那么测试工作将可以大大简化了。正因如此，在实际项目中，基于SOAP对WebService进行测试的方法应用得更为普遍。

本文将继续在天气预报WebService服务的案例基础上，详细讲解如何采用LoadRunner基于SOAP对WebService进行测试。

需要说明的是，本文只针对测试脚本的开发展开描述，对测试场景的设计暂不进行讨论。

本文中采用的LoadRunner版本为V11.0，不同版本可能会存在一定差异。

## 获取SOAP报文

基于SOAP对WebService进行测试，第一步当然是要先获取到被测接口的SOAP报文，通常可在被测系统的接口设计说明文档（如果有的话）中查询得到，也可直接找开发人员获取。

从测试WebService接口的角度来说，SOAP报文应该至少包含哪些要素呢？

在本文的演示案例中，以接口getWeatherbyCityName为例，大家在[getWeatherbyCityName的介绍页面](http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx?op=getWeatherbyCityName)中可以看到，getWeatherbyCityName支持SOAP 1.1和SOAP 1.2。本文采用SOAP 1.1进行演示。

采用SOAP 1.1的请求报文如下所示：

```xml
POST /WebServices/WeatherWebService.asmx HTTP/1.1
Host: webservice.webxml.com.cn
Content-Type: text/xml; charset=utf-8
Content-Length: length
SOAPAction: "http://WebXml.com.cn/getWeatherbyCityName"

<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <getWeatherbyCityName xmlns="http://WebXml.com.cn/">
      <theCityName>string</theCityName>
    </getWeatherbyCityName>
  </soap:Body>
</soap:Envelope>
```

将上面这段xml代码保存至一个xml文件，如getWeatherbyCityName.xml，即得到测试所需的SOAP报文。

在报文头中，我们还获取到两个重要信息：

- Service的URL为`/WebServices/WeatherWebService.asmx`，加上被测系统的域名后得到完整的URL为http://webservice.webxml.com.cn/WebServices/WeatherWebService.asmx
- SOAPAction: "http://WebXml.com.cn/getWeatherbyCityName"

## 在LoadRunner中导入SOAP报文

在LoadRunner的Web Services协议中，点击【Import SOAP】，加载之前准备好的SOAP报文，即xml文件；加载完成后，在URL和SOAP Action中分别填入获取得到的地址信息；在Response Parameter中填写存储返回内容的参数名称；如下图所示。

![](/images/130806_01.png)

点击【OK】后，便能在脚本界面中生成一个soap_request函数，如下图所示。

![](/images/130806_02.png)

通过上图可知，SOAP报文中的全部内容已成功转换为LoadRunner的soap_request函数。

## 回放脚本，查看结果

将脚本中的字段theCityName赋值为“广州”；在“Run-time Settings”中打开日志“Extended log”，勾选“Parameter substitution”和“Data returned by server”。运行脚本后，查看“Replay Log”，如下图所示。

![](/images/130806_03.png)

在这里如果将脚本回放得到的结果与在浏览器中调用返回的结果进行对比，会发现内容并不一致。在LoadRunner脚本中将theCityName更改为“深圳”、“上海”等城市后重新回放脚本，会发现内容仍然不一致，且LoadRunner每次回放得到的结果都相同。

回顾报文中的Content-Type信息可知，请求报文与响应报文的编码均为UTF-8。因此可以猜想该问题是由于LoadRunner脚本中的编码不为UTF-8造成的，从而使得脚本中的设置的汉字theCityName不被服务商所识别。

对LR脚本中需传送的汉字进行编码转换，即将脚本中的汉字转换为UTF-8，转换方法如下图所示：

![](/images/130806_04.png)

重新回放脚本，查看Replay Log。再次对比LoadRunner的Replay Log和浏览器的返回页面可知，LoadRunner对Web Service实现了正确的调用。

通过该案例可知，调用WebService时需要保证输入参数的编码与WebService服务的编码一致，只有这样才能返回正确的结果，这一点需要在调试脚本时格外注意。
