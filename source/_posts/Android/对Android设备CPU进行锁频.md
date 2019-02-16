---
title: 对Android设备CPU进行锁频
permalink: post/Android-CPU-lock-frequency
date: 2016/04/18
tags: [Android, CPU]
---

本文对Android设备CPU的状态查看方法和锁频（lock frequency）方法进行详细介绍。这有什么用？作为测试工程师，你值得了解。

## CPU频率

首先说下CPU的频率。我们都知道，CPU的工作频率越高，运算就越快，但能耗也更高。然而很多时候，设备并不需要那么高的计算性能，这个时候，我们就希望能降低CPU的工作频率，追求较低的能耗，以此实现更长的待机时间。

基于此需求，当前电子设备的CPU都会存在多个工作频率，并能根据实际场景进行CPU频率的自动切换，以此达到平衡计算性能与能耗的目的。

## 锁频的用途

那么为什么需要锁频呢？

对于普通用户来说，可能对这些场景比较熟悉：

- 在家用笔记本电脑玩游戏的时候，电脑连着电源，不在乎能耗，只想要尽可能高的性能，这个时候就选择高性能模式，即保持CPU在最高频率工作。
- 旅行途中使用笔记本电脑，靠电池供电，希望电脑能待机尽可能久，这时就选择省电模式，即CPU保持在最低频率运行。

作为一名测试工程师，我们在进行软件测试的时候，为了让测试结果真实反映软件本身的效率，从控制变量法的角度，我们希望测试结果尽量不受到硬件本身的影响。这个时候，我们就可以尝试对设备的CPU进行锁频，即保证在测试的过程中，硬件设备的CPU运行在一个恒定的频率。

说到这里先埋个伏笔，在chromium官方测试库中，部分测试场景在初始化测试环境时，就会将设备所有CPU的频率调到最高状态，后续我会单独以一篇博客的形式对那部分的源码进行分析。对于等不及的朋友，可以先去看下源码，源码路径为`pylib/perf/PerfControl.SetHighPerfMode`。

## 查看CPU状态信息

在修改CPU的状态之前，我们需要先查看CPU的属性和状态信息，这样才能有针对性地进行正确的设置。

对于CPU的状态，我们通常会关注两类信息，一是整体层面的，即CPU运行的核数；二是细节层面的，即各个CPU的工作状态，包括所处工作模式、频率大小等。

在Android系统中，CPU相关的信息存储在`/sys/devices/system/cpu`目录的文件中，我们可以通过读取该目录下的特定文件获得当前设备的CPU状态信息，也可以通过对该目录下的特定文件进行写值，实现对CPU频率等状态信息的更改。

本文以`Nexus 5`（系统版本5.1.1）为例，后面的例子均以该设备为例。不同的机型和Android系统版本可能会存在一些差异，请知悉。

在`/sys/devices/system/cpu`目录中，文件结构如下所示。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ ll
drwxr-xr-x root     root              2016-01-20 01:36 cpu0
drwxr-xr-x root     root              2016-01-20 21:06 cpu1
drwxr-xr-x root     root              2016-01-20 21:07 cpu2
drwxr-xr-x root     root              2016-01-20 21:07 cpu3
-rw------- root     root         4096 1970-01-17 10:27 cpuctl
drwxr-xr-x root     root              1970-01-17 10:27 cpufreq
drwxr-xr-x root     root              1970-01-17 10:27 cpuidle
-r--r--r-- root     root         4096 1970-01-17 10:27 kernel_max
-r--r--r-- root     root         4096 1970-01-17 10:27 offline
-r--r--r-- root     root         4096 1970-01-17 10:27 online
-r--r--r-- root     root         4096 1970-01-17 10:27 possible
drwxr-xr-x root     root              1970-01-17 10:27 power
-r--r--r-- root     root         4096 1970-01-17 10:27 present
-rw-r--r-- root     root         4096 1970-01-17 10:27 uevent
~~~

### 1、view overall cpu info

在`possible`文件中，存储的是当前设备可用的CPU，显示形式以数字的形式。例如`0-3`代表的就是当前设备总共有4个核，编号分别为0，1，2，3。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ cat possible
0-3
~~~

