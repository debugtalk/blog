---
title: ApiTestEngine 演进之路（0）开发未动，测试先行
permalink: post/ApiTestEngine-0-setup-CI-test
date: 2017/06/20
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
  - Mock
---

在[《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]一文中，我详细介绍了[`ApiTestEngine`][ApiTestEngine]诞生的背景，并对其核心特性进行了详尽的剖析。

接下来，我将在《ApiTestEngine演进之路》系列文章中讲解[`ApiTestEngine`][ApiTestEngine]是如何从第一行代码开始，逐步实现接口自动化测试框架的核心功能特性的。

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
$ export FLASK_APP=tests/api_server.py
$ flask run
 * Serving Flask app "tests.api_server"
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
# tests/base.py
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
# tests/test_apiserver.py
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

## 为项目添加单元测试覆盖率检查（coveralls）

对项目添加持续集成构建检查以后，就能完全保证我们提交的代码运行没问题么？

答案是并不能。试想，假如我们整个项目中就只有一条单元测试用例，甚至这一条单元测试用例还是个假用例，即没有调用任何代码，那么可想而知，我们的持续集成构建检查总是成功的，并没有起到检查的作用。

因此，这里还涉及到一个单元测试覆盖率的问题。

怎么理解单元测试覆盖率呢？简单地说，就是我们在执行单元测试时运行代码的行数，与项目总代码数的比值。

对于主流的编程语言，都存在大量的覆盖率检查工具，可以帮助我们快速统计单元测试覆盖率。在Python中，用的最多的覆盖率检查工具是[`coverage`][coverage]。

要使用[`coverage`][coverage]，需要先进行安装，采用`pip`的安装方式如下：

```bash
$ pip install coverage
```

然后，我们就可以采用如下命令执行单元测试。

```bash
$ coverage run --source=ate -m unittest discover
```

这里需要说明的是，`--source`参数的作用是指定统计的目录，如果不指定该参数，则会将所有依赖库也计算进去，但由于很多依赖库在安装时是没有包含测试代码的，因此会造成统计得到的单元测试覆盖率远低于实际的情况。在上面的命令中，就只统计了`ate`目录下的单元测试覆盖率；如果要统计当前项目的覆盖率，那么可以指定`--source=.`（即当前目录下的所有子文夹）。

采用上述命令执行完单元测试后，会在当前目录下生成一个统计结果文件，`.coverage`，里面包含了详细的统计结果。

```text
cat .coverage
!coverage.py: This is a private format, don't read it directly!{"lines":{"/Users/Leo/MyProjects/ApiTestEngine/ate/__init__.py":[1],"/Users/Leo/MyProjects/
ApiTestEngine/ate/testcase.py":[1,2,4,6,9,15,42,7,12,40,46,64,67,68,69,70,48,49,62,72,74,13,65,51,52,53,56,60,58,54,55],"/Users/Leo/MyProjects/ApiTestEngi
ne/ate/exception.py":[2,4,5,9,12,15,16,6,7],"/Users/Leo/MyProjects/ApiTestEngine/ate/utils.py":[1,2,3,4,5,7,9,11,12,14,15,18,22,25,47,51,55,65,77,90,129,1
41,27,31,32,19,20,23,34,41,43,45,56,57,59,60,48,49,154,163,166,170,172,173,174,176,177,181,182,183,186,187,189,91,92,66,67,72,73,74,94,95,97,98,101,102,78
,80,81,82,84,85,88,103,104,106,108,110,115,121,122,124,125,127,58,52,53,184,185,109,116,118,119,112,113,132,134,135,136,137,139,63,164,155,157,158,159,161
,167,168,192,68,69],"/Users/Leo/MyProjects/ApiTestEngine/ate/context.py":[1,3,5,6,10,16,30,45,7,8,25,26,28,41,42,43,49,55,58,59,63,64,56,74,65,68,69,72,66
,27,13,14,50,53,52,70],"/Users/Leo/MyProjects/ApiTestEngine/ate/main.py":[1,2,4,7,9,10,15,21,38,51,25,27,28,29,30,32,33,11,12,13,34,36,42,43,45,46,47,49],
"/Users/Leo/MyProjects/ApiTestEngine/ate/runner.py":[1,3,4,5,8,10,15,46,68,97,135,11,12,13,35,36,38,39,41,42,44,82,63,65,66,84,86,87,88,92,93,94,95,124,12
6,127,128,129,130,131,133,154]}}%
```

