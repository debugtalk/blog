---
title: ApiTestEngine 演化之路（0）开发未动，测试先行
permalink: post/ApiTestEngine-0-setup-CI-test
tags:
  - 自动化测试
  - 测试框架
  - Mock
---

在[《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]一文中，我详细介绍了[`ApiTestEngine`][ApiTestEngine]诞生的背景，并对其核心特性进行了详尽的剖析。

接下来，我将在《ApiTestEngine演化之路》系列文章中讲解[`ApiTestEngine`][ApiTestEngine]是如何从第一行代码开始，逐步实现接口自动化测试框架的核心功能特性的。

相信大家都有听说过`TDD`（`测试驱动开发`）这种开发模式，虽然网络上对该种开发模式存在异议，但我个人是非常推荐使用该种开发方式的。关于`TDD`的优势，我就不在此赘述了，我就只说下自己受益最深的两个方面。

- 测试驱动，其实也是需求驱动。在开发正式代码之前，可以先将需求转换为单元测试用例，然后再逐步实现正式代码，直至将所有单元测试用例跑通。这可以帮助我们总是聚焦在要实现的功能特性上，避免跑偏。特别是像我们做测试开发的，通常没有需求文档和设计文档，如果没有清晰的思路，很可能做着做着就不知道自己做到哪儿了。
- 高覆盖率的单元测试代码，对项目质量有充足的信心。因为是先写测试再写实现，所以正常情况下，所有的功能特性都应该能被单元测试覆盖到。再结合持续集成的手段，我们可以轻松保证每个版本都是高质量并且可用的。

所以，[`ApiTestEngine`][ApiTestEngine]项目也将采用`TDD`的开发模式。本篇文章就重点介绍下采用`TDD`之前需要做的一些准备工作。

## 搭建API接口服务（Mock Server）

接口测试框架要运行起来，必然需要有可用的API接口服务。因此，在开始构建我们的接口测试框架之前，最好先搭建一套简单的API接口服务，也就是`Mock Server`，然后我们在采用`TDD`开发模式的时候，就可以随时随地将框架代码跑起来，开发效率也会大幅提升。

为什么不直接采用已有的业务系统API接口服务呢？

这是因为通常业务系统的接口比较复杂，并且耦合了许多业务逻辑，甚至还可能涉及到和其它业务系统的交互，搭建或维护一套测试环境的成本可能会非常高。另一方面，接口测试框架需要具有一定的通用性，其功能特性很难在一个特定的业务系统中找到所有合适的接口。就拿最简单的接口请求方法来说，测试框架需要支持`GET/POST/HEAD/PUT/DELETE`方法，但是可能在我们已有的业务系统中只有`GET/POST`接口。

自行搭建API接口服务的另一个好处在于，我们可以随时调整接口的实现方式，来满足接口测试框架特定的功能特性，从而使我们总是能将注意力集中在测试框架本身。比较好的做法是，先搭建最简单的接口服务，在此基础上将接口测试框架搭建起来，实现最基本的功能；后面在实现框架的高级功能特性时，我们再对该接口服务进行拓展升级，例如增加签名校验机制等，来适配测试框架的高级功能特性。

幸运的是，使用`Python`搭建API接口服务十分简单，特别是在结合使用[`Flask`][Flask]框架的情况下。

例如，我们想实现一套可以对用户账号进行增删改查（`CRUD`）功能的接口服务，用户账号的存储结构大致如下：

```json
users_dict = {
   'uid1': {
       'name': 'name1',
       'password': 'pwd1'
   },
   'uid2': {
       'name': 'name2',
       'password': 'pwd2'
   }
}
```

那么，新增（Create）和更新（Update）功能的接口就可以通过如下方式实现。

```python
import json
from flask import Flask
from flask import request, make_response

app = Flask(__name__)
users_dict = {}

@app.route('/api/users/<int:uid>', methods=['POST'])
def create_user(uid):
    user = request.get_json()
    if uid not in users_dict:
        result = {
            'success': True,
            'msg': "user created successfully."
        }
        status_code = 201
        users_dict[uid] = user
    else:
        result = {
            'success': False,
            'msg': "user already existed."
        }
        status_code = 500

    response = make_response(json.dumps(result), status_code)
    response.headers["Content-Type"] = "application/json"
    return response

@app.route('/api/users/<int:uid>', methods=['PUT'])
def update_user(uid):
    user = users_dict.get(uid, {})
    if user:
        user = request.get_json()
        success = True
        status_code = 200
    else:
        success = False
        status_code = 404

    result = {
        'success': success,
        'data': user
    }
    response = make_response(json.dumps(result), status_code)
    response.headers["Content-Type"] = "application/json"
    return response
```

限于篇幅，其它类型的接口实现就不在此赘述，完整的接口实现可以参考[项目源码][api_server]。

接口服务就绪后，按照`Flask`官方文档，可以通过如下方式进行启动：

```text
$ export FLASK_APP=test/api_server.py
$ flask run
 * Serving Flask app "test.api_server"
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
```

启动后，我们就可以通过请求接口来调用已经实现的接口功能了。例如，先创建一个用户，然后查看所有用户的信息，在`Python`终端中的调用方式如下：

```text
$ python
Python 3.6.0 (default, Mar 24 2017, 16:58:25)
>>> import requests
>>> requests.post('http://127.0.0.1:5000/api/users/1000', json={'name': 'user1', 'password': '123456'})
<Response [201]>
>>> resp = requests.get('http://127.0.0.1:5000/api/users')
>>> resp.content
b'{"success": true, "count": 1, "items": [{"name": "user1", "password": "123456"}]}'
>>>
```

