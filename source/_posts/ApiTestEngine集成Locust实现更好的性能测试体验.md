---
title: ApiTestEngine 集成 Locust 实现更好的性能测试体验
permalink: post/apitestengine-supersede-locust
date: 2017/08/27
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
  - Locust
---

[`ApiTestEngine`]不是接口测试框架么，也能实现性能测试？

是的，你没有看错，[`ApiTestEngine`]集成了[`Locust`]性能测试框架，只需一份测试用例，就能同时实现接口自动化测试和接口性能测试，在不改变[`Locust`]任何特性的情况下，甚至比`Locust`本身更易用。

如果你还没有接触过[`Locust`]这款性能测试工具，那么这篇文章可能不适合你。但我还是强烈推荐你了解一下这款工具。简单地说，[`Locust`]是一款采用`Python`语言编写实现的开源性能测试工具，简洁、轻量、高效，并发机制基于`gevent`协程，可以实现单机模拟生成较高的并发压力。关于[`Locust`]的特性介绍和使用教程，我之前已经写过不少，你们可以在我的博客中找到[对应文章][debugtalk-locust]。

如果你对实现的过程没有兴趣，可以直接跳转到文章底部，看`最终实现效果`章节。

## 灵感来源

在当前市面上的测试工具中，接口测试和性能测试基本上是两个泾渭分明的领域。这也意味着，针对同一个系统的服务端接口，我们要对其实现接口自动化测试和接口性能测试时，通常都是采用不同的工具，分别维护两份测试脚本或用例。

之前我也是这么做的。但是在做了一段时间后我就在想，不管是接口功能测试，还是接口性能测试，核心都是要模拟对接口发起请求，然后对接口响应内容进行解析和校验；唯一的差异在于，接口性能测试存在并发的概念，相当于模拟了大量用户同时在做接口测试。

既然如此，那接口自动化测试用例和接口性能测试脚本理应可以合并为一套，这样就可以避免重复的脚本开发工作了。

在开发[`ApiTestEngine`]的过程中，之前的文章也说过，[`ApiTestEngine`]完全基于[`Python-Requests`]库实现HTTP的请求处理，可以在编写接口测试用例时复用到[`Python-Requests`]的所有功能特性。而之前在学习[`Locust`]的源码时，发现[`Locust`]在实现HTTP请求的时候，也完全是基于[`Python-Requests`]库。

在这一层关系的基础上，我提出一个大胆的设想，能否通过一些方式或手段，可以使[`ApiTestEngine`]中编写的`YAML/JSON`格式的接口测试用例，也能直接让[`Locust`]直接调用呢？

## 灵感初探

想法有了以后，就开始探索实现的方法了。

首先，我们可以看下[`Locust`]的脚本形式。如下例子是一个比较简单的场景（截取自官网首页）。

```python
from locust import HttpLocust, TaskSet, task

class WebsiteTasks(TaskSet):
    def on_start(self):
        self.client.post("/login", {
            "username": "test_user",
            "password": ""
        })

    @task
    def index(self):
        self.client.get("/")

    @task
    def about(self):
        self.client.get("/about/")

class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    min_wait = 5000
    max_wait = 15000
```

在[`Locust`]的脚本中，我们会在`TaskSet`子类中描述单个用户的行为，每一个带有`@task`装饰器的方法都对应着一个HTTP请求场景。而[`Locust`]的一个很大特点就是，所有的测试用例脚本都是`Python`文件，因此我们可以采用Python实现各种复杂的场景。

等等！模拟单个用户请求，而且还是纯粹的Python语言，我们不是在接口测试中已经实现的功能么？

例如，下面的代码就是从单元测试中截取的测试用例。

```python
def test_run_testset(self):
    testcase_file_path = os.path.join(
        os.getcwd(), 'examples/quickstart-demo-rev-3.yml')
    testsets = utils.load_testcases_by_path(testcase_file_path)
    results = self.test_runner.run_testset(testsets[0])
```

`test_runner.run_testset`是已经在`ApiTestEngine`中实现的方法，作用是传入测试用例（`YAML/JSON`）的路径，然后就可以加载测试用例，运行整个测试场景。并且，由于我们在测试用例`YAML/JSON`中已经描述了`validators`，即接口的校验部分，因此我们也无需再对接口响应结果进行校验描述了。

接下来，实现方式就非常简单了。

我们只需要制作一个`locustfile.py`的模板文件，内容如下。

