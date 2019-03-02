---
title: Android开发环境配置1：详解Bootloader
permalink: post/android-development-environment-bootloader
date: 2015/07/03
categories:
  - 环境搭建
tags:
  - Android
---

在刚接触Android开发时，通常需要对设备进行root操作，而在root之前，必须要做的一步就是先对设备的Bootloader进行解锁。那么什么是Bootloader？为什么必须要对Bootloader进行解锁？如何对Bootloader进行解锁？本文便围绕着几个问题展开进行介绍。


## About Bootloader

顾名思义，Bootloader是操作系统在启动之前需要执行的一段小程序。通过这段小程序，我们可以初始化硬件设备、建立内存空间的映射表，从而建立适当的系统软硬件环境，为最终调用操作系统内核做好准备。

虽然Android系统是开源的，但是设备制造商为了保证系统的稳定性，以及维护自身某些方面的利益，并不希望用户更换为其它厂商的ROM。因此，通常各家设备制造商都会对Bootloader进行加锁。在设备Bootloader处于锁定状态时，无法对ROM进行更改，不能进行root操作，也无法刷机为别的ROM。而要解除这些限制，就需要对Bootloader进行解锁。


## How to Unlock Bootloader
不同机型以及不同Android版本的Bootloader的解锁方式略有不同，但基本思路和步骤都是类似的。

本文以设备机型Nexus 5、ROM版本4.4.4为例，讲解解锁Bootloader的具体步骤；PC机的操作系统为Linux（Debian）。


### 1、准备工作（Prerequisites）

- 配置Android调试环境：安装adb和fastboot工具，开启USB调试模式（USB debugging），建立手机与电脑之间的USB调试连接。
- 数据备份：需要注意的是，bootloader解锁操作会将手机恢复至出厂设置，并清空所有用户数据。因此，在解锁前需要进行必要的数据备份。

### 2、将手机切换至`fastboot`模式

不管是要查看Bootloader是否锁定，还是要对Bootloader进行解锁、锁定操作，均需要将手机切换至`fastboot`模式。切换至`fastboot`模式可以采用如下两种方式中的任意一种。

- 采用`adb`命令：将手机开机后连接至电脑，在命令终端中输入`adb reboot bootloader`。
- 开机时采用组合按键：将手机关机，同时按住组合按键数秒；不同机型的组合按键略有不同，Nexus 5的组合按键为`Volume Down`和`Power`。

进入到`fastboot`模式后，可以看到如下信息。

~~~
FASTBOOT MODE
PRODUCT_NAME - hammerhead
VARIANT - hammerhead D821(E) 16GB
HW VERSION - rev_11
BOOTLOADER VERSION - HHZ11k
BASEBAND VERSION - M897aA-2.0.50.1.16
CARRIER INFO - None
SERIAL NUMBER - 03f7fc7ad0081a10
SIGNING - production
SECURE BOOT - enabled
LOCK STATE - locked
~~~

在`LOCK STATE`一项中，可以看到手机当前处于锁定（locked）状态，若需要进行`root`操作，则必须先进行解锁（unlock）。如果手机已经处于解锁（unlocked）状态了，则不用再进行`unlock`操作。

### 3、对锁定（locked）设备进行解锁（unlock）操作

解锁操作需要将手机通过USB数据线与电脑连接，在电脑的命令终端中通过`fastboot`工具命令进行解锁操作。

首先，保持手机与电脑的USB连接，在命令终端中查看手机在`fastboot`模式下与电脑的连接状态。若连接正常，则可以看到如下信息。

~~~bash
$ fastboot devices
03f7fc7ad0081a10	fastboot
~~~

然后，在电脑的命令终端中输入如下命令。在手机上会显示`Unblock bootloader?`警告提示信息，用手机的音量键选择`Yes`后，按下手机的电源键进行确认。接下来手机便会进行unlock操作。

~~~bash
$ fastboot oem unlock
...
OKAY [ 14.907s]
finished. total time: 14.907s
~~~

出现如上响应信息后，则表明手机已经解锁成功。在手机屏幕上，也可以看到`fastboot`模式页面中，`LOCK STATE`的属性值已经变为`unlocked`。

~~~bash
$ fastboot reboot
~~~

手机unlock完成后，会恢复到出厂设置，`USB调试模式`设置也已失效，需要重新进行设置。
