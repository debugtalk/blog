---
title: Android开发环境配置2：详解Recovery
permalink: post/android-development-environment-recovery
date: 2015/07/04
categories:
  - 3. Testing
  - Android
tags:
  - Android
  - Recovery
---

不管是尝试对Android手机进行刷机的普通用户，还是刚接触Android应用开发的开发者，都会接触到Recovery。本文将从什么是Recovery，怎么在Android设备中安装Recovery环境，如何使用Recovery几个方面对Android Recovery进行介绍。


## What is Recovery

通常，在Android设备中会预装`Recovery`环境，可以用于还原出厂设置、升级操作系统、以及进行问题诊断等。

从类别上，`Recovery`环境分为两种，Google官方的（the Stock Recovery）`Recovery`环境和第三方的`Recovery`环境（the Custom Recovery）。

### 1、the Stock Recovery

Google官方的`Recovery`环境提供的功能十分有限，主要包括：

- 重置出厂设置，清除所有数据
- 擦除cache分区
- 刷入官方的升级文件来升级系统

### 2、the Custom Recovery

针对Google官方`Recovery`环境功能的不足，许多组织、机构或个人定制了功能更为强大的`Recovery`环境，统称为第三方`Recovery`环境。当前最为流行的有两个：ClockworkMod Recovery (CWM)、Team Win Recovery Project (TWRP)。

第三方`Recovery`环境除了具有Google官方`Recovery`环境的功能外，还增加了其它特性，主要包括：

- 创建、恢复系统备份
- 安装自定义的ROM
- 安装、删除应用程序


## How to Install Recovery

通常，Android设备出厂时都会带有官方的`Recovery`环境。如果我们需要获取更多的功能，就需要自己安装第三方`Recovery`环境来替换官方的`Recovery`环境。

### 1、准备工作（Prerequisites）

- 配置Android调试环境：安装adb和fastboot工具，开启USB调试模式（USB debugging），建立手机与电脑之间的USB调试连接。
- Android设备的Bootloader已完成解锁（unlocked）。
- 下载第三方`Recovery`镜像包，例如，openrecovery-twrp-2.8.7.1-hammerhead.img

### 2、切换至fastboot模式

在`flash`操作前，先将设备切换至`fastboot`模式。

~~~bash
$ adb reboot bootloader
~~~

通过`fastboot devices`命令可以查看到手机与电脑直接的连接状态。

~~~bash
$ fastboot devices
03f7fc7ad0081a10	fastboot
~~~

### 3、安装Custom Recovery

在`fastboot`模式下，在电脑的命令终端中执行如下命令，写入`recovery.img`，并进行重启。

~~~bash
$ fastboot flash recovery openrecovery-twrp-2.8.7.1-hammerhead.img
sending 'recovery' (14694 KB)...
OKAY [  0.709s]
writing 'recovery'...
OKAY [  1.133s]
finished. total time: 1.842s

$ fastboot reboot
rebooting...
finished. total time: 0.408s
~~~


## How to Use Recovery

### 进入Recovery环境

在手机开机状态下，可以通过如下命令进入`Recovery`环境。

~~~bash
$ adb reboot recovery
$ adb shell
~ #
~~~

从上可以看出，在`Recovery`环境下，用户具有`root`权限。

### 在Recovery环境的手机资源管理器中安装`zip`格式的软件

如果要安装某些`root`权限的软件，例如`SuperSU.zip`，而手机却没有root权限，就可以在`Recovery`环境下进行安装。

在`Recovery`环境下，将要安装的应用程序安装包push至手机任意文件夹。

~~~bash
$ adb push UPDATE-SuperSU-v2.46.zip /sdcard/!ReadyToFlash/Root_Files/UPDATE-SuperSU-v2.46.zip
4604 KB/s (4017098 bytes in 0.852s)
~~~

然后在手机`Recovery`环境的资源管理器中找到该文件，点击安装即可。

### 采用sideload方式安装zip格式的软件

在`Recovery`环境下，在手机端开启`ADB Sideload`，开启后，可以看到手机处于`sideload`模式。

~~~bash
$ adb devices
List of devices attached
03f7fc7ad0081a10	sideload
~~~

采用`adb sideload <filename.Zip>`命令，即可进行`zip`软件包的安装。

~~~bash
$ adb sideload busybox-signed.zip
Total xfer: 1.24x
~~~

在手机端可以看到如下日志信息。

~~~
Undating partition details...
...done
Full  SELinux support is present.
MTP enabled
Starting ADB  sideload feature ...
Installing '/sideload/package.zip'...
************************
Install Busybox apk
************************
- Mounting file  systems ...
- Installing Busybox free ...
- Unmounting file system ...
Done!
~~~

### 在Recovery启动过程中执行命令

对于`2.1`及以上版本的`TWRP Recovery`中，可以使用`OpenRecoveryScript`引擎，在`TWRP Recovery`启动时执行命令。

具体的方式为，在Android设备的`/cache/recovery/`目录下创建`openrecoveryscript`文件，并在其中写入执行命令。

例如：

~~~vim
# /cache/recovery/openrecoveryscript
set tw_signed_zip_verify 0
install /data/local/tmp/perm-recovery-signed.zip
install /data/local/tmp/UPDATE-SuperSU-v2.46.zip
install /data/local/tmp/busybox-signed.zip
~~~
