---
title: 深入浅出开源性能测试工具 Locust（使用篇）
permalink: post/head-first-locust-user-guide
date: 2017/02/22
categories:
  - Testing
  - 性能测试
tags:
  - Locust
---

在[《【LocustPlus序】漫谈服务端性能测试》](/post/locustplus-talk-about-performance-test/)中，我对服务端性能测试的基础概念和性能测试工具的基本原理进行了介绍，并且重点推荐了`Locust`这一款开源性能测试工具。然而，当前在网络上针对`Locust`的教程极少，不管是中文还是英文，基本都是介绍安装方法和简单的测试案例演示，但对于较复杂测试场景的案例演示却基本没有，因此很多测试人员都感觉难以将`Locust`应用到实际的性能测试工作当中。

经过一段时间的摸索，包括通读`Locust`官方文档和项目源码，并且在多个性能测试项目中对`Locust`进行应用实践，事实证明，`Locust`完全能满足日常的性能测试需求，`LoadRunner`能实现的功能`Locust`也基本都能实现。

本文将从`Locust`的功能特性出发，结合实例对`Locust`的使用方法进行介绍。考虑到大众普遍对`LoadRunner`比较熟悉，在讲解`Locust`时也会采用`LoadRunner`的一些概念进行类比。

## 概述

先从`Locust`的名字说起。`Locust`的原意是蝗虫，原作者之所以选择这个名字，估计也是听过这么一句俗语，“蝗虫过境，寸草不生”。我在网上找了张图片，大家可以感受下。

![](/images/14875962785342.jpg)

而`Locust`工具生成的并发请求就跟一大群蝗虫一般，对我们的被测系统发起攻击，以此检测系统在高并发压力下是否能正常运转。

在[《【LocustPlus序】漫谈服务端性能测试》](/post/locustplus-talk-about-performance-test/)中说过，服务端性能测试工具最核心的部分是压力发生器，而压力发生器的核心要点有两个，一是真实模拟用户操作，二是模拟有效并发。

在`Locust`测试框架中，测试场景是采用纯Python脚本进行描述的。对于最常见的`HTTP(S)`协议的系统，`Locust`采用Python的`requests`库作为客户端，使得脚本编写大大简化，富有表现力的同时且极具美感。而对于其它协议类型的系统，`Locust`也提供了接口，只要我们能采用Python编写对应的请求客户端，就能方便地采用`Locust`实现压力测试。从这个角度来说，`Locust`可以用于压测任意类型的系统。

在模拟有效并发方面，`Locust`的优势在于其摒弃了进程和线程，完全基于事件驱动，使用`gevent`提供的`非阻塞IO`和`coroutine`来实现网络层的并发请求，因此即使是单台压力机也能产生数千并发请求数；再加上对分布式运行的支持，理论上来说，`Locust`能在使用较少压力机的前提下支持极高并发数的测试。

## 脚本编写

编写`Locust`脚本，是使用`Locust`的第一步，也是最为重要的一步。

### 简单示例

先来看一个最简单的示例。

```python
from locust import HttpLocust, TaskSet, task

class WebsiteTasks(TaskSet):
    def on_start(self):
        self.client.post("/login", {
            "username": "test",
            "password": "123456"
        })

    @task(2)
    def index(self):
        self.client.get("/")

    @task(1)
    def about(self):
        self.client.get("/about/")

class WebsiteUser(HttpLocust):
    task_set = WebsiteTasks
    host = "https://debugtalk.com"
    min_wait = 1000
    max_wait = 5000
```

在这个示例中，定义了针对`https://debugtalk.com`网站的测试场景：先模拟用户登录系统，然后随机地访问首页（`/`）和关于页面（`/about/`），请求比例为`2:1`；并且，在测试过程中，两次请求的间隔时间为`1~5`秒间的随机值。

那么，如上Python脚本是如何表达出以上测试场景的呢？

从脚本中可以看出，脚本主要包含两个类，一个是`WebsiteUser`（继承自`HttpLocust`，而`HttpLocust`继承自`Locust`），另一个是`WebsiteTasks`（继承自`TaskSet`）。事实上，在`Locust`的测试脚本中，所有业务测试场景都是在`Locust`和`TaskSet`两个类的继承子类中进行描述的。

那如何理解`Locust`和`TaskSet`这两个类呢？

简单地说，`Locust类`就好比是一群蝗虫，而每一只蝗虫就是一个类的实例。相应的，`TaskSet类`就好比是蝗虫的大脑，控制着蝗虫的具体行为，即实际业务场景测试对应的任务集。

