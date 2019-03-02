---
title: ApiTestEngine 演进之路（1）搭建基础框架
permalink: post/ApiTestEngine-1-setup-basic-framework
date: 2017/06/22
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在[《ApiTestEngine 演进之路（0）开发未动，测试先行》][ApiTestEngine-dev-0]一文中，我对[`ApiTestEngine`][ApiTestEngine]项目正式开始前的准备工作进行了介绍，包括构建API接口服务（`Mock Server`）、搭建项目单元测试框架、实现持续集成构建检查机制（[`Travis CI`][travis-ci]）等。

接下来，我们就开始构建[`ApiTestEngine`][ApiTestEngine]项目的基础框架，实现基本功能吧。

## 接口测试的核心要素

既然是从零开始，那我们不妨先想下，对于接口测试来说，最基本最核心的要素有哪些？

事实上，不管是手工进行接口测试，还是自动化测试平台执行接口测试，接口测试的核心要素都可以概括为如下三点：

- 发起接口请求（Request）
- 解析接口响应（Response）
- 检查接口测试结果

这对于任意类型的接口测试也都是适用的。

在本系列文章中，我们关注的是API接口的测试，更具体地，是基于HTTP协议的API接口的测试。所以我们的问题就进一步简化了，只需要关注`HTTP`协议层面的请求和响应即可。

好在对于绝大多数接口系统，都有明确的API接口文档，里面会定义好接口请求的参数（包括Headers和Body），并同时描述好接口响应的内容（包括Headers和Body）。而我们需要做的，就是根据接口文档的描述，在`HTTP`请求中按照接口规范填写请求的参数，然后读取接口的`HTTP`响应内容，将接口的实际响应内容与我们的预期结果进行对比，以此判断接口功能是否正常。这里的预期结果，应该是包含在接口测试用例里面的。

由此可知，实现接口测试框架的第一步是完成对`HTTP`请求响应处理的支持。

## HTTP客户端的最佳选择

[`ApiTestEngine`][ApiTestEngine]项目选择`Python`作为编程语言，而在`Python`中实现`HTTP`请求，毫无疑问，[`Requests`][Requests]库是最佳选择，简洁优雅，功能强大，可轻松支持`API`接口的多种请求方法，包括`GET/POST/HEAD/PUT/DELETE`等。

并且，更赞的地方在于，[`Requests`][Requests]库针对所有的`HTTP`请求方法，都可以采用一套统一的接口。

```python
requests.request(method, url, **kwargs)
```

其中，`kwargs`中可以包含`HTTP`请求的所有可能需要用到的信息，例如`headers`、`cookies`、`params`、`data`、`auth`等。

这有什么好处呢？

好处在于，这可以帮助我们轻松实现测试数据与框架代码的分离。我们只需要遵循[`Requests`][Requests]库的参数规范，在接口测试用例中复用[`Requests`][Requests]参数的概念即可。而对于框架的测试用例执行引擎来说，处理逻辑就异常简单了，直接读取测试用例中的参数，传参给`Requests`发起请求即可。

如果还感觉不好理解，没关系，直接看案例。

## 测试用例描述

在我们搭建的API接口服务（`Mock Server`）中，我们想测试“创建一个用户，该用户之前不存在”的场景

在上一篇文章中，我们也在`unittest`中对该测试场景实现了测试脚本。

```python
def test_create_user_not_existed(self):
   self.clear_users()

   url = "%s/api/users/%d" % (self.host, 1000)
   data = {
       "name": "user1",
       "password": "123456"
   }
   resp = self.api_client.post(url, json=data)

   self.assertEqual(201, resp.status_code)
   self.assertEqual(True, resp.json()["success"])
```

在该用例中，我们实现了`HTTP POST`请求，`api_client.post(url, json=data)`，然后对响应结果进行解析，并检查`resp.status_code`、`resp.json()["success"]`是否满足预期。

可以看出，采用代码编写测试用例时会用到许多编程语言的语法，对于不会编程的人来说上手难度较大。更大的问题在于，当我们编写大量测试用例之后，因为模式基本都是固定的，所以会发现存在大量相似或重复的脚本，这给脚本的维护带来了很大的问题。

那如何将测试用例与脚本代码进行分离呢？

考虑到`JSON`格式在编程语言中处理是最方便的，分离后的测试用例可采用`JSON`描述如下：

```json
{
   "name": "create user which does not exist",
   "request": {
       "url": "http://127.0.0.1:5000/api/users/1000",
       "method": "POST",
       "headers": {
           "content-type": "application/json"
       },
       "json": {
           "name": "user1",
           "password": "123456"
       }
   },
   "response": {
       "status_code": 201,
       "headers": {
           "Content-Type": "application/json"
       },
       "body": {
           "success": true,
           "msg": "user created successfully."
       }
   }
}
```

不难看出，如上`JSON`结构体包含了测试用例的完整描述信息。

需要特别注意的是，这里使用了一个讨巧的方式，就是在请求的参数中充分复用了[`Requests`][Requests]的参数规范。例如，我们要`POST`一个`JSON`的结构体，那么我们就直接将`json`作为`request`的参数名，这和前面写脚本时用的`api_client.post(url, json=data)`是一致的。

