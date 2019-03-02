---
title: 通过 API 远程管理 Jenkins
permalink: post/manage-Jenkins-via-remote-api
date: 2016/05/02
categories:
  - Development
tags:
  - Jenkins
---

## 背景介绍

最近接到一个需求，需要对公司内部的Android性能测试平台的分支管理模块进行改造。

为了更好地说明问题，在下图中展示了一个精简的持续集成测试系统。

![Jenkins DroidTestbed](/images/Jenkins-DroidTestbed.png)

在该系统中，Jenkins负责定时检测代码库（`Code Repository`）的代码更新情况，当检测到有新的代码提交时，自动采用最新的代码进行构建，并采用构建得到的包（apk）触发自动化测试平台（`DroidTestbed`）执行测试任务。

然后再说下分支管理模块。

由于我们的持续集成平台通常不止监控一个产品，而每个产品又不止监控一个tag（例如/trunk，/projects/cn/10.9.8），因此，我们的持续集成平台需要有分支管理的功能，即针对每一个产品的每一个tag，单独创建一个分支，并针对各个分支单独指定测试用例集合测试设备。

具体实现方面，出于单一职责的原则，我们对功能进行了如下划分：

- 在Jenkins端针对每一个分支创建一个Job；
- 在`DroidTestbed`端配置测试资源，针对每一个分支分别绑定测试用例集和测试设备，每一个分支会存在一个单独的branch_id；
- 在Jenkins端的Job配置中，保存该分支在`DroidTestbed`中对应的`branch_id`，实现`Jenkins`与`DroidTestbed`的关联。

整个过程看上去并没有什么问题，那为什么需要对分支管理模块进行改造呢？

问题就出现在分支配置上面。

试想一下，每次要新增或修改一个分支的时候，由于Jenkins端和DroidTestbed端的配置是独立的，那么我们就只能在两个平台上分别进行配置。

另一方面，配置工作本身也较为复杂，例如，在Jenkins端就需要设置的参数包括：repository_url，tag，ref_tag，ref_revision，branch_id，schedule，user_name等；而这其中的大部分参数同样也要在DroidTestbed端进行配置。

根据历史经验，但凡涉及到复杂且重复的手工操作时，就容易出错。实际情况的确是这样的。在该功能上线后，由于配置复杂，业务组的同学每次要新增一个监控分支时，都需要找到管理员来帮忙配置（说实话，管理员对业务同学能配置正确也没信心）；即使是管理员，也出现过好几次因为疏忽造成配置错误的情况。

那么，这个问题要怎么解决呢？

## Jenkins Remote API 的简介

绕了这么大一个圈子，终于引出本文的主题，Jenkins Remote API。

实际上，Jenkins本身支持丰富的API接口，我们通过远程调用接口，基本上可以实现所有需要的功能，例如：

- 从Jenkins获取Job状态信息
- 触发Jenkins执行构建
- 创建、复制、修改、删除Job

回到前面的案例，我们就可以将配置操作全部放在`DroidTestbed`中，只需要在保存配置项时，由`DroidTestbed`自动调用Jenkins的Remote API，即可实现配置的同步。

## Jenkins Remote API 的调用

现在我们来看下如何调用Jenkins的Remote API。

Jenkins的Remote API以`REST-like`的形式进行提供，通过对特定的API执行POST请求即可实现对Jenkins的操作。

例如，我们搭建的Jenkins站点为`http://jenkins.debugtalk.com:8080`，那么，访问`http://jenkins.debugtalk.com:8080/api`即可查看到该站点所有可用的API；若想若某个具体的Job进行操作，如job名称`android_core_dashboard_trunk`，它的管理页面为`http://jenkins.debugtalk.com:8080/job/android_core_dashboard_trunk`，那么我们访问`http://jenkins.debugtalk.com:8080/job/android_core_dashboard_trunk/api/`即可查看到该job可用的API。