这个比喻可能不是很准确，接下来，我将分别对`Locust`和`TaskSet`两个类进行详细介绍。

### class HttpLocust(Locust)

在`Locust类`中，具有一个`client`属性，它对应着虚拟用户作为客户端所具备的请求能力，也就是我们常说的请求方法。通常情况下，我们不会直接使用`Locust`类，因为其`client`属性没有绑定任何方法。因此在使用`Locust`时，需要先继承`Locust类`，然后在继承子类中的`client`属性中绑定客户端的实现类。

对于常见的`HTTP(S)`协议，`Locust`已经实现了`HttpLocust`类，其`client`属性绑定了`HttpSession`类，而`HttpSession`又继承自`requests.Session`。因此在测试`HTTP(S)`的`Locust脚本`中，我们可以通过`client`属性来使用`Python requests`库的所有方法，包括`GET/POST/HEAD/PUT/DELETE/PATCH`等，调用方式也与`requests`完全一致。另外，由于`requests.Session`的使用，因此`client`的方法调用之间就自动具有了状态记忆的功能。常见的场景就是，在登录系统后可以维持登录状态的`Session`，从而后续HTTP请求操作都能带上登录态。

而对于`HTTP(S)`以外的协议，我们同样可以使用`Locust`进行测试，只是需要我们自行实现客户端。在客户端的具体实现上，可通过注册事件的方式，在请求成功时触发`events.request_success`，在请求失败时触发`events.request_failure`即可。然后创建一个继承自`Locust类`的类，对其设置一个`client`属性并与我们实现的客户端进行绑定。后续，我们就可以像使用`HttpLocust类`一样，测试其它协议类型的系统。

原理就是这样简单！

在`Locust类`中，除了`client`属性，还有几个属性需要关注下：

- `task_set`: 指向一个`TaskSet`类，`TaskSet`类定义了用户的任务信息，该属性为必填；
- `max_wait/min_wait`: 每个用户执行两个任务间隔时间的上下限（毫秒），具体数值在上下限中随机取值，若不指定则默认间隔时间固定为1秒；
- `host`：被测系统的host，当在终端中启动`locust`时没有指定`--host`参数时才会用到；
- `weight`：同时运行多个`Locust类`时会用到，用于控制不同类型任务的执行权重。

测试开始后，每个虚拟用户（`Locust实例`）的运行逻辑都会遵循如下规律：

1. 先执行`WebsiteTasks`中的`on_start`（只执行一次），作为初始化；
2. 从`WebsiteTasks`中随机挑选（如果定义了任务间的权重关系，那么就是按照权重关系随机挑选）一个任务执行；
3. 根据`Locust类`中`min_wait`和`max_wait`定义的间隔时间范围（如果`TaskSet类`中也定义了`min_wait`或者`max_wait`，以`TaskSet`中的优先），在时间范围中随机取一个值，休眠等待；
4. 重复`2~3`步骤，直至测试任务终止。

### class TaskSet

再说下`TaskSet类`。

性能测试工具要模拟用户的业务操作，就需要通过脚本模拟用户的行为。在前面的比喻中说到，`TaskSet类`好比蝗虫的大脑，控制着蝗虫的具体行为。

具体地，`TaskSet类`实现了虚拟用户所执行任务的调度算法，包括规划任务执行顺序（`schedule_task`）、挑选下一个任务（`execute_next_task`）、执行任务（`execute_task`）、休眠等待（`wait`）、中断控制（`interrupt`）等等。在此基础上，我们就可以在`TaskSet`子类中采用非常简洁的方式来描述虚拟用户的业务测试场景，对虚拟用户的所有行为（任务）进行组织和描述，并可以对不同任务的权重进行配置。

在`TaskSet`子类中定义任务信息时，可以采取两种方式，`@task装饰器`和`tasks属性`。

采用`@task装饰器`定义任务信息时，描述形式如下：

```python
from locust import TaskSet, task

class UserBehavior(TaskSet):
    @task(1)
    def test_job1(self):
        self.client.get('/job1')

    @task(2)
    def test_job2(self):
        self.client.get('/job2')
```

采用`tasks属性`定义任务信息时，描述形式如下：

```python
from locust import TaskSet

def test_job1(obj):
    obj.client.get('/job1')

def test_job2(obj):
    obj.client.get('/job2')

class UserBehavior(TaskSet):
    tasks = {test_job1:1, test_job2:2}
    # tasks = [(test_job1,1), (test_job1,2)] # 两种方式等价
```

