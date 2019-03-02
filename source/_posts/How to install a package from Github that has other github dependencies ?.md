---
title: How to install a package from Github that has other github dependencies ?
permalink: post/How-to-install-a-package-from-Github-that-has-other-github-dependencies
date: 2017/08/05
categories:
  - Development
tags:
  - Python
  - pip
  - Github
---

最近在开发`ApiTestEngine`时遇到一个安装包依赖的问题，耗费了不少时间寻找解决方案，考虑到还算比较有普遍性，因此总结形成这篇文章。

## 从 pip install 说起

先不那么简单地描述下背景。

[`ApiTestEngine`][ApiTestEngine]作为一款接口测试工具，需要具有灵活的命令行调用方式，因此最好能在系统中进行安装并注册为一个`CLI`命令。

在Python中，安装依赖库的最佳方式是采用[`pip`][pip]，例如安装[`Locust`][locust]时，就可以采用如下命令搞定。

```text
$ pip install locustio
Collecting locustio
  Using cached locustio-0.7.5.tar.gz
[...]
Successfully installed locustio-0.7.5
```

但要想采用`pip install SomePackage`的方式，前提是`SomePackage`已经托管在`PyPI`。关于`PyPI`，可以理解为`Python`语言的第三方库的仓库索引，当前绝大多数流行的`Python`第三方库都托管在`PyPI`上。

但是，这里存在一个问题。在`PyPI`当中，所有的包都是由其作者自行上传的。如果作者比较懒，那么可能托管在`PyPI`上的最新版本相较于最新代码就会比较滞后。

`Locust`就是一个典型的例子。从上面的安装过程可以看出，我们采用`pip install locustio`安装的`Locust`版本是`v0.7.5`，而在`Locust`的`Github`仓库中，`v0.7.5`已经是一年之前的版本了。也是因为这个原因，之前在我的博客里面介绍`Locust`的[图表展示功能][locust-user-guide]后，已经有不下5个人向我咨询为啥他们看不到这个图表模块。这是因为`Locust`的图表模块是在今年（2017）年初时添加的功能，master分支的代码版本也已经升级到`v0.8a2`了，但`PyPI`上的版本却一直没有更新。

而要想使用到项目最新的功能，就只能采用源码进行安装。

大多数编程语言在使用源码进行安装时，都需要先将源码下载到本地，然后通过命令进行编译，例如`Linux`中常见的`make && make install`。对于`Python`项目来说，也可以采用类似的模式，先将项目`clone`到本地，然后进入到项目的根目录，执行`python setup.py install`。

```text
$ git clone https://github.com/locustio/locust.git
$ cd locust
$ python setup.py install
[...]
Finished processing dependencies for locustio==0.8a2
```

不过，要想采用这种方式进行安装也是有前提的，那就是项目必须已经实现了基于`setuptools`的安装方式，并在项目的根目录下存在`setup.py`。

可以看出，这种安装方式还是比较繁琐的，需要好几步才能完成安装。而且，对于大多数使用者来说，他们并不需要阅读项目源码，因此`clone`操作也实属多余。

可喜的是，`pip`不仅支持安装`PyPI`上的包，也可以直接通过项目的`git`地址进行安装。还是以`Locust`项目为例，我们通过`pip`命令也可以实现一条命令安装`Github`项目源码。

```text
$ pip install git+https://github.com/locustio/locust.git@master#egg=locustio
Collecting locustio from git+https://github.com/locustio/locust.git@master#egg=locustio
[...]
Successfully installed locustio-0.8a2
```

对于项目地址来说，完整的描述应该是：

```text
pip install vcs+protocol://repo_url/#egg=pkg&subdirectory=pkg_dir
```

这里的`vcs`也不仅限于`git`，`svn`和`hg`也是一样的，而`protocol`除了采用`SSH`形式的项目地址，也可以采用`HTTPS`的地址，在此不再展开。

通过这种方式，我们就总是可以使用到项目的最新功能特性了。当然，前提条件也是一样的，需要项目中已经实现了`setup.py`。

考虑到`ApiTestEngine`还处于频繁的新特性开发阶段，因此这种途径无疑是让用户安装使用最新代码的最佳方式。

## 问题缘由

在[`ApiTestEngine`][ApiTestEngine]中，存在测试结果报告展示这一部分的功能，而这部分的功能是需要依赖于另外一个托管在GitHub上的项目，[`PyUnitReport`][PyUnitReport]。

于是，问题就变为：如何构造`ApiTestEngine`项目的`setup.py`，可以实现用户在安装`ApiTestEngine`时自动安装`PyUnitReport`依赖。

对于这个需求，已经确定可行的办法：先通过`pip`安装依赖的库（`PyUnitReport`），然后再安装当前项目（`ApiTestEngine`）。

```text
$ pip install git+https://github.com/debugtalk/PyUnitReport.git#egg=PyUnitReport
$ pip install git+https://github.com/debugtalk/ApiTestEngine.git#egg=ApiTestEngine
```

这种方式虽然可行，但是需要执行两条命令，显然不是我们想要的效果。

经过搜索，发现针对该需求，可以在`setuptools.setup()`中通过`install_requires`和`dependency_links`这两个配置项组合实现。

