---
title: HttpRunner 支持 HAR 意味着什么？
permalink: post/HttpRunner-supports-HAR
date: 2017/11/14
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
  - HAR
---

`HttpRunner`开始支持`HAR`啦！！！

如果你还没有体会到这三个感叹号的含义，那们你可能对`HAR`还不了解。

## HAR 是什么？

`HAR`的全称为`HTTP Archive`，是[`W3C(World Wide Web Consortium)`][w3c]发布的一个通用标准。简单地说，`HAR`是一个约定的`JSON`文件格式，用于记录`HTTP`请求交互的所有内容，包括请求响应的详细记录和性能度量数据。

虽然当前`HAR`标准还处于`Draft`状态，但它已经被业界广泛地采用了，许多我们日常使用的工具都已支持`HAR`。在下面罗列的工具中，相信大家都已经比较熟悉了。

- Fiddler
- Charles Web Proxy
- Google Chrome
- Firebug
- HttpWatch
- Firefox
- Internet Explorer 9
- Microsoft Edge
- Paw
- Restlet Client

可以看出，工具覆盖了主流的抓包工具、浏览器和接口测试工具。这些工具都支持`HAR`标准，可以将录制得到的数据包导出为`.har`的文件。

假如我们可以将`HAR`格式转换为`HttpRunner`的自动化测试用例，这就相当于`HttpRunner`可以和非常多的工具结合使用，并获得了接口录制和用例生成功能，灵活性和易用性都将得到极大的提升。

那么，将`HAR`格式转换为`HttpRunner`的自动化测试用例是否可行呢？

我们不妨先研究下`HAR`的格式。

## HAR 格式详解

通过如上列出的任意一款工具，都可以将录制得到的数据包导出为`.har`的文件。我们采用文本编辑器打开`.har`文件后，会发现是一个`JSON`的数据结构。

默认情况下，`.har`文件的`JSON`数据结构是经过压缩的，直接看可能不够直观。推荐大家可以在文本编辑器中安装`Prettify JSON`的插件，然后就可以将压缩后的`JSON`数据一键转换为美观的格式。

更好的方式是，我们可以直接查看`W3C`编写的[`HAR`格式标准][har-specs]。

通过文档可知，`HAR`是只有一个key的`JSON`数据结构，并且key值只能为`log`；而`log`的值也为一个`JSON`结构，里面的key包括：`version`、`creator`、`browser`、`pages`、`entries`、`comment`。

```json
{
    "log": {
        "version": "",
        "creator": {},
        "browser": {},
        "pages": [],
        "entries": [],
        "comment": ""
    }
}
```

其中，`version`、`creator`和`entries`是必有字段，不管是哪款工具导出的`.har`文件，肯定都会包含这三个字段。而我们在转换生成自动化测试用例时，只需获取HTTP请求和响应的内容，这些全都包含在`entries`里面，因此我们只需要关注`entries`的内容即可。

`entries`字段对应的值为一个列表型数据结构，里面的值按照请求时间进行排序，罗列出各个HTTP请求的详细内容。具体地，HTTP请求记录的信息如下所示：

```json
"entries": [
    {
        "pageref": "page_0",
        "startedDateTime": "2009-04-16T12:07:23.596Z",
        "time": 50,
        "request": {...},
        "response": {...},
        "cache": {...},
        "timings": {},
        "serverIPAddress": "10.0.0.1",
        "connection": "52492",
        "comment": ""
    },
]
```

由此可见，记录的HTTP信息非常全面，包含了HTTP请求交互过程中的所有内容。

而从生成自动化测试用例的角度来看，我们并不需要那么多信息，我们只需从中提取关键信息即可。

编写自动化测试用例，最关键的信息是要知道接口的请求URL、请求方法、请求headers、请求数据等，这些都包含在`request`字段对应的字典中。

```json
"request": {
    "method": "GET",
    "url": "http://www.example.com/path/?param=value",
    "httpVersion": "HTTP/1.1",
    "cookies": [],
    "headers": [],
    "queryString" : [],
    "postData" : {},
    "headersSize" : 150,
    "bodySize" : 0,
    "comment" : ""
}
```

根据这些信息，我们就可以完成HTTP请求的构造。

当请求发送出去后，我们要想实现自动化地判断接口响应是否正确，我们还需要设置一些断言。而与HTTP响应相关的所有信息全都包含在`response`字段对应的字典中。

```json
"response": {
    "status": 200,
    "statusText": "OK",
    "httpVersion": "HTTP/1.1",
    "cookies": [],
    "headers": [],
    "content": {},
    "redirectURL": "",
    "headersSize" : 160,
    "bodySize" : 850,
    "comment" : ""
}
```

