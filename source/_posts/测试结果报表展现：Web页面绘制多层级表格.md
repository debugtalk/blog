---
title: 测试结果报表展现：Web页面绘制多层级表格
permalink: post/render-multi-level-table-in-webpage
date: 2016/03/20
categories:
  - Development
  - 前端
tags:
  - Javascript
---

## 背景描述
在Android性能测试中，每一个测试任务都对应了1个测试用例、1台测试设备、一个测试包，并且在测试结果中包含了多个指标项。通常，我们希望能对两个不同版本测试包的测试结果进行对比，并能在Web页面上以表格的形式进行展现。

很自然地，我们会想到采用如下形式展现对比结果。

![render table three levels](/images/render_table_three_levels.png)
图1 三层表格

对应地，采用如下数据结构存储结果数据。

~~~json
data_hash = {
  "pkg_array": ["pkg1", "pkg2"],
  "data": {
    "testcase1": {
      "device1": {
        "indicator1": ["value1", "value2"],
        "indicator2": ["value3", "value4"],
      },
      "device2": {
        "indicator1": ["value5", "value6"],
        "indicator2": ["value7", "value8"],
      },
    },
    "testcase2": {
      "device1": {
        "indicator1": ["value9", "value10"],
        "indicator2": ["value11", "value12"],
      },
      "device2": {
        "indicator1": ["value13", "value14"],
        "indicator2": ["value15", "value16"],
      },
    },
  }
}
~~~

想法明确了，那要怎么实现呢？

对于像我这样没学过前端的人来说，最难的就是如何通过代码绘制层级表格的问题。

## 第一次尝试：绘制2层表格

为了简化问题分析过程，先尝试对两层表格进行绘制。

![render table two levels](/images/render_table_two_levels.png)
图2 两层表格

简化后的数据结构如下：

~~~json
two_level_data_hash = {
  "pkg_array": ["pkg1", "pkg2"],
  "data": {
    "device1": {
      "indicator1": ["value1", "value2"],
      "indicator2": ["value3", "value4"],
    },
    "device2": {
      "indicator1": ["value5", "value6"],
      "indicator2": ["value7", "value8"],
    },
  }
}
~~~

如上表格对应的html代码如下。

~~~html
<table border="1">
<tr>
  <th>Device</th>
  <th>Indicator</th>
  <th>Pkg1</th>
  <th>Pkg2</th>
</tr>
<tr>
  <td rowspan="2">device1</td>
  <td>indicator1</td>
  <td>value1</td>
  <td>value2</td>
</tr>
<tr>
  <td>indicator2</td>
  <td>value3</td>
  <td>value4</td>
</tr>
</table>
~~~

可以看出，绘制层级表格的关键在于`tr`和`rowspan`的控制上。
因此，我们可以尝试采用如下JavaScript代码进行生成。

~~~js
function render_two_level_table(two_level_data_hash){
  pkg_array = two_level_data_hash["pkg_array"];
  table_header = "<tr>";
  table_header += "<th>Device</th><th colspan='1'>Indicator</th>";
  for(var pkg_index in pkg_array){
    table_header += "<th>" + pkg_array[pkg_index] + "</th>"
  }
  table_header += "</tr>";

  data = two_level_data_hash["data"];
  table_body = "";
  for(var device in data){
    is_first_indicator_row = true;
    table_body += "<tr><td rowspan='" + data[device].length + "'>" + device + "</td>";

    for(var indicator in data[device]){
      if(!is_first_indicator_row){
        table_body += "<tr>";
      }
      table_body += "<td>" + indicator + "</td>";
      value_list = data[device][indicator];
      for(var index in value_list){
        table_body += "<td>" + value_list[index] + "</td>";
      }
      table_body += "</tr>";
      is_first_indicator_row = false;
    }
    table_body += "</tr>";
  }

  table_content = "<table border='1'>" + table_header + table_body + "</table>";
  $("#table").html(table_content);
}
~~~

在绘制indicator单元格的时候，为了判断当前indicator是否是当前device对应的第一个，即是否需要添加`<tr>`格式符，我们引入了`is_first_indicator_row`变量；`is_first_indicator_row`初始为true，绘制完第一个indicator以后变为false；绘制当前device剩余indicator的时候，由于`is_first_indicator_row`为false，因此每次都会加上`<tr>`格式符。

在判断device单元格的行跨度(`rowspan`)时，由于indicator是device的key，因此我们可以通过当前device中key的数量来得到`rowspan`，即`two_level_data_hash[device].length`。

绘制下一个device对应的数据时，再重复以上流程。

可以看出，为了正确打印`<tr>`格式符，我们做了不少工作。两层表格的绘制方法解决了，那如何绘制三层表格呢？