在如上两种定义任务信息的方式中，均设置了权重属性，即执行`test_job2`的频率是`test_job1`的两倍。

若不指定执行任务的权重，则相当于比例为`1:1`。

```python
from locust import TaskSet, task

class UserBehavior(TaskSet):
    @task
    def test_job1(self):
        self.client.get('/job1')

    @task
    def test_job2(self):
        self.client.get('/job2')
```

```python
from locust import TaskSet

def test_job1(obj):
    obj.client.get('/job1')

def test_job2(obj):
    obj.client.get('/job2')

class UserBehavior(TaskSet):
    tasks = [test_job1, test_job2]
    # tasks = {test_job1:1, test_job2:1} # 两种方式等价
```

在`TaskSet`子类中除了定义任务信息，还有一个是经常用到的，那就是`on_start`函数。这个和`LoadRunner`中的`vuser_init`功能相同，在正式执行测试前执行一次，主要用于完成一些初始化的工作。例如，当测试某个搜索功能，而该搜索功能又要求必须为登录态的时候，就可以先在`on_start`中进行登录操作；前面也提到，`HttpLocust`使用到了`requests.Session`，因此后续所有任务执行过程中就都具有登录态了。

### 脚本增强

掌握了`HttpLocust`和`TaskSet`，我们就基本具备了编写测试脚本的能力。此时再回过头来看前面的案例，相信大家都能很好的理解了。

然而，当面对较复杂的测试场景，可能有的同学还是会感觉无从下手；例如，很多时候脚本需要做关联或参数化处理，这些在`LoadRunner`中集成的功能，换到`Locust`中就不知道怎么实现了。可能也是这方面的原因，造成很多测试人员都感觉难以将Locust应用到实际的性能测试工作当中。

其实这也跟`Locust`的目标定位有关，`Locust`的定位就是`small and very hackable`。但是小巧并不意味着功能弱，我们完全可以通过Python脚本本身来实现各种各样的功能，如果大家有疑问，我们不妨逐项分解来看。

在`LoadRunner`这款功能全面应用广泛的商业性能测试工具中，脚本增强无非就涉及到四个方面：

- 关联
- 参数化
- 检查点
- 集合点

先说关联这一项。在某些请求中，需要携带之前从Server端返回的参数，因此在构造请求时需要先从之前请求的Response中提取出所需的参数，常见场景就是`session_id`。针对这种情况，`LoadRunner`虽然可能通过录制脚本进行自动关联，但是效果并不理想，在实际测试过程中也基本都是靠测试人员手动的来进行关联处理。

在`LoadRunner`中手动进行关联处理时，主要是通过使用注册型函数，例如`web_reg_save_param`，对前一个请求的响应结果进行解析，根据左右边界或其它特征定位到参数值并将其保存到参数变量，然后在后续请求中使用该参数。采用同样的思想，我们在`Locust`脚本中也完全可以实现同样的功能，毕竟只是Python脚本，通过官方库函数`re.search`就能实现所有需求。甚至针对html页面，我们也可以采用`lxml`库，通过`etree.HTML(html).xpath`来更优雅地实现元素定位。

然后再来看参数化这一项。这一项极其普遍，主要是用在测试数据方面。但通过归纳，发现其实也可以概括为三种类型。

- 循环取数据，数据可重复使用：e.g. 模拟3用户并发请求网页，总共有100个URL地址，每个虚拟用户都会依次循环加载这100个URL地址；
- 保证并发测试数据唯一性，不循环取数据：e.g. 模拟3用户并发注册账号，总共有90个账号，要求注册账号不重复，注册完毕后结束测试；
- 保证并发测试数据唯一性，循环取数据：模拟3用户并发登录账号，总共有90个账号，要求并发登录账号不相同，但数据可循环使用。

通过以上归纳，可以确信地说，以上三种类型基本上可以覆盖我们日常性能测试工作中的所有参数化场景。

在`LoadRunner`中是有一个集成的参数化模块，可以直接配置参数化策略。那在`Locust`要怎样实现该需求呢？

