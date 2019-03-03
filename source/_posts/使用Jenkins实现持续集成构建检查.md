---
title: 使用 Jenkins 实现持续集成构建检查
permalink: post/Jenkins-CI-Automation-Test
date: 2016/08/14
categories:
  - Development
tags:
  - Jenkins
  - iOS
---

通过[《使用Jenkins搭建iOS/Android持续集成打包平台》](/post/iOS-Android-Packing-with-Jenkins/)和[《关于持续集成打包平台的Jenkins配置和构建脚本实现细节》](/post/iOS-Android-Packing-with-Jenkins-details/)两篇文章，我们已经在原理概念和实践操作两个层面掌握了如何搭建一个完整的持续集成打包平台。

不过，在实际使用过程中，发现有时候还会存在一个问题。研发同学提交新的代码后，Jenkins端可以成功执行构建，并生成安装包；然而在将安装包安装至移动设备时，却发现有时候会出现无法成功安装，或者安装后出现启动闪退的情况。

为了及时发现该类问题，我们还需要对每次构建生成的安装包进行检查。本文便是对构建检查涉及到的方法进行介绍。

## 构建生成`.app`

为了降低问题的复杂度，我们可以选择在模拟器中运行构建生成的安装包。之前在[《从0到1搭建移动App功能自动化测试平台（1）：模拟器中运行iOS应用》](/post/build-app-automated-test-platform-from-0-to-1-Appium-inspector-iOS-simulator/)也讲解过，要在模拟器中运行iOS应用，需要在Xcode中编译时选择模拟器类型，并且编译生成的文件后缀为`.app`。

对应的，构建生成`.app`的命令如下：

```bash
# build .app file from source code
xcodebuild \    # xctool
  -workspace ${WORKSPACE_PATH} \
  -scheme ${SCHEME} \
  -configuration ${CONFIGURATION} \
  -sdk ${SDK} \
  -derivedDataPath ${OUTPUT_FOLDER}
```

**xcodebuild/xctool参数说明**：

- `-workspace`：需要打包的workspace，后面接的文件一定要是`.xcworkspace`结尾的；
- `-scheme`：需要打包的Scheme，一般与`$project_name`相同；
- `-sdk`：区分iphone device和Simulator，可通过`xcodebuild -showsdks`获取，例如`iphonesimulator9.3`。
- `-configuration`：需要打包的配置文件，我们一般在项目中添加多个配置，适合不同的环境，Release/Debug；
- `-derivedDataPath`：指定编译结果文件的存储路径；例如，指定`-derivedDataPath build_outputs`时，将在项目根目录下创建一个`build_outputs`文件夹，生成的`.app`文件将位于`build_outputs/Build/Products/${CONFIGURATION}-iphoneos`中。

同样地，这里也可以使用`xctool`代替`xcodebuild`。

这里使用到的命令和参数基本上和[《关于持续集成打包平台的Jenkins配置和构建脚本实现细节》](/post/iOS-Android-Packing-with-Jenkins-details/)一文中的大致相同，唯一需要特别注意的是`-sdk`参数。因为是要在模拟器中运行，因此`-sdk`参数要设置为`iphonesimulator`，而非`iphoneos`。

命令成功执行后，就会在指定的`${OUTPUT_FOLDER}`目录中生成`${SCHEME}.app`文件，这也就是我们构建生成的产物。另外，熟悉`iOS`的同学都知道，`.app`文件其实是一个文件夹，为了实现更好的存储，我们也可以额外地再做一步操作，将`.app`文件夹压缩转换为`.zip`格式，而且Appium也是支持读取`.zip`格式的安装包的。