## 第二次尝试：绘制3层表格

回到背景描述里面的需求，若按照上面的思路，我们要绘制三层表格时，就需要引入两个变量，`is_first_device_row`和`is_first_indicator_row`，分别用于标记device和indicator是否第一次出现。

那对于`rowspan`呢？这貌似就有点麻烦了。因为我们在绘制testcase单元格的时候，`rowspan`的取值应该是当前testcase包含的所有device各自包含的indicator的数量总和，而我们并不能像之前的方式那样直接得到这个数值。

那要怎么处理呢？我们可以尝试写一个函数`row_num`，来计算得到给定JSON数据里面包含的子节点的总数。

实现方式如下：

~~~js
function render_three_level_table(data_hash){
  pkg_array = data_hash["pkg_array"];
  table_header = "<tr>";
  table_header += "<th>TestCase</th><th>Device</th><th colspan='1'>Indicator</th>";
  for(var pkg_index in pkg_array){
    table_header += "<th>" + pkg_array[pkg_index] + "</th>";
  }
  table_header += "</tr>";

  data = data_hash["data"];
  table_body = "";
  for(var testcase in data){
    is_first_row_device = true;
    table_body += "<tr><td rowspan='" + row_num(data[testcase]) + "'>" + testcase + "</td>";

    for(var device in data[testcase]){
      if(!is_first_row_device){
        table_body += "<tr>";
      }
      table_body += "<td rowspan='" + row_num(data[testcase][device]) + "'>" + device + "</td>";

      is_first_row_indicator = true;
      for(var indicator in data[testcase][device]){
        if(!is_first_row_indicator){
          table_body += "<tr>";
        }
        table_body += "<td>" + indicator + "</td>";

        value_list = data[testcase][device][indicator];
        for(var index in value_list){
          table_body += "<td>" + value_list[index] + "</td>";
        }
        table_body += "</tr>";
      }
      table_body += "</tr>";
      is_first_row_indicator = false;
    }
    table_body += "</tr>";
    is_first_row_device = false;
  }

  table_content = "<table border='1'>" + table_header + table_body + "</table>";
  $("#table").html(table_content);
}

function row_num(data){
  var counter = 0;
  if(data.constructor == Array){
    return 1;
  }

  for(key in data){
    var tmp = data[key];
    if(tmp.constructor == Array)
    {
      counter += 1;
    }else{
      counter += row_num(tmp);
    }
  }
  return counter;
}
~~~

在计算`rowspan`时，我们用到了递归的方法，实现了对当前testcase或当前device所对应的indicator总数的计算。

通过以上方式，我们实现了三层表格的绘制。可以看出，三层表格的判断逻辑比两层表格复杂了很多，那如果我们还想绘制更多层次的表格呢？显然，这种方法已不再适用，我们不可能每增加一层就新增加一个标识变量，而且对于数据层级不固定的情况，采用这种方式是完全无法实现自适应的。

## 重构：递归！

回顾上面的代码，我们不难发现，三层表格的代码相比于两层表格的代码，存在着不少重复，而且可以预见，如果我们采用同样的方式去绘制更多层次表格的话，重复的代码会出现得更多。

一定有更简洁的方法！对，递归！

其实刚才我们在计算`rowspan`时已经体会到了递归的好处，它可以自适应多层次的数据结构。我们也完全可以将这个思想应用到表格层级的绘制上面。

观察背景描述中的数据结构，不难发现，对比数据存储于Array中，而中间层的value都是Hash结构，因此，我们可以通过这个区别，编写递归调用方法。

~~~js
function render_table(data_hash){
  var res = "";
  for(var key in data_hash){
    var tmp = data_hash[key];
    if(tmp.constructor == Array)
    {
      res += "<tr><td rowspan='" + row_num(tmp)+ "'>" + key + "</td>";
      for(value_index in tmp){
        var value = tmp[value_index];
        res += "<td>" + value + "</td>";
      }
      res += "</tr>";
    }else{
      res += "<tr><td rowspan='" + row_num(tmp) + "'>" + key + "</td>" + "</tr>";
      res += render_table(tmp);
    }
  }
  return res;
}

function row_num(data){
  var counter = 1;
  if(data.constructor == Array){
    return counter;
  }

  for(key in data){
    var tmp = data[key];
    if(tmp.constructor == Array)
    {
      counter += 1;
    }else{
      counter += row_num(tmp);
    }
  }
  return counter;
}

table_body = "";
table_body += render_table(data_hash);
~~~

采用了递归的方式以后，我们就不用再关注表格的层级了，只要是传入数据的数据结构与背景描述里面的类似，那么就可以自动绘制出任意层级的表格。