## 测试用例执行引擎

在如上测试用例描述的基础上，测试用例执行引擎就很简单了，以下几行代码就足够了。

```python
def run_single_testcase(testcase):
   req_kwargs = testcase['request']

   try:
       url = req_kwargs.pop('url')
       method = req_kwargs.pop('method')
   except KeyError:
       raise exception.ParamsError("Params Error")

   resp_obj = requests.request(url=url, method=method, **req_kwargs)
   diff_content = utils.diff_response(resp_obj, testcase['response'])
   success = False if diff_content else True
   return success, diff_content
```

可以看出，不管是什么`HTTP`请求方法的用例，该执行引擎都是适用的。

只需要先从测试用例中获取到HTTP接口请求参数，`testcase['request']`：

```json
{
  "url": "http://127.0.0.1:5000/api/users/1000",
  "method": "POST",
  "headers": {
      "content-type": "application/json"
  },
  "json": {
      "name": "user1",
      "password": "123456"
  }
}
```

然后发起`HTTP`请求：

```python
requests.request(url=url, method=method, **req_kwargs)
```

最后再检查测试结果：

```python
utils.diff_response(resp_obj, testcase['response'])
```

在测试用例执行引擎完成后，执行测试用例的方式也很简单。同样是在`unittest`中调用执行测试用例，就可以写成如下形式：

```python
def test_run_single_testcase_success(self):
   testcase_file_path = os.path.join(os.getcwd(), 'tests/data/demo.json')
   testcases = utils.load_testcases(testcase_file_path)
   success, _ = self.test_runner.run_single_testcase(testcases[0])
   self.assertTrue(success)
```

可以看出，模式还是很固定：加载用例、执行用例、判断用例执行是否成功。如果每条测试用例都要在`unittest.TestCase`分别写一个单元测试进行调用，还是会存在大量重复工作。

所以比较好的做法是，再实现一个单元测试用例生成功能；这部分先不展开，后面再进行详细描述。

## 结果判断处理逻辑

这里再单独讲下对结果的判断逻辑处理，也就是`diff_response`函数。

```python
def diff_response(resp_obj, expected_resp_json)
    diff_content = {}
    resp_info = parse_response_object(resp_obj)

    # 对比 status_code，将差异存入 diff_content
    # 对比 Headers，将差异存入 diff_content
    # 对比 Body，将差异存入 diff_content

    return diff_content
```

其中，`expected_resp_json`参数就是我们在测试用例中描述的`response`部分，作为测试用例的预期结果描述信息，是判断实际接口响应是否正常的参考标准。

而`resp_obj`参数，就是实际接口响应的`Response`实例，详细的定义可以参考`requests.Response`[描述文档](http://docs.python-requests.org/en/master/api/#requests.Response)。

为了更好地实现结果对比，我们也将`resp_obj`解析为与`expected_resp_json`相同的数据结构。

```python
def parse_response_object(resp_obj):
    try:
        resp_body = resp_obj.json()
    except ValueError:
        resp_body = resp_obj.text

    return {
        'status_code': resp_obj.status_code,
        'headers': resp_obj.headers,
        'body': resp_body
    }
```

那么最后再进行对比就很好实现了，只需要编写一个通用的`JSON`结构体比对函数即可。

```python
def diff_json(current_json, expected_json):
    json_diff = {}

    for key, expected_value in expected_json.items():
        value = current_json.get(key, None)
        if str(value) != str(expected_value):
            json_diff[key] = {
                'value': value,
                'expected': expected_value
            }

    return json_diff
```

这里只罗列了核心处理流程的代码实现，其它的辅助功能，例如加载`JSON/YAML`测试用例等功能，请直接阅读阅读[项目源码](https://github.com/debugtalk/ApiTestEngine/tree/master/ate)。

## 总结

经过本文中的工作，我们已经完成了[`ApiTestEngine`][ApiTestEngine]基础框架的搭建，并实现了两项最基本的功能：

- 支持API接口的多种请求方法，包括 GET/POST/HEAD/PUT/DELETE 等
- 测试用例与代码分离，测试用例维护方式简洁优雅，支持`YAML/JSON`

然而，在实际项目中的接口通常比较复杂，例如包含签名校验等机制，这使得我们在配置接口测试用例时还是会比较繁琐。

在下一篇文章中，我们将着手解决这个问题，通过对框架增加模板配置功能，实现接口业务参数和技术细节的分离。

## 阅读更多

- [《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]
- [《ApiTestEngine 演进之路（0）开发未动，测试先行》][ApiTestEngine-dev-0]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]


[ApiTestEngine-Intro]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[ApiTestEngine-dev-0]: https://debugtalk.com/post/ApiTestEngine-0-setup-CI-test/
[travis-ci]: https://travis-ci.org/
[Requests]: http://docs.python-requests.org/en/master/
[Requests-api]: http://docs.python-requests.org/en/master/api/
