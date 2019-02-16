---
title: Android开发环境配置0：adb和fastboot
permalink: post/android-development-environment-adb-and-fastboot
date: 2015/07/02
tags: [Android, adb, fastboot, 环境搭建]
---

## 1、安装adb和fastboot

在对Android进行调试时，常用的工具有adb和fastboot。

### Install Android SDK

adb和fastboot包含在Android SDK的`Platform-tools package`里面，安装Android SDK后也就具备了adb和fastboot工具。

下载并安装[Android SDK tools](https://developer.android.com/sdk/index.html#Other)，打开`SDK Manager`并安装`Android SDK Platform-tools package`。

安装完成后，adb和fastboot的存放路径为`<path-to-sdk>/platform-tools`。为了方便后续使用，可对其配置环境变量。

`vim ~/.bashrc`:

~~~bash
if [ -d "<path-to-sdk>/platform-tools" ] ; then
  export PATH="<path-to-sdk>/platform-tools:$PATH"
fi
~~~

### Install from the command line

如果只是使用adb和fastboot工具，而不想安装完整的`Android SDK`，可以采用如下方式单独进行安装。

for debian-based Linux distributions:

~~~bash
$ sudo apt-get install android-tools-adb
$ sudo apt-get install android-tools-fastboot
~~~

for rpm-based Linux distributions(Fedora/Centos/RHEL):
~~~bash
$ sudo yum install android-tools
~~~

在`Mac OS X`中，可以采用`homebrew`进行安装：

~~~bash
$ brew install android-platform-tools
~~~

## 2、开启USB调试模式（USB debugging）

对手机进行unlock或root操作需要开启手机的USB调试模式，该设置在手机设置菜单的开发者选项（Developer Options）里面。
对于`3.2`及以前的Android版本，开发者选项的设置位置为：`Settings > Applications > Development`；
对于`4.0`及以上的Android版本，开发者选项的设置位置为：`Setting -> Developer Options`；需要注意的是，对于`4.2`及以上的Android版本，开发者选项默认是隐藏的，开启方式为：进入`Setting -> About Phone`，连续点击7次`Build number`。

进入开发者选项设置页面，开启开发者选项，并勾选USB调试模式。

## 3、建立手机与电脑之间的USB调试连接
对于Windows/Mac OSX的开发环境，安装好adb的USB驱动即可。
对于Linux（Debian based）系统的开发环境，若要使用adb或者fastboot工具对手机进行USB调试，则需要配置`udev`规则。

### 创建并配置`51-android.rules`文件
创建`51-android.rules`文件，并设置Read权限。

~~~bash
$ sudo touch /etc/udev/rules.d/51-android.rules
$ sudo chmod a+r /etc/udev/rules.d/51-android.rules
$ sudo vim /etc/udev/rules.d/51-android.rules
~~~

在`51-android.rules`文件中，按照如下格式进行配置。

~~~vim
#HTC
SUBSYSTEM=="usb", ATTR{idVendor}=="0bb4", MODE="0664", GROUP="plugdev"
~~~

在该配置文件中：
- `ATTR{idVendor}`：设备厂商的编号，每个厂商都有专属的唯一编号，例如HTC的venderID为`0bb4`
- `MODE`：指定了对该类设备的操作权限，通常设置为`0664`
- `GROUP`：指定了该类设备的用户组，通常设置为`plugdev`

对于venderID，可以在此处查看到主流厂商的编号：[all vendors listed by Google](http://developer.android.com/tools/device.html#VendorIds)
除此之外，也可以将手机通过USB连接至电脑，采用`lsusb`命令进行查看。该命令会列出连接至电脑的所有设备，`ID`属性值即为设备厂商的venderID。例如，在如下命令执行返回结果中可以看到，HTC的venderID为`0bb4`

~~~bash
$ lsusb
Bus 002 Device 001: ID 1d6b:0003 Linux Foundation 3.0 root hub
Bus 001 Device 004: ID 0e0f:0002 VMware, Inc. Virtual USB Hub
Bus 001 Device 003: ID 0e0f:0002 VMware, Inc. Virtual USB Hub
Bus 001 Device 033: ID 0bb4:0cd6 HTC (High Tech Computer Corp.)
Bus 001 Device 002: ID 0e0f:0003 VMware, Inc. Virtual Mouse
Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 003 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
Bus 004 Device 002: ID 0e0f:0002 VMware, Inc. Virtual USB Hub
Bus 004 Device 001: ID 1d6b:0001 Linux Foundation 1.1 root hub
~~~

对`udev`配置完成后还不能即时生效，需要重启系统，或者重启`udev`才能使其生效。

~~~bash
$ sudo /etc/init.d/udev restart
~~~

或者

~~~bash
$ sudo sh -c "(udevadm control --reload-rules && udevadm trigger --action=change)"
~~~

再次将手机通过USB连接至电脑后，系统便能检测到设备。

### 配置用户组
如果当前登录用户不在`plugdev`用户组内，采用adb或者fastboot工具进行调试的时候需要`sudo`权限。为了避免每次都这么麻烦，可以将当前登录用户添加至`plugdev`用户组。

~~~bash
leo@debian8:~$ groups
leo cdrom floppy audio dip video netdev scanner lpadmin    # 可以看出，当前用户leo并不在用户组plugdev里面
leo@debian8:~$ sudo gpasswd -a username plugdev            # 将用户leo添加至用户组plugdev
leo@debian8:~$ groups
leo cdrom floppy audio dip video plugdev netdev scanner lpadmin    # 用户leo已属于用户组plugdev
~~~

### RSA指纹密钥认证

对于`4.2.2`及以上的Android版本，将手机开启USB调试模式并连接至电脑以后，手机屏幕上会出现电脑的RSA指纹密钥验证确认请求，这是Android的一套安全机制，只有点击确认以后才能从电脑上通过adb命令与手机建立调试连接。通常，勾选【Always allow from this computer】并点击确认后，手机便与电脑建立了认证连接，之后即可在电脑上采用`adb`、`fastboot`工具对手机进行操作。

~~~bash
$ adb devices
List of devices attached
HT259W103035	unauthorized    # 若为进行RSA指纹密钥验证确认，则会出现unauthorized提示

$ adb devices
List of devices attached
HT259W103035	device          # 显示device，则说明已经建立了调试连接
~~~

需要说明的是，对于`4.2.2`及以上的Android版本，adb版本要求`1.0.31`及以上，对应的Android SDK的版本要求为`r16.0.1`及以上。
