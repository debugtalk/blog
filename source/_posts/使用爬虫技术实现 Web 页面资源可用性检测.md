---
title: 使用爬虫技术实现 Web 页面资源可用性检测
permalink: post/requests-crawler
date: 2018/05/28
categories:
  - Testing
  - 自动化测试
tags:
  - requests-crawler
  - requests-html
---

## 背景

对于电商类型和内容服务类型的网站，经常会出现因为配置错误造成页面链接无法访问的情况（404）。

显然，要确保网站中的所有链接都具有可访问性，通过人工进行检测肯定是不现实的，常用的做法是使用爬虫技术定期对网站进行资源爬取，及时发现访问异常的链接。

对于网络爬虫，当前市面上已经存在大量的开源项目和技术讨论的文章。不过，感觉大家普遍都将焦点集中在爬取效率方面，例如当前就存在大量讨论不同并发机制哪个效率更高的文章，而在爬虫的其它特性方面探讨的不多。

个人认为，爬虫的核心特性除了`快`，还应该包括`全`和`稳`，并且从重要性的排序来看，`全`、`稳`、`快`应该是从高到低的。

`全`排在第一位，是因为这是爬虫的基本功能，若爬取的页面不全，就会出现信息遗漏的情况，这种情况肯定是不允许的；而`稳`排在第二位，是因为爬虫通常都是需要长期稳定运行的，若因为策略处理不当造成爬虫运行过程中偶尔无法正常访问页面，肯定也是无法接受的；最后才是`快`，我们通常需要爬取的页面链接会非常多，因此效率就很关键，但这也必须建立在`全`和`稳`的基础上。

当然，爬虫本身是一个很深的技术领域，我接触的也只是皮毛。本文只针对使用爬虫技术实现 Web 页面资源可用性检测的实际场景，详细剖析下其中涉及到的几个技术点，重点解决如下几个问题：

- 全：如何才能爬取网站所有的页面链接？特别是当前许多网站的页面内容都是要靠前端渲染生成的，爬虫要如何支持这种情况？
- 稳：很多网站都有访问频率限制，若爬虫策略处理不当，就常出现 403 和 503 的问题，该种问题要怎么解决？
- 快：如何在保障爬虫功能正常的前提下，尽可能地提升爬虫效率？

## 爬虫实现前端页面渲染

在早些年，基本上绝大多数网站都是通过后端渲染的，即在服务器端组装形成完整的 HTML 页面，然后再将完整页面返回给前端进行展现。而近年来，随着 AJAX 技术的不断普及，以及 AngularJS 这类 SPA 框架的广泛应用，前端渲染的页面越来越多。

不知大家有没有听说过，前端渲染相比于后端渲染，是不利于进行 SEO 的，因为对爬虫不友好。究其原因，就是因为前端渲染的页面是需要在浏览器端执行 JavaScript 代码（即 AJAX 请求）才能获取后端数据，然后才能拼装成完整的 HTML 页面。

针对这类情况，当前也已经有很多解决方案，最常用的就是借助 PhantomJS、[puppeteer] 这类 Headless 浏览器工具，相当于在爬虫中内置一个浏览器内核，对抓取的页面先渲染（执行 Javascript 脚本），然后再对页面内容进行抓取。

不过，要使用这类技术，通常都是需要使用 Javascript 来开发爬虫工具，对于我这种写惯了 Python 的人来说的确有些痛苦。

直到某一天，[kennethreitz] 大神发布了开源项目 [requests-html]，看到项目介绍中的那句 `Full JavaScript support!` 时不禁热泪盈眶，就是它了！该项目在 GitHub 上发布后不到三天，star 数就达到 5000 以上，足见其影响力。

[requests-html] 为啥会这么火？

写过 Python 的人，基本上都会使用 [requests] 这么一个 HTTP 库，说它是最好的 HTTP 库一点也不夸张（不限编程语言），对于其介绍语 `HTTP Requests for Humans` 也当之无愧。也是因为这个原因，[Locust] 和 [HttpRunner] 都是基于 [requests] 来进行开发的。