但是，这个结果就不是给人看的。要想直观地看到统计报告，需要再执行命令`coverage report -m`，执行完后，就可以看到详细的统计数据了。

```bash
➜  ApiTestEngine git:(master) ✗ coverage report -m
Name               Stmts   Miss  Cover   Missing
------------------------------------------------
ate/__init__.py        0      0   100%
ate/context.py        35      0   100%
ate/exception.py      11      2    82%   10, 13
ate/main.py           34      7    79%   18-19, 54-62
ate/runner.py         44      2    95%   89-90
ate/testcase.py       30      0   100%
ate/utils.py         112      8    93%   13, 29, 36-39, 178-179
------------------------------------------------
TOTAL                266     19    93%
```

通过这个报告，可以看到项目整体的单元测试覆盖率为`93%`，并清晰地展示了每个源代码文件的具体覆盖率数据，以及没有覆盖到的代码行数。

那要怎么将覆盖率检查添加到我们的持续集成（Travis CI）中呢？

事实上，当前存在多个可选服务，可以与`Travis CI`配合使用。当前，使用得比较广泛的是[`coveralls`][coveralls]，针对Public类型的GitHub仓库，这也是一个免费服务。

[`coveralls`][coveralls]的使用方式与[`Travis CI`][travis-ci]类似，也需要先在[`coveralls`][coveralls]网站上采用GitHub账号授权登录，然后开启需要进行检查的GitHub仓库。而要执行的命令，也可以在`.travis.yml`配置文件中指定。

增加覆盖率检查后的`.travis.yml`配置文件内容如下。

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
  - pip install coverage
  - pip install coveralls
script:
  - coverage run --source=. -m unittest discover
after_success:
  - coveralls
```

如上配置应该也很好理解，要使用`coveralls`的服务，需要先安装`coveralls`。在采用`coverage`执行完单元测试后，要将结果上报到[`coveralls`][coveralls]网站，需要再执行`coveralls`命令。由于`coveralls`命令只有在测试覆盖率检查成功以后运行才有意义，因此可将其放在`after_success`部分。

配置完毕后，后续每次提交代码时，`GitHub`就会调用`Travis CI`实现构建检查，并同时统计得到单元测试覆盖率。

下图是某次提交代码时的覆盖率检查。

![](/images/coveralls-result.jpg)

另外，我们在`GitHub`项目的`README.md`中也同样可以添加一个`Status Image`，实时显示项目的单元测试覆盖率。

![](/images/github-coveralls-badge.jpg)

配置方式也跟之前类似，在[`coveralls`][coveralls]中获取到项目`Status Image`的URL地址，然后添加到`README.md`即可。

![](/images/coveralls-image-url.jpg)

最后需要说明的是，项目的单元测试覆盖率只能起到参考作用，没有被单元测试覆盖到的代码我们不能说它肯定有问题，100%覆盖率的代码也并不能保证它肯定没有问题。归根结底，这还是要依赖于单元测试的策略实现，因此我们在写单元测试的时候也要尽可能多地覆盖到各种逻辑路径，以及兼顾到各种异常情况。

## 写在后面

通过本文中的工作，我们就对项目搭建好了测试框架，并实现了持续集成构建检查机制。从下一篇开始，我们就将开始逐步实现接口自动化测试框架的核心功能特性了。

## 阅读更多

- [《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]

[ApiTestEngine-Intro]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[Flask]: http://flask.pocoo.org/
[api_server]: https://github.com/debugtalk/ApiTestEngine/blob/master/tests/api_server.py
[locust-test-webserver]: https://github.com/locustio/locust/blob/master/locust/test/test_web.py
[travis-ci]: https://travis-ci.org/
[coverage]: https://coverage.readthedocs.io
[coveralls]: https://coveralls.io
