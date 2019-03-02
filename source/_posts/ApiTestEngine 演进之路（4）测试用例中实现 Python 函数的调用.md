---
title: ApiTestEngine 演进之路（4）测试用例中实现 Python 函数的调用
permalink: post/ApiTestEngine-4-call-functions-in-yaml-testcases
date: 2017/07/17
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
---

在[《测试用例中实现`Python`函数的定义》][ApiTestEngine-3]中，介绍了在`YAML/JSON`测试用例中实现`Python`函数定义的两种方法，以及它们各自适用的场景。

但是在`YAML/JSON`文本中要怎样实现函数的调用和传参呢？

```yaml
variables:
   - TOKEN: debugtalk
   - json: {}
   - random: ${gen_random_string(5)}
   - authorization: ${gen_md5($TOKEN, $json, $random)}
```

例如上面的例子（YAML格式），`gen_random_string`和`gen_md5`都是已经定义好的函数，但`${gen_random_string(5)}`和`${gen_md5($TOKEN, $json, $random)}`终究只是文本字符串，程序是如何将其解析为实际的函数和参数，并实现调用的呢？

本文将对此进行重点讲解。

## 函数的调用形式

在`Python`语言中，函数的调用形式包含如下四种形式：

- 无参数：func()
- 顺序参数：func(a, b)
- 字典参数：func(a=1, b=2)
- 混合类型参数：func(1, 2, a=3, b=4)

之前在[《探索优雅的测试用例描述方式》][ApiTestEngine-2]中介绍过，我们选择使用`${}`作为函数转义符，在`YAML/JSON`用例描述中调用已经定义好的函数。

于是，以上四种类型的函数定义在`YAML/JSON`中就会写成如下样子。

- 无参数：${func()}
- 顺序参数：${func(a, b)}
- 字典参数：${func(a=1, b=2)}
- 混合类型参数：${func(1, 2, a=3, b=4)}

还是之前的例子：

```yaml
- test:
    name: create user which does not exist
    import_module_functions:
        - tests.data.custom_functions
    variables:
        - TOKEN: debugtalk
        - json: {"name": "user", "password": "123456"}
        - random: ${gen_random_string(5)}
        - authorization: ${gen_md5($TOKEN, $json, $random)}
    request:
        url: http://127.0.0.1:5000/api/users/1000
        method: POST
        headers:
            Content-Type: application/json
            authorization: $authorization
            random: $random
        json: $json
    validators:
        - {"check": "status_code", "comparator": "eq", "expected": 201}
        - {"check": "content.success", "comparator": "eq", "expected": true}
```

在这里面有一个`variables`模块，之前已经出现过很多次，也一直都没有讲解。但是，本文也不打算进行讲解，该部分内容将在下一篇讲解参数的定义和引用时再详细展开。

当前我们只需要知道，在该用例描述中，`${gen_random_string(5)}`和`${gen_md5($TOKEN, $json, $random)}`均实现了函数的传参和调用，而调用的函数正式之前我们定义的`gen_random_string`和`gen_md5`。

这里应该比较好理解，因为函数调用形式与在`Python`脚本中完全相同。但难点在于，这些描述在`YAML/JSON`中都是文本字符串形式，[`ApiTestEngine`][ApiTestEngine]在加载测试用例的时候，是怎么识别出函数并完成调用的呢？

具体地，这里可以拆分为三个需求点：

- 如何在`YAML/JSON`文本中识别函数？
- 如何将文本字符串的函数拆分为函数名称和参数？
- 如何使用函数名称和参数实现对应函数的调用？

## 正则表达式的妙用

对于第一个需求点，我们之前已经做好了铺垫，设计了`${}`作为函数的转义符；而当初之所以这么设计，也是为了在加载测试用例时便于解析识别，因为我们可以通过使用正则表达式，非常准确地将函数从文本格式的测试用例中提取出来。

