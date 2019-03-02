---
title: 关于持续集成打包平台的 Jenkins 配置和构建脚本实现细节
permalink: post/iOS-Android-Packing-with-Jenkins-details
date: 2016/07/26
categories:
  - Development
tags:
  - Jenkins
  - iOS
---

在[《使用Jenkins搭建iOS/Android持续集成打包平台》](/post/iOS-Android-Packing-with-Jenkins/)一文中，我对如何使用Jenkins搭建iOS/Android持续集成打包平台的基础概念和实施流程进行了介绍。本文作为配套，对搭建持续集成打包平台中涉及到的执行命令、构建脚本（build.py），以及Jenkins的配置进行详细的补充说明。

当然，如果你不关心技术实现细节，也可以完全不用理会，直接参照【开箱即用】部分按照步骤进行操作即可。

## 关于iOS的构建

对iOS源码进行构建，目标是要生成`.ipa`文件，即iOS应用安装包。

当前，构建方式主要包括两种：

- `源码` -> `.archive`文件 -> `.ipa`文件
- `源码` -> `.app`文件 -> `.ipa`文件

这两种方式的主要差异是生成的中间产物不同，对应的，两种构建方式采用的命令也不同。

### `源码` -> `.archive` -> `.ipa`

```bash
# build archive file from source code
xcodebuild \    # xctool
  -workspace ${WORKSPACE_PATH} \
  -scheme ${SCHEME} \
  -configuration ${CONFIGURATION} \
  -sdk ${SDK}
  -archivePath ${archive_path}
  archive
```

`archive`：对编译结果进行归档，会生成一个`.xcarchive`的文件，位于`-archivePath`指定的目录中。需要注意的是，对模拟器类型的`sdk`无法使用`archive`命令。

```bash
# export ipa file from .archive
xcodebuild -exportArchive \
  -exportFormat format \
  -archivePath xcarchivepath \
  -exportPath destinationpath \
  -exportProvisioningProfile profilename \
  [-exportSigningIdentity identityname]
  [-exportInstallerIdentity identityname]
```

### `源码` -> `.app` -> `.ipa`

```bash
# build .app file from source code
xcodebuild \    # xctool
  -workspace ${WORKSPACE_PATH} \
  -scheme ${SCHEME} \
  -configuration ${CONFIGURATION} \
  -sdk ${SDK}
  -derivedDataPath ${OUTPUT_FOLDER}
```

```bash
# convert .app file to ipa file
xcrun \
  -sdk iphoneos \
  PackageApplication \
  -v ${OUTPUT_FOLDER}/Release-iphoneos/xxx.app \
  -o ${OUTPUT_FOLDER}/Release-iphoneos/xxx.ipa
```

### 参数说明

**xcodebuild/xctool参数**：

- `-workspace`：需要打包的workspace，后面接的文件一定要是`.xcworkspace`结尾的；
- `-scheme`：需要打包的Scheme，一般与`$project_name`相同；
- `-sdk`：区分iphone device和Simulator，可通过`xcodebuild -showsdks`获取，例如`iphoneos`和`iphonesimulator9.3`；
- `-configuration`：需要打包的配置文件，我们一般在项目中添加多个配置，适合不同的环境，Release/Debug；
- `-exportFormat`：导出的格式，通常填写为`ipa`；
- `-archivePath`：`.xcarchive`文件的路径；
- `-exportPath`：导出文件（`.ipa`）的路径；
- `-exportProvisioningProfile`：profile文件证书；
- `-derivedDataPath`：指定编译结果文件的存储路径；例如，指定`-derivedDataPath ${OUTPUT_FOLDER}`时，将在项目根目录下创建一个`${OUTPUT_FOLDER}`文件夹，生成的`.app`文件将位于`${OUTPUT_FOLDER}/Build/Products/${CONFIGURATION}-iphoneos`中。

除了采用官方的`xcodebuild`命令，还可以使用由Facebook开发维护的`xctool`。`xctool`命令的使用方法基本与`xcodebuild`一致，但是输出的日志会清晰很多，而且还有许多其它优化，详情请参考`xctool`的官方文档。

**xcrun参数**：

- `-v`：指定`.app`文件的路径
- `-o`：指定生成`.ipa`文件的路径

### 补充说明

**1、获取Targets、Schemes、Configurations参数**

在填写`target`/`workspace`/`scheme`/`configuration`等参数时，如果不知道该怎么填写，可以在项目根目录下执行`xcodebuild -list`命令，它会列出当前项目的所有可选参数。

```bash
➜  Store_iOS git:(NPED) ✗ xcodebuild -list
Information about project "Store":
    Targets:
        Store
        StoreCI

    Build Configurations:
        Debug
        Release

    If no build configuration is specified and -scheme is not passed then "Release" is used.

    Schemes:
        Store
        StoreCI
```

