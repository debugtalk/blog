---
title: 约定大于配置：ApiTestEngine实现热加载机制
permalink: post/apitestengine-hot-plugin
date: 2017/09/09
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

## 背景描述

在[`ApiTestEngine`][ApiTestEngine]中编写测试用例时，我们有时需要定义全局的变量，或者引用外部函数实现一些动态的计算逻辑。当前采用的方式是：

- 若需定义全局的参数变量，则要在`YAML/JSON`的`config`中，使用`variables`定义变量；
- 若需引用外部函数，则要在`YAML/JSON`的`config`中，使用`import_module_items`导入指定的`Python`模块。

虽然这种方式提供了极大的灵活性，但是对于用户来说可能会显得比较复杂。另外一方面，这种方式也会造成大量重复的情况。

例如，对于变量来说，假如我们的项目中存在100个测试场景，而每个场景中都需要将用户账号（`test@ijd`）作为全局变量来使用，那么在现有模式下，我们只能在这100个`YAML/JSON`文件的`config`中都采用如下方式定义一遍：

```yaml
- config:
    name: "smoketest for scenario A."
    variables:
        - username: test@ijd
```

同样的，对于外部函数来说，假如我们项目的100个测试场景都需要用到生成随机字符串的函数（`gen_random_string`），那么我们也不得不在这100个`YAML/JSON`文件的`config`中都导入一次该函数所在的`Python`模块（假设相对于工作目录的路径为`extra/utils.py`）。

```yaml
- config:
    name: "smoketest for scenario A."
    import_module_items:
        - extra.utils
```

由此可见，当测试场景越来越多以后，要维护好全局变量和外部函数，必定会是一个很大的工作量。

那么，如果既要能引用公共的变量和函数，又要减少重复的定义和导入，那要怎么做呢？

## pytest 的 conftest.py

前段时间在接触`pytest`时，看到`pytest`支持`conftest.py`的插件机制，这是一种在测试文件中可以实现模块自动发现和热加载的机制。具体地，只要是在文件目录存在命名为`conftest.py`的文件，里面定义的`hook`函数都会在`pytest`运行过程中被导入，并可被测试用例进行调用。同时，`conftest.py`存在优先级策略，从测试用例所在目录到系统根目录的整个路径中，越靠近测试用例的`conftest.py`优先级越高。

其实这也是采用了`约定大于配置`（`convention over configuration`）的思想。`约定大于配置`是一种软件设计范式，旨在减少软件开发人员需做决定的数量，在遵从约定的过程中就不自觉地沿用了最佳工程实践。我个人也是比较喜欢这种方式的，所以在设计`ApiTestEngine`的时候，也借鉴了一些类似的思想。

受到该启发，我想也可以采用类似的思想，采用自动热加载的机制，解决背景描述中存在的重复定义和引用的问题。

既然是`约定大于配置`，那么我们首先就得定一个默认的`Python`模块名，类似于`pytest`的`conftest.py`。

这就是`debugtalk.py`。

## debugtalk.py 的命名由来

为啥会采用`debugtalk.py`这个命名呢？

其实当时在想这个名字的时候也是耗费了很多心思，毕竟是要遵从`约定大于配置`的思想，因此在设计这个约定的命名时就格外谨慎，但始终没有想到一个既合适又满意的。

在我看来，这个命名应该至少满足如下两个条件：

- 唯一性强
- 简单易记

首先，约定的模块名应该具有较强的唯一性和较高的区分度，是用户通常都不会采用的命名；否则，可能就会出现测试用例在运行过程中，热加载时导入预期之外的`Python`模块。

但也不能仅仅为了具有区分度，就使用一个很长或者毫无意义的字符串作为模块名；毕竟还是要给用户使用的，总不能每次写用例时还要去查看下文档吧；所以命名简单易记便于用户使用也很重要。

也是因为这两个有点互相矛盾的原则，让我在设计命名时很是纠结。最终在拉同事讨论良久而无果的时候，同事说，不如就命名为`debugtalk.py`得了。

仔细一想，这命名还真符合要求。在唯一性方面，采用`debugtalk.py`在`Google`、`Bing`、`Baidu`等搜索引擎中采用精确匹配，基本没有无关信息，这样在后续遇到问题时，也容易搜索到已有的解决方案；而在简单易记方面，相信这个命名也不会太复杂。

当然，`debugtalk.py`只是作为框架默认加载的`Python`模块名，如果你不喜欢，也可以进行配置修改。

## 热加载机制实现原理