具体地，配置方式如下：

```text
install_requires=[
   "requests",
   "flask",
   "PyYAML",
   "coveralls",
   "coverage",
   "PyUnitReport"
],
dependency_links=[
   "git+https://github.com/debugtalk/PyUnitReport.git#egg=PyUnitReport"
],
```

这里有一点需要格外注意，那就是指定的依赖包如果存在于`PyPI`，那么只需要在`install_requires`中指定包名和版本号即可（不指定版本号时，默认安装最新版本）；而对于以仓库URL地址存在的依赖包，那么不仅需要在`dependency_links`中指定，同时也要在`install_requires`中指定。

然后，就可以直接通过`ApiTestEngine`项目的git地址一键进行安装了。

```text
$ pip install git+https://github.com/debugtalk/ApiTestEngine.git#egg=ApiTestEngine
```

虽然在寻找解决办法的过程中，看到大家都在说`dependency_links`由于安全性的问题，即将被弃用，而且在`setuptools`的官方文章中的确也没有看到`dependency_links`的描述。

```text
DEPRECATION: Dependency Links processing has been deprecated and will be removed in a future release.
```

不过在我本地的`macOS`系统上尝试发现，该种方式的确是可行的，因此就采用这种方式进行发布了。

但是当我后续在`Linux`服务器上安装时，却无法成功，总是在安装`PyUnitReport`依赖库的时候报错：

```text
$ pip install git+https://github.com/debugtalk/ApiTestEngine.git#egg=ApiTestEngine
[...]
Collecting PyUnitReport (from ApiTestEngine)
  Could not find a version that satisfies the requirement PyUnitReport (from ApiTestEngine) (from versions: )
No matching distribution found for PyUnitReport (from ApiTestEngine)
```

另外，同时也有多个用户反馈了同样的问题，这才发现这种方式在`Linux`和`Windows`下是不行的。

然后，再次经过大量的搜索，却始终没有特别明确的答案，搞得我也在怀疑，`dependency_links`到底是不是真的已经弃用了，但是就算是弃用了，也应该有新的替代方案啊，但也并没有找到。

这个问题就这么放了差不多一个星期的样子。

## 解决方案

今天周末在家，想来想去，不解决始终不爽，虽然只是多执行一条命令的问题。

于是又是经过大量搜索，幸运的是终于从`pypa/pip`的`issues`中找到一条[`issue`][pip-3610]，作者是[`Dominik Neise`][dneise]，他详细描述了他遇到的问题和尝试过的方法，看到他的描述我真是惊呆了，跟我的情况完全一模一样不说，连尝试的思路也完全一致。

然后，在下面的回复中，看到了[`Gary Wu`][garywu]和[`kbuilds`][kbuilds]的解答，总算是找到了问题的原因和解决方案。

问题在于，在`dependency_links`中指定仓库URL地址的时候，在指定`egg`信息时，`pip`还同时需要一个版本号（`version number`），并且以短横线`-`分隔，然后执行的时候再加上`--process-dependency-links`参数。

回到之前的`dependency_links`，我们应该写成如下形式。

```text
dependency_links=[
   "git+https://github.com/debugtalk/PyUnitReport.git#egg=PyUnitReport-0"
]
```

在这里，短横线`-`后面我并没有填写`PyUnitReport`实际的版本号，因为经过尝试发现，这里填写任意数值都是成功的，因此我就填写为`0`了，省得后续在升级`PyUnitReport`以后还要来修改这个地方。

然后，就可以通过如下命令进行安装了。

```text
$ pip install --process-dependency-links git+https://github.com/debugtalk/ApiTestEngine.git#egg=ApiTestEngine
```

至此，问题总算解决了。

## 后记

那么，`dependency_links`到底是不是要废弃了呢？

从`pip`的`GitHub`项目中看到这么一个[`issue`][pip-4187]，`--process-dependency-links`之前废弃了一段时间，但是又给加回来了，因为当前还没有更好的可替代的方案。因此，在出现替代方案之前，`dependency_links`应该是最好的方式了吧。

最后再感叹下，老外提问时描述问题的专业性和细致程度真是令人佩服，大家可以再仔细看下这个[`issue`][dneise]好好感受下。

## 阅读更多

- http://setuptools.readthedocs.io/en/latest/setuptools.html#dependencies-that-aren-t-in-pypi
- https://pip.pypa.io/en/stable/reference/pip_install/
- https://github.com/pypa/pip/issues/3610
- https://github.com/pypa/pip/issues/4187

[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[pip]: https://pip.pypa.io/en/stable/
[locust]: http://locust.io/
[locust-github]: https://github.com/locustio/locust
[locust-user-guide]: https://debugtalk.com/post/head-first-locust-user-guide/
[PyUnitReport]: https://github.com/debugtalk/PyUnitReport
[pip-3610]: https://github.com/pypa/pip/issues/3610
[dneise]: https://github.com/pypa/pip/issues/3610#issue-147115114
[garywu]: https://github.com/pypa/pip/issues/3610#issuecomment-283578756
[kbuilds]: https://github.com/pypa/pip/issues/3610#issuecomment-317281367
[pip-4187]: https://github.com/pypa/pip/issues/4187
