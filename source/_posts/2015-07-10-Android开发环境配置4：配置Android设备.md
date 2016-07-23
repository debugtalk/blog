---
title: Android开发环境配置4：配置Android设备
permalink: post/android-development-environment-device-configuration
tags: [Android, configuration]
---

对于用于持续集成性能测试（或者自动化测试）的Android设备，在刷机之后需要进行一些配置。不同的Android系统版本在设置上会有些差异，但基本上都应包含的设置项都类似，如下是以Nexus 5为例进行说明。

【Settings】->【About Phone】，连续点击7次【Build number】，开启开发者模式；  
【Settings】->【Developer options】，开启【stay awake】和【USB debugging】；  
【Settings】->【Security】，开启【Unknown sources】(Allow installation of apps from sources other than the Play Store)，因为实验室的包还未获得Play Store的签名，因此必须开启这个开关，才能正常安装开发包。  
【Settings】->【Security】，将【Screen lock】设置为None，防止设备出现锁屏的情况。  
【Settings】->【Display】，将【Sleep】设置为最长时限。  
【Settings】->【Display】，将【Auto-rotate screen】关闭，因为某些测试场景时会用到屏幕分辨率。
