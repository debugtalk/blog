---
title: 性能指标--并发用户数（Concurrent Users）
permalink: post/performance-index-concurrent-users
date: 2013/07/31
categories:
  - Testing
  - 性能测试
tags:
  - 指标
---

**并发用户数**是指：在某一时间点，与被测目标系统同时进行交互的客户端用户的数量。

并发用户数有以下几种含义：

### 并发虚拟用户数（Concurrent Virtual Users，Users_CVU）
在使用专用的测试工具（如Loadrunner、Jmeter）时用于模拟客户端用户的进程或线程的数量；该参数是针对*客户端*（generator）而言的。

### 有效并发虚拟用户数（Effective Concurrent Virtual Users，Users_ECVU）
被评估目标系统实际感受到的等效于业务请求压力的无思考时间的并发用户数；该参数是针对被评估的*目标系统*（Target System）而言的。

如果使用测试工具对目标系统进行压力加载时设定了思考时间（Think Time），那么实际有效的并发虚拟用户数可使用如下公式计算得出：

Users_ECVU=Users_CVU*Time_ART/(Time_ART+Time_TotalThinkTime)

其中：

- Time_ART --- 目标系统实际运行时的平均响应时间
- Time_TotalThinkTime --- 虚拟用户执行一次该交易过程中使用的思考时间的总和

由此可见：

- 增加思考时间意味着减少对目标系统的业务请求压力；
- 当思考时间为零时，有效并发虚拟用户数与并发虚拟用户数相等。

### 内在并发用户数（Limited Concurrent Users，Users_LCU）

目标系统内部能够同时并行处理的客户端用户数。

该参数体现了目标系统的内在并发度，因此当对目标系统进行任何有效的优化和调整之后，其内在并发用户数即内在并发度就会发生变化，通常来讲是指改变目标系统的第一瓶颈后会发生变化。

当 Users_ECVU<=Users_LCU 时，目标系统可以真正地并行处理所有被加载用户的任务请求，此时交易的响应时间会相对保持不变，即交易的实际响应时间，也是交易在目标系统中处理的最快时长；

当 Users_ECVU>Users_LCU 时，目标系统会利用内部的请求调度机制将多出的请求进行排队并在所有的用户请求之间进行任务切换处理，外在表现就是被加载交易的响应时间开始延长。

### 并发在线用户数（Concurrent Online Users，Users_COU）

一般是指实际生产系统中已经和目标系统建立了会话连接的用户总数，并发在线用户数通常是指实际的客户端操作员的数量，是人工发起的业务会话的数量。

并发在线用户数产生的请求压力可以通过公式计算出目标系统感受到的实际业务请求压力，即有效并发虚拟用户数，公式如下：

Users_ECVU=Users_COU*Time_ART/Time_AverageIntervalRequestTime

其中：

- Time_ART --- 目标系统实际运行时的平均响应时间
- Time_AverageIntervalRequestTime --- 每个操作员用户发起该交易请求的平均间隔时间
