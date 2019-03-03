---
title: HttpRunner 的测试用例分层机制
permalink: post/HttpRunner-testcase-layer
date: 2017/12/23
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

## 背景描述

在`HttpRunner`中，测试用例引擎最大的特色就是支持`YAML/JSON`格式的用例描述形式。

采用`YAML/JSON`格式编写维护测试用例，优势还是很明显的：

- 相比于表格形式，具有更加强大的灵活性和更丰富的信息承载能力；
- 相比于代码形式，减少了不必要的编程语言语法重复，并最大化地统一了用例描述形式，提高了用例的可维护性。

以最常见的登录注销为例，我们的测试用例通常会描述为如下形式：

```yaml
- config:
    name: demo-login-logoff
    variable_binds:
        - UserName: test001
        - Password: 123456
    request:
        base_url: http://xxx.debugtalk.com
        headers:
            Accept: application/json
            User-Agent: iOS/10.3

- test:
    name: Login
    request:
        url: /api/v1/Account/Login
        method: POST
        json:
            UserName: $UserName
            Pwd: $Password
            VerCode: ""
    validators:
        - eq: ["status_code", 200]
        - eq: ["content.IsSuccess", True]
        - eq: ["content.Code", 200]

- test:
    name: Logoff
    request:
        url: /api/v1/Account/LoginOff
        method: GET
    validators:
        - eq: ["status_code", 200]
        - eq: ["content.IsSuccess", True]
        - eq: ["content.Code", 200]
```

相信大家已经对该种用例描述形式十分熟悉了。不过，该种描述形式的问题在于，接口通常会出现在多个测试场景中，而每次都需要对接口进行定义描述，包括请求的URL、Header、Body、以及预期响应值等，这就会产生大量的重复。

例如，在某个项目中存在三个测试场景：

- 场景A：注册新账号（`API_1/2`）、登录新注册的账号（`API_3/4/5`）、查看登录状态（`API_6`）；
- 场景B：登录已有账号（`API_3/4/5`）、注销登录（`API_7/8`）；
- 场景C：注销登录（`API_7/8`）、查看登录状态（`API_6`）、注册新账号（`API_1/2`）。

按照常规的接口测试用例编写方式，我们需要创建3个场景文件，然后在各个文件中分别描述三个测试场景相关的接口信息。示意图如下所示。

![](/images/httprunner-testcase-layer-1.jpeg)

在本例中，接口（`API_1/2/6`）在场景A和场景C中都进行了定义；接口（`API_3/4/5`）在场景A和场景B中都进行了定义；接口（`API_7/8`）在场景B和场景C中都进行了定义。可以预见，当测试场景增多以后，接口定义描述的维护就会变得非常困难和繁琐。

## 接口的分层定义描述

那要如何进行优化呢？

其实也很简单，在编程语言中，如果出现重复代码块，我们通常会将其封装为类或方法，然后在需要时进行调用，以此来消除重复。同样地，我们也可以将项目的API进行统一定义，里面包含API的请求和预期响应描述，然后在测试场景中进行引用即可。

示意图如下所示。

![](/images/httprunner-testcase-layer-2.jpeg)

具体地，我们可以约定将项目的所有API接口定义放置在`api`目录下，并在`api`目录中按照项目的系统模块来组织接口的定义；同时，将测试场景放置到`testcases`目录中。

此时测试用例文件的目录结构如下所示：

```bash
✗ tree tests
tests
├── api
│   └── v1
│       ├── Account.yml
│       ├── BusinessTrip.yml
│       ├── Common.yml
│       └── Leave.yml
├── debugtalk.py
└── testcases
    ├── scenario_A.yml
    ├── scenario_B.yml
    └── scenario_C.yml
```

而对于API接口的定义，与之前的描述方式基本一致，只做了两点调整：

- 接口定义块（`block`）的标识为`api`；
- 接口定义块中包含`def`字段，形式为`api_name(*args)`，作为接口的唯一标识ID；需要注意的是，即使`api`没有参数，也需要带上括号，`api_name()`；这和编程语言中定义函数是一样的。

```yaml
- api:
    def: api_v1_Account_Login_POST($UserName, $Password)
    request:
        url: /api/v1/Account/Login
        method: POST
        json:
            UserName: $UserName
            Pwd: $Password
            VerCode: ""
    validators:
        - eq: ["status_code", 200]
        - eq: ["content.IsSuccess", True]
        - eq: ["content.Code", 200]

- api:
    def: api_v1_Account_LoginOff_GET()
    request:
        url: /api/v1/Account/LoginOff
        method: GET
    validators:
        - eq: ["status_code", 200]
        - eq: ["content.IsSuccess", True]
        - eq: ["content.Code", 200]
```

有了接口的定义描述后，我们编写测试场景时就可以直接引用接口定义了。

