---
title: ApiTestEngine 正式更名为 HttpRunner
permalink: post/ApiTestEngine-rename-to-HttpRunner
date: 2017/11/08
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在[《ApiTestEngine，不再局限于API的测试》][1]一文的末尾，我提到随着`ApiTestEngine`的发展，它的实际功能特性和名字已经不大匹配，需要考虑改名了。

经过慎重考虑，最终决定将`ApiTestEngine`正式更名为`HttpRunner`。

## 名字的由来

为什么选择`HttpRunner`这个名字呢？

在改名之前，我的想法很明确，就是要在新名字中体现该工具最核心的两个特点：

- 该工具可实现任意基于HTTP协议接口的测试（自动化测试、持续集成、线上监控都是以此作为基础）
- 该工具可同时实现性能测试（这是区别于其它工具的最大卖点）

围绕着这两点，我开始踏上了纠结的取名之路。

首先想到的，`ApiTestEngine`实现`HTTP`请求是依赖于[`Python Requests`][Requests]，实现性能测试是依赖于[`Locust`][Locust]，而`Locust`同样依赖于`Python Requests`。可以说，`ApiTestEngine`完全是构建在`Python Requests`之上的，后续无论怎么进化，这一层关系应该都不会变。

考虑到`Python Requests`的`slogan`是：

> Python HTTP Requests for Humans™

因此，我想在`ApiTestEngine`的新名字中应该包含`HTTP`。

那如何体现性能测试呢？

想到的关键词就`load`、`perf`、`meter`这些（来源于LoadRunner，NeoLoad，JMeter），但又不能直接用，因为名字中带有这些词让人感觉就只是性能测试工具。而且，还要考虑跟`HTTP`这个词进行搭配。

最终，感觉`runner`这个词比较合适，一方面这来源于`LoadRunner`，大众的认可度可能会比较高；同时，这个词用在自动化测试和性能测试上都不会太牵强。

更重要的是，`HttpRunner`这个组合词当前还没有人用过，不管是`PyPI`还是`GitHub`，甚至域名都是可注册状态。

所以，就认定`HttpRunner`这个名字了。

## 相关影响

`ApiTestEngine`更名为`HttpRunner`之后，会对用户产生哪些影响呢？

先说结论，没有任何不好的影响！

在链接访问方面，受益于GitHub仓库链接的自动重定向机制，仓库在改名或者过户（Transfer ownership）之后，访问原有链接会自动实现重定向，因此之前博客中的链接也都不会受到影响。

新的仓库地址：https://github.com/HttpRunner/HttpRunner

在使用的命令方面，`HttpRunner`采用`httprunner`作为新的命令代替原有的`ate`命令；当然，为了考虑兼容性，`HttpRunner`对`ate`命令也进行了保留，因此`httprunner`和`ate`命令同时可用，并完全等价。在性能测试方面，`locusts`命令保持不变。

```bash
$ httprunner -V
HttpRunner version: 0.8.1b
PyUnitReport version: 0.1.3b
```

既然是全新的名字，新的篇章必然也得有一些新的东西。

为了方面用户安装，`HttpRunner`已托管至[`PyPI`][PyPI]；后续大家可以方便的采用`pip`命令进行安装。

```bash
$ pip install HttpRunner
```

同时，`HttpRunner`新增了大量使用说明文档（之前的博客主要都是开发过程记录），并托管到专业的`readthedocs`上面。在文档语言方面，英文优先，中文相对滞后。

访问网址：

- 英文：http://httprunner.readthedocs.io/
- 中文（滞后）：http://httprunner-cn.readthedocs.io/

另外，为了具有更高的逼格，同时购入域名`httprunner.top`，后续将作为项目的主页地址。当前还处于实名认证中，预计2~3个工作日后就可以访问了。

关于项目改名这事儿，就说到这儿吧，希望你们也喜欢。

> Hello World, HttpRunner.



[1]: https://debugtalk.com/post/apitestengine-not-only-about-json-api/
[Requests]: http://python-requests.org
[Locust]: http://locust.io
[PyPI]: https://pypi.python.org/pypi/HttpRunner
