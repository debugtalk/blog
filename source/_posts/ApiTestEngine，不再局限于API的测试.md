---
title: ApiTestEngine，不再局限于 API 的测试
permalink: post/apitestengine-not-only-about-json-api
date: 2017/11/06
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
  - 正则表达式
---

## 背景

从编写[《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine]至今，已经快半年了。在这一段时间内，`ApiTestEngine`经过持续迭代，也已完全实现了当初预设的目标。

然而，在设计`ApiTestEngine`之初只考虑了面向最常规的API接口类型，即`HTTP`响应内容为`JSON`数据结构的类型。那么，如果`HTTP`接口响应内容不是`JSON`，而是`XML`或`SOAP`，甚至为`HTML`呢？

答案是，不支持！

不支持的原因是什么呢？

其实，不管是何种业务类型或者技术架构的系统接口，我们在对其进行测试时都可以拆分为三步：

- 发起接口请求（Request）
- 解析接口响应（Parse Response）
- 校验测试结果（Validation）

而`ApiTestEngine`不支持`XML/HTML`类型的接口，问题恰恰是出现在`解析接口响应`和`校验测试结果`这两个环节。考虑到`校验测试结果`环节是依赖于`解析接口响应`，即需要先从接口响应结果中解析出具体的字段，才能实现与预期结果的校验检测，因此，制约`ApiTestEngine`无法支持`XML/HTML`类型接口的根本原因在于无法支持对`XML/HTML`的解析。

也因为这个原因，`ApiTestEngine`存在局限性，没法推广到公司内部的所有项目组。遇到`JSON`类型以外的接口时，只能再使用别的测试工具，体验上很是不爽。

在经历了一段时间的不爽后，我开始重新思考`ApiTestEngine`的设计，希望使其具有更大的适用范围。通过前面的分析我们也不难看出，解决问题的关键在于实现针对`XML/HTML`的解析器。

## JSON接口的解析

在实现`XML/HTML`的解析器之前，我们不妨先看下`ApiTestEngine`的`JSON`解析器是怎么工作的。

在`JSON`类型的数据结构中，无论结构有多么复杂，数据字段都只可能为如下三种数据类型之一：

- 值（value）类型，包括数字、字符串等；该种数据类型的特点是不会再有下一层极的数据；
- 字典（dict）类型；该种数据类型的特点是包含无序的下一层极的数据；
- 列表（list）类型：该种数据类型的特点是包含有序的下一层极的数据。

基于这一背景，`ApiTestEngine`在实现`JSON`的字段提取器（`extractor`）时，就采用了点（`.`）的运算符。

例如，假如`HTTP`接口响应的`headers`和`body`为如下内容：

response headers:

```json
{
    "Content-Type": "application/json",
    "Content-Length": 69
}
```

response body:

```json
{
    "success": false,
    "person": {
        "name": {
            "first_name": "Leo",
            "last_name": "Lee",
        },
        "age": 29,
        "cities": ["Guangzhou", "Shenzhen"]
    }
}
```

那么对应的字段提取方式就为：

```text
"headers.content-type" => "application/json"
"headers.content-length" => 69
"body.success"/"content.success"/"text.success" => false

"content.person.name.first_name" => "Leo"
"content.person.age" => 29
"content.person.cities" => ["Guangzhou", "Shenzhen"]
"content.person.cities.0" => "Guangzhou"
"content.person.cities.1" => "Shenzhen"
```

可以看出，通过点（`.`）运算符，我们可以从上往下逐级定位到具体的字段：

- 当下一级为字典时，通过`.key`来指定下一级的节点，例如`.person`，指定了`content`下的`person`节点；
- 当下一级为列表时，通过`.index`来指定下一级的节点，例如`.0`，指定了`cities`下的第一个元素。

定位到具体字段后，我们也就可以方便地提取字段值供后续使用了，作为参数或者进行结果校验均可。

## 实现XML/HTML的解析器

从点（`.`）运算符的描述形式上来看，它和`XML/HTML`的`xpath`十分类似。既然如此，那我们针对`XML/HTML`类型的接口，是否可以基于`xpath`来实现解析器呢？

在大多数情况下的确可以。例如，针对如下HTML页面，当我们要获取标题信息时，我们就可以通过`xpath`来指定提取字段：`body/h1`

```html
<html>
    <body>
        <h1>订单页面</h1>
        <div>
            <p>订单号：SA89193</p>
        </div>
    </body>
</html>
```

然而，如果我们想获取订单号（SA89193）时，使用`xpath`就没有办法了（通过`body/div/p`获取到的是`订单号：SA89193`，还需进一步地进行处理）。

那除了`xpath`，我们还能使用什么其它方法从`XML/HTML`中提取特定字段呢？

由于早些年对`LoadRunner`比较熟悉，因此我首先想到了`LoadRunner`的`web_reg_save_param`函数；在该函数中，我们可以通过指定左右边界（LB & RB）来查找字段，将其提取出来并保存到变量中供后续使用。借鉴这种方式虽然可行，但在描述方式上还是比较复杂，特别是在`YAML`测试用例的`extract`中描述的时候。

再一想，这种方式的底层实现不就是正则表达式么。而且我们通过Python脚本解析网页时，采用正则表达式来对目标字段进行匹配和提取，的确也是通用性非常强的方式。

例如，假设我们现在想从`https://debugtalk.com`首页中提取出座右铭，通过查看网页源代码，我们可以看到座右铭对应的位置。

```html
<h2 class="blog-motto">探索一个软件工程师的无限可能</h2>
```

那么，要提取“探索一个软件工程师的无限可能”字符串时，我们就可以使用正则表达式`r"blog-motto\">(.*)</h2>"`进行匹配，然后使用`regex`的`group`将匹配内容提取出来。

对应的Python脚本实现如下所示。

```bash
>>> import re, requests
>>> resp = requests.get("https://debugtalk.com")
>>> content = resp.text
>>> matched = re.search(r"blog-motto\">(.*)</h2>", content)
>>> matched.group(1)
'探索一个软件工程师的无限可能'
```

思路确定后，实现起来就很快了。

此处省略256字。。。

最终，我在`ApiTestEngine`中新增实现了一个基于正则表达式的提取器。使用形式与JSON解析保持一致，只需要将之前的点（`.`）运算符更改为正则表达式即可。

还是前面提取座右铭的例子，我们就可以通过`YAML`格式来编写测试用例。

```yaml
- test:
    name: demo
    request:
        url: https://debugtalk.com/
        method: GET
    extract:
        - motto: 'blog-motto\">(.*)</h2>'
    validate:
        - {"check": "status_code", "expected": 200}
```

需要说明的是，指定的正则表达式必须满足`r".*\(.*\).*"`的格式要求，必须并且只能有一个分组（即一对括号）。如果在同一段内容中需要提取多个字段，那就分多次匹配即可。

## 写在最后

实现了基于正则表达式的提取器后，我们就彻底实现了对任意格式`HTTP`响应内容的解析，不仅限于`XML/HTML`类型，对于任意基于`HTTP`协议的的接口，`ApiTestEngine`都可以适用了。当然，如果接口响应是`JSON`类型，我们虽然可以也使用正则表达式提取，但更建议采用原有的点（`.`）运算符形式，因为描述更清晰。

至此，`ApiTestEngine`可以说是真正意义上实现了，面向任意类型的`HTTP`协议接口，只需要编写维护一份`YAML`用例，即可同时实现接口自动化测试、性能测试、持续集成、线上监控的全测试类型覆盖！

现在看来，`ApiTestEngine`的名字与其实际功能有些不大匹配了，是该考虑改名了。


[ApiTestEngine]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
