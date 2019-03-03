---
title: HttpRunner 通过 skip 机制实现对测试用例的分组执行控制
permalink: post/HttpRunner-skip-feature
date: 2018/02/08
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

## 背景介绍

近期，某位同学对`HttpRunner`提了一个[需求点][1]：

> 能否支持类似unittest中的skip注解，方便灵活剔除某些用例，不执行。
> 目前在接口测试日常构建中，会遇到一些接口开发暂时屏蔽了或者降级，导致用例执行失败；所以想当遇到这些情况的时候，能够临时剔除掉某些用例不执行；等后续恢复后，再去掉，然后恢复执行。

针对这种情况，`HttpRunner`的确没有直接支持。之所以说是没有`直接`支持，是因为在`HttpRunner`中存在`times`关键字，可以指定某个`test`的运行次数。

例如，如下`test`中指定了`times`为3，那么该`test`就会运行3次。

```yaml
- test:
    name: demo
    times: 3
    request: {...}
    validate: [...]
```

假如要实现临时屏蔽掉某些`test`，那么就可以将对应`test`的`times`设置为0。

这虽然也能勉强实现需求，但是这跟直接将临时不运行的`test`注释掉没什么区别，都需要对测试用例内容进行改动，使用上很是不方便。

考虑到该需求的普遍性，`HttpRunner`的确应该增加对该种情况的支持。

在这方面，`unittest`已经有了清晰的定义，有三种常用的装饰器可以控制单元测试用例是否被执行：

- @unittest.skip(reason)：无条件跳过当前测试用例
- @unittest.skipIf(condition, reason)：当条件表达式的值为true时跳过当前测试用例
- @unittest.skipUnless(condition, reason)：当条件表达式的值为false时跳过当前测试用例

该功能完全满足我们的需求，因此，我们可以直接复用其概念，尝试实现同样的功能。

## 实现方式

目标明确了，那需要怎么实现呢？

首先，我们先看下`unittest`中这三个函数是怎么实现的；这三个函数定义在`unittest/case.py`中。

```python
class SkipTest(Exception):
    """
    Raise this exception in a test to skip it.

    Usually you can use TestCase.skipTest() or one of the skipping decorators
    instead of raising this directly.
    """
    pass

def skip(reason):
    """
    Unconditionally skip a test.
    """
    def decorator(test_item):
        if not isinstance(test_item, (type, types.ClassType)):
            @functools.wraps(test_item)
            def skip_wrapper(*args, **kwargs):
                raise SkipTest(reason)
            test_item = skip_wrapper

        test_item.__unittest_skip__ = True
        test_item.__unittest_skip_why__ = reason
        return test_item
    return decorator

def skipIf(condition, reason):
    """
    Skip a test if the condition is true.
    """
    if condition:
        return skip(reason)
    return _id

def skipUnless(condition, reason):
    """
    Skip a test unless the condition is true.
    """
    if not condition:
        return skip(reason)
    return _id
```

不难看出，核心有两点：

- 对于`skip`，只需要在该测试用例中`raise SkipTest(reason)`，而`SkipTest`是`unittest/case.py`中定义的一个异常类；
- 对于`skipIf`和`skipUnless`，相比于`skip`，主要是需要指定一个条件表达式（condition），然后根据该表达式的实际值来决定是否`skip`当前测试用例。

明确了这两点之后，我们要如何在`HttpRunner`中实现同样的功能，思路应该就比较清晰了。

因为`HttpRunner`同样也是采用`unittest`来组织和驱动测试用例执行的，而具体的执行控制部分都是在`httprunner/runner.py`的`_run_test`方法中；同时，在`_run_test`方法中会传入`testcase_dict`，也就是具体测试用例的全部信息。

那么，最简单的做法，就是在`YAML/JSON`测试用例中，新增`skip/skipIf/skipUnless`参数，然后在`_run_test`方法中根据参数内容来决定是否执行`raise SkipTest(reason)`。

例如，在`YAML`测试用例中，我们可以按照如下形式新增`skip`字段，其中对应的值部分就是我们需要的`reason`。

```yaml
- test:
    name: demo
    skip: "skip this test unconditionally"
    request: {...}
    validate: [...]
```

接下来在`_run_test`方法，要处理就十分简单，只需要判断`testcase_dict`中是否包含`skip`字段，假如包含，则执行`raise SkipTest(reason)`即可。

```python
def _run_test(self, testcase_dict):
    ...

    if "skip" in testcase_dict:
        skip_reason = testcase_dict["skip"]
        raise SkipTest(skip_reason)

    ...
```

这对于`skip`机制来做，完全满足需求；但对于`skipIf/skipUnless`，可能就会麻烦些，因为我们的用例是在`YAML/JSON`文本格式的文件中，没法像在`unittest`中执行`condition`那样的Python表达式。

嗯？谁说在`YAML/JSON`中就不能执行函数表达式的？在`HttpRunner`中，我们已经实现了该功能，即：

- 在`debugtalk.py`中定义函数，例如`func(a, b)`
- 在`YAML/JSON`中通过`${func(a,b)}`对函数进行调用

在此基础上，我们要实现`skipIf/skipUnless`就很简单了；很自然地，我们可以想到采用如下形式来进行描述。

```yaml
- test:
    name: create user which existed (skip if condition)
    skipIf: ${skip_test_in_production_env()}
    request: {...}
    validate: [...]
```

其中，`skip_test_in_production_env`定义在`debugtalk.py`文件中。

```python
def skip_test_in_production_env():
    """ skip this test in production environment
    """
    return os.environ["TEST_ENV"] == "PRODUCTION"
```

然后，在`_run_test`方法中，我们只需要判断`testcase_dict`中是否包含`skipIf`字段，假如包含，则将其对应的函数表达式取出，运行得到其结果，最后再根据运算结果来判断是否执行`raise SkipTest(reason)`。对函数表达式进行解析的方法在`httprunner/context.py`的`exec_content_functions`函数中，具体实现方式可阅读之前的文章。

```python
def _run_test(self, testcase_dict):
    ...

    if "skip" in testcase_dict:
        skip_reason = testcase_dict["skip"]
        raise SkipTest(skip_reason)
    elif "skipIf" in testcase_dict:
        skip_if_condition = testcase_dict["skipIf"]
        if self.context.exec_content_functions(skip_if_condition):
            skip_reason = "{} evaluate to True".format(skip_if_condition)
            raise SkipTest(skip_reason)

    ...
```

`skipUnless`与`skipIf`类似，不再重复。

通过该种方式，我们就可以实现在不对测试用例文件做任何修改的情况下，通过外部方式（例如设定环境变量的值）就可以控制是否执行某些测试用例。

## 效果展示

`skip/skipIf/skipUnless`机制实现后，我们对测试用例的执行控制就更加灵活方便了。

例如，我们可以很容易地实现如下常见的测试场景：

- 对测试用例进行分组，P0/P1/P2等，然后根据实际需求选择执行哪些用例
- 通过环境变量来控制是否执行某些用例

更重要的是，我们无需对测试用例文件进行任何修改。

在`HttpRunner`项目中存在一个示例文件，[`httprunner/tests/data/demo_testset_cli.yml`][2]，大家可以此作为参考。

在运行该测试集后，生成的测试报告如下所示。

![](/images/httprunner-skip.jpg)



[1]: https://github.com/HttpRunner/HttpRunner/issues/96
[2]: https://github.com/HttpRunner/HttpRunner/blob/master/tests/data/demo_testset_cli.yml
