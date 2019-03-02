---
title: 300 行 Python 代码打造实用接口测试框架
permalink: post/300-lines-python-code-api-test-framework
date: 2017/06/28
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在刚开始实现[`ApiTestEngine`][ApiTestEngine]的时候，[`卡斯（kasi）`][kasi]提议做一个Java版的。对于这样的建议，我当然是拒绝的，瞬即回复了他，“人生苦短，回头是岸啊”。

当然，我没好意思跟他说的是，我不会Java啊。不过最主要的原因嘛，还是因为Python的语法简洁，可以采用很少的代码量实现丰富的功能。

有多简洁呢？

刚在`coveralls`上看了下[`ApiTestEngine`][ApiTestEngine]框架的[代码统计行数][ApiTestEngine-coveralls]，总行数只有268行，还不足300行。

![](/images/ApiTestEngine-stat-ate.jpg)

当然，这个行数指的是框架本身的`Python`代码行数，不包括示例注释的行数。从上图可以看出来，`LINES`列是文件总行数，`RELEVANT`列是实际的`Python`代码行数。例如`ate/runner.py`文件，注释的行数是远多于实际代码行数的。

最极端的一个例子是，`ate/testcase.py`文件中的[`parse`函数][testcase-parse]，示例注释行数35行，`Python`代码只有2行。

```python
def parse(self, testcase_template):
   """ parse testcase_template, replace all variables with bind value.
   variables marker: ${variable}.
   @param (dict) testcase_template
       {
           "request": {
               "url": "http://127.0.0.1:5000/api/users/${uid}",
               "method": "POST",
               "headers": {
                   "Content-Type": "application/json",
                   "authorization": "${authorization}",
                   "random": "${random}"
               },
               "body": "${data}"
           },
           "response": {
               "status_code": "${expected_status}"
           }
       }
   @return (dict) parsed testcase with bind values
       {
           "request": {
               "url": "http://127.0.0.1:5000/api/users/1000",
               "method": "POST",
               "headers": {
                   "Content-Type": "application/json",
                   "authorization": "a83de0ff8d2e896dbd8efb81ba14e17d",
                   "random": "A2dEx"
               },
               "body": '{"name": "user", "password": "123456"}'
           },
           "response": {
               "status_code": 201
           }
       }
   """
   return self.substitute(testcase_template)
```

另外，如果算上单元测试用例的行数（731行），总的`Python`代码行数能达到1000行的样子。嗯，代码可以精简，但是单元测试覆盖率还是要保证的，不达到90%以上的单元测试覆盖率，真不好意思说自己做了开源项目啊。

![](/images/ApiTestEngine-stat-all.jpg)

那这不足300行的Python代码，实际实现了哪些功能呢？

对比下[《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]中规划的特性，已经实现了大半（前六项），至少已经算是一个有模有样的接口测试框架了。

- 支持API接口的多种请求方法，包括 GET/POST/HEAD/PUT/DELETE 等
- 测试用例与代码分离，测试用例维护方式简洁优雅，支持`YAML/JSON`
- 测试用例描述方式具有表现力，可采用简洁的方式描述输入参数和预期输出结果
- 接口测试用例具有可复用性，便于创建复杂测试场景
- 测试执行方式简单灵活，支持单接口调用测试、批量接口调用测试、定时任务执行测试
- 具有可扩展性，便于扩展实现Web平台化
- 测试结果统计报告简洁清晰，附带详尽日志记录，包括接口请求耗时、请求响应数据等
- 身兼多职，同时实现接口管理、接口自动化测试、接口性能测试（结合Locust）

后面剩下的特性还在实现的过程中，但是可以预见得到，最后框架本身总的`Python`代码行数也不会超过500行。

当然，单纯地比代码行数的确是没有什么意义，写得爽写得开心才是最重要的。

最后引用下`Guido van Rossum`的语录：

> Life is short, go Pythonic!

## 阅读更多

- [《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]
- [《ApiTestEngine 演化之路（0）开发未动，测试先行》][ApiTestEngine-dev-0]
- [《ApiTestEngine 演进之路（1）搭建基础框架》][ApiTestEngine-dev-1]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]

## 最后的最后

[《ApiTestEngine 演进之路》][ApiTestEngine-series]系列文章还在继续写，只是前几天主要精力在编码实现上，博客方面没有同步更新，接下来我会整理好思路，继续完成余下的部分。

另外，如果大家对Python编程感兴趣，给大家推荐一个专注Python原创技术分享的公众号，⎡Python之禅⎦（VTtalk），里面关于Python的干货非常多，讲解也很通俗易懂，现在我如果有理解得不够透彻的概念，基本都会先到这个公众号里面去搜索下。


[kasi]: https://testerhome.com/kasi
[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[testcase-parse]: https://github.com/debugtalk/ApiTestEngine/blob/master/ate/testcase.py
[ApiTestEngine-Intro]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[ApiTestEngine-dev-0]: https://debugtalk.com/post/ApiTestEngine-0-setup-CI-test/
[ApiTestEngine-dev-1]: https://debugtalk.com/post/ApiTestEngine-1-setup-basic-framework/
[ApiTestEngine-coveralls]: https://coveralls.io/github/debugtalk/ApiTestEngine?branch=master
[ApiTestEngine-series]: https://debugtalk.com/tags/ApiTestEngine
