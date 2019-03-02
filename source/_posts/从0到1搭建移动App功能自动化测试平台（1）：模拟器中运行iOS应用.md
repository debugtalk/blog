---
title: 从0到1搭建移动App功能自动化测试平台（1）：模拟器中运行iOS应用
permalink: post/build-app-automated-test-platform-from-0-to-1-Appium-inspector-iOS-simulator
date: 2016/05/21
categories:
  - Testing
  - 自动化测试
tags:
  - Appium
  - iOS
  - AppiumBooster
---

在上一篇文章中，我对本系列教程的项目背景进行了介绍，并对自动化测试平台的建设进行了规划。

在本文中，我将在已准备就绪的iOS自动化测试环境的基础上，通过Appium调用模拟器运行iOS应用。内容很是基础，熟悉的同学可直接略过。

## iOS应用安装包的基础知识

作为完全的iOS新手，困惑的第一个问题就是iOS安装包文件。

在Android系统中，安装App的途径很多，除了各类应用市场，普通用户也经常直接下载apk安装包文件后手动进行安装，因此大家对Android的安装包文件都比较熟悉。

但是对于iOS系统就不一样了，由于我们普通用户在iOS上安装应用的时候基本上只能通过Apple Store进行安装（未越狱），没有机会接触原始的安装包文件，因此往往连iOS应用的安装包到底是什么格式后缀都不清楚。

现在我们想在Appium App中通过模拟器运行被测应用，需要指定iOS app的安装包路径，因此需要首先获得一个iOS app安装包。

![Appium initialize iOS Settings](/images/Appium_iOS_Settings_init.jpg)

那么iOS app的安装包长啥样呢？

或者在这个问题之前，我们先来看下另一个问题：对于iOS设备来说，如果不通过Apple Store，我们可以怎样安装一个应用？

针对这个问题，我搜了些资料，也请教了周围的同事，了解到的途径有如下几个：

- 企业证书：该种方式适用于企业内部；通过企业证书编译出的iOS应用，无需上传至Apple Store，即可无限制的安装到企业员工的iOS设备中。只是需要解决的一个问题是，由于iOS设备没有文件管理器，没法将安装包拷贝到iOS设备中，因此常用的做法是将安装包（`.ipa`文件）上传至一些下载服务器（例如`fir.im`），并生成二维码，然后用户扫描二维码后即可通过浏览器下载安装包并进行安装。由此联想到另外一个方法，通过微信文件传输助手将安装包（`.ipa`）传输至iOS设备，然后再进行安装应该也是可以的吧？这种方法不知在原理上是否可行，因为在试验时由于安装包大于30M，微信无法传输，所以没能进行验证。
- Xcode：该种方式适用于iOS开发者；开发者在Xcode中连上iOS设备对源码进行编译，编译生成的应用会自动安装至iOS设备。当然，该种方式也是需要iOS开发者证书。
- PP助手：该种方式适用于普通用户；PP助手是一个非苹果官方的设备资源管理工具，可以实现对未越狱的iOS设备进行应用管理，也可以安装本地`.ipa`文件，前提是`.ipa`文件具有合适的签名。

在上面列举的安装应用的途径中，反复提到了`.ipa`文件，那`.ipa`应该就是iOS应用程序的后缀了吧？暂且这么认为吧。

再回到前面的场景，要在iOS模拟器中运行iOS应用，我们是否可以找研发人员要一个`.ipa`安装包文件，然后就能在模拟器中加载运行应用呢？

刚开始的时候我是这么认为的。于是我获取到`.ipa`文件后，在`App Path`中填写该文件的路径，然后启动Appium Server；接着我再打开Inspector时，发现iOS模拟器启动了，但是在应用启动的时候就出问题了，始终无法正常启动，感觉像是启动崩溃，反复尝试多次仍然如此。

再次经过Google，总算是明白出现问题的原因了，总结下来有如下几点：

- 不管是从Apple Store或iTunes上下载的应用，还是在Xcode中针对真机设备编译生成的`.ipa`文件，都是面向于ARM处理器的iOS设备，只能在真机设备中进行安装；
- 而在Mac OSX系统中运行的iOS模拟器，运行环境是基于Intel处理器的；
- 因此，若是针对真机设备编译生成的`.ipa`文件，是无法在iOS模拟器中正常运行的，毕竟处理器架构都不一样；
- 要想在iOS模拟器中运行应用，则必须在Xcode中编译时选择模拟器类型；编译生成的文件后缀为`.app`。