而 [requests-html]，则是 [kennethreitz] 在 [requests] 的基础上开发的另一个开源项目，除了可以复用 [requests] 的全部功能外，还实现了对 HTML 页面的解析，即支持对 Javascript 的执行，以及通过 CSS 和 XPath 对 HTML 页面元素进行提取的功能，这些都是编写爬虫工具非常需要的功能。

在实现 Javascript 执行方面，[requests-html] 也并没有自己造轮子，而是借助了 [pyppeteer] 这个开源项目。还记得前面提到的 [puppeteer] 项目么，这是 GoogleChrome 官方实现的 `Node API`；而 [pyppeteer] 这个项目，则相当于是使用 Python 语言对 puppeteer 的非官方实现，基本具有 [puppeteer] 的所有功能。

理清了以上关系后，相信大家对 [requests-html] 也就有了更好的理解。

在使用方面，[requests-html] 也十分简单，用法与 [requests] 基本相同，只是多了 `render` 功能。

```python
from requests_html import HTMLSession

session = HTMLSession()
r = session.get('http://python-requests.org')
r.html.render()
```

在执行 `render()` 之后，返回的就是经过渲染后的页面内容。

## 爬虫实现访问频率控制

为了防止流量攻击，很多网站都有访问频率限制，即限制单个 IP 在一定时间段内的访问次数。若超过这个设定的限制，服务器端就会拒绝访问请求，即响应状态码为 403（Forbidden）。

这用来应对外部的流量攻击或者爬虫是可以的，但在这个限定策略下，公司内部的爬虫测试工具同样也无法正常使用了。针对这个问题，常用的做法就是在应用系统中开设白名单，将公司内部的爬虫测试服务器 IP 加到白名单中，然后针对白名单中的 IP 不做限制，或者提升限额。但这同样可能会出现问题。因为应用服务器的性能不是无限的，假如爬虫的访问频率超过了应用服务器的处理极限，那么就会造成应用服务器不可用的情况，即响应状态码为 503（Service Unavailable Error）。

基于以上原因，爬虫的访问频率应该是要与项目组的开发和运维进行统一评估后确定的；而对于爬虫工具而言，实现对访问频率的控制也就很有必要了。

那要怎样实现访问频率的控制呢？

我们可以先回到爬虫本身的实现机制。对于爬虫来说，不管采用什么实现形式，应该都可以概括为生产者和消费者模型，即：

- 消费者：爬取新的页面
- 生产者：对爬取的页面进行解析，得到需要爬取的页面链接

对于这种模型，最简单的做法是使用一个 FIFO 的队列，用于存储未爬取的链接队列（unvisited_urls_queue）。不管是采用何种并发机制，这个队列都可以在各个 worker 中共享。对于每一个 worker 来说，都可以按照如下做法：

- 从 unvisited_urls_queue 队首中取出一个链接进行访问；
- 解析出页面中的链接，遍历所有的链接，找出未访问过的链接；
- 将未访问过的链接加入到 unvisited_urls_queue 队尾
- 直到 unvisited_urls_queue 为空时终止任务

然后回到我们的问题，要限制访问频率，即单位时间内请求的链接数目。显然，worker 之间相互独立，要在执行端层面协同实现整体的频率控制并不容易。但从上面的步骤中可以看出，unvisited_urls_queue 被所有 worker 共享，并且作为源头供给的角色。那么只要我们可以实现对 unvisited_urls_queue 补充的数量控制，就实现了爬虫整体的访问频率控制。

以上思路是正确的，但在具体实现的时候会存在几个问题：

- 需要一个用于存储已经访问链接的集合（visited_urls_set），该集合需要在各个 worker 中实现共享；
- 需要一个全局的计数器，统计到达设定时间间隔（rps即1秒，rpm即1分钟）时已访问的总链接数；

并且在当前的实际场景中，最佳的并发机制是选择多进程（下文会详细说明原因），每个 worker 在不同的进程中，那要实现对集合的共享就不大容易了。同时，如果每个 worker 都要负责对总请求数进行判断，即将访问频率的控制逻辑放到 worker 中实现，那对于 worker 来说会是一个负担，逻辑上也会比较复杂。