答案依旧很简单，使用Python的`list`和`queue`数据结构即可！具体做法是，在`WebsiteUser`定义一个数据集，然后所有虚拟用户在`WebsiteTasks`中就可以共享该数据集了。如果不要求数据唯一性，数据集选择`list`数据结构，从头到尾循环遍历即可；如果要求数据唯一性，数据集选择`queue`数据结构，取数据时进行`queue.get()`操作即可，并且这也不会循环取数据；至于涉及到需要循环取数据的情况，那也简单，每次取完数据后再将数据插入到队尾即可，`queue.put_nowait(data)`。

最后再说下检查点。该功能在`LoadRunner`中通常是使用`web_reg_find`这类注册函数进行检查的。在`Locust`脚本中，处理就更方便了，只需要对响应的内容关键字进行`assert xxx in response`操作即可。

针对如上各种脚本增强的场景，我也通过代码示例分别进行了演示。但考虑到文章中插入太多代码会影响到阅读，因此将代码示例部分剥离了出来，如有需要请点击查看[《深入浅出开源性能测试工具Locust（脚本增强）》](/post/head-first-locust-advanced-script/)。

## Locust运行模式

在开始运行`Locust`脚本之前，我们先来看下`Locust`支持的运行模式。

运行`Locust`时，通常会使用到两种运行模式：单进程运行和多进程分布式运行。

单进程运行模式的意思是，`Locust`所有的虚拟并发用户均运行在单个`Python`进程中，具体从使用形式上，又分为`no_web`和`web`两种形式。该种模式由于单进程的原因，并不能完全发挥压力机所有处理器的能力，因此主要用于调试脚本和小并发压测的情况。

当并发压力要求较高时，就需要用到`Locust`的多进程分布式运行模式。从字面意思上看，大家可能第一反应就是多台压力机同时运行，每台压力机分担负载一部分的压力生成。的确，`Locust`支持任意多台压力机（一主多从）的分布式运行模式，但这里说到的多进程分布式运行模式还有另外一种情况，就是在同一台压力机上开启多个`slave`的情况。这是因为当前阶段大多数计算机的CPU都是多处理器（`multiple processor cores`），单进程运行模式下只能用到一个处理器的能力，而通过在一台压力机上运行多个`slave`，就能调用多个处理器的能力了。比较好的做法是，如果一台压力机有`N`个处理器内核，那么就在这台压力机上启动一个`master`，`N`个`slave`。当然，我们也可以启动`N`的倍数个`slave`，但是根据我的试验数据，效果跟`N`个差不多，因此只需要启动`N`个`slave`即可。

## 脚本调试

`Locust`脚本编写完毕后，通常不会那么顺利，在正式开始性能测试之前还需要先调试运行下。

不过，`Locust`脚本虽然为Python脚本，但却很难直接当做Python脚本运行起来，为什么呢？这主要还是因为`Locust`脚本中引用了`HttpLocust`和`TaskSet`这两个类，如果要想直接对其进行调用测试，会发现编写启动脚本是一个比较困难的事情。因为这个原因，刚接触`Locust`的同学可能就会觉得`Locust`脚本不好调试。

但这个问题也能克服，那就是借助`Locust`的单进程`no_web`运行模式。

在`Locust`的单进程`no_web`运行模式中，我们可以通过`--no_web`参数，指定并发数（`-c`）和总执行次数（`-n`），直接在`Terminal`中执行脚本。

在此基础上，当我们想要调试`Locust`脚本时，就可以在脚本中需要调试的地方通过`print`打印日志，然后将并发数和总执行次数都指定为1，执行形式如下所示。

```bash
$ locust -f locustfile.py --no_web -c 1 -n 1
```

通过这种方式，我们就能很方便地对`Locust`脚本进行调试了。

## 执行测试

`Locust`脚本调试通过后，就算是完成了所有准备工作，可以开始进行压力测试了。

`Locust`是通过在`Terminal`中执行命令进行启动的，通用的参数有如下两个：

- `-H, --host`：被测系统的`host`，若在`Terminal`中不进行指定，就需要在`Locust`子类中通过`host`参数进行指定；
- `-f, --locustfile`：指定执行的`Locust`脚本文件；

除了这两个通用的参数，我们还需要根据实际测试场景，选择不同的`Locust`运行模式，而模式的指定也是通过其它参数来进行控制的。

### 单进程运行

**no_web**

如果采用`no_web`形式，则需使用`--no-web`参数，并会用到如下几个参数。

- `-c, --clients`：指定并发用户数；
- `-n, --num-request`：指定总执行测试；
- `-r, --hatch-rate`：指定并发加压速率，默认值位1。