## 准备`.app`文件

接下来，就说下如何获取`.app`文件。

虽然是测试人员，不会对被测iOS项目贡献代码，但是也不能总是找研发帮忙编译生成`.app`文件。所以，在本地搭建完整的iOS项目开发环境还是很有必要的。

对于iOS开发环境的搭建，当前社区中应该已经有了很多完整的教程，我在这儿就不详细描述了，只简单说下我搭建过程中涉及到的几个点。

首先，Mac OSX、Xcode、Apple Developer Tools这些基础环境的安装，在上一篇文章中已经进行说明了；

然后，申请项目源码的访问权限，`git clone`到本地；

接着是项目依赖环境的问题；通常一个较大型的iOS项目都会引用许多第三方库，而这些依赖库并不会直接保存到项目仓库中，通常是采用`CocoaPods`进行管理；简单地说，`CocoaPods`是针对`Swift`和`Objective-C`项目的依赖管理器，类似于Java中的`Maven`，Ruby中的`Gem`，Python中的`pip`。

当然，iOS项目的依赖管理工具也不是只有`CocoaPods`一个，如果是采用的别的依赖管理器，请自行查找对应的资料。

采用`CocoaPods`管理的项目，在项目根目录下会包含`Podfile`和`Podfile.lock`文件，里面记录了当前项目依赖的第三方库以及对应的版本号。

安装`CocoaPods`很简单，采用`gem`即可。

```sh
$ sudo gem install cocoapods
```

然后，进入到iOS项目的目录，执行`pod install`命令即可安装当前项目的所有依赖。

```sh
$ cd Project_Folder
$ pod install
Re-creating CocoaPods due to major version update.
Analyzing dependencies
.....（略）
Downloading dependencies
.....（略）
Generating Pods project
Integrating client project
Sending stats
Pod installation complete! There are 27 dependencies from the Podfile and 28 total pods installed.
```

