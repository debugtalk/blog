---
title: LoadRuner 中的参数与变量
permalink: post/loadrunner-parameter-variable
date: 2013/08/12
categories:
  - Testing
  - 性能测试
tags:
  - LoadRunner
---

在LoadRunner脚本开发中，经常会遇到参数与变量相互转换的情况，本文对常见的转换情形进行了方法总结。

## 变量的赋值
```C
//将字符串赋值给变量
char strTemp[30];
strcpy(strTemp, "Hello World!!");

//错误的字符串赋值方式
strTemp = "Hello World!!";
/* 注：
 * 在LR中若直接将字符串赋值给变量，编译时将会报错
 * 报错信息：operands of = have illegal types `char' and `pointer to char'
 */

//将数值赋值给变量
int x = 10;
/* 注：
 * 在LR中，变量的声明一定要放在脚本的最前面，且声明的语句中不要有其他的脚本代码
 * 若将以上申明放置在脚本中部，将会产生如下形式的报错信息
 * illegal statement termination
 * skipping 'int'
 * undeclared identifier 'x'
 */
```

## 参数的赋值
```C
//将字符串赋值给参数
lr_save_string("Hello World!!","paraStr");

//将变量中的值赋值给参数
char strTemp[30];
strcpy(strTemp, "Hello World") ;
lr_save_string(strTemp, "paraStr");

//将数值直接赋值给参数
lr_save_int(123, "paraNum");

//将变量中的数值赋值给参数
int num = 10;
lr_save_int(num*2, "paraNum");
```

## 参数的取值
```C
//从参数中进行取值，不管参数是字符串还是数值
lr_eval_string("{paraStr}");
lr_eval_string("{paraNum}");
//取出的值均为字符串类型，因此输出时格式需为"%s"
lr_output_message("%s", lr_eval_string("{paraNum}"));
```

## 参数=>变量
```C
//将参数转换为字符串变量，参数paraStr中的值为"Hello World!!"
char strTemp[30];
strcpy(strTemp, lr_eval_string("{paraStr}"));
lr_output_message("%s", strTemp);

//将参数转换为数值变量，参数paraNum中的值为"246"
int num;
num = atoi(lr_eval_string("{paraNum}"));    //将字符串转换为数值
lr_output_message("%d", num);

//将参数格式化输出到变量
SeatPrefListCount = atoi( lr_eval_string("{SeatPrefList_count}") );
sprintf(varRandomSeatPref, "{SeatPrefList_%d}", 1+rand()%SeatPrefListCount);
//将格式化的随机日期写入变量varRandomDepartDate
sprintf(varRandomDepartDate, "%d/%d/%d", 1+rand()%12, 1+rand()%28, 2009+rand()%6);
```

## 参数=>参数
```C
//参数的复制：将参数paraStr_1的值复制到参数paraStr_2
lr_save_string(lr_eval_string("{paraStr_1}"),"paraStr_2");
```