```bash
$ locust -H https://debugtalk.com -f demo.py --no-web -c1 -n2
[2017-02-21 21:27:26,522] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
[2017-02-21 21:27:26,523] Leos-MacBook-Air.local/INFO/locust.runners: Hatching and swarming 1 clients at the rate 1 clients/s...
 Name                                                          # reqs      # fails     Avg     Min     Max  |  Median   req/s
--------------------------------------------------------------------------------------------------------------------------------------
--------------------------------------------------------------------------------------------------------------------------------------
 Total                                                              0     0(0.00%)                                       0.00

[2017-02-21 21:27:27,526] Leos-MacBook-Air.local/INFO/locust.runners: All locusts hatched: WebsiteUser: 1
[2017-02-21 21:27:27,527] Leos-MacBook-Air.local/INFO/locust.runners: Resetting stats

 Name                                                          # reqs      # fails     Avg     Min     Max  |  Median   req/s
--------------------------------------------------------------------------------------------------------------------------------------
 GET /about/                                                        0     0(0.00%)       0       0       0  |       0    0.00
--------------------------------------------------------------------------------------------------------------------------------------
 Total                                                              0     0(0.00%)                                       0.00

 Name                                                          # reqs      # fails     Avg     Min     Max  |  Median   req/s
--------------------------------------------------------------------------------------------------------------------------------------
 GET /about/                                                        1     0(0.00%)      17      17      17  |      17    0.00
--------------------------------------------------------------------------------------------------------------------------------------
 Total                                                              1     0(0.00%)                                       0.00

[2017-02-21 21:27:32,420] Leos-MacBook-Air.local/INFO/locust.runners: All locusts dead

[2017-02-21 21:27:32,421] Leos-MacBook-Air.local/INFO/locust.main: Shutting down (exit code 0), bye.
 Name                                                          # reqs      # fails     Avg     Min     Max  |  Median   req/s
--------------------------------------------------------------------------------------------------------------------------------------
 GET /                                                              1     0(0.00%)      20      20      20  |      20    0.00
 GET /about/                                                        1     0(0.00%)      17      17      17  |      17    0.00
--------------------------------------------------------------------------------------------------------------------------------------
 Total                                                              2     0(0.00%)                                       0.00

Percentage of the requests completed within given times
 Name                                                           # reqs    50%    66%    75%    80%    90%    95%    98%    99%   100%
--------------------------------------------------------------------------------------------------------------------------------------
 GET /                                                               1     20     20     20     20     20     20     20     20     20
 GET /about/                                                         1     17     17     17     17     17     17     17     17     17
--------------------------------------------------------------------------------------------------------------------------------------
```

**web**

如果采用`web`形式，，则通常情况下无需指定其它额外参数，`Locust`默认采用`8089`端口启动`web`；如果要使用其它端口，就可以使用如下参数进行指定。

- `-P, --port`：指定web端口，默认为`8089`.

```bash
$ locust -H https://debugtalk.com -f demo.py
[2017-02-21 21:31:26,334] Leos-MacBook-Air.local/INFO/locust.main: Starting web monitor at *:8089
[2017-02-21 21:31:26,334] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
```

此时，`Locust`并没有开始执行测试，还需要在Web页面中配置参数后进行启动。

如果`Locust`运行在本机，在浏览器中访问`http://localhost:8089`即可进入`Locust`的Web管理页面；如果`Locust`运行在其它机器上，那么在浏览器中访问`http://locust_machine_ip:8089`即可。

在`Locust`的Web管理页面中，需要配置的参数只有两个：

- `Number of users to simulate`: 设置并发用户数，对应中`no_web`模式的`-c, --clients`参数；
- `Hatch rate (users spawned/second)`: 启动虚拟用户的速率，对应着`no_web`模式的`-r, --hatch-rate`参数。

参数配置完毕后，点击【Start swarming】即可开始测试。

### 多进程分布式运行

不管是`单机多进程`，还是`多机负载`模式，运行方式都是一样的，都是先运行一个`master`，再启动多个`slave`。

启动`master`时，需要使用`--master`参数；同样的，如果要使用`8089`以外的端口，还需要使用`-P, --port`参数。

```bash
$ locust -H https://debugtalk.com -f demo.py --master --port=8088
[2017-02-21 22:59:57,308] Leos-MacBook-Air.local/INFO/locust.main: Starting web monitor at *:8088
[2017-02-21 22:59:57,310] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
```

`master`启动后，还需要启动`slave`才能执行测试任务。