既然`Python`函数的调用形式是确定的，都是`函数名(参数)`的形式，那么使用正则表达式的分组匹配功能，我们就可以很好地实现函数名称与参数的匹配，也就实现了第二个需求点。

例如，我们可以采用如下正则表达式，来对`YAML/JSON`中的每一个值（Value）进行匹配性检查。

```regex
r"^\$\{(\w+)\((.*)\)\}$"
```

```bash
>>> import re
>>> regex = r"^\$\{(\w+)\((.*)\)\}$"
>>> string = "${func(3, 5)}"
>>> matched = re.match(regex, string)
>>> matched.group(1)
'func'
>>> matched.group(2)
'3, 5'
>>>
>>> string = "${func(a=1, b=2)}"
>>> matched = re.match(regex, string)
>>> matched.group(1)
'func'
>>> matched.group(2)
'a=1, b=2'
```

可以看出，通过如上正则表达式，如果满足匹配条件，那么`matched.group(1)`就是函数的名称，`matched.group(2)`就是函数的参数。

思路是完全可行的，不过我们在匹配参数部分的时候是采用`.*`的形式，也就是任意字符匹配，匹配的方式不是很严谨。考虑到正常的函数参数部分可能使用到的字符，我们可以采用如下更严谨的正则表达式。

```regex
r"^\$\{(\w+)\(([\$\w =,]*)\)\}$"
```

这里限定了五种可能用到的字符，`\w`代表任意字母或数字，`= ,`代表的是等号、空格和逗号，这些都是参数中可能用到的。而`\$`符号，大家应该还记得，这也是我们设计采用的变量转义符，`$var`将不再代表的是普遍的字符串，而是`var`变量的值。

有了这个基础，实现如下`is_functon`函数，就可以判断某个字符串是否为函数调用。

```python
function_regexp = re.compile(r"^\$\{(\w+)\(([\$\w =,]*)\)\}$")

def is_functon(content):
    matched = function_regexp.match(content)
    return True if matched else False
```

不过这里还有一个问题。通过上面的正则表达式，是可以将函数名称和参数部分拆分开了，但是在参数部分，还没法区分具体的参数类型。

例如，在前面的例子中，从`${func(3, 5)}`解析出来的参数为`3, 5`，从`${func(a=1, b=2)}`解析出来的参数为`a=1, b=2`，我们通过肉眼可以识别出这分别对应着顺序参数和字典参数两种类型，但是程序就没法自动识别了，毕竟对于程序来说它们都只是字符串而已。

所以，这里还需要再做一步操作，就是将参数字符串解析为对程序友好的形式。

什么叫对程序友好的形式呢？这里就又要用到[上一篇文章][ApiTestEngine-3]讲到的可变参数和关键字参数形式了，也就是`func(*args, **kwargs)`的形式。

试想，如果我们可以将所有顺序参数都转换为`args`列表，将所有字典参数都转换为`kwargs`字典，那么对于任意函数类型，我们都可以采用`func(*args, **kwargs)`的调用形式。

于是，问题就转换为，如何将参数部分转换为`args`和`kwargs`两部分。

这就比较简单了。因为在函数的参数部分，顺序参数必须位于字典参数前面，并且以逗号间隔；而字典参数呢，总是以`key=value`的形式出现，并且也以逗号间隔。

那么我们就可以利用参数部分的这个特征，来进行字符串的处理。处理算法如下：

- 采用逗号作为分隔符将字符串进行拆分；
- 对每一部分进行判断，如果不包含等号，那么就是顺序参数，将其加入（`append`）到`args`列表；
- 如果包含等号，那么就是字典参数，采用等号作为分隔符进行进一步拆分得到`key-value`键值对，然后再加入到`kwargs`字典。

对应的`Python`代码实现如下：

