---
title: ApiTestEngine 演进之路（2）探索优雅的测试用例描述方式
permalink: post/ApiTestEngine-2-best-testcase-description
date: 2017/07/07
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在[《ApiTestEngine 演进之路（1）搭建基础框架》][ApiTestEngine-1]一文中，我们完成了[`ApiTestEngine`][ApiTestEngine]基础框架的搭建，并实现了简单接口的测试功能。

接下来，我们就针对复杂类型的接口（例如包含签名校验等机制），通过对接口的业务参数和技术细节进行分离，实现简洁优雅的接口测试用例描述。

## 传统的测试用例编写方式

对于在自动化测试中将`测试数据`与`代码实现`进行分离的好处，我之前已经讲过多次，这里不再重复。

测试数据与代码实现分离后，简单的接口还好，测试用例编写不会有什么问题；但是当面对复杂一点的接口（例如包含签名校验等机制）时，我们编写自动化测试用例还是会比较繁琐。

我们从一个最常见的案例入手，看下编写自动化测试用例的过程，相信大家看完后就会对上面那段话有很深的感受。

以API接口服务（`Mock Server`）的创建新用户功能为例，该接口描述如下：

> 请求数据：
> Url: http://127.0.0.1:5000/api/users/1000
> Method: POST
> Headers: {"content-type": "application/json", "Random": "A2dEx", "Authorization": "47f135c33e858f2e3f55156ae9f78ee1"}
> Body: {"name": "user1", "password": "123456"}
>
> 预期的正常响应数据：
> Status_Code: 201
> Headers: {'Date': 'Fri, 23 Jun 2017 07:05:41 GMT', 'Content-Length': '54', 'Content-Type': 'application/json', 'Server': 'Werkzeug/0.12.2 Python/2.7.13'}
> Body: {"msg": "user created successfully.", "success": true, "uuid": "JsdfwerL"}

其中，请求`Headers`中的`Random`字段是一个5位长的随机字符串，`Authorization`字段是一个签名值，签名方式为`TOKEN+RequestBody+Random`拼接字符串的`MD5`值。更具体的，`RequestBody`要求字典的`Key`值按照由小到大的排序方式。接口请求成功后，返回的是一个`JSON`结构，里面的`success`字段标识请求成功与否的状态，如果成功，`uuid`字段标识新创建用户的唯一ID。

相信只要是接触过接口测试的同学对此应该都会很熟悉，这也是后台系统普遍采用的签名校验方式。在具体的系统中，可能字符串拼接方式或签名算法存在差异，但是模式基本上都是类似的。

那么面对这样一个接口，我们会怎样编写接口测试用例呢？

首先，请求的数据是要有的，我们会先准备一个可用的账号，例如`{"password": "123456", "name": "user1"}`。

然后，由于接口存在签名校验机制，因此我们除了要知道服务器端使用的TOKEN（假设为`debugtalk`）外，还要准备好`Random`字段和`Authorization`字段。`Random`字段好说，我们随便生成一个，例如`A2dEx`；`Authorization`字段就会复杂不少，需要我们按照规定先将`RequestBody`根据字典的`Key`值进行排序，得到`{"name": "user1", "password": "123456"}`，然后与`TOKEN`和`Random`字段拼接字符串得到`debugtalk{"password": "123456", "name": "user1"}A2dEx`，接着再找一个`MD5`工具，计算得到签名值`a83de0ff8d2e896dbd8efb81ba14e17d`。

最后，我们才可以完成测试用例的编写。假如我们采用`YAML`编写测试用例，那么用例写好后应该就是如下样子。

```YAML
-
    name: create user which does not exist
    request:
        url: http://127.0.0.1:5000/api/users/1000
        method: POST
        headers:
            Content-Type: application/json
            authorization: a83de0ff8d2e896dbd8efb81ba14e17d
            random: A2dEx
    data:
        name: user1
        password: 123456
    response:
        status_code: 201
        headers:
            Content-Type: application/json
        body:
            success: true
            msg: user created successfully.
            uuid: JsdfwerL
```

该测试用例可以在`ApiTestEngine`中正常运行，我们也可以采用同样的方式，对系统的所有接口编写测试用例，以此实现项目的接口自动化测试覆盖。

但问题在于，每个接口通常会对应多条测试用例，差异只是在于请求的数据会略有不同，而测试用例量越大，我们人工去准备测试数据的工作量也就越大。更令人抓狂的是，我们的系统接口不是一直不变的，有时候会根据业务需求的变化进行一些调整，相应地，我们的测试数据也需要进行同步更新，这样一来，所有相关的测试用例数据就又得重新计算一遍（任意字段数据产生变化，签名值就会大不相同）。

可以看出，如果是采用这种方式编写维护接口测试用例，人力和时间成本都会非常高，最终的结果必然是接口自动化测试难以在实际项目中得以开展。

## 理想的用例描述方式

在上面案例中，编写接口测试用例时之所以会很繁琐，主要是因为接口存在签名校验机制，导致我们在准备测试数据时耗费了太多时间在这上面。