从通用性的角度考虑，我们会判断HTTP响应的状态码是否正确，这对应着`status`字段；如果我们还想在接口业务层面具有更多的判断，我们还会判断响应内容中的一些关键字段是否符合预期，这对应着`content`字段。

```json
"content": {
    "size": 33,
    "compression": 0,
    "mimeType": "text/html; charset=utf-8",
    "text": "\n",
    "comment": ""
}
```

对于`content`字段，可能会稍微复杂一些，因为接口响应内容的格式可能多种多样。

例如，响应内容可能`text/html`页面的形式，也可能是`application/json`的形式，具体类型可以查看`mimeType`得到，而具体的内容存储在`text`字段中。

另外，有时候响应数据还可能是经过编码的，用的最多的编码方式为`base64`。我们可以根据`encoding`字段获取得到具体的编码形式，然后采用对应的解码方式对`text`进行解码，最终获得原始的响应内容。

```json
"content": {
    "size": 63,
    "mimeType": "application/json; charset=utf-8",
    "text": "eyJJc1N1Y2Nlc3MiOnRydWUsIkNvZGUiOjIwMCwiVmFsdWUiOnsiQmxuUmVzdWx0Ijp0cnVlfX0=",
    "encoding": "base64"
},
```

以上面的`content`为例，我们通过`encoding`查看到编码形式为`base64`，并通过`text`字段获取到编码后的内容；那么我们就可以采用`base64`的解码函数，转换得到原始的内容。

```bash
>>> import base64
>>> base64.b64decode(text)
b'{"IsSuccess":true,"Code":200,"Value":{"BlnResult":true}}'
```

同时，我们根据`mimeType`可以得到响应内容`application/json`数据类型，那么就可以对其再进行`json.loads`操作，最终得到可供程序处理的`JSON`数据结构。

通过上述对`HAR`格式的详细介绍，可以看出`HAR`格式十分清晰，在对其充分了解的基础上，再编写测试用例转换工具就很简单了。

## har2case

编码过程没有太多值得说的，直接看最终成品吧。

最终产出的工具就是[`har2case`][har2case]，是一个命令行工具，可以直接将`.har`文件转换为`YAML`或`JSON`格式的自动化测试用例。

当前`har2case`已经上传到`PYPI`上了，通过`pip`或`easy_install`即可安装。

```bash
$ pip install har2case
# or
$ easy_install har2case
```

使用方式很简单，只需在`har2case`命令后分别带上`HAR`源文件路径和目标生成的`YAML/JSON`路径即可。

```bash
$ har2case tests/data/demo.har demo.yml
INFO:root:Generate YAML testset successfully: demo.yml

$ har2case tests/data/demo.har demo.json
INFO:root:Generate JSON testset successfully: demo.json
```

可以看出，具体是生成`YAML`还是`JSON`格式的问题，取决于指定目标文件的后缀：后缀为`.yml`或`.yaml`则生成`YAML`文件，后缀为`.json`则生成`JSON`文件。

如果不指定目标文件也行，则会默认生成`JSON`文件，文件名称和路径与`.har`源文件相同。

```bash
$ har2case tests/data/demo.har
INFO:root:Generate JSON testset successfully: tests/data/demo.json
```

具体的使用方式可以通过执行`har2case -h`查看。

在大多数情况下，生成的用例可直接在`HttpRunner`中使用，当然，是做接口自动化测试、接口性能测试，还是持续集成线上监控，这都取决于你。

不过，假如录制的场景中包含动态关联的情况，即后续接口请求参数依赖于前面接口的响应，并且每次调用接口时参数都会动态变化，那么就需要人工再对生成的脚本进行关联处理，甚至包括编写一些自定义函数等。

## 后续计划

读到这里，相信大家应该能体会到文章开头那三个感叹号的含义了，我也的确是带着难以言表的兴奋之情发布这个新功能的。

经过小范围的实际使用，效果很是不错，接口自动化测试用例的编写效率得到了极大的提升。而且，由于`HAR`本身的开放性，留给用户的选择非常多。

即便如此，我觉得`HttpRunner`的易用性还可以得到更大的提升。

当前，我规划了两项新特性将在近期完成：

- 支持`PostMan`：将`Postman Collection Format`格式转换为`HttpRunner`支持的`YAML/JSON`测试用例；
- 支持`Swagger`：将`Swagger`定义的API转换为`HttpRunner`支持的`YAML/JSON`测试用例。

等这两个新特性完成之后，相信`HttpRunner`会更上一个台阶。

如果你们有什么更好的想法，欢迎联系我。


[w3c]: https://www.w3.org/
[har-specs]: https://dvcs.w3.org/hg/webperf/raw-file/tip/specs/HAR/Overview.html
[har2case]: https://github.com/HttpRunner/har2case