通过接口请求结果可见，接口服务运行正常。

## 在单元测试用例中使用 Mock Server

API接口服务（`Mock Server`）已经有了，但是如果每次运行单元测试时都要先在外部手工启动API接口服务的话，做法实在是不够优雅。

推荐的做法是，制作一个`ApiServerUnittest`基类，在其中添加`setUpClass`类方法，用于启动API接口服务（`Mock Server`）；添加`tearDownClass`类方法，用于停止API接口服务。由于`setUpClass`会在单元测试用例集初始化的时候执行一次，所以可以保证单元测试用例在运行的时候API服务处于可用状态；而`tearDownClass`会在单元测试用例集执行完毕后运行一次，停止API接口服务，从而避免对下一次启动产生影响。

```python
# test/base.py
import multiprocessing
import time
import unittest
from . import api_server

class ApiServerUnittest(unittest.TestCase):
    """
    Test case class that sets up an HTTP server which can be used within the tests
    """
    @classmethod
    def setUpClass(cls):
        cls.api_server_process = multiprocessing.Process(
            target=api_server.app.run
        )
        cls.api_server_process.start()
        time.sleep(0.1)

    @classmethod
    def tearDownClass(cls):
        cls.api_server_process.terminate()
```

这里采用的是多进程的方式（`multiprocessing`），所以我们的单元测试用例可以和API接口服务（`Mock Server`）同时运行。除了多进程的方式，我看到`locust`项目采用的是[`gevent.pywsgi.WSGIServer`][locust-test-webserver]的方式，不过由于在`gevent`中要实现异步需要先`monkey.patch_all()`，感觉比较麻烦，而且还需要引入`gevent`这么一个第三方依赖库，所以还是决定采用`multiprocessing`的方式了。至于为什么没有选择多线程模型（`threading`），是因为线程至不支持显式终止的（`terminate`），要实现终止服务会比使用`multiprocessing`更为复杂。

不过需要注意的是，由于启动`Server`存在一定的耗时，因此在启动完毕后必须要等待一段时间（本例中`0.1秒`就足够了），否则在执行单元测试用例时，调用的API接口可能还处于不可用状态。

`ApiServerUnittest`基类就绪后，对于需要用到`Mock Server`的单元测试用例集，只需要继承`ApiServerUnittest`即可；其它的写法跟普通的单元测试完全一致。

例如，下例包含一个单元测试用例，测试“创建一个用户，该用户之前不存在”的场景。

```python
# test/test_apiserver.py
import requests
from .base import ApiServerUnittest

class TestApiServer(ApiServerUnittest):
    def setUp(self):
        super(TestApiServer, self).setUp()
        self.host = "http://127.0.0.1:5000"
        self.api_client = requests.Session()
        self.clear_users()

    def tearDown(self):
        super(TestApiServer, self).tearDown()

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

## 为项目添加持续集成构建检查（Travis CI）

当我们的项目具有单元测试之后，我们就可以为项目添加持续集成构建检查，从而在每次提交代码至`GitHub`时都运行测试，确保我们每次提交的代码都是可正常部署及运行的。

要实现这个功能，推荐使用[`Travis CI`][travis-ci]提供的服务，该服务对于GitHub公有仓库是免费的。要完成配置，操作也很简单，基本上只有三步：

- 在[`Travis CI`][travis-ci]使用GitHub账号授权登录；
- 在[`Travis CI`][travis-ci]的个人`profile`页面开启需要持续集成的项目；
- 在`Github`项目的根目录下添加`.travis.yml`配置文件。

大多数情况下，`.travis.yml`配置文件可以很简单，例如[`ApiTestEngine`][ApiTestEngine]的配置就只有如下几行：

```yaml
sudo: false
language: python
python:
  - 2.7
  - 3.3
  - 3.4
  - 3.5
  - 3.6
install:
  - pip install -r requirements.txt
script:
  - python -m unittest discover
```

具体含义不用解释也可以很容易看懂，其中`install`中包含我们项目的依赖库安装命令，`script`中包含执行构建测试的命令。

配置完毕后，后续每次提交代码时，`GitHub`就会调用`Travis CI`实现构建检查；并且更赞的在于，构建检查可以同时在多个指定的`Python`版本环境中进行。

下图是某次提交代码时的构建结果。

![](/images/travis-check-result.jpg)

另外，我们还可以在`GitHub`项目的`README.md`中添加一个`Status Image`，实时显示项目的构建状态，就像下图显示的样子。

![](/images/github-readme-travis-status-image.jpg)

配置方式也是很简单，只需要先在`Travis CI`中获取到项目`Status Image`的URL地址，然后添加到`README.md`即可。

![](/images/travis-status-image-url.jpg)

## 写在后面

通过本文中的工作，我们就对项目搭建好了测试框架，并实现了持续集成构建检查机制。从下一篇开始，我们就将开始逐步实现接口自动化测试框架的核心功能特性了。

## 阅读更多

- [《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]

[ApiTestEngine-Intro]: http://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[Flask]: http://flask.pocoo.org/
[api_server]: https://github.com/debugtalk/ApiTestEngine/blob/master/test/api_server.py
[locust-test-webserver]: https://github.com/locustio/locust/blob/master/locust/test/test_web.py
[travis-ci]: https://travis-ci.org/