在`online`文件中，存储的是当前设备正在运行的CPU。因为有时候设备不需要很高的性能，就可以将部分CPU关闭。不过需要注意的是，不管什么时候，`CPU0`始终都会处于运行状态。`online`文件的存储格式与`possible`类似，如果只有部分CPU运行，且CPU编号不连续的时候，会以逗号进行隔开；例如，`0,2`表示当前CPU0和CPU2处于运行状态。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ cat online
0,2
~~~

对应的，`offline`文件标示的是当前设备处于关闭状态的CPU，这和`online`作为互补，并集刚好就是设备的所有CPU，即`possible`文件中的内容。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ cat offline
1,3
~~~

### 2、view specified cpu info

接下来，我们要获取到特定CPU的信息，就需要进入到对应的文件夹，例如，`cpu0/`对应的就是CPU0的信息。

在`/sys/devices/system/cpu/cpu0`目录中，文件结构如下所示。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ ll cpu0
drwxr-xr-x root     root              2016-01-20 01:37 cpufreq
drwxr-xr-x root     root              1970-01-17 10:27 cpuidle
-r-------- root     root         4096 1970-01-17 10:27 crash_notes
-rw-r--r-- root     root         4096 2016-01-20 01:36 online
drwxr-xr-x root     root              1970-01-17 10:27 power
drwxr-xr-x root     root              1970-01-17 10:27 rq-stats
lrwxrwxrwx root     root              1970-01-17 10:27 subsystem
drwxr-xr-x root     root              1970-01-17 10:27 topology
-rw-r--r-- root     root         4096 1970-01-17 10:27 uevent
~~~

其中，`online`文件的内容表示当前CPU是否处于运行状态，若处于运行状态，则内容为1，否则为0；这个和上面讲到的`/sys/devices/system/cpu/online`能进行对应。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ cat cpu0/online
1
~~~

在`cpu0/cpufreq/`目录下，存储的就是与CPU0的频率相关的信息，文件结构如下所示。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ ll cpu0/cpufreq/
-rw-r--r-- root     root         4096 2016-01-20 01:57 UV_mV_table
-r--r--r-- root     root         4096 2016-01-20 01:57 affected_cpus
-r--r--r-- root     root         4096 2016-01-20 01:57 cpu_utilization
-r-------- root     root         4096 2016-01-20 01:57 cpuinfo_cur_freq
-r--r--r-- root     root         4096 2016-01-20 02:00 cpuinfo_max_freq
-r--r--r-- root     root         4096 2016-01-20 01:39 cpuinfo_min_freq
-r--r--r-- root     root         4096 2016-01-20 01:57 cpuinfo_transition_latency
-r--r--r-- root     root         4096 2016-01-20 01:57 related_cpus
-r--r--r-- root     root         4096 2016-01-20 01:39 scaling_available_frequencies
-r--r--r-- root     root         4096 2016-01-20 01:57 scaling_available_governors
-r--r--r-- root     root         4096 2016-01-20 01:50 scaling_cur_freq
-r--r--r-- root     root         4096 2016-01-20 01:57 scaling_driver
-rw-r--r-- root     root         4096 2016-01-20 01:50 scaling_governor
-rw-r--r-- root     root         4096 2016-01-20 08:29 scaling_max_freq
-rw-r--r-- root     root         4096 2016-01-20 08:29 scaling_min_freq
-rw-r--r-- root     root         4096 2016-01-20 02:52 scaling_setspeed
~~~

在这个目录中，我们需要关注的文件比较多。

首先是`scaling_available_governors`和`scaling_governor`。这里的`governor`大家可以理解为CPU的工作模式，`scaling_available_governors`中存储了当前CPU支持的所有工作模式，而`scaling_governor`存储的是CPU当前所处的工作模式。

~~~shell
shell@hammerhead:/sys/devices/system/cpu $ cat cpu0/cpufreq/scaling_available_governors
impulse dancedance smartmax interactive conservative ondemand userspace powersave Lionheart bioshock performance

shell@hammerhead:/sys/devices/system/cpu $ cat cpu0/cpufreq/scaling_governor
performance
~~~

可以看到，`Nexus 5`支持非常多的工作模式，这里只对几个常见的模式进行简单说明。

