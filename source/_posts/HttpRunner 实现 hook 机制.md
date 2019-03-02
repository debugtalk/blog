---
title: HttpRunner 实现 hook 机制
permalink: post/httprunner-hook
date: 2018/05/12
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
  - hook
---

## 背景

在自动化测试中，通常在测试开始前需要做一些预处理操作，以及在测试结束后做一些清理性的工作。

例如，测试使用手机号注册账号的接口：

- 测试开始前需要确保该手机号未进行过注册，常用的做法是先在数据库中删除该手机号相关的账号数据（若存在）；
- 测试结束后，为了减少对测试环境的影响，常用的做法是在数据库中将本次测试产生的相关数据删除掉。

显然，在自动化测试中的这类预处理操作和清理性工作，由人工来做肯定是不合适的，我们最好的方式还是在测试脚本中进行实现，也就是我们常说的 hook 机制。

hook 机制的概念很简单，在各个主流的测试工具和测试框架中也很常见。

例如 Python 的 unittest 框架，常用的就有如下几种 hook 函数。

- setUp：在每个 test 运行前执行
- tearDown：在每个 test 运行后执行
- setUpClass：在整个用例集运行前执行
- tearDownClass：在整个用例集运行后执行

概括地讲，就是针对自动化测试用例，要在单个测试用例和整个测试用例集的前后实现 hook 函数。

## 描述方式设想

在 HttpRunner 的 YAML/JSON 测试用例文件中，本身就具有分层的思想，用例集层面的配置在 config 中，用例层面的配置在 test 中；同时，在 YAML/JSON 中也实现了比较方便的函数调用机制，`$func($a, $b)`。

因此，我们可以新增两个关键字：`setup_hooks` 和 `teardown_hooks`。类似于 variables 和 parameters 关键字，根据关键字放置的位置来决定是用例集层面还是单个用例层面。

根据设想，我们就可以采用如下形式来描述 hook 机制。

```yaml
- config:
    name: basic test with httpbin
    request:
        base_url: http://127.0.0.1:3458/
    setup_hooks:
        - ${hook_print(setup_testset)}
    teardown_hooks:
        - ${hook_print(teardown_testset)}

- test:
    name: get headers
    times: 2
    request:
        url: /headers
        method: GET
    setup_hooks:
        - ${hook_print(---setup-testcase)}
    teardown_hooks:
        - ${hook_print(---teardown-testcase)}
    validate:
        - eq: ["status_code", 200]
        - eq: [content.headers.Host, "127.0.0.1:3458"]
```

同时，hook 函数需要定义在项目的 debugtalk.py 中。

```python
def hook_print(msg):
    print(msg)
```

## 基本实现方式

基于 hook 机制的简单概念，要在 HttpRunner 中实现类似功能也就很容易了。

在 HttpRunner 中，负责测试执行的类为 `httprunner/runner.py` 中的 Runner。因此，要实现用例集层面的 hook 机制，只需要将用例集的 setup_hooks 放置到 `__init__` 中，将 teardown_hooks 放置到 `__del__` 中。

```python
class Runner(object):

    def __init__(self, config_dict=None, http_client_session=None):
        # 省略

        # testset setup hooks
        testset_setup_hooks = config_dict.pop("setup_hooks", [])
        if testset_setup_hooks:
            self.do_hook_actions(testset_setup_hooks)

        # testset teardown hooks
        self.testset_teardown_hooks = config_dict.pop("teardown_hooks", [])

    def __del__(self):
        if self.testset_teardown_hooks:
            self.do_hook_actions(self.testset_teardown_hooks)

```

类似地，要实现单个用例层面的 hook 机制，只需要将单个用例的 setup_hooks 放置到 request 之前，将 teardown_hooks 放置到 request 之后。

```python
class Runner(object):

    def run_test(self, testcase_dict):

        # 省略

        # setup hooks
        setup_hooks = testcase_dict.get("setup_hooks", [])
        self.do_hook_actions(setup_hooks)

        # request
        resp = self.http_client_session.request(method, url, name=group_name, **parsed_request)

        # teardown hooks
        teardown_hooks = testcase_dict.get("teardown_hooks", [])
        if teardown_hooks:
            self.do_hook_actions(teardown_hooks)

        # 省略
```

至于具体执行 hook 函数的 do_hook_actions，因为之前我们已经实现了文本格式函数描述的解析器 `context.eval_content`，因此直接调用就可以了。