然后，再来讲解下热加载机制的实现。

其实原理也不复杂，从背景描述可以看出，我们期望实现的需求主要有两点：

- 自动发现`debugtalk.py`函数模块，并且具有优先级策略；
- 将`debugtalk.py`函数模块中的变量和函数导入到当前框架运行的内存空间。

将这两点与测试用例引擎的实现机制结合起来，`ApiTestEngine`在运行过程中的热加载机制应该就如下图所示。

![](/images/ate-hot-plugin.png)

这个流程图对热加载机制描述得已经足够清晰了，我再针对其中的几个点进行说明：

1、在初始化测试用例集（testset）的时候，除了将`config`中`variables`和`import_module_items`指定的变量和函数导入外，还会默认导入`ate/built_in.py`模块。之所以这么做，是因为对于大多数系统可能都会用到一些通用的函数，例如获取当前时间戳（`get_timestamp`）、生成随机字符串（`gen_random_string`）等。与其在每个项目中都单独去实现这些函数，不如就将其添加到框架中作为默认支持的函数（相当于框架层面的`debugtalk.py`），这样大家在项目中就不需要再重复做这些基础性工作了。

2、在`ApiTestEngine`框架中，存在测试用例（`testcase`）和测试用例集（`testset`）两个层面的作用域，两者的界限十分明确。这样设计的目的在于，我们既可以实现用例集层面的变量和函数的定义和导入，也可以保障各个用例之间的独立性，不至于出现作用域相互污染的情况。具体地，作用域在用例集初始化时定义或导入的变量和函数，会存储在用例集层面的作用域；而在运行每条测试用例时，会先继承（`deepcopy`）用例集层面的作用域，如果存在同名的变量或函数定义，则会对用例集层面的变量和函数进行覆盖，同时用例集层面的变量和函数也并不会被修改。

3、从热加载的顺序可以看出，查找变量或函数的顺序是从测试用例所在目录开始，沿着父路径逐层往上，直到系统的根目录。因此，我们可以利用这个优先级原则来组织我们的用例和依赖的`Python`函数模块。例如，我们可以将不同模块的测试用例集文件放在不同的文件夹下：针对各个模块独有的依赖函数和变量，可以放置在对应文件夹的`debugtalk.py`文件中；而整个项目公共的函数和变量，就可以放置到项目文件夹的`debugtalk.py`中。

文件组织结构如下所示：

```bash
➜  project ✗ tree .
.
├── debugtalk.py
├── module_A
│   ├── __init__.py
│   ├── debugtalk.py
│   ├── testsetA1.yml
│   └── testsetA2.yml
└── module_B
    ├── __init__.py
    ├── debugtalk.py
    ├── testsetB1.yml
    └── testsetB2.yml
```

这其中还有一点需要格外注意。因为我们在框架运行过程中需要将`debugtalk.py`作为函数模块进行导入，因此我们首先要保障`debugtalk.py`满足`Python`模块的要求，也就是在对应的文件夹中要包含`__init__.py`文件。

如果对热加载机制的实现感兴趣，可直接阅读框架源码，重点只需查看[`ate/utils.py`][ate-utils]中的三个函数：

- search_conf_item(start_path, item_type, item_name)
- get_imported_module_from_file(file_path)
- filter_module(module, filter_type)

## 测试用例编写方式的变化

在新增`热加载机制`之后，编写测试用例的方式发生一些改变（优化），主要包括三点：

- 导入`Python`模块的关键词改名为`import_module_items`（原名为`import_module_functions`）；
- 不再需要显式指定导入的`Python`模块路径，变更为热加载机制自动发现；
- `Python`模块中的变量也会被导入，公共变量可放置在`Python`模块中，而不再必须通过`variables`定义。

考虑到兼容性问题，框架升级的同时也保留了对原有测试用例编写方式的支持，因此框架升级对已有测试用例的正常运行也不会造成影响。不过，我还是强烈建议大家采用最新的用例编写方式，充分利用热加载机制带来的便利。

## 写在最后

现在回过头来看[`ApiTestEngine`][ApiTestEngine]的演进历程，以及之前写的关于[`ApiTestEngine`][ApiTestEngine]设计方面的文章，会发现当初的确是有一些考虑不周全的地方。也许这也是编程的乐趣所在吧，在前行的道路中，总会有新的感悟和新的收获，迭代优化的过程，就仿佛是在打磨一件艺术品。

这种感觉，甚好！

[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[ate-utils]: https://github.com/debugtalk/ApiTestEngine/blob/master/ate/utils.py