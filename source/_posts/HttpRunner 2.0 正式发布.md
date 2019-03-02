---
title: HttpRunner 2.0 正式发布
permalink: post/httprunner-2.0-release
date: 2019/01/01
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在 2017 年 6 月份的时候我写了一篇博客，[《接口自动化测试的最佳工程实践（ApiTestEngine）》][1]，并同时开始了 ApiTestEngine（HttpRunner的前身）的开发工作。转眼间一年半过去了，回顾历程不禁感慨万千。HttpRunner 从最开始的个人业余练手项目，居然一路迭代至今，不仅在大疆内部成为了测试技术体系的基石，在测试业界也有了一定的知名度，形成了一定的开源生态并被众多公司广泛使用，这都是我始料未及的。

但随着 HttpRunner 的发展，我在收获成就感的同时，亦感到巨大的压力。HttpRunner 在被广泛使用的过程中暴露出了不少缺陷，而且有些缺陷是设计理念层面的，这主要都是源于我个人对自动化测试理解的偏差造成的。因此，在近期相当长的一段时间内，我仔细研究了当前主流自动化测试工具，更多的从产品的角度，学习它们的设计理念，并回归测试的本质，对 HttpRunner 的概念重新进行了梳理。

难以避免地，HttpRunner 面临着一些与之前版本兼容的问题。对此我也纠结了许久，到底要不要保持兼容性。如果不兼容，那么对于老用户来说可能会造成一定的升级成本；但如果保持兼容，那么就相当于继续保留之前错误的设计理念，对后续的推广和迭代也会造成沉重的负担。最终，我还是决定告别过去，给 HttpRunner 一个新的开始。

经过两个月的迭代开发，HttpRunner 2.0 版本的核心功能已开发完毕，并且在大疆内部数十个项目中都已投入使用（实践证明，升级也并没有多么痛苦）。趁着 2019 开年之际，HttpRunner 2.0 正式在 [PyPI][PyPI] 上发布了。从版本号可以看出，这会是一个全新的版本，本文就围绕 HttpRunner 2.0 的功能实现和开源项目管理两方面进行下介绍。

## 功能实现

在 2.0 版本中，功能实现方面变化最大的有两部分，测试用例的组织描述方式，以及 HttpRunner 本身的模块化拆分。当时也是为了完成这两部分的改造，基本上对 HttpRunner 80% 以上的代码进行了重构。除了这两大部分的改造，2.0 版本对于测试报告展现、性能测试支持、参数传参机制等一系列功能特性都进行了较大的优化和提升。

本文就只针对测试用例组织调整和模块化拆分的变化进行下介绍，其它功能特性后续会在使用说明文档中进行详细描述。

### 测试用例组织调整

之所以要对测试用例的组织描述方式进行改造，是因为 HttpRunner 在一开始并没有清晰准确的定义。对于 HttpRunner 的老用户应该会有印象，在之前的博客文章中会提到 `YAML/JSON` 文件中的上下文作用域包含了 `测试用例集（testset）` 和 `测试用例（test）` 两个层级；而在测试用例分层机制中，又存在 `模块存储目录（suite）`、`场景文件存储目录（testcases）` 这样的概念，实在是令人困惑和费解。

事实上，之前的概念本身就是有问题的，而这些概念又是自动化测试工具（框架）中最核心的内容，必须尽快纠正。这也是推动 HttpRunner 升级到 2.0 版本最根本的原因。

在此我也不再针对之前错误的概念进行过多阐述了，我们不妨回归测试用例的本质，多思考下测试用例的定义及其关键要素。

那么，测试用例（testcase）的准确定义是什么呢？我们不妨看下 [wiki][wiki_testcase] 上的描述。

> A test case is a specification of the inputs, execution conditions, testing procedure, and expected results that define a single test to be executed to achieve a particular software testing objective, such as to exercise a particular program path or to verify compliance with a specific requirement.

概括下来，一条测试用例（testcase）应该是为了测试某个特定的功能逻辑而精心设计的，并且至少包含如下几点：

- 明确的测试目的（achieve a particular software testing objective）
- 明确的输入（inputs）
- 明确的运行环境（execution conditions）
- 明确的测试步骤描述（testing procedure）
- 明确的预期结果（expected results）

对应地，我们就可以对 HttpRunner 的测试用例描述方式进行如下设计：

- 测试用例应该是完整且独立的，每条测试用例应该是都可以独立运行的；在 HttpRunner 中，每个 `YAML/JSON` 文件对应一条测试用例。
- 测试用例包含`测试脚本`和`测试数据`两部分：
    - 测试用例 = 测试脚本 + 测试数据
    - `测试脚本`重点是描述测试的`业务功能逻辑`，包括预置条件、测试步骤、预期结果等，并且可以结合辅助函数（debugtalk.py）实现复杂的运算逻辑；可以将`测试脚本`理解为编程语言中的`类（class）`；
    - `测试数据`重点是对应测试的`业务数据逻辑`，可以理解为类的实例化数据；`测试数据`和`测试脚本`分离后，就可以比较方便地实现数据驱动测试，通过对测试脚本传入一组数据，实现同一业务功能在不同数据逻辑下的测试验证。