**2、清除缓存文件**

在每次build之后，工程目录下会遗留一些缓存文件，以便下次build时减少编译时间。然而，若因为工程配置错误等问题造成编译失败后，下次再编译时就可能会受到缓存的影响。

因此，在持续集成构建脚本中，比较好的做法是在每次build之前都清理一下上一次编译遗留的缓存文件。

```bash
# clean before build
xctool \
  -workspace ${WORKSPACE_PATH} \
  -scheme ${SCHEME} \
  -configuration ${CONFIGURATION} \
  clean
```

`clean`：清除编译产生的问题，下次编译就是全新的编译了

**3、处理Cocoapod依赖库**

另外一个需要注意的是，若项目是采用Cocoapod管理项目依赖，每次拉取最新代码后直接编译可能会报错。这往往是因为其他同事更新了依赖库（新增了第三方库或升级了某些库），而本地还采用之前的第三方库进行编译，从而会出现依赖库缺失或版本不匹配等问题。

应对的做法是，在每次build之前都更新一下Cocoapod。

```bash
# Update pod repository
pod repo update
# Install pod dependencies
pod install
```

**4、修改编译包的版本号**

通过持续集成打包，我们会得到大量的安装包。为了便于区分，比较好的做法是在App中显示版本号，并将版本号与Jenkins的`BUILD_NUMBER`关联起来。

例如，当前项目的主版本号为`2.6.0`，本次构建的`BUILD_NUMBER`为130，那么我们就可以将本次构建的App版本号设置为`2.6.0.130`。通过这种方式，我们可以通过App中显示的版本号快速定位到具体到构建历史，从而对应到具体的代码提交记录。

要实现对App版本号的设置，只需要在打包前对`Info.plist`文件中的`CFBundleVersion`和`CFBundleShortVersionString`进行修改即可。在Python中，利用`plistlib`库可以很方便地实现对`Info.plist`文件的读写。

**5、模拟器运行**

如果持续集成测试是要运行在iOS模拟器上，那么就需要构建生成`.app`文件。

在前面讲解的两种构建方式中，中间产物都包含了`.app`文件。对于以`.xcarchive`为中间产物的方式，生成的`.app`文件位于`output_dir/StoreCI_Release.xcarchive/Products/Applications/`目录中。

不过，这个`.app`文件在模拟器中还无法直接运行，还需要在Xcode中修改`Supported Platforms`，例如，将`iphoneos`更改为`iOS`。详细原因请参考[《从0到1搭建移动App功能自动化测试平台（1）：模拟器中运行iOS应用》](/post/build-app-automated-test-platform-from-0-to-1-Appium-inspector-iOS-simulator/)


## 关于Android的构建

待续

## 关于构建脚本

