---
title: SQL语句中关于NULL的那些坑
permalink: post/traps-in-sql-null
date: 2016/04/25
categories:
  - Development
tags:
  - SQL
---

## 问题描述

今天在跟进公司内部测试平台线上问题的时候，发现一个忽略已久的问题。

为了简化问题描述，将其进行了抽象。

有一张数据表`qms_branch`，里面包含了一批形式如下所示的数据：

id | name | types
--- | --- | ---
1 | dashboard_trunk | dashboard
2 | monkey_trunk | monkey
3 | dashboard_projects_10_9_9 | dashboard
4 | performance_trunk |
5 | performance_projects_10_9_8 | performance

在系统的某个页面中，需要展示出所有`dashboard`类型以外的分支，于是就采用如下方式进行查询（Rails）。

~~~ruby
branches = Qms::Branch.where("types!='dashboard'")
~~~

这个方式有问题么？

之前我是觉得没什么问题。但是在代码上线后，实际使用时发现部分分支没有加载出来，这就包括了`performance_trunk`分支。

然后就是问题定位，到MySQL的控制台采用SQL语句进行查询：

~~~sql
SELECT * FROM qms_branch WHERE types != 'dashboard'
~~~

发现在查询结果中的确没有包含`performance_trunk`分支。

这是什么原因呢？为什么在第4条数据中，`types`属性的值明明就不是`dashboard`，但是采用`types!='dashboard'`就无法查询得到结果呢？

## 原因追溯

查看数据表`qms_branch`的结构，看到`types`字段的属性为：`DEFAULT NULL`。

经过查询资料，在[w3schools](http://www.w3schools.com/sql/sql_null_values.asp)上找到了答案。

> - NULL is used as a placeholder for unknown or inapplicable values, it is treated differently from other values.
> - It is not possible to test for NULL values with comparison operators, such as =, <, or <>. We will have to use the IS NULL and IS NOT NULL operators instead.

也就是说，在SQL中，`NULL`并不能采用`!=`与数值进行比较，若要进行比较，我们只能采用`IS NULL`或`IS NOT NULL`。

于是，我们将SQL语句改为如下形式：

~~~sql
SELECT * FROM qms_branch WHERE types IS NULL or types != 'dashboard'
~~~

再次查询时，结果集就包含`performance_trunk`分支了。

## 问题延伸

通过上面例子，我们知道在对NULL进行判断处理时，只能采用`IS NULL`或`IS NOT NULL`，而不能采用`=, <, <>, !=`这些操作符。

那除此之外，还有别的可能存在的坑么？

再看一个例子：

有一张数据表`table_foo`，其中有一个字段`value_field`，我们想从这张表中筛选出所有`value_field`为'value1'，'value2'或NULL的记录。

那么，我们采用`IN`操作符，通过如下SQL语句进行查询。

~~~sql
SELECT * FROM table_foo WHERE value_field IN ('value1', 'value2', NULL)
~~~

这会存在问题么？我们并没有采用`=, <, <>, !=`对NULL进行比较哦。

答案是同样存在问题！

因为在SQL中，`IN`语句会被转换为多个`=`语句。例如，上面例子中的SQL在执行时就会被转换为如下SQL语句：

~~~sql
SELECT * FROM table_foo WHERE value_field = 'value1' OR value_field = 'value2' OR value_field = NULL
~~~

而这个时候，执行`value_field = NULL`时就会出现问题了。

正确的做法应该是将`NULL`相关的判断独立出来，如下SQL才是正确的写法。

~~~sql
SELECT * FROM table_foo WHERE value_field IN ('value1', 'value2') OR value_field IS NULL
~~~