```python
#coding: utf-8
import zmq
import os
from locust import HttpLocust, TaskSet, task
from ate import utils, runner

class WebPageTasks(TaskSet):
    def on_start(self):
        self.test_runner = runner.Runner(self.client)
        self.testset = self.locust.testset

    @task
    def test_specified_scenario(self):
       self.test_runner.run_testset(self.testset)

class WebPageUser(HttpLocust):
    host = ''
    task_set = WebPageTasks
    min_wait = 1000
    max_wait = 5000

    testcase_file_path = os.path.join(os.getcwd(), 'skypixel.yml')
    testsets = utils.load_testcases_by_path(testcase_file_path)
    testset = testsets[0]
```

可以看出，整个文件中，只有测试用例文件的路径是与具体测试场景相关的，其它内容全都可以不变。

于是，针对不同的测试场景，我们只需要将`testcase_file_path`替换为接口测试用例文件的路径，即可实现对应场景的接口性能测试。

```bash
➜  ApiTestEngine git:(master) ✗ locust -f locustfile.py
[2017-08-27 11:30:01,829] bogon/INFO/locust.main: Starting web monitor at *:8089
[2017-08-27 11:30:01,831] bogon/INFO/locust.main: Starting Locust 0.8a2
```

后面的操作就完全是[`Locust`]的内容了，使用方式完全一样。

![](/images/locust-start.jpg)

## 优化1：自动生成locustfile

通过前面的探索实践，我们基本上就实现了一份测试用例同时兼具接口自动化测试和接口性能测试的功能。

然而，在使用上还不够便捷，主要有两点：

- 需要手工修改模板文件中的`testcase_file_path`路径；
- `locustfile.py`模板文件的路径必须放在`ApiTestEngine`的项目根目录下。

于是，我产生了让`ApiTestEngine`框架本身自动生成`locustfile.py`文件的想法。

在实现这个想法的过程中，我想过两种方式。

第一种，通过分析[`Locust`]的源码，可以看到`Locust`在`main.py`中具有一个`load_locustfile`方法，可以加载Python格式的文件，并提取出其中的`locust_classes`（也就是`Locust`的子类）；后续，就是将`locust_classes`作为参数传给`Locust`的`Runner`了。

若采用这种思路，我们就可以实现一个类似`load_locustfile`的方法，将`YAML/JSON`文件中的内容动态生成`locust_classes`，然后再传给`Locust`的`Runner`。这里面会涉及到动态地创建类和添加方法，好处是不需要生成`locustfile.py`中间文件，并且可以实现最大的灵活性，但缺点在于需要改变[`Locust`]的源码，即重新实现[`Locust`]的`main.py`中的多个函数。虽然难度不会太大，但考虑到后续需要与[`Locust`]的更新保持一致，具有一定的维护工作量，便放弃了该种方案。

第二种，就是生成`locustfile.py`这样一个中间文件，然后将文件路径传给`Locust`。这样的好处在于我们可以不改变[`Locust`]的任何地方，直接对其进行使用。与[`Locust`]的传统使用方式差异在于，之前我们是在`Terminal`中通过参数启动`Locust`，而现在我们是在`ApiTestEngine`框架中通过Python代码启动`Locust`。

具体地，我在`setup.py`的`entry_points`中新增了一个命令`locusts`，并绑定了对应的程序入口。

```python
entry_points={
    'console_scripts': [
        'ate=ate.cli:main_ate',
        'locusts=ate.cli:main_locust'
    ]
}
```

在`ate/cli.py`中新增了`main_locust`函数，作为`locusts`命令的入口。

```python
def main_locust():
    """ Performance test with locust: parse command line options and run commands.
    """
    try:
        from locust.main import main
    except ImportError:
        print("Locust is not installed, exit.")
        exit(1)

    sys.argv[0] = 'locust'
    if len(sys.argv) == 1:
        sys.argv.extend(["-h"])

    if sys.argv[1] in ["-h", "--help", "-V", "--version"]:
        main()
        sys.exit(0)

    try:
        testcase_index = sys.argv.index('-f') + 1
        assert testcase_index < len(sys.argv)
    except (ValueError, AssertionError):
        print("Testcase file is not specified, exit.")
        sys.exit(1)

    testcase_file_path = sys.argv[testcase_index]
    sys.argv[testcase_index] = parse_locustfile(testcase_file_path)
    main()
```

