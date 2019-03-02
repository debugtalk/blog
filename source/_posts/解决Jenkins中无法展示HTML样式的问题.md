---
title: 解决 Jenkins 中无法展示 HTML 样式的问题
permalink: post/solve-Jenkins-can-not-show-html-css
date: 2017/07/24
categories:
  - Development
tags:
  - Jenkins
---

## 问题描述

对于测试报告来说，除了内容的简洁精炼，样式的美观也很重要。常用的做法是，采用`HTML`格式的文档，并搭配`CSS`和`JS`，实现自定义的样式和动画效果（例如展开、折叠等）。

在`Jenkins`中要展示`HTML`文档，通常采用的方式有两种：

- 使用[`HTML Publisher Plugin`][HTML-Publisher-Plugin]；
- 使用`Files to archive`功能，在`Build Artifacts`中显示`HTML`文档链接。

第一种方式配合插件，可以通过图形化操作实现简易配置，并且展示效果也不错；而第二种方式的优势在于使用`Jenkins`自带的功能，不依赖插件也能实现基本的需求。

然而，不管是采用哪种方式，都有可能会遇到一种情况，就是展示出来的`HTML`报告样式全无。在浏览器的`Network`中查看资源加载情况，会发现相关的`CSS`和`JS`都没法正常加载。

```text
Refused to load the stylesheet 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css' because it violates the following Content Security Policy directive: "style-src 'self'".
Refused to apply inline style because it violates the following Content Security Policy directive: "style-src 'self'". Either the 'unsafe-inline' keyword, a hash ('sha256-0EZqoz+oBhx7gF4nvY2bSqoGyy4zLjNF+SDQXGp/ZrY='), or a nonce ('nonce-...') is required to enable inline execution.
Blocked script execution in 'http://10.13.0.146:8888/job/SkyPixel-SmokeTest/34/artifact/reports/SkyPixel-smoketest/34.html' because the document's frame is sandboxed and the 'allow-scripts' permission is not set.
Refused to load the stylesheet 'https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/css/bootstrap.min.css' because it violates the following Content Security Policy directive: "style-src 'self'".
```

## 问题分析

出现该现象的原因在于`Jenkins`中配置的`CSP`（`Content Security Policy`）。

简单地说，这是`Jenkins`的一个安全策略，默认会设置为一个非常严格的权限集，以防止Jenkins用户在`workspace`、`/userContent`、`archived artifacts`中受到恶意`HTML/JS`文件的攻击。

默认地，该权限集会设置为：

```text
sandbox; default-src 'none'; img-src 'self'; style-src 'self';
```

在该配置下，只允许加载：

- Jenkins服务器上托管的`CSS`文件
- Jenkins服务器上托管的图片文件

而如下形式的内容都会被禁止：

- JavaScript
- plugins (object/embed)
- HTML中的内联样式表（`Inline style sheets`），以及引用的外站CSS文件
- HTML中的内联图片（`Inline image definitions`），以及外站引用的图片文件
- frames
- web fonts
- XHR/AJAX
- etc.

可以看出，这个限制非常严格，在此限制下也就不难理解为什么我们的`HTML`没法正常展示样式了。

## 解决方案

### 临时解决方案

要解决该问题，方式也比较简单，就是修改`Content Security Policy`的默认配置。

修改方式为，进入`Manage Jenkins`->`Script console`，输入如下命令并进行执行。

```groovy
System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")
```

当看到如下结果后，则说明配置修改已经生效。

```text
Result
Result:
```

再次进行构建，新生成的`HTML`就可以正常展示样式了。需要说明的是，该操作对之前构建生成的`HTML`报告无效。

### 永久解决方案

不过，该方法还存在一个问题：该配置只是临时生效，当重启`Jenkins`后，`Content Security Policy`又会恢复为默认值，从而`HTML`样式又没法展示了。

当前，`Jenkins`官方还没有相应的解决方法，我们只能在每次启动或重启`Jenkins`时，重新修改该安全策略。

如果手工地来重复这项工作，也是可行，但并不是一个好的解决方案。

回到刚才的`Script console`，会发现我们执行的命令其实就是一段`Groovy`代码；那么，如果我们可以实现在`Jenkins`每次启动时自动地执行该`Groovy`代码，那么也就同样能解决我们的问题了。

好在`Jenkins`已经有相应的插件：

- [`Startup Trigger`][Startup Trigger]: 可实现在`Jenkins`节点(master/slave)启动时触发构建；
- [`Groovy plugin`][Groovy plugin]: 可实现直接执行`Groovy`代码。

搜索安装`startup-trigger-plugin`和`Groovy`插件后，我们就可以进行配置了。

配置方式如下：

- 新建一个job，该job专门用于`Jenkins`启动时执行的配置命令；
- 在`Build Triggers`模块下，勾选`Build when job nodes start`；
- 在`Build`模块下，`Add build step`->`Execute system Groovy script`，在`Groovy Script`中输入配置命令，`System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "")`。

需要注意的是，添加构建步骤的时候，应该选择`Execute system Groovy script`，而不是`Execute Groovy script`。关于这两者之间的差异，简单地说，`Groovy Script`相当于是运行在`master/slave`系统`JVM`环境中，而`system groovy script`，则是运行在`Jenkins master`的`JVM`环境中，与前面提到的`Jenkins Script Console`功能相同。如需了解更多信息，可查看[`Groovy plugin`的详细说明][Groovy plugin]。

至此，我们就彻底解决`HTML`样式展示异常的问题了。

但还有一点需要格外注意，在本文的演示中，我们修改`CSP`（`Content Security Policy`）配置时关闭了的所有安全保护策略，即将`hudson.model.DirectoryBrowserSupport.CSP`设置为空，其实这是存在很大的安全隐患的。

正确的做法，我们应该是结合项目的实际情况，选择对应的安全策略。例如，如果我们需要开启脚本文件加载，但是只限于Jenkins服务器上托管的`CSS`文件，那么就可以采用如下配置。

```groovy
System.setProperty("hudson.model.DirectoryBrowserSupport.CSP", "sandbox; style-src 'self';")
```

除此之外，`CSP`可以实现非常精细的权限配置，详细配置可参考[`Content Security Policy Reference`][CSP]。

## 阅读更多

- [Configuring Content Security Policy][Configuring Content Security Policy]
- [Content Security Policy Reference][CSP]

[HTML-Publisher-Plugin]: https://wiki.jenkins.io/display/JENKINS/HTML+Publisher+Plugin
[Startup Trigger]: https://wiki.jenkins.io/display/JENKINS/Startup+Trigger
[Groovy plugin]: https://wiki.jenkins.io/display/JENKINS/Groovy+plugin
[CSP]: https://content-security-policy.com/
[Configuring Content Security Policy]: https://wiki.jenkins.io/display/JENKINS/Configuring+Content+Security+Policy