关于`CocoaPods`的更多信息，请自行查看[官方网站](https://cocoapods.org)

在依赖安装完成后，正常情况下，就可以在Xcode中编译项目了。

没有别的需要注意的，将target选择为模拟器（iOS Simulator）即可。而且针对模拟器进行编译时，也不会涉及到开发者证书的问题，项目配置上会简单很多。待后续讲到真机上的自动化测试时，我再对证书方面的内容进行补充。

编译完成后，在Products目录下，就可以看到`XXX.app`文件，这里的`XXX`就是项目名称；然后，选中`XXX.app`文件，【Show in Finder】，即可在文件目录中定位到该文件。

接下来，将`XXX.app`文件拷贝出来，或者复制该文件的`Full path`，怎样都行，只要在`Appium`的`App Path`中能定位到该文件就行。

## 模拟器中运行iOS应用

被测应用`.app`准备就绪后，接下来就可以在iOS模拟器中运行了。

回到前面的那张图。启动`Appium app`后，对于模拟器运行的情况，在`iOS Settings`中必须设置的参数项就3个，`App Path`、`Force Device`和`Platform Version`。对于真机运行的情况，后续再单独进行说明。

设置完毕后，点击【Launch】，启动`Appium Server`。

![Appium inspector button](/images/Appium_Inspector_Button.jpg)

然后，点击图中红框处的按钮，即可通过`Inspector`启动模拟器，并在模拟器中加载iOS应用。

![Appium iOS Simulator Console](/images/Appium_iOS_Simulator_Console.jpg)

在模拟器中，我们可以像在真机中一样，体验被测应用的各项功能；并且，在Appium的日志台中，可以实时查看到日志信息。

## 经历的一个坑

整个过程是挺简单的，不过，在探索过程中我还是有遇到一个坑。

通过`Inspector`启动模拟器时，总是弹框报错，报错形式如下。

![Appium Inspector Error](/images/Appium_Inspector_Error.jpg)

刚开始出现这问题时百思不得其解，因为提示的信息并不明显，Google了好一阵也没找到原因。最后只有详细去看日志信息，才发现问题所在。

在日志中，发现的报错信息如下：

```
[iOS] Error: Could not find a device to launch. You requested 'iPhone 6 (8.4)', but the available devices were: ["Apple TV 1080p (9.2) [98638D25-7C82-48DF-BDCA-7F682F951533] (Simulator)","iPad 2 (9.2) [5E22F53E-EAB3-45DF-A1DD-10F58E920679] (Simulator)","iPad 2 (9.3) [4B2D2F9A-C099-4C13-8DE9-27C826A521C2] (Simulator)","iPad Air (9.2) [825E4997-9CD8-4225-9977-4C7AE2C98389] (Simulator)","iPad Air (9.3) [E4523799-E35F-4499-832B-12CF33F09144] (Simulator)","iPad Air 2 (9.2) [8057039D-F848-453E-97EC-2F75CAEA2E77] (Simulator)","iPad Air 2 (9.3) [0B8F49DA-832A-4248-BA1D-9DA5D11E31FD] (Simulator)","iPad Pro (9.2) [AF1F2D06-3067-41B5-AC2B-4B0ED88BF5D9] (Simulator)","iPad Pro (9.3) [C39617A6-9D91-4C0B-B25B-741BD57B016C] (Simulator)","iPad Retina (9.2) [D3C694E1-E3B4-47BE-AB5E-80B3D4E22FC2] (Simulator)","iPad Retina (9.3) [907C7B06-ED2C-48AC-AC46-04E4AD6E0CA3] (Simulator)","iPhone 4s (9.2) [1A786195-94E3-4908-8309-7B66D84E4619] (Simulator)","iPhone 4s (9.3) [3F76F34B-5A8F-4FD1-928D-56F84C192DDD] (Simulator)","iPhone 5 (9.2) [0D79A4CA-71EB-48A6-9EE4-172BEF3EB4E0] (Simulator)","iPhone 5 (9.3) [04270D44-F831-4253-95F2-3D205D2BC0D9] (Simulator)","iPhone 5s (9.2) [13A16C07-3C5B-4B04-A94B-B40A63238958] (Simulator)","iPhone 5s (9.3) [D30A7B34-BA01-4203-80DA-FAEA436725F9] (Simulator)","iPhone 6 (9.2) [5D01650F-2A31-4D53-A47A-CCF7FD552ADD] (Simulator)","iPhone 6 (9.3) [2F0810F6-C73B-4BA4-93BA-06D4B6D96BDA] (Simulator)","iPhone 6 Plus (9.2) [9A840B78-E6CE-4D18-BE83-16B590411641] (Simulator)","iPhone 6 Plus (9.3) [27C6557A-B09D-4D8A-9846-DA8FE0A8E8D5] (Simulator)","iPhone 6s (9.2) [E7F5B8A5-0E85-404F-A4D4-191D63E7EC1B] (Simulator)","iPhone 6s (9.3) [6F702911-13C2-472C-9ECD-BADD4385CB77] (Simulator)","iPhone 6s (9.3) + Apple Watch - 38mm (2.2) [B63FFAA4-00A4-473B-9462-3664F41F9001] (Simulator)","iPhone 6s Plus (9.2) [58837F78-511A-4F0B-9DDF-782E3B9935BD] (Simulator)","iPhone 6s Plus (9.3) [C31003C6-DCE2-414D-AD7F-376F6FA995B0] (Simulator)","iPhone 6s Plus (9.3) + Apple Watch - 42mm (2.2) [E3154768-CA23-45CC-90E5-2D0386A57B7D] (Simulator)"]
```

问题在于，我设置`iOS Settings`时，将`Force Device`设置为"iPhone 6"，将`Platform Version`设置为“8.4”，但是经过组合，`iPhone 6 (8.4)`并不在可用的模拟器设备列表中。

再来看日志中提示的可用设备，发现“iPhone 6”设备对应的`Platform Version`只有“9.2”和“9.3”。然后回到`iOS Settings`，发现`Platform Version`的下拉框可选项就没有“9.2”和“9.3”，最新的一个可选版本也就是“8.4”。

![Appium iOS Settings bug](/images/Appium_iOS_Settings_bug.jpg)

这应该是`Appium app`的一个bug吧。不过好在`Platform Version`参数虽然是通过下拉框选择，但是也可以在框内直接填写内容。于是我在`Platform Version`设置框内填写为“9.3”，然后再次启动时，发现iOS模拟器就可以正常启动了。

## To be continued ...

现在，我们已经成功地通过Appium Inspector调用模拟器并运行iOS应用，接下来，我们就要开始尝试编写自动化测试用例了。

在下一篇文章中，我们将对Appium Inspector的功能进行熟悉，通过Inspector来查看iOS应用的UI元素信息，并尝试采用脚本语言与UI进行交互操作。