若你执行`locusts -V`或`locusts -h`，会发现效果与`locust`的特性完全一致。

```bash
$ locusts -V
[2017-08-27 12:41:27,740] bogon/INFO/stdout: Locust 0.8a2
[2017-08-27 12:41:27,740] bogon/INFO/stdout:
```

事实上，通过上面的代码（`main_locust`）也可以看出，`locusts`命令只是对`locust`进行了一层封装，用法基本等价。唯一的差异在于，当`-f`参数指定的是`YAML/JSON`格式的用例文件时，会先转换为Python格式的`locustfile.py`，然后再传给`locust`。

至于解析函数`parse_locustfile`，实现起来也很简单。我们只需要在框架中保存一份`locustfile.py`的模板文件（`ate/locustfile_template`），并将`testcase_file_path`采用占位符代替。然后，在解析函数中，就可以读取整个模板文件，将其中的占位符替换为`YAML/JSON`用例文件的实际路径，然后再保存为`locustfile.py`，并返回其路径即可。

具体的代码就不贴了，有兴趣的话可自行查看。

通过这一轮优化，`ApiTestEngine`就继承了[`Locust`]的全部功能，并且可以直接指定`YAML/JSON`格式的文件启动[`Locust`]执行性能测试。

```bash
$ locusts -f examples/first-testcase.yml
[2017-08-18 17:20:43,915] Leos-MacBook-Air.local/INFO/locust.main: Starting web monitor at *:8089
[2017-08-18 17:20:43,918] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
```

## 优化2：一键启动多个locust实例

经过第一轮优化后，本来应该是告一段落了，因为此时`ApiTestEngine`已经可以非常便捷地实现接口自动化测试和接口性能测试的切换了。

直到有一天，在`TesterHome`论坛讨论`Locust`的一个[回复][keithmork-reply]中，[`@keithmork`]说了这么一句话。

> 期待有一天`ApiTestEngine`的热度超过`Locust`本身

看到这句话时我真的不禁泪流满面。虽然我也是一直在用心维护`ApiTestEngine`，却从未有过这样的奢望。

但反过来细想，为啥不能有这样的想法呢？当前`ApiTestEngine`已经继承了`Locust`的所有功能，在不影响`Locust`已有特性的同时，还可以采用`YAML/JSON`格式来编写维护测试用例，并实现了一份测试用例可同时用于接口自动化和接口性能测试的目的。

这些特性都是`Locust`所不曾拥有的，而对于使用者来说的确也都是比较实用的功能。

于是，新的目标在内心深处萌芽了，那就是在`ApiTestEngine`中通过对`Locust`更好的封装，让`Locust`的使用者体验更爽。

然后，我又想到了自己之前做的一个开源项目，[`debugtalk/stormer`][stormer]。当时做这个项目的初衷在于，当我们使用`Locust`进行压测时，要想使用压测机所有CPU的性能，就需要采用`master-slave`模式。因为`Locust`默认是单进程运行的，只能运行在压测机的一个CPU核上；而通过采用`master-slave`模式，启动多个`slave`，就可以让不同的`slave`运行在不同的CPU核上，从而充分发挥压测机多核处理器的性能。

而在实际使用`Locust`的时候，每次只能手动启动`master`，并依次手动启动多个`slave`。若遇到测试脚本调整的情况，就需要逐一结束`Locust`的所有进程，然后再重复之前的启动步骤。如果有使用过`Locust`的同学，应该对此痛苦的经历都有比较深的体会。当时也是基于这一痛点，我开发了[`debugtalk/stormer`][stormer]，目的就是可以一次性启动或销毁多个`Locust`实例。这个脚本做出来后，自己用得甚爽，也得到了`Github`上一些朋友的青睐。

既然现在要提升`ApiTestEngine`针对`Locust`的使用便捷性，那么这个特性毫无疑问也应该加进去。就此，[`debugtalk/stormer`][stormer]项目便被废弃，正式合并到`debugtalk/ApiTestEngine`。

想法明确后，实现起来也挺简单的。

原则还是保持不变，那就是不改变[`Locust`]本身的特性，只在传参的时候在中间层进行操作。

具体地，我们可以新增一个`--full-speed`参数。当不指定该参数时，使用方式跟之前完全相同；而指定`--full-speed`参数后，就可以采用多进程的方式启动多个实例（实例个数等于压测机的处理器核数）。

```python
def main_locust():
    # do original work

    if "--full-speed" in sys.argv:
        locusts.run_locusts_at_full_speed(sys.argv)
    else:
        locusts.main()
```