至此，适用于iOS模拟器运行的构建产物已准备就绪。这里涉及到的脚本实现已更新至[【debugtalk/JenkinsTemplateForApp】](https://github.com/debugtalk/JenkinsTemplateForApp)。

## 实现构建检查

那要怎样对构建生成的产物进行检查呢？

最简单的方式，就是在iOS模拟器中运行构建生成的`.app`，并执行一组基本的自动化测试用例。在执行过程中，如果出现无法成功安装，或者安装成功后启动出现闪退，或者自动化测试用例执行失败等异常情况，则说明我们最新提交的代码存在问题，需要通知研发同学及时进行修复。

而这些实现方式，其实我在[《从0到1搭建移动App功能自动化测试平台》](/tags/F0T1/)系列文章中都已经进行了详细讲解，并形成了一套较为成熟的自动化测试框架，【[debugtalk/AppiumBooster](https://github.com/debugtalk/AppiumBooster)】。

在此基础上，我们无需再做其它工作，只需要按照`debugtalk/AppiumBooster`的要求在表格中编写一组基本的自动化测试用例，即可采用如下方式执行构建检查。

```bash
$ cd ${AppiumBooster_Folder}
$ ruby run.rb -p "${OUTPUT_FOLDER}/${SCHEME}.app.zip" --disable_output_color > test_result.log
```

在如上命令中，通过`-p`参数指定构建生成的安装包，然后就可以在iOS模拟器中运行事先编写好的自动化测试用例，从而实现构建检查。

在这里，我们还可以通过`--disable_output_color`开关将输出日志的颜色关闭。~~之所以实现这么一个功能，是因为在Jenkins中本来也无法显示颜色，但是如果还将Terminal中有颜色的日志内容输出到Jenkins中，就会出现一些额外的字符，比较影响日志的美观。~~

现在，我们已经分别实现了代码构建和构建检查这两个核心的操作环节，而要执行最终的持续集成，我们还需要做最后一项工作，即在Jenkins中将这两个环节串联起来。

## Jenkins配置

关于Jenkins的相关基础概念、实施流程和配置细节，我在[之前的文章](/tags/Jenkins/)中已经讲解得非常详细了。在此我就只进行一点补充。

要实现在构建完成后再运行一些额外的脚本，例如我们的构建检查命令，需要使用到Jenkins的一个插件，`Post-Build Script Plug-in`。

安装完该插件后，在Jenkins配置界面的`Post-build Actions`栏目中，`Add post-build action`选项列表中就会多出`Execute a set of scripts`选项。选择该项后，会出现如下配置界面。

![Jenkins Post_build_Actions Execute_shell menu](/images/Jenkins_Post_build_Actions_Execute_shell_menu.jpg)

选择`Execute shell`后，会出现一个文本框，然后我们就可以将构建检查的命令填写到里面。

![Jenkins Post_build_Actions Execute_shell](/images/Jenkins_Post_build_Actions_Execute_shell.jpg)

在这里我们用到了`${AppiumBooster_Folder}`参数，该参数也需要通过`String Parameter`来进行定义，用于指定`AppiumBooster`项目的路径。

![Jenkins String Parameter](/images/Jenkins_String_Parameter.jpg)

最后，为了便于将执行自动化测试用例的日志和执行构建的日志分开，我们将执行自动化测试用例的日志写入到了`test_result.log`文件中。然后，在`Archives build artifacts`中就可以通过`${AppiumBooster_Folder}/test_result.log`将执行构建检查的日志收集起来，并展示到每次构建的页面中。

延续一贯的`开箱即用`原则，我将使用Jenkins实现持续集成构建检查涉及到的Jenkins配置也做成了一套模板，并更新到【[debugtalk/JenkinsTemplateForApp](https://github.com/debugtalk/JenkinsTemplateForApp)】中了，供大家参考。

## 写在最后

至此，通过[本系列的几篇文章](/tags/Jenkins/)，关于如何使用Jenkins实现移动APP持续集成的相关内容应该都已经覆盖得差不多了。

不过，由于我个人的近期工作主要集中在iOS部分，因此在讲解的过程中都是以iOS为主。后续在将工作重心移到Android部分后，我会再在`DebugTalk`的这几篇文章中更新Android部分的内容。


