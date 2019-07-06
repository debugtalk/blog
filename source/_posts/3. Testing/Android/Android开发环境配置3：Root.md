---
title: Android 开发环境配置3：Root
permalink: post/android-development-environment-root
date: 2015/07/05
categories:
  - 3. Testing
  - Android
tags:
  - Android
---

## What is root

### root的原理

破解Android root权限的本质是：

在系统中加入一个任何用户都可能用于登陆的su命令。或者说替换掉系统中的su程序，因为系统中的默认su程序需要验证实际用户权限，只有root和shell用户才有权运行系统默认的su程序，其他用户运行都会返回错误。而破解后的su将不检查实际用户权限，这样普通的用户也将可以运行su程序，也可以通过su程序将自己的权限提升。


### 判断手机是否root

通过`adb shell`连接至手机以后，执行`su`命令，如果无法执行，则说明该手机无`root`权限。

~~~bash
$ adb shell
shell@hammerhead:/ $
shell@hammerhead:/ $ su
su command not found
~~~


## How to root

本文中用到的操作系统为Linux（Debian）；Android设备型号为Nexus 5（HAMMERHEAD），Android版本为4.4.4（Build Num KTU84P）

### 准备工作（Prerequisites）

- 配置Android调试环境：安装adb和fastboot工具，开启USB调试模式（USB debugging），建立手机与电脑之间的USB调试连接。
- Android设备的Bootloader已完成解锁（unlocked）。
- 下载已经完成root的boot.img，例如，CF-Auto-Root-hammerhead-hammerhead-nexus5.img
- 下载第三方`TWRP Recovery`镜像包，例如，openrecovery-twrp-2.8.7.1-hammerhead.img

### 方法1：flash `rooted` boot.img

进行root操作，最便捷方式的便是刷入已经root过的`boot.img`对原有`boot`区域进行擦写覆盖。
对于Nexus设备，可以在[`CF-Auto-Root Repository`](https://autoroot.chainfire.eu/)网站上下载对应设备型号的镜像文件，该镜像中包含了`SuperSU`程序。

在`flash`操作前，先将设备切换至`fastboot`模式。

~~~bash
$ adb reboot bootloader
~~~

在`fastboot`模式下，在电脑的命令终端中执行如下命令。

~~~bash
$ fastboot flash boot CF-Auto-Root-hammerhead-hammerhead-nexus5.img
sending 'boot' (9222 KB)...
OKAY [  0.525s]
writing 'boot'...
OKAY [  0.787s]
finished. total time: 1.313s

$ fastboot reboot
rebooting...

finished. total time: 0.511s
~~~

采用`fastboot flash boot XXX_boot.img`进行操作时，手机会将`XXX_boot.img`下载至设备并对`boot`区域进行擦写覆盖，从而使手机获得root权限。即使手机再次重启，root权限仍然存在。

再次通过`adb shell`连接至手机，可以看见，现在已经获取到了`root`权限。

~~~bash
$ adb shell
root@hammerhead:/ #
~~~

### 方法2、在`Recovery`环境下安装`SuperSU`

该种方法的实现思路在于，给手机安装`Custom Recovery`，然后在`recovery`模式下手工安装`SuperSU`。

具体的操作方式在《[详解Recovery]({% post_url 2015-07-04-Android开发环境配置2：详解Recovery %})》一文中进行了介绍。

### 方法3、采用`TWRP Recovery`的OpenRecoveryScript引擎执行命令

对于`2.1`及以上版本的`TWRP Recovery`中，可以使用`OpenRecoveryScript`引擎，在`TWRP Recovery`启动时执行命令。

#### 1、传输root文件至Android设备

在Android设备未获得root权限之前，具有Write权限的文件夹并不多，通常可将要写入的文件传输至`/data/local/tmp/`路径下。

~~~bash
$ adb push UPDATE-SuperSU-v2.46.zip /data/local/tmp/UPDATE-SuperSU-v2.46.zip
$ adb push busybox-signed.zip /data/local/tmp/busybox-signed.zip
~~~

#### 2、获取临时root权限

由于后续操作中要向`/cache/recovery/`目录写入文件，需要用到root权限。针对这种情况，可以采用已经root过的boot.img进行启动，临时获得root权限。

首先，将设备切换至`fastboot`模式

~~~bash
$ adb reboot bootloader
~~~

然后，采用已经root过的boot.img进行启动。

~~~bash
$ fastboot boot modified_boot_hammerhead_4.4.4_KTU84P.img
downloading 'boot.img'...
OKAY [  0.463s]
booting...
OKAY [  0.110s]
finished. total time: 0.573s
~~~

此处与方法1的区别在于，这里只是临时地采用已经root过的boot.img进行启动，但并没有对`boot`分区进行写入。当手机重启后，仍然是采用原有的`kernel`进行启动。

#### 3、创建`openrecoveryscript`文件

~~~bash
$ touch openrecoveryscript
~~~

在`openrecoveryscript`文件中，写入如下内容。其中，`zip`软件包的路径要求是存在于Android设备中的完整路径。

~~~vim
# openrecoveryscript
set tw_signed_zip_verify 0
install /data/local/tmp/perm-recovery-signed.zip
install /data/local/tmp/UPDATE-SuperSU-v2.46.zip
install /data/local/tmp/busybox-signed.zip
~~~

#### 4、写入`openrecoveryscript`文件

此处就是需要临时用到root权限的地方。

~~~bash
$ adb push openrecoveryscript /cache/recovery/openrecoveryscript
2 KB/s (169 bytes in 0.057s)
~~~

如果没有root权限，写入文件时会提示`Permission denied`。

~~~bash
$ adb push openrecoveryscript /cache/recovery/openrecoveryscript
failed to copy 'openrecoveryscript' to '/cache/recovery/openrecoveryscript': Permission denied
~~~

#### 5、启动`TWRP Recovery`环境

启动`TWRP Recovery`时，会执行`/cache/recovery/openrecoveryscript`文件中的命令，即安装`SuperSU`等root软件。

如果手机之前并未安装`TWRP Recovery`，也可以直接采用`TWRP Recovery`的镜像包进行启动，同样可以完成`/cache/recovery/openrecoveryscript`文件中命令的执行。

~~~bash
fastboot boot openrecovery-twrp-2.8.7.1-hammerhead.img
~~~