更详细的POST调用方式的介绍可以参考Jenkins的官方[wiki](https://wiki.jenkins-ci.org/display/JENKINS/Remote+access+API)，在此就不过多进行介绍。

可以看出，通过对特定API执行POST请求操作较为原始，因为我们需要关注过多底层细节。事实上，当前已经有前辈针对这一痛点，对底层的POST操作细节进行了封装，形成了一些`wrapper`方便我们从上层进行更便捷的操作。

这类`wrapper`实现的功能类似，都可以方便我们在代码中通过更简洁的方式调用Jenkins API，实现对Jenkins的远程管理，我们只需要根据我们采用的具体编程语言来选择对应的`wrapper`即可。当然，如果没有找到合适的，我们也可以参照已有的开源`wrapper`，自己再造一个轮子，原理都是相同的。

在Jenkins的官方wiki中，推荐了两个较为成熟的`API wrapper`，一个是基于Python实现的[`salimfadhley/jenkinsapi`](https://github.com/salimfadhley/jenkinsapi)，另一个是基于Ruby实现的[`arangamani/jenkins_api_client`](https://github.com/arangamani/jenkins_api_client)。

以`salimfadhley/jenkinsapi`为例，通过使用`jenkinsapi`，我们在Python中就可以很方便地管理Jenkins。常见的操作方式示例如下。

~~~python
>>> import jenkinsapi
>>> from jenkinsapi.jenkins import Jenkins

# 指定Jenkins实例
>>> J = Jenkins('http://jenkins.debugtalk.com:8080')

# 查看Jenkins版本
>>> J.version
1.542

# 查看Jenkins的所有jobs
>>> J.keys()
['foo', 'test_jenkinsapi']

# 查看指定job的配置信息
>>> J['test_jenkinsapi'].get_config()

# 创建Jenkins job
>>> jobName = 'test_job'
>>> EMPTY_JOB_CONFIG = '''
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions>jkkjjk</actions>
  <description></description>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class="vector"/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>
'''
>>> new_job = J.create_job(jobName, EMPTY_JOB_CONFIG)

# 更新Jenkins job的配置
>>> import xml.etree.ElementTree as et
>>> new_conf = new_job.get_config()
>>> root = et.fromstring(new_conf.strip())
>>> builders = root.find('builders')
>>> shell = et.SubElement(builders, 'hudson.tasks.Shell')
>>> command = et.SubElement(shell, 'command')
>>> command.text = "ls"
>>> J[jobName].update_config(et.tostring(root))

# 删除Jenkins job
>>> J.delete_job(jobName)
~~~

更多的使用方法可参考项目文档。

有些同学在认真研究了这些开源库后也许会说，官方文档已经翻遍了，但是文档中对用法的描述太少了，也没给出API调用的示例，还是不知道怎么使用啊。这个问题在开源库中的确也是普遍存在的。

介绍个技巧，通常优秀的开源库都会很重视测试，作者可能在文档中没有针对每一个API接口的调用方式进行说明，但通常会针对各个接口编写较为完整的测试代码。我们通过阅读测试代码，就可以充分了解API接口的使用方法了，这也比直接阅读文档有效率得多。

## Read More ...

最后，如果感觉上面给的示例还不够，还想看看在实际项目中如何远程管理Jenkins，那么可以关注我最近在做的一个开源项目。

先看下整体的系统架构图。

![DroidTestbed DroidMeter](/images/DroidTestbed-DroidMeter.png)

整个系统实现的功能是Android App的性能持续集成测试平台，主要由`DroidTestbed`和`DroidMeter`两部分组成。

其中，`DroidTestbed`部分采用`Ruby on Rails`编写，核心角色为测试任务管理，可实现测试资源（测试用例、测试设备等）配置，根据代码提交自动触发执行测试任务、测试设备自动化调度、测试任务手动下发，测试结果报表查看等。`DroidMeter`负责具体的性能测试执行，采用Python编写，可实现控制Android设备执行测试场景，采集性能测试数据，包括内存、启动时间、帧率、包大小、网速、流量等等。

本文暂时不对该系统进行过多介绍，我后续会单独对各个模块涉及到的技术展开进行详细介绍。如果感兴趣，可关注我的GitHub或微信公众号【DebugTalk】。