启动`slave`时需要使用`--slave`参数；在`slave`中，就不需要再指定端口了。

```bash
$ locust -H https://debugtalk.com -f demo.py --slave
[2017-02-21 23:07:58,696] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
[2017-02-21 23:07:58,696] Leos-MacBook-Air.local/INFO/locust.runners: Client 'Leos-MacBook-Air.local_980ab0eec2bca517d03feb60c31d6a3a' reported as
 ready. Currently 2 clients ready to swarm.
```

如果`slave`与`master`不在同一台机器上，还需要通过`--master-host`参数再指定`master`的IP地址。

```bash
$ locust -H https://debugtalk.com -f demo.py --slave --master-host=<locust_machine_ip>
[2017-02-21 23:07:58,696] Leos-MacBook-Air.local/INFO/locust.main: Starting Locust 0.8a2
[2017-02-21 23:07:58,696] Leos-MacBook-Air.local/INFO/locust.runners: Client 'Leos-MacBook-Air.local_980ab0eec2bca517d03feb60c31d6a3a' reported as
 ready. Currently 2 clients ready to swarm.
```

`master`和`slave`都启动完毕后，就可以在浏览器中通过`http://locust_machine_ip:8089`进入`Locust`的Web管理页面了。使用方式跟单进程`web`形式完全相同，只是此时是通过多进程负载来生成并发压力，在`web`管理界面中也能看到实际的`slave`数量。

## 测试结果展示

`Locust`在执行测试的过程中，我们可以在`web`界面中实时地看到结果运行情况。

相比于`LoadRunner`，`Locust`的结果展示十分简单，主要就四个指标：`并发数`、`RPS`、`响应时间`、`异常率`。但对于大多数场景来说，这几个指标已经足够了。

![](/images/14877299635610.jpg)

在上图中，`RPS`和`平均响应时间`这两个指标显示的值都是根据最近2秒请求响应数据计算得到的统计值，我们也可以理解为瞬时值。

如果想看性能指标数据的走势，就可以在`Charts`栏查看。在这里，可以查看到`RPS`和`平均响应时间`在整个运行过程中的波动情况。这个功能之前在`Locust`中一直是缺失的，直到最近，这个坑才被我之前在`阿里移动`的同事（网络ID[`myzhan`](http://myzhan.github.io/)）给填上了。当前该功能已经合并到`Locust`了，更新到最新版即可使用。

![](/images/14877300553617.jpg)

除了以上数据，`Locust`还提供了整个运行过程数据的百分比统计值，例如我们常用的`90%响应时间`、`响应时间中位值`，该数据可以通过`Download response time distribution CSV`获得，数据展示效果如下所示。

![](/images/14877305222231.jpg)

## 总结

通过前面对`Locust`全方位的讲解，相信大家对`Locust`的功能特性已经非常熟悉了，在实际项目中将`Locust`作为生产力工具应该也没啥问题了。

不过，任何一款工具都不是完美的，必定都会存在一些不足之处。但是好在`Locust`具有极强的可定制型，当我们遇到一些特有的需求时，可以在`Locust`上很方便地实现扩展。

还是前面提到的那位技术大牛（`myzhan`），他为了摆脱`CPython`的`GIL`和`gevent`的 `monkey_patch()`，将`Locust`的`slave`端采用`golang`进行了重写，采用`goroutine`取代了`gevent`。经过测试，相较于原生的`Python`实现，他的这套`golang`实现具有`5~10`倍以上的性能提升。当前，他已经将该实现开源，项目名称为[`myzhan/boomer`](https://github.com/myzhan/boomer)，如果大家感兴趣，可以阅读他的博客文章进一步了解，[《用 golang 来编写压测工具》](http://myzhan.github.io/2016/03/01/write-a-load-testing-tool-in-golang/)。

如果我们也想在`Locust`的基础上进行二次开发，那要怎么开始呢？

毫无疑问，阅读`Locust`的项目源码是必不可少的第一步。可能对于很多人来说，阅读开源项目源码是一件十分困难的事情，不知道如何着手，在知乎上也看到好多关于如何阅读开源项目源码的提问。事实上，`Locust`项目的代码结构清晰，核心代码量也比较少，十分适合阅读学习。哪怕只是想体验下阅读开源项目源码，或者说想提升下自己的`Python`技能，`Locust`也是个不错的选择。

在下一篇文章中，我将对`Locust`源码进行解析，《深入浅出开源性能测试工具Locust（源码篇）》，敬请期待！