对于构建脚本（[`build.py`](https://github.com/debugtalk/JenkinsTemplateForApp/blob/master/workspace/YourProject/Build_scripts/build.py)）本身，源码应该是最好的说明文档。

在`build.py`脚本中，主要实现的功能就四点：

- 执行构建命令，编译生成`.ipa`文件，这部分包含了`关于iOS的构建`部分的全部内容；
- 构建时动态修改`Info.plist`，将编译包的版本号与Jenkins的BuildNumber关联起来；
- 上传`.ipa`文件至`pyger`/`fir.im`平台，并且做了失败重试机制；
- 解析`pyger`/`fir.im`平台页面中的二维码，将二维码图片保存到本地。

需要说明的是，对于构建任务中常用的可配置参数，例如`BRANCH`/`SCHEME`/`CONFIGURATION`/`OUTPUT_FOLDER`等，需要在构建脚本中通过`OptionParser`的方式实现可传参数机制。这样我们不仅可以命令行中通过传参的方式灵活地调用构建脚本，也可以在Jenkins中实现参数传递。

之所以强调`常用的`可配置参数，这是为了尽可能减少参数数目，降低脚本调用的复杂度。像`PROVISIONING_PROFILE`和`pgyer/fir.im`账号这种比较固定的配置参数，就可以写死在脚本中。因此，在使用构建脚本（build.py）之前，需要先在脚本中配置下`PROVISIONING_PROFILE`和`pgyer/fir.im`账号。

另外还想多说一句，`pyger`/`fir.im`这类第三方平台在为我们提供便利的同时，稳定性不可控也是一个不得不考虑的问题。在我使用`pgyer`平台期间，就遇到了平台服务变动、接口时而不稳定出现502等问题。因此，最好的方式还是自行搭建一套类似的服务，反正我是打算这么做了。

## Jenkins的详细配置

对于Jenkins的详细配置，需要补充说明的有四点。

### 1、参数的传递

在构建脚本中，我们已经对常用的可配置参数实现了可传参机制。例如，在Terminal中可以通过如下形式调用构建脚本。

```bash
$ python build.py --scheme SCHEME --workspace Store.xcworkspace --configuration CONFIGURATION --output OUTPUT_FOLDER
```

那么我们在Jenkins中要怎样才能指定参数呢？

实际上，Jenkins针对项目具有参数化的功能。在项目的配置选项中，勾选`This project is parameterized`后，就可以为当前project添加多种类型的参数，包括：

- Boolean Parameter
- Choice Parameter
- Credentials Parameter
- File Parameter
- Multi-line String Parameter
- Password Parameter
- Run Parameter
- String Parameter

通常，我们可以选择使用`String Parameter`来定义自定义参数，并可对每个参数设置默认值。

当我们配置了`BRANCH`、`SCHEME`、`CONFIGURATION`、`OUTPUT_FOLDER`、`BUILD_VERSION`这几个参数后，我们就可以在`Build`配置区域的`Execute shell`通过如下形式来进行参数传递。

```bash
$ python ${WORKSPACE}/Build_scripts/build.py \
    --scheme ${SCHEME} \
    --workspace ${WORKSPACE}/Store.xcworkspace \
    --configuration ${CONFIGURATION} \
    --output ${WORKSPACE}/${OUTPUT_FOLDER} \
    --build_version ${BUILD_VERSION}.${BUILD_NUMBER}
```

可以看出，参数的传递方式很简单，只需要预先定义好了自定义参数，然后就可以通过`${Param}`的形式来进行调用了。

不过你也许会问，`WORKSPACE`和`BUILD_NUMBER`这两个参数我们并未进行定义，为什么也能进行调用呢？这是因为Jenkins自带部分与项目相关的环境变量，例如`BRANCH_NAME`、`JOB_NAME`等，这部分参数可以在shell脚本中直接进行调用。完整的环境变量可在`Jenkins_Url/env-vars.html/`中查看。

配置完成后，就可以在`Build with Parameters`中通过如下形式手动触发构建。

![Jenkins manul build](/images/Jenkins_manul_build.jpg)

### 2、修改build名称

在`Build History`列表中，构建任务的名称默认显示为按照build次数递增的`BUILD_NUMBER`。有时候我们可能想在build名称中包含更多的信息，例如包含当次构建的`SCHEME`和`CONFIGURATION`，这时我们就可以通过修改`BuildName`实现。

Jenkins默认不支持`BuildName`设置，但可通过安装`build-name-setter`插件进行实现。安装`build-name-setter`插件后，在配置页面的`Build Environment`栏目下会出现`Set Build Name`配置项，然后在`Build Name`中就可以通过环境变量参数来设置build名称。

例如，要将build名称设置为上面截图中的`StoreCI_Release_#130`样式，就可以在`Build Name`中配置为`${SCHEME}_${CONFIGURATION}_#${BUILD_NUMBER}`。

除了在`Build Name`中传递环境变量参数，`build-name-setter`还可以实现许多更加强大的自定义功能，大家可自行探索。

### 3、展示二维码图片

然后再说下如何在`Build History`列表中展示每次构建对应的二维码图片。

![Jenkins build history](/images/Jenkins_build_history.jpg)

需要说明的是，在上图中，绿色框对应的内容是`BuildName`，我们可以通过`build-name-setter`插件来实现自定义配置；但是红色框已经不在`BuildName`的范围之内，而是对应的`BuildDescription`。

同样地，Jenkins默认不支持在构建过程中自动修改`BuildDescription`，需要通过安装`description setter plugin`插件来辅助实现。安装`description setter plugin`插件后，在配置页面的`Build`栏目下，`Add build step`中会出现`Set build description`配置项，添加该配置项后就会出现如下配置框。

![Jenkins set build description](/images/Jenkins_set_build_description.jpg)

该功能的强大之处在于，它可以在构建日志中通过正则表达式来匹配内容，并将匹配到的内容添加到`BuildDescription`中去。

例如，我们想要展示的二维码图片是在每次构建过程中生成的，因此我们首先要获取到二维码图片文件。

我的做法是，在`build.py`中将蒲公英平台返回的应用下载页面地址和二维码图片地址打印到log中。

```
appDownloadPage: https://www.pgyer.com/035aaf10acf5dd7c279c4fe423a57674
appQRCodeURL: https://o1wjx1evz.qnssl.com/app/qrcodeHistory/fe7a8c9051f0c7fc0affc78f40c20a4b5e4bdb4c77b91a29501f55fd9039c659
Save QRCode image to file: /Users/Leo/.jenkins/workspace/DebugTalk_Plus_Store_iOS/build_outputs/QRCode.png
```

然后，在`Set build description`配置项的`Regular expression`就可以按照如下正则表达式进行匹配：

```
appDownloadPage: (.*)$
```

接下来，就可以在`Description`中对匹配到的结果进行引用。

```
<img src='${BUILD_URL}artifact/build_outputs/QRCode.png'>\n<a href='\1'>Install Online</a>
```

在这里，我们用到了HTML的标签，而Jenkins的`Markup Formatter`默认是采用`Plain text`模式，因此还需要对Jenkins对系统配置进行修改，在[《使用Jenkins搭建iOS/Android持续集成打包平台》](/post/iOS-Android-Packing-with-Jenkins/)中已进行了详细说明，在此就不再重复。

通过以上方式，就可以实现前面图片中的效果。

### 4、收集编译成果物

在上面讲解的展示二维码图片一节中，用到了`${BUILD_URL}artifact/build_outputs/QRCode.png`一项，这里的URL就是用到了编译成果物收集后保存的路径。

`Archives build artifacts`是Jenkins默认自带的功能，无需安装插件。该功能在配置页面的`Post-build Actions`栏目下，在`Add post-build action`的列表中选择添加`Archives build artifacts`。

添加后的配置页面如下图所示：

![Jenkins archive the artifacts](/images/Jenkins_archive_the_artifacts.jpg)

通常，我们只需要配置`Files to archive`即可。定位文件时，可以通过正则表达式进行匹配，也可以调用项目的环境变量；多个文件通过逗号进行分隔。

例如，假如我们想收集`QRCode.png`、`StoreCI_Release.ipa`、`Info.plist`这三个文件，那么我们就可以通过如下表达式来进行指定。

```
${OUTPUT_FOLDER}/*.ipa,${OUTPUT_FOLDER}/QRCode.png,${OUTPUT_FOLDER}/*.xcarchive/Info.plist
```

当然，目标文件的具体位置是我们在构建脚本（`build.py`）中预先进行处理的。

通过这种方式，我们就可以实现在每次完成构建后将需要的文件收集起来进行存档，以便后续在Jenkins的任务页面中进行下载。

![show artifacts of Jenkins](/images/Jenkins_show_artifacts.jpg)

也可以直接通过归档文件的URL进行访问。例如，上图中`QRCode.png`的URL为`Jenkins_Url/job/JenkinsJobName/131/artifact/build_outputs/QRCode.png`，而`Jenkins_Url/job/JenkinsJobName/131/`即是`${BUILD_URL}`，因此可以直接通过`${BUILD_URL}artifact/build_outputs/QRCode.png`引用。

## 总结

至此，[《使用Jenkins搭建iOS/Android持续集成打包平台》](/post/iOS-Android-Packing-with-Jenkins/)一文中涉及到的Jenkins配置和构建脚本实现细节均已补充完毕了。相信大家结合这两篇文章，应该会对如何使用Jenkins搭建iOS/Android持续集成打包平台的基础概念和实现细节都有一个比较清晰的认识。

对于还未完善的部分，我后续将在博客中进行更新。

操作手册请参考文章末尾的【开箱即用】部分，祝大家玩得愉快！

## 开箱即用

GitHub地址：https://github.com/debugtalk/JenkinsTemplateForApp

### 1、添加构建脚本

- 在构建脚本中配置`PROVISIONING_PROFILE`和`pgyer/fir.im`账号；
- 在目标构建代码库的根目录中，创建`Build_scripts`文件夹，并将`build.py`拷贝到`Build_scripts`中；
- 将`Build_scripts/build.py`提交到项目中。

除了与Jenkins实现持续集成，构建脚本还可单独使用，使用方式如下：

```bash
$ python ${WORKSPACE}/Build_scripts/build.py \
	--scheme ${SCHEME} \
    --workspace ${WORKSPACE}/Store.xcworkspace \
    --configuration ${CONFIGURATION} \
    --output ${WORKSPACE}/${OUTPUT_FOLDER}
```

### 2、运行jenkins，安装必备插件

```bash
$ nohup java -jar jenkins_located_path/jenkins.war &
```

### 3、创建Jenkins Job

- 在Jenkins中创建一个`Freestyle project`类型的Job，先不进行任何配置；
- 然后将`config.xml`文件拷贝到`~/.jenkins/jobs/YourProject/`中覆盖原有配置文件，重启Jenkins；
- 完成配置文件替换和重启后，刚创建好的Job就已完成了大部分配置；
- 在`Job Configure`中根据项目实际情况调整配置，其中`Git Repositories`是必须修改的，其它配置项可选择性地进行调整。

### 4、done！