- performance：最高性能模式，即使系统负载非常低，cpu也在最高频率下运行。
- powersave：省电模式，与performance模式相反，cpu始终在最低频率下运行。
- ondemand：CPU频率跟随系统负载进行变化。
- userspace：可以简单理解为自定义模式，在该模式下可以对频率进行设定。

对于各种模式对应的含义和策略，在此不进行展开，大家有兴趣的可以自行搜索。

然后是CPU的工作频率范围，对应的文件有`cpuinfo_max_freq`、`cpuinfo_min_freq`、`scaling_max_freq`、`scaling_min_freq`。

以`cpuinfo_`为前缀的表示CPU硬件支持的频率范围，反映的是CPU自身的特性，与CPU的工作模式无关。而以`scaling_`为前缀的表示CPU在当前工作模式下的频率范围。

那么，当前CPU工作的频率是多少，我们要怎么查看呢？

查看`cpuinfo_cur_freq`或`scaling_cur_freq`即可。`cpuinfo_cur_freq`代表通过硬件实际上读到的频率值，而`scaling_cur_freq`则是软件当前的设置值，多数情况下这两个值是一致的，但是也有可能因为硬件的原因，有微小的差异。

~~~shell
root@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq # cat cpuinfo_cur_freq
1574400
root@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq # cat scaling_cur_freq
1574400
~~~

## 更改CPU状态信息

最后回到我们本文的主题，如何对CPU的频率进行设定呢？

这也和CPU信息查看对应，分为对CPU整体运行情况的设置，和对特定CPU工作模式的设定。

在此，有两点需要特别进行说明。

首先，对于高通的CPU，存在一个系统服务，叫作`mpdecision service`。当这个系统服务处于运行状态时，我们无法对CPU的状态信息进行更改。因此，如果我们要更改高通CPU的工作模式，第一步要做的就是终止`mpdecision`系统服务。

操作起来也很简单，在Android shell里面执行如下命令即可。

~~~shell
stop mpdecision
~~~

第二点需要注意的是，如果我们想要实现对特定CPU的工作状态进行设置，就必须将`scaling_governor`设置为`userspace`，只有这样，我们才能对`scaling_setspeed`进行设置。

~~~shell
root@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq # cat scaling_setspeed
<unsupported>

root@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq # echo userspace > scaling_governor
root@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq # cat scaling_setspeed
1574400
~~~

### 1、set overall cpu info

从宏观层面，我们可以对CPU运行的核数进行设置，即可实现对特定CPU的开启和关闭。当然，我们在前面已经说过，CPU0始终会处于运行状态，因此我们无法将CPU0进行关闭。

设置的方式很简单，就是往`/sys/devices/system/cpu/cpu[i]/online`文件中写值即可，写1时开启指定CPU，写0时关闭指定CPU。

~~~shell
# turn off cpu1
root@hammerhead:/sys/devices/system/cpu/cpu1 # echo 0 > online
root@hammerhead:/sys/devices/system/cpu/cpu1 # cat online
0
~~~

### 2、set specified cpu info

在对特定CPU的频率进行设定前，我们需要知道的是，CPU并不能工作在任意频率下，我们只能将CPU的频率设定为它支持的数值。

通过查看`scaling_available_frequencies`，我们可以获得当前CPU支持的频率值。

~~~shell
root@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq # cat scaling_available_frequencies
300000 422400 652800 729600 883200 960000 1036800 1190400 1267200 1497600 1574400 1728000 1958400 2265600
~~~

接下来，我们就可以对CPU的工作频率进行设置了。

如何进行设置呢？刚开始的时候，我觉得将特定的频率值写入`scaling_setspeed`或`scaling_cur_freq`就可以了，通过Google搜索得到的方法中也是这种方式。

但经过尝试，发现并不可行。为什么会这样？我也还没有找到答案，希望知道原因的朋友能告诉我。

最后经过尝试，发现通过同时将`scaling_max_freq`和`scaling_min_freq`设置为目标频率值，就可以成功地对CPU频率完成设置。

~~~shell
# before setting
shell@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq $ cat scaling_cur_freq
1574400

# setting
shell@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq $ echo 1728000 > scaling_min_freq
shell@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq $ echo 1728000 > scaling_max_freq

# after setting
shell@hammerhead:/sys/devices/system/cpu/cpu0/cpufreq $ cat scaling_cur_freq
1728000
~~~
