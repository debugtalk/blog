---
title: HttpRunner 的结果校验器优化
permalink: post/HttpRunner-validator-optimization
date: 2017/12/13
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在测试用例中，包含预期结果这么一项，用于辅助测试人员执行测试用例时判断系统的功能是否正常。而在自动化测试中，我们的目标是让测试用例自动执行，因此自动化测试用例中同样需要包含预期结果一项，只不过系统响应结果不再由人工来进行判断，而是交由测试工具或框架来实现。

这部分功能对应的就是测试结果校验器（validator），基本上能称得上自动化测试工具或框架的都包含该功能特性。

## 设计之初

`HttpRunner`在设计之初，结果校验器（validator）的实现比较简单。

对于每一个`test`，可以指定0个或多个校验项，放置在`validate`中。在自动化测试执行的时候，会在发起HTTP请求、解析结果响应之后，逐个检查各个校验项，若存在任意校验项不通过的情况，则该`test`将终止并被标记为失败。

```yaml
- test:
    name: get token
    request:
        url: http://127.0.0.1:5000/api/get-token
        method: GET
    extract:
        - token: content.token
    validate:
        - {"check": "status_code", "comparator": "eq", "expect": 200}
        - {"check": "content.token", "comparator": "len_eq", "expect": 16}
```

如上例所示，每一个校验项均为一个`json`结构，里面包含`check`、`expect`、`comparator`三个属性字段。其中，`check`对应着要检查的字段，`expect`对应着检查字段预期的值，这两项是必须指定的；`comparator`字段对应着比较方法，若不指定，则默认采用`eq`，即检查字段与预期值相等。

为了实现尽可能强大的检查功能，`check`属性值可通过链式操作精确指定具体的字段，`comparator`也内置实现了大量的检查功能。

举个例子可能会更清晰些。假如某结构的响应结果如下：

```json
// status code: 200

// response headers
{
   "Content-Type": "application/json"
}

// response body content
{
   "success": False,
   "person": {
       "name": {
           "first_name": "Leo",
           "last_name": "Lee",
       },
       "age": 29,
       "cities": ["Guangzhou", "Shenzhen"]
   }
}
```

那么假如我们要检查`status code`，`check`就可以指定为`status_code`；假如要检查`response headers`中的`Content-Type`，`check`就可以指定为`headers.content-type`；假如要检查`response body`中的`first_name`，`check`就可以指定为`content.person.name.first_name`。可以看出，假如下一层级为字典结构，那么就可以通过`.`运算符指定下一层级的`key`，依次类推。

对于字段内容为列表`list`的情况略有不同，我们需要通过序号来指定具体检查哪一项内容。例如，`Guangzhou`对应的检查项为`content.person.cities.0`，`Shenzhen`对应的检查项为`content.person.cities.1`。

在比较方式（`comparator`）方面，`HttpRunner`除了`eq`，还内置了大量的检查方法。例如，我们可以通过`gt`、`ge`、`lt`、`le`等比较数值大小，通过`len_eq`、`len_gt`、`len_lt`等比较长度是否相等（列表、字典、字符串均适用），通过`contains`、`contained_by`来判断包含关系，通过`startswith`、`endswith`判断字符串的开头结尾，甚至通过`regex_match`来判断是否满足正则匹配等。详细的比较方式还有许多，需要时可查看[comparator]表格。

## 存在的局限性

在大多数情况下，`HttpRunner`的结果校验器（validator）是够用的。不过问题在于，框架不可能为用户实现所有的检查方法，假如用户需要某些特殊的检查方法时，`HttpRunner`就没法实现了。