```python
def parse_function(content):
    function_meta = {
        "args": [],
        "kwargs": {}
    }
    matched = function_regexp.match(content)
    function_meta["func_name"] = matched.group(1)

    args_str = matched.group(2).replace(" ", "")
    if args_str == "":
        return function_meta

    args_list = args_str.split(',')
    for arg in args_list:
        if '=' in arg:
            key, value = arg.split('=')
            function_meta["kwargs"][key] = parse_string_value(value)
        else:
            function_meta["args"].append(parse_string_value(arg))

    return function_meta
```

可以看出，通过`parse_function`函数，可以将一个函数调用的字符串转换为函数的结构体。

例如，`${func(1, 2, a=3, b=4)}`字符串，经过`parse_function`转换后，就可以得到该函数的名称和参数信息：

```json
function_meta = {
    'func_name': 'func',
    'args': [1, 2],
    'kwargs': {'a':3, 'b':4}
}
```

这也就彻底解决了第二个需求点。

## 实现函数的调用

在此基础上，我们再看第三个需求点，如何使用函数名称和参数实现对应函数的调用，其实也就很简单了。

在[上一篇文章][ApiTestEngine-3]中，我们实现了对函数的定义，并且将所有定义好的函数都添加到了一个字典当中，假如字典名称为`custom_functions_dict`，那么根据以上的函数信息（`function_meta`），就可以采用如下方式进行调用。

```python
func_name = function_meta['func_name']
args = function_meta['args']
kwargs = function_meta['kwargs']
custom_functions_dict[func_name](*args, **kwargs)
```

具体的，在`ApiTestEngine`中对应的`Python`代码片段如下：

```python
def get_eval_value(self, data):
   """ evaluate data recursively, each variable in data will be evaluated.
   """
   if isinstance(data, (list, tuple)):
       return [self.get_eval_value(item) for item in data]

   if isinstance(data, dict):
       evaluated_data = {}
       for key, value in data.items():
           evaluated_data[key] = self.get_eval_value(value)

       return evaluated_data

   if isinstance(data, (int, float)):
       return data

   # data is in string format here
   data = "" if data is None else data.strip()
   if utils.is_variable(data):
       # variable marker: $var
       variable_name = utils.parse_variable(data)
       value = self.testcase_variables_mapping.get(variable_name)
       if value is None:
           raise exception.ParamsError(
               "%s is not defined in bind variables!" % variable_name)
       return value

   elif utils.is_functon(data):
       # function marker: ${func(1, 2, a=3, b=4)}
       fuction_meta = utils.parse_function(data)
       func_name = fuction_meta['func_name']
       args = fuction_meta.get('args', [])
       kwargs = fuction_meta.get('kwargs', {})
       args = self.get_eval_value(args)
       kwargs = self.get_eval_value(kwargs)
       return self.testcase_config["functions"][func_name](*args, **kwargs)
   else:
       return data
```

这里还用到了递归的概念，当参数是变量（例如`gen_md5($TOKEN, $json, $random)`），或者为列表、字典等嵌套类型时，也可以实现正常的解析。

## 总结

到此为止，我们就解决了测试用例（`YAML/JSON`）中实现`Python`函数定义和调用的问题。

还记得[《探索优雅的测试用例描述方式》][ApiTestEngine-2]末尾提到的用例模板引擎技术实现的三大块内容么？

- 如何在用例描述（`YAML/JSON`）中实现函数的定义和调用
- 如何在用例描述中实现参数的定义和引用，包括用例内部和用例集之间
- 如何在用例描述中实现预期结果的描述和测试结果的校验

第一块总算是讲完了，下一篇文章将开始讲解如何在用例描述中实现参数的定义和引用的问题。

## 相关文章

- [《ApiTestEngine 演进之路（2）探索优雅的测试用例描述方式》][ApiTestEngine-2]
- [《ApiTestEngine 演进之路（3）测试用例中实现`Python`函数的定义》][ApiTestEngine-3]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]


[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[ApiTestEngine-2]: https://debugtalk.com/post/ApiTestEngine-2-best-testcase-description/
[ApiTestEngine-3]: https://debugtalk.com/post/ApiTestEngine-3-define-functions-in-yaml-testcases/