- 测试用例是测试步骤的`有序`集合，而对于接口测试来说，每一个测试步骤应该就对应一个 API 的请求描述。
- 测试场景和测试用例集应该是同一概念，它们都是测试用例的`无序`集合，集合中的测试用例应该都是相互独立，不存在先后依赖关系的；如果确实存在先后依赖关系怎么办，例如登录功能和下单功能；正确的做法应该是，在下单测试用例的预置条件中执行登录操作。

理清这些概念后，那么 `接口（API）`、`测试用例（testcase）`、`辅助函数（debugtalk.py）`、`YAML/JSON`、`hooks`、`validate`、`环境变量`、`数据驱动`、`测试场景`、`测试用例集` 这些概念及其相互之间的关系也就清晰了。关于更具体的内容本文不再展开，后续会单独写文档并结合示例进行详细的讲解。


### 模块化拆分（Pipline）

随着 HttpRunner 功能的逐步增长，如何避免代码出现臃肿，如何提升功能特性迭代开发效率，如何提高代码单元测试覆盖率，如何保证框架本身的灵活性，这些都是 HttpRunner 本身的架构设计需要重点考虑的。

具体怎么去做呢？我采用的方式是遵循 Unix 哲学，重点围绕如下两点原则：

- Write programs that do one thing and do it well.
- Write programs to work together.

简而言之，就是在 HttpRunner 内部将功能进行模块化拆分，每一个模块只单独负责一个具体的功能，并且对该功能定义好输入和输出，各个功能模块也是可以独立运行的；从总体层面，将这个功能模块组装起来，就形成了 HttpRunner 的核心功能，包括自动化测试和性能测试等。

具体地，HttpRunner 被主要拆分为 6 个模块。

- `load_tests`: 加载测试项目文件，包括测试脚本（YAML/JSON）、辅助函数（debugtalk.py）、环境变量（.env）、数据文件（csv）等；该阶段主要负责文件加载，不会涉及解析和动态运算的操作。
- `parse_tests`: 对加载后的项目文件内容进行解析，包括 变量（variables）、base_url 的优先级替换和运算，辅助函数运算，引用 API 和 testcase 的查找和替换，参数化生成测试用例集等。
- add tests to test suite: 将解析后的测试用例添加到 unittest，组装成 `unittest.TestSuite`。
- run test suite: 使用 unittest 运行组装好的 `unittest.TestSuite`。
- aggregate results: 对测试过程的结果数据进行汇总，得到汇总结果数据。
- generate html report: 基于 Jinja2 测试报告模板，使用汇总结果数据生成 html 测试报告。

为了更好地展现自动化测试的运行过程，提升出现问题时排查的效率，HttpRunner 在运行时还可以通过增加 `--save-tests` 参数，将各个阶段的数据保存为 JSON 文件。

- XXX.loaded.json: load_tests 运行后加载生成的数据结构
- XXX.parsed.json: parse_tests 运行后解析生成的数据结构
- XXX.summary.json: 最终汇总得到的测试结果数据结构

可以看出，这 6 个模块组装在一起，就像一条流水线（Pipline）一样，各模块分工协作各司其职，最终完成了整个测试流程。

基于这样的模块化拆分，HttpRunner 极大地避免了代码臃肿的问题，每个模块都专注于解决具体的问题，不仅可测试性得到了保障，遇到问题时排查起来也方便了很多。同时，因为每个模块都可以独立运行，在基于 HttpRunner 做二次开发时也十分方便，减少了很多重复开发工作量。

## 开源项目管理

除了功能实现方面的调整，为了 HttpRunner 能有更长远的发展，我也开始思考如何借助社区的力量，吸引更多的人加入进来。特别地，近期在学习 ASF（Apache Software Foundation）如何运作开源项目时，也对 `Community Over Code` 理念颇为赞同。

当然，HttpRunner 现在仍然是一个很小的项目，不管是产品设计还是代码实现都还很稚嫩。但我也不希望它只是一个个人自嗨的项目，因此从 2.0 版本开始，我希望能尽可能地将项目管理规范化，并寻找更多志同道合的人加入进来共同完善它。

开源项目管理是一个很大的话题，当前我也还处于初学者的状态，因此本文就不再进行展开，只介绍下 HttpRunner 在 2.0 版本中将改进的几个方面。

### logo

作为一个产品，不仅要有个好名字，也要有个好的 logo。这个“好”的评价标准可能因人而异，但它应该是唯一的，能与产品本身定位相吻合的。