这的确是一个问题，之前`Junho2010`提的issue [#29]中举了一个例子，应该也算是比较有代表性。

> 发送请求时的数据使用了随机生成，然后需要比较结果中的数据是否是和这个相关（通过某个算法转换）。比如我输入的是321，我的结果是`(3+2+1) * avg(3+2+1)`这种转化，目前的comparator是比较难于实现的。

要解决这个问题，最好的方式应该是在`HttpRunner`中实现自定义结果校验器的机制；用户在有需要的时候，可以自己编写校验函数，然后在`validate`中引用校验函数。之前也介绍过`HttpRunner`的热加载机制，[《约定大于配置：ApiTestEngine实现热加载机制》][hot-plugin]，自定义结果校验器应该也是可以采用这种方式来实现的。

第二个需要优化的点，`HttpRunner`的结果校验器还不支持变量引用，会造成某些场景下的局限性。例如，`testwangchao`曾提过一个issue [#52]：

> 接口response内，会返回数据库内的自增ID。ID校验的时候，希望`expected`为参数化的值。

```yaml
validate:
    - {"check": "content.data.table_list.0.id", "expected": "$id"}
```

另外，在[《ApiTestEngine，不再局限于API的测试》][not-only-about-json-api]一文中有介绍过，结果提取器（`extract`）新增实现了通过正则表达式对任意文本响应内容的字段提取。考虑到结果校验器（`validate`）也需要先从结果响应中提取出特定字段才能与预期值进行比较，在具体实现上完全可以复用同一部分代码，因此在`validate`的`check`部分也可以进行统一化处理。

经过前面的局限性问题描述，我们的改造目标也明确了，主要有三个方面：

- 新增支持自定义结果校验器
- 结果校验器中实现变量引用
- 结果校验内容新增支持正则表达式提取

## 改造结果

具体的改造过程就不写了，有兴趣的同学可以直接阅读源码，重点查看[`httprunner/context.py`][context.py]中的`parse_validator`、`do_validation`和`validate`三个函数。

经过优化后，改造目标中的三项功能都实现了。为了更好地展现改造后的结果校验器，此处将结合实例进行演示。

### 新增支持自定义结果校验器

先来看第一个优化项，新增支持自定义结果校验器。

假设我们需要使用HTTP响应状态码各个数字的和来进行校验，例如，`201`状态码对应的数字和为3，`503`状态码对应的数字和为8。该实例只是为了演示用，实际上并不会用到这样的校验方式。

首先，该种校验方式在`HttpRunner`中并没有内置，因此需要我们自己来实现。实现方式与热加载机制相同，只需要将自定义的校验函数放置到当前`YAML/JSON`文件同级或者父级目录的`debugtalk.py`中。

对于自定义的校验函数，需要遵循三个规则：

- 自定义校验函数需放置到`debugtalk.py`中
- 参数有两个：第一个为原始数据，第二个为原始数据经过运算后得到的预期结果值
- 在校验函数中通过`assert`将实际运算结果与预期结果值进行比较

对于前面提到的演示案例，我们就可以在`debugtalk.py`中编写如下校验函数。

```python
def sum_status_code(status_code, expect_sum):
    """ sum status code digits
        e.g. 400 => 4, 201 => 3
    """
    sum_value = 0
    for digit in str(status_code):
        sum_value += int(digit)

    assert sum_value == expect_sum
```

然后，在`YAML/JSON`格式测试用例的`validate`中，我们就可以将校验函数名称`sum_status_code`作为`comparator`进行使用了。

```yaml
- test:
    name: get token
    request:
        url: http://127.0.0.1:5000/api/get-token
        method: GET
    validate:
        - {"check": "status_code", "comparator": "eq", "expect": 200}
        - {"check": "status_code", "comparator": "sum_status_code", "expect": 2}
```

由此可见，自定义的校验函数`sum_status_code`与`HttpRunner`内置的校验方法`eq`在使用方式上完全相同，应该没有理解上的难度。

### 结果校验器中实现变量引用

对于第二个优化项，结果校验器中实现变量引用。在使用方式上我们应该与`request`中的变量引用一致，即通过`$var`的方式来引用变量`var`。

```yaml
- test:
    name: get token
    request:
        url: http://127.0.0.1:5000/api/get-token
        method: GET
    variables:
        - expect_status_code: 200
        - token_len: 16
    extract:
        - token: content.token
    validate:
        - {"check": "status_code", "comparator": "eq", "expect": "$expect_status_code"}
        - {"check": "content.token", "comparator": "len_eq", "expect": "$token_len"}
        - {"check": "$token", "comparator": "len_eq", "expect": "$token_len"}
```

通过以上示例可以看出，在结果校验器`validate`中，`check`和`expect`均可实现实现变量的引用；而引用的变量，可以来自四种类型：

- 当前`test`中定义的`variables`，例如`expect_status_code`
- 当前`test`中提取（`extract`）的结果变量，例如`token`
- 当前测试用例集`testset`中，先前`test`中提取（`extract`）的结果变量
- 当前测试用例集`testset`中，全局配置`config`中定义的变量

而`check`字段除了可以引用变量，以及保留了之前的链式操作定位字段（例如上例中的`content.token`）外，还新增了采用正则表达式提取内容的方式，也就是第三个优化项。

### 结果校验内容新增支持正则表达式提取

假设如下接口的响应结果内容为`LB123abcRB789`，那么要提取出`abc`部分进行校验，就可以采用如下描述方式。

```yaml
- test:
    name: get token
    request:
        url: http://127.0.0.1:5000/api/get-token
        method: GET
    validate:
        - {"check": "LB123(.*)RB789", "comparator": "eq", "expect": "abc"}
```

可见在使用方式上与在结果提取器（`extract`）中完全相同。

### 结果校验器的进一步简化

最后，为了进一步简化结果校验的描述，我在`validate`中新增实现了一种描述方式。

简化后的描述方式与原始方式对比如下：

```yaml
validate:
    - comparator_name: [check_item, expect_value]
    - {"check": check_item, "comparator": comparator_name, "expect": expect_value}
```

同样是前面的例子，采用新的描述方式后会更加简洁。而两种方式表达的含义是完全等价的。

```yaml
- test:
    name: get token
    request:
        url: http://127.0.0.1:5000/api/get-token
        method: GET
    validate:
        - eq: ["status_code", $expect_status_code]
        - sum_status_code: ["status_code", 2]
        - len_eq: ["$token", $token_len]
        - len_eq: ["content.token", 16]
        - eq: ["LB123(.*)RB789", "abc"]
```

当然，此次优化保证了与历史版本的兼容，之前编写的测试用例脚本的运行是完全不会受到任何影响的。


[comparator]: http://httprunner.readthedocs.io/en/latest/write-testcases.html#comparator
[#29]: https://github.com/HttpRunner/HttpRunner/issues/29
[hot-plugin]: https://debugtalk.com/post/apitestengine-hot-plugin/
[#52]: https://github.com/HttpRunner/HttpRunner/issues/52
[not-only-about-json-api]: https://debugtalk.com/post/apitestengine-not-only-about-json-api/
[context.py]: https://github.com/HttpRunner/HttpRunner/blob/master/httprunner/context.py