```python
def do_hook_actions(self, actions):
    for action in actions:
        logger.log_debug("call hook: {}".format(action))
        self.context.eval_content(action)
```

通过以上方式，我们就在 HttpRunner 中实现了用例集和单个用例层面的 hook 机制。

还是上面的测试用例，我们执行的效果如下所示。

```text
$ hrun tests/httpbin/hooks.yml
setup_testset
get headers
INFO     GET /headers
---setup-testcase
INFO     status_code: 200, response_time(ms): 10.29 ms, response_length: 151 bytes
---teardown-testcase
.
get headers
INFO     GET /headers
---setup-testcase
INFO     status_code: 200, response_time(ms): 4.46 ms, response_length: 151 bytes
---teardown-testcase
.

----------------------------------------------------------------------
Ran 2 tests in 0.028s

OK
teardown_testset
```

可以看出，这的确已经满足了我们在用例集和单个用例层面的 hook 需求。

## 进一步优化

以上实现已经可以满足大多数场景的测试需求了，不过还有两种场景无法满足：

- 需要对请求的 request 内容进行预处理，例如，根据请求方法和请求的 Content-Type 来对请求的 data 进行加工处理；
- 需要根据响应结果来进行不同的后续处理，例如，根据接口响应的状态码来进行不同时间的延迟等待。

在之前的实现方式中，我们无法实现上述两个场景，是因为我们无法将请求的 request 内容和响应的结果传给 hook 函数。

问题明确了，要进行进一步优化也就容易了。

因为我们在 hook 函数（类似于`$func($a, $b)`）中，是可以传入变量的，而变量都是存在于当前测试用例的上下文（context）中的，那么我们只要将 request 内容和请求响应分别作为变量绑定到当前测试用例的上下文即可。

具体地，我们可以约定两个变量，`$request`和`$response`，分别对应测试用例的请求内容（request）和响应实例（requests.Response）。

```python
class Runner(object):

    def run_test(self, testcase_dict):

        self.context.bind_variables({"request": parsed_request}, level="testcase")

        # 省略

        # setup hooks
        setup_hooks = testcase_dict.get("setup_hooks", [])
        self.do_hook_actions(setup_hooks)

        # request
        resp = self.http_client_session.request(method, url, name=group_name, **parsed_request)

        # teardown hooks
        teardown_hooks = testcase_dict.get("teardown_hooks", [])
        if teardown_hooks:
            self.context.bind_variables({"response": resp}, level="testcase")
            self.do_hook_actions(teardown_hooks)

        # 省略
```

在优化后的实现中，新增了两次调用，`self.context.bind_variables`，作用就是将解析后的 request 内容和请求的响应实例绑定到当前测试用例的上下文中。

然后，我们在 YAML/JSON 测试用例中就可以在需要的时候调用`$request`和`$response`了。

```yaml
- test:
    name: headers
    request:
        url: /headers
        method: GET
    setup_hooks:
        - ${setup_hook_prepare_kwargs($request)}
    teardown_hooks:
        - ${teardown_hook_sleep_N_secs($response, 1)}
    validate:
        - eq: ["status_code", 200]
        - eq: [content.headers.Host, "127.0.0.1:3458"]
```

对应的 hook 函数如下所示：

```python
def setup_hook_prepare_kwargs(request):
    if request["method"] == "POST":
        content_type = request.get("headers", {}).get("content-type")
        if content_type and "data" in request:
            # if request content-type is application/json, request data should be dumped
            if content_type.startswith("application/json") and isinstance(request["data"], (dict, list)):
                request["data"] = json.dumps(request["data"])

            if isinstance(request["data"], str):
                request["data"] = request["data"].encode('utf-8')

def teardown_hook_sleep_N_secs(response, n_secs):
    """ sleep n seconds after request
    """
    if response.status_code == 200:
        time.sleep(0.1)
    else:
        time.sleep(n_secs)
```

值得特别说明的是，因为 request 是可变参数类型（dict），因此该函数参数为引用传递，我们在 hook 函数里面对 request 进行修改后，后续在实际请求时也同样会发生改变，这对于我们需要对请求参数进行预处理时尤其有用。

## 更多内容

- 中文使用说明文档：http://cn.httprunner.org/advanced/request-hook/
- 代码实现：[GitHub commit](https://github.com/HttpRunner/HttpRunner/commit/2bb84b38745d004d336ed9867df5e63534b596bc)