具体实现逻辑在`ate/locusts.py`中：

```python
import multiprocessing
from locust.main import main

def start_master(sys_argv):
    sys_argv.append("--master")
    sys.argv = sys_argv
    main()

def start_slave(sys_argv):
    sys_argv.extend(["--slave"])
    sys.argv = sys_argv
    main()

def run_locusts_at_full_speed(sys_argv):
    sys_argv.pop(sys_argv.index("--full-speed"))
    slaves_num = multiprocessing.cpu_count()

    processes = []
    for _ in range(slaves_num):
        p_slave = multiprocessing.Process(target=start_slave, args=(sys_argv,))
        p_slave.daemon = True
        p_slave.start()
        processes.append(p_slave)

    try:
        start_master(sys_argv)
    except KeyboardInterrupt:
        sys.exit(0)
```

由此可见，关键点也就是使用了`multiprocessing.Process`，在不同的进程中分别调用`Locust`的`main()`函数，实现逻辑十分简单。

## 最终实现效果

经过前面的优化，采用`ApiTestEngine`执行性能测试时，使用就十分便捷了。

安装`ApiTestEngine`后，系统中就具有了`locusts`命令，使用方式跟`Locust`框架的`locust`几乎完全相同，我们完全可以使用`locusts`命令代替原生的`locust`命令。

例如，下面的命令执行效果与`locust`完全一致。

```bash
$ locusts -V
$ locusts -h
$ locusts -f locustfile.py
$ locusts -f locustfile.py --master -P 8088
$ locusts -f locustfile.py --slave &
```

差异在于，`locusts`具有更加丰富的功能。

在`ApiTestEngine`中编写的`YAML/JSON`格式的接口测试用例文件，直接运行就可以启动`Locust`运行性能测试。

```bash
$ locusts -f examples/first-testcase.yml
[2017-08-18 17:20:43,915] Leos-MacBook-Air.local/INFO/locust.main: Starting web monitor at *:8089
[2017-08-18 17:20:43,918] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
```

加上`--full-speed`参数，就可以同时启动多个`Locust`实例（实例个数等于处理器核数），充分发挥压测机多核处理器的性能。

```bash
$ locusts -f examples/first-testcase.yml --full-speed -P 8088
[2017-08-26 23:51:47,071] bogon/INFO/locust.main: Starting web monitor at *:8088
[2017-08-26 23:51:47,075] bogon/INFO/locust.main: Starting Locust 0.8a2
[2017-08-26 23:51:47,078] bogon/INFO/locust.main: Starting Locust 0.8a2
[2017-08-26 23:51:47,080] bogon/INFO/locust.main: Starting Locust 0.8a2
[2017-08-26 23:51:47,083] bogon/INFO/locust.main: Starting Locust 0.8a2
[2017-08-26 23:51:47,084] bogon/INFO/locust.runners: Client 'bogon_656e0af8e968a8533d379dd252422ad3' reported as ready. Currently 1 clients ready to swarm.
[2017-08-26 23:51:47,085] bogon/INFO/locust.runners: Client 'bogon_09f73850252ee4ec739ed77d3c4c6dba' reported as ready. Currently 2 clients ready to swarm.
[2017-08-26 23:51:47,084] bogon/INFO/locust.main: Starting Locust 0.8a2
[2017-08-26 23:51:47,085] bogon/INFO/locust.runners: Client 'bogon_869f7ed671b1a9952b56610f01e2006f' reported as ready. Currently 3 clients ready to swarm.
[2017-08-26 23:51:47,085] bogon/INFO/locust.runners: Client 'bogon_80a804cda36b80fac17b57fd2d5e7cdb' reported as ready. Currently 4 clients ready to swarm.
```

![](/images/locusts-full-speed.jpg)

后续，[`ApiTestEngine`]将持续进行优化，欢迎大家多多反馈改进建议。

Enjoy!

[`ApiTestEngine`]: https://github.com/debugtalk/ApiTestEngine
[`Locust`]: http://locust.io/
[debugtalk-locust]: https://debugtalk.com/tags/Locust/
[`Python-Requests`]: http://docs.python-requests.org/en/master/
[`@keithmork`]: https://testerhome.com/keithmork
[keithmork-reply]: https://testerhome.com/topics/9277#reply-84542
[stormer]: https://github.com/debugtalk/Stormer