然而，对于测试人员来说，接口的业务功能才是需要关注的，至于接口采用什么签名校验机制这类技术细节，的确不应耗费过多时间和精力。所以，我们的接口测试框架应该设法将接口的技术细节实现和业务参数进行拆分，并能自动处理与技术细节相关的部分，从而让业务测试人员只需要关注业务参数部分。

那要怎么实现呢？

在开始实现之前，我们不妨借鉴`BDD`（行为驱动开发）的思想，先想下如何编写接口测试用例的体验最友好，换句话说，就是让业务测试人员写用例写得最爽。

还是上面案例的接口测试用例，可以看出，最耗时的地方主要是计算签名校验值部分。按理说，签名校验算法我们是已知的，要是可以在测试用例中直接调用签名算法函数就好了。

事实上，这也是各种模板语言普遍采用的方式，例如`Jinja2`模板语言，可以在`{% raw %}{% %}{% endraw %}`中执行函数语句，在`{% raw %}{{ }}{% endraw %}`中可以调用变量参数。之前我在设计[`AppiumBooster`][AppiumBooster]时也采用了类似的思想，可以通过`${config.TestEnvAccount.UserName}`的方式在测试用例中引用预定义的全局变量。

基于该思路，假设我们已经实现了`gen_random_string`这样一个生成指定位数的随机字符串的函数，以及`gen_md5`这样一个计算签名校验值的函数，那么我们就可以尝试采用如下方式来描述我们的测试用例：

```YAML
- test:
    name: create user which does not exist
    variables:
        - TOKEN: debugtalk
        - random: ${gen_random_string(5)}
        - json: {"name": "user", "password": "123456"}
        - authorization: ${gen_md5($TOKEN, $json, $random)}
    request:
        url: http://127.0.0.1:5000/api/users/1000
        method: POST
        headers:
            Content-Type: application/json
            authorization: $authorization
            random: $random
        json: $json
    extractors:
        user_uuid: content.uuid
    validators:
        - {"check": "status_code", "comparator": "eq", "expected": 201}
        - {"check": "content.success", "comparator": "eq", "expected": true}
```

在如上用例中，用到了两种转义符：

- `$`作为变量转义符，`$var`将不再代表的是普遍的字符串，而是`var`变量的值；
- `${}`作为函数的转义符，`${}`内可以直接填写函数名称及调用参数，甚至可以包含变量。

为什么会选择采用这种描述方式？（`Why？`）

其实这也是我经过大量思考和实践之后，才最终确定的描述方式。如果真要讲述这个思路历程。。。还是不细说了，此处可省下一万字。（主要的思路无非就是要实现转义的效果，并且表达要简洁清晰，因此必然会用到特殊字符；而特殊字符在`YAML`中大多都已经有了特定的含义，排除掉不可用的之后，剩下的真没几个了，然后再借鉴其它框架常用的符号，所以说最终选择`$`和`${}`也算是必然。）

可以确定的是，这种描述方式的好处非常明显，不仅可以实现复杂计算逻辑的函数调用，还可以实现变量的定义和引用。

除了转义符，由于接口测试中经常需要对结果中的特定字段进行提取，作为后续接口请求的参数，因此我们实现了`extractors`这样一个结果提取器，只要返回结果是JSON类型，就可以将其中的任意字段进行提取，并保存到一个变量中，方便后续接口请求进行引用。

另外，为了更好地实现对接口响应结果的校验，我们废弃了先前的方式，实现了独立的结果校验器`validators`。这是因为，很多时候在比较响应结果时，并不能简单地按照字段值是否相等来进行校验，除此之外，我们可能还需要检查某个字段的长度是否为指定位数，元素列表个数是否大于某个数值，甚至某个字符串是否满足正则匹配等等。

相信你们肯定会想，以上这些描述方式的确是很简洁，但更多地感觉是在臆想，就像开始说的`gen_random_string`和`gen_md5`函数，我们只是假设已经定义好了。就算描述得再优雅再完美，终究也还只是`YAML/JSON`文本格式而已，要怎样才能转换为执行的代码呢？

这就要解决`How？`的问题了。

嗯，这就是用例模板引擎的核心了，也算是`ApiTestEngine`最核心的功能特性。

更具体的，从技术实现角度，主要分为三大块：

- 如何在用例描述（`YAML/JSON`）中实现函数的定义和调用
- 如何在用例描述中实现参数的定义和引用，包括用例内部和用例集之间
- 如何在用例描述中实现预期结果的描述和测试结果的校验

这三大块内容涉及到较多的技术实现细节，我们将在后续的文章中结合代码逐个深入进行讲解。

## 阅读更多

- [《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]
- [《ApiTestEngine 演化之路（0）开发未动，测试先行》][ApiTestEngine-dev-0]
- [《ApiTestEngine 演进之路（1）搭建基础框架》][ApiTestEngine-1]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]

[ApiTestEngine-1]: https://debugtalk.com/post/ApiTestEngine-1-setup-basic-framework/
[ApiTestEngine-Intro]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[ApiTestEngine-dev-0]: https://debugtalk.com/post/ApiTestEngine-0-setup-CI-test/