同样是背景描述中的登录注销场景，测试用例就描述为变为如下形式。

```yaml
- config:
    name: demo
    variable_binds:
        - UserName: test001
        - Password: 123456
    request:
        base_url: http://xxx.debugtalk.com
        headers:
            Accept: application/json
            User-Agent: iOS/10.3

- test:
    name: Login
    api: api_v1_Account_Login_POST($UserName, $Password)

- test:
    name: Logoff
    api: api_v1_Account_LoginOff_GET()
```

不难看出，对API接口进行分层定义后，我们在测试用例场景中引用接口定义时，与编程语言里面调用函数的形式基本完全一样，只需要指定接口的名称，以及所需传递的参数值；同样的，即使没有参数，也需要带上括号。

实现接口的分层定义描述后，我们就可以避免接口的重复定义。但是，我们回过头来看之前的案例，发现仍然会存在一定的重复。

![](/images/httprunner-testcase-layer-3.jpeg)

如上图所示，场景A和场景C都包含了注册新账号（`API_1/2`）和查看登录状态（`API_6`），场景A和场景B都包含了登录已有账号（`API_3/4/5`），场景B和场景C都包含了注销登录（`API_7/8`）。

虽然我们已经将接口的定义描述抽离出来，避免了重复的定义；但是在实际业务场景中，某些功能（例如登录、注销）会在多个场景中重复出现，而该功能又涉及到多个接口的组合调用，这同样也会出现大量的重复。

## 接口的模块化封装

玩过积木的同学可能就会想到，我们也可以将系统的常用功能封装为模块（suite），只需要在模块中定义一次，然后就可以在测试场景中重复进行引用，从而避免了模块功能的重复描述。

![](/images/httprunner-testcase-layer-4.jpeg)

具体地，我们可以约定将项目的所有模块定义放置在`suite`目录下，并在`suite`目录中按照项目的功能来组织模块的定义。

后续，我们在`testcases`目录中描述测试场景时，就可同时引用接口定义和模块定义了；模块和接口的混合调用，必将为我们编写测试场景带来极大的灵活性。

此时测试用例文件的目录结构如下所示：

```bash
✗ tree tests
tests
├── api
│   └── v1
│       ├── Account.yml
│       ├── BusinessTrip.yml
│       ├── Common.yml
│       └── Leave.yml
├── debugtalk.py
├── suite
│   ├── BusinessTravelApplication
│   │   ├── approve-application.yml
│   │   ├── executive-application.yml
│   │   ├── reject-application.yml
│   │   └── submit-application.yml
│   └── LeaveApplication
│       ├── approve.yml
│       ├── cancel.yml
│       └── submit-application.yml
└── testcases
    ├── scenario_A.yml
    ├── scenario_B.yml
    └── scenario_C.yml
```

需要注意的是，我们在组织测试用例描述的文件目录结构时，遵循约定大于配置的原则：

- API接口定义必须放置在`api`目录下
- 模块定义必须放置在`suite`目录下
- 测试场景文件必须放置在`testcases`目录下
- 相关的函数定义放置在`debugtalk.py`中

至此，我们实现了测试用例的`接口-模块-场景`分层，从而彻底避免了重复定义描述。

## 脚手架工具

得益于约定大于配置的原则，在`HttpRunner`中实现了一个脚手架工具，可以快速创建项目的目录结构。该想法来源于`Django`的`django-admin.py startproject project_name`。

使用方式也与`Django`类似，只需要通过`--startproject`指定新项目的名称即可。

```bash
$ hrun --startproject helloworld
INFO:root: Start to create new project: /Users/Leo/MyProjects/helloworld
INFO:root:      created folder: /Users/Leo/MyProjects/helloworld
INFO:root:      created folder: /Users/Leo/MyProjects/helloworld/tests
INFO:root:      created folder: /Users/Leo/MyProjects/helloworld/tests/api
INFO:root:      created folder: /Users/Leo/MyProjects/helloworld/tests/suite
INFO:root:      created folder: /Users/Leo/MyProjects/helloworld/tests/testcases
INFO:root:      created file: /Users/Leo/MyProjects/helloworld/tests/debugtalk.py
```

运行之后，就会在指定的目录中生成新项目的目录结构，接下来，我们就可以按照测试用例的`接口-模块-场景`分层原则往里面添加用例描述信息了。

## 总结

如果看到这里你还不明白测试用例分层的必要性，那也没关系，测试用例分层不是必须的，你还是可以按照之前的方式组织测试用例。不过当你某一天发现需要进行分层管理时，你会发现它就在那里，很实用。

最后，在`HttpRunner`项目的[`examples/HelloWorld`][HelloWorld]目录中，包含了一份完整的分层测试用例示例，相信会对大家有所帮助。


[HelloWorld]: https://github.com/HttpRunner/HttpRunner/tree/master/examples/HelloWorld