因此比较好的方式是，除了未访问链接队列（unvisited_urls_queue），另外再新增一个爬取结果的存储队列（fetched_urls_queue），这两个队列都在各个 worker 中共享。那么，接下来逻辑就变得简单了：

- 在各个 worker 中，只需要从 unvisited_urls_queue 中取数据，解析出结果后统统存储到 fetched_urls_queue，无需关注访问频率的问题；
- 在主进程中，不断地从 fetched_urls_queue 取数据，将未访问过的链接添加到 unvisited_urls_queue，在添加之前进行访问频率控制。

具体的控制方法也很简单，假设我们是要实现 RPS 的控制，那么就可以使用如下方式（只截取关键片段）：

```python
start_timer = time.time()
requests_queued = 0

while True:
    try:
        url = self.fetched_urls_queue.get(timeout=5)
    except queue.Empty:
        break

    # visited url will not be crawled twice
    if url in self.visited_urls_set:
        continue

    # limit rps or rpm
    if requests_queued >= self.requests_limit:
        runtime_secs = time.time() - start_timer
        if runtime_secs < self.interval_limit:
            sleep_secs = self.interval_limit - runtime_secs
            # exceed rps limit, sleep
            time.sleep(sleep_secs)

        start_timer = time.time()
        requests_queued = 0

    self.unvisited_urls_queue.put(url)
    self.visited_urls_set.add(url)
    requests_queued += 1
```

## 提升爬虫效率

对于提升爬虫效率这部分，当前已经有大量的讨论了，重点都是集中在不同的并发机制上面，包括多进程、多线程、asyncio等。

不过，他们的并发测试结果对于本文中讨论的爬虫场景并不适用。因为在本文的爬虫场景中，实现前端页面渲染是最核心的一项功能特性，而要实现前端页面渲染，底层都是需要使用浏览器内核的，相当于每个 worker 在运行时都会跑一个 Chromium 实例。

众所周知，Chromium 对于 CPU 和内存的开销都是比较大的，因此为了避免机器资源出现瓶颈，使用多进程机制（multiprocessing）充分调用多处理器的硬件资源无疑是最佳的选择。

另一个需要注意也是比较被大家忽略的点，就是在页面链接的请求方法上。

请求页面链接，不都是使用 GET 方法么？

的确，使用 GET 请求肯定是可行的，但问题在于，GET 请求时会加载页面中的所有资源信息，这本身会是比较耗时的，特别是遇到链接为比较大的图片或者附件的时候。这无疑会耗费很多无谓的时间，毕竟我们的目的只是为了检测链接资源是否可访问而已。

比较好的的做法是对网站的链接进行分类：

- 资源型链接，包括图片、CSS、JS、文件、视频、附件等，这类链接只需检测可访问性；
- 外站链接，这类链接只需检测该链接本身的可访问性，无需进一步检测该链接加载后页面中包含的链接；
- 本站页面链接，这类链接除了需要检测该链接本身的可访问性，还需要进一步检测该链接加载后页面中包含的链接的可访问性；

在如上分类中，除了第三类是必须要使用 GET 方法获取页面并加载完整内容（render），前两类完全可以使用 HEAD 方法进行代替。一方面，HEAD 方法只会获取状态码和 headers 而不获取 body，比 GET 方法高效很多；另一方面，前两类链接也无需进行页面渲染，省去了调用 Chromium 进行解析的步骤，执行效率的提高也会非常明显。

## 总结

本文针对如何使用爬虫技术实现 Web 页面资源可用性检测进行了讲解，重点围绕爬虫如何实现 `全`、`稳`、`快` 三个核心特性进行了展开。对于爬虫技术的更多内容，后续有机会我们再进一步进行探讨。



[kennethreitz]: https://github.com/kennethreitz
[requests]: https://github.com/requests/requests
[requests-html]: https://github.com/kennethreitz/requests-html
[pyppeteer]: https://github.com/miyakogi/pyppeteer
[puppeteer]: https://github.com/GoogleChrome/puppeteer
[Locust]: https://github.com/locustio/locust
[HttpRunner]: https://github.com/HttpRunner/HttpRunner
