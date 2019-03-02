---
title: LoadRunner 中获取当前系统时间
permalink: post/loadrunner-get-system-time
date: 2013/10/28
categories:
  - Testing
  - 性能测试
tags:
  - LoadRunner
---

## 引言

在测试场景中，常会遇到需要提交系统时间的情况。本文对使用LoadRunner获取系统时间的几种方法进行探讨。

常用的方法有如下四种：

- 方法一：使用LR的参数化功能
- 方法二：使用LR函数lr_save_datetime()
- 方法三：使用C语言标准函数库中的time()和ctime()
- 方法四：使用C语言的tm结构，把时间分解成若干元素，再根据需求进行重组

## 方法一：使用LR的参数化功能

操作步骤：

1、在Parameter List窗口中新建一个参数localtime_now，Parameter type选择为【Date/Time】
2、设置Date/Time format，具体格式可参照帮助手册，例如%Y-%m-%d %H:%M:%S对应的是2013-10-28 16:43:06
3、在脚本中，利用函数lr_eval_string将参数localtime_now转换为变量tt_1
4、在脚本中引用变量tt_1

对应的脚本如下：

```C
char *tt_1;
tt_1 = lr_eval_string("{localtime_now}");
lr_message("系统当前的时间为：%s", tt_1);
```

运行结果：
系统当前的时间为：2013-10-28 16:43:06

## 方法二：使用LR函数lr_save_datetime()

在LoadRunner中，函数lr_save_datetime可以将当前时间赋值给指定参数，并可在赋值时选择时间样式。

```C
char *tt_2;
//获得当前系统时间，并根据设置的格式将当前时间赋值给 times
lr_save_datetime("%Y-%m-%d %H:%M:%S", DATE_NOW+TIME_NOW, "localtime_2");
tt_2 = lr_eval_string("{localtime_2}");
lr_message("系统当前的时间为：%s", tt_2);
```

运行结果：
系统当前的时间为：2013-10-28 17:43:16

## 方法三：使用C语言标准函数库中的time()和ctime()

对应的脚本如下：

```C
long tt_3;
time(&tt_3);
lr_message("系统当前的时间为：%s", ctime(&tt_3));
```

运行结果：
系统当前的时间为：Mon Oct 28 17:43:16 2013

## 方法四：tm结构分解

说明：tm结构即是一个结构体，将时间分解为9个部分，将时间的各个部分赋值给不同的变量，然后根据实际需求，将各个部分进行重组后使用。

对应的脚本如下：

```C
Action()
{
    struct tm {
        int second;   //取得当前秒数(在分钟后)；取值区间为[0,59]
        int minute;   //取得当前分钟数(在小时后)；取值区间为[0,59]
        int hour;     //取得当前小时数(从凌晨0点开始)；取值区间为[0,23]
        int day;      //取得当前天数(从上月结束开始)；取值区间为[1,31]
        int month;    //取得当前月份数(从1月开始)；取值区间为[0,11]
        int year;     //取得当前年份数(从1900年开始)
        int weekday;  //取得当前日期数(为了获取星期几，从上个星期日开始)；取值区间为[0,6]
        int yearday;  //取得当前年份天数(从1月1日开始)；取值区间为[0,365]
        int daylight; //取得当前夏令时标识符，实行夏令时的时候，daylight取得一个正数
        //不实行夏令时的进候，daylight为0；
        //不了解情况时，daylight为负数
    };

    long timenow;    //定义保存时间的变量
    struct tm *now;  //定义结构指针
    int year, month, day, weekday, hour, minute, second;
    char *week;
    time(&timenow);  //获取当前时间
    now = (struct tm *)localtime(&timenow);  //把当前时间的结构指针赋值给now
    year = now->year;
    month = now->month;
    day = now->day;
    hour = now->hour;   //获取hour值
    minute = now->minute; //获取minute值
    second = now->second; //获取second值
    weekday = now->weekday;//获取week值

    switch(weekday)//判断得到中文的星期
    {
        case 1:week ="星期一";
        break;
        case 2:week ="星期二";
        break;
        case 3:week ="星期三";
        break;
        case 4:week ="星期四";
        break;
        case 5:week ="星期五";
        break;
        case 6:week ="星期六";
        break;
        case 0:week ="星期日";
        break;
    };

    lr_message("使用tm结构获取的当前时间为：%d-%d-%d %s %d:%d:%d",year,month,day,week,hour,minute,second);

    return 0;
}
```

运行结果：
使用tm结构获取的当前时间为：113-9-28 星期一 17:43:16