之前 HttpRunner 也有个 logo，但说来惭愧，那个 logo 是在网上找的，可能存在侵权的问题是一方面，logo 展示的含义与产品本身也没有太多的关联。

因此，借着 2.0 版本发布之际，我自己用 Keynote 画了一个。

![HttpRunner-logo](/images/HttpRunner-logo.png)

个人的美工水平实在有限，让大家见笑了。

对于 logo 设计的解释，主要有如下三点：

- 中间是个拼图（puzzle pieces），形似 H 字母，恰好是 HttpRunner 的首字母
- 拼图的寓意，对应的也是 HttpRunner 的设计理念；HttpRunner 本身作为一个基础框架，可以组装形成各种类型的测试平台，而在 HttpRunner 内部，也是充分解耦的各个模块组装在一起形成的
- 最后从实际的展示效果来看，个人感觉看着还是比较舒服的，在 `HttpRunner 天使用户群` 里给大家看了下，普遍反馈也都不错

### 版本号机制

作为一个开源的基础框架，版本号是至关重要的。但在之前，HttpRunner 缺乏版本规划，也没有规范的版本号机制，版本号管理的确存在较大的问题。

因此，从 2.0 版本开始，HttpRunner 在版本号机制方面需要规范起来。经过一轮调研，最终确定使用 [`Semantic Versioning`][SemVer] 的机制。该机制由 GitHub 联合创始人 Tom Preston-Werner 编写，当前被广泛采用，遵循该机制也可以更好地与开源生态统一，避免出现 “dependency hell” 的情况。

具体地，HttpRunner 将采用 `MAJOR.MINOR.PATCH` 的版本号机制。

- MAJOR: 重大版本升级并出现前后版本不兼容时加 1
- MINOR: 大版本内新增功能并且保持版本内兼容性时加 1
- PATCH: 功能迭代过程中进行问题修复（bugfix）时加 1

当然，在实际迭代开发过程中，肯定也不会每次提交（commit）都对 PATCH 加 1；在遵循如上主体原则的前提下，也会根据需要，在版本号后面添加先行版本号（-alpha/beta/rc）或版本编译元数据（+20190101）作为延伸。


### HREPs

在今年的一些大会上，我分享 HttpRunner 的开发设计思路时提到了`博客驱动开发`，主要思路就是在开发重要的功能特性之前，不是直接开始写代码，而是先写一篇博客详细介绍该功能的需求背景、目标达成的效果、以及设计思路。通过这种方式，一方面可以帮助自己真正地想清楚要做的事情，同时也可以通过开源社区的反馈来从更全面的角度审视自己的想法，继而纠正可能存在的偏差，或弥补思考的不足。

直到我后来更深入地了解到了 [`PEPs`][peps](Python Enhancement Proposals)，以及类似的 [`IPEPs`][ipeps](IPython Enhancement Proposals)，我才知道原来我曾经使用过的`博客驱动开发`并不是一个新方法，而是已经被广泛使用且行之有效的开发方式。

因此，从 2.0 版本开始，在 HttpRunner 的开发方面我想继续沿用这种方式，并且将其固化为一种机制。形式方面，会借鉴 [`PEPs`][peps] 的方式，新增 [HREPs][HREPs](HttpRunner Enhancement Proposals)；关于 HREPs 的分类和运作机制，后面我再具体进行梳理。

### License

最后再说下 License 方面。

HttpRunner 最开始选择的是 [MIT][MIT] 开源协议，从 2.0 版本开始，将切换为 [Apache-2.0][Apache-2.0] 协议。

如果熟悉这两个 License 的具体含义，应该清楚这两个协议对于用户来说都是十分友好的，不管是个人或商业使用，还是基于 HttpRunner 的二次开发，开源或闭源，都是没有任何限制的，因此协议切换对于大家来说没有任何影响。

## 总结

以上，便是 HttpRunner 2.0 发布将带来的主要变化。

截止当前，HttpRunner 在 [GitHub][httprunner] 上已经收获了近一千个star，在 TesterHome 的[开源项目列表][2]中也排到了第二名的位置，在此十分感谢大家的支持和认可。

希望 HttpRunner 2.0 会是一个新的开始，朝着更高的目标迈进。



[1]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[PyPI]: https://pypi.org/project/HttpRunner/
[wiki_testcase]: https://en.wikipedia.org/wiki/Test_case
[SemVer]: https://semver.org/
[peps]: https://www.python.org/dev/peps/
[ipeps]: https://github.com/ipython/ipython/wiki/IPEPs:-IPython-Enhancement-Proposals
[HREPs]: https://github.com/HttpRunner/HREP
[MIT]: https://opensource.org/licenses/MIT
[Apache-2.0]: https://www.apache.org/licenses/LICENSE-2.0
[httprunner]: https://github.com/HttpRunner/HttpRunner
[2]: https://testerhome.com/opensource_projects
