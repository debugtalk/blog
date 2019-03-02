---
title: ApiTestEngine 演进之路（3）测试用例中实现 Python 函数的定义
permalink: post/ApiTestEngine-3-define-functions-in-yaml-testcases
date: 2017/07/11
categories:
  - Development
  - 测试框架
tags:
  - HttpRunner
  - lambda
---

在[《ApiTestEngine 演进之路（2）探索优雅的测试用例描述方式》][ApiTestEngine-2]中，我们臆想了一种简洁优雅的用例描述方式，接下来，我们就从技术实现的角度，逐项进行深入讲解，将臆想变成现实。

本文先解决第一个问题，“如何在用例描述（`YAML/JSON`）中实现函数的定义和调用”。

> 在写作的过程中，发现要将其中的原理阐述清楚，要写的内容实在是太多，因此将问题再拆分为“函数定义”和“函数调用”两部分，本文只讲解“函数定义”部分的内容。

## 实现函数的定义

在之前，我们假设存在`gen_random_string`这样一个生成指定位数随机字符串的函数，以及`gen_md5`这样一个计算签名校验值的函数，我们不妨先尝试通过`Python`语言进行具体的实现。

```python
import hashlib
import random
import string

def gen_random_string(str_len):
    return ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(str_len))

def gen_md5(*args):
    return hashlib.md5("".join(args).encode('utf-8')).hexdigest()

gen_random_string(5) # => A2dEx

TOKEN = "debugtalk"
data = '{"name": "user", "password": "123456"}'
random = "A2dEx"
gen_md5(TOKEN, data, random) # => a83de0ff8d2e896dbd8efb81ba14e17d
```

熟悉`Python`语言的人对以上代码应该都不会有理解上的难度。可能部分新接触`Python`的同学对`gen_md5`函数的`*args`传参方式会比较陌生，我也简单地补充下基础知识。

在`Python`中，函数参数共有四种，必选参数、默认参数、可变参数和关键字参数。

必选参数和默认参数大家应该都很熟悉，绝大多数编程语言里面都有类似的概念。

```python
def func(x, y, a=1, b=2):
    return x + y + a + b

func(1, 2) # => 6
func(1, 2, b=3) # => 7
```

在上面例子中，`x`和`y`是必选参数，`a`和`b`是默认参数。除了显示地定义必选参数和默认参数，我们还可以通过使用可变参数和关键字参数的形式，实现更灵活的函数参数定义。

```python
def func(*args, **kwargs):
    return sum(args) + sum(kwargs.values())

args = [1, 2]
kwargs = {'a':3, 'b':4}
func(*args, **kwargs) # => 10

args = []
kwargs = {'a':3, 'b':4, 'c': 5}
func(*args, **kwargs) # => 12
```

之所以说更灵活，是因为当使用可变参数和关键字参数时（`func(*args, **kwargs)`），我们在调用函数时就可以传入0个或任意多个必选参数和默认参数，所有必选参数将作为`tuple/list`的形式传给可变参数（`args`），并将所有默认参数作为`dict`的形式传给关键字参数（`kwargs`）。另外，可变参数和关键字参数也并不是要同时使用，只使用一种也是可以的。

在前面定义的`gen_md5(*args)`函数中，我们就可以将任意多个字符串传入，然后得到拼接字符串的`MD5`值。

现在再回到测试用例描述文件，由于是纯文本格式（`YAML/JSON`），我们没法直接写`Python`代码，那要怎样才能定义函数呢？

之前接触过一些函数式编程，所以我首先想到的是借助`lambda`实现匿名函数。如果对函数式编程不了解，可以看下我之前写过的一篇文章，[《Python的函数式编程--从入门到⎡放弃⎦》][python-functional-programming]。

## 方法一：通过lambda实现函数定义

使用`lambda`有什么好处呢？

最简单直接的一点，通过`lambda`关键字，我们可以将函数写到一行里面。例如，同样是前面提到的`gen_random_string`函数和`gen_md5`函数，通过`lambda`的实现方式就是如下的形式。

```python
gen_random_string = lambda str_len: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(str_len))
gen_md5 = lambda *str_args: hashlib.md5(''.join(str_args).encode('utf-8'))

gen_random_string(5) # => A2dEx

TOKEN = "debugtalk"
data = '{"name": "user", "password": "123456"}'
random = "A2dEx"
gen_md5(TOKEN, data, random) # => a83de0ff8d2e896dbd8efb81ba14e17d
```

可以看出，采用`lambda`定义的函数跟之前的函数功能完全一致，调用方式相同，运算结果也完全一样。

然后，我们在测试用例里面，通过新增一个`function_binds`模块，就可以将函数定义与函数名称绑定了。

```YAML
- test:
    name: create user which does not exist
    function_binds:
        gen_random_string: "lambda str_len: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(str_len))"
        gen_md5: "lambda *str_args: hashlib.md5(''.join(str_args).encode('utf-8'))
    variables:
        - TOKEN: debugtalk
        - random: ${gen_random_string(5)}
        - json: {"name": "user", "password": "123456"}
        - authorization: ${gen_md5($TOKEN, $json, $random)}
```

可能有些同学还是无法理解，在上面`YAML`文件中，即使将函数定义与函数名称绑定了，但是加载`YAML`文件后，函数名称对应的值也只是一个字符串而已，这还是没法运行啊。

这就又要用到`eval`黑科技了。通过`eval`函数，可以执行字符串表达式，并返回表达式的值。

```python
gen_random_string = "lambda str_len: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(str_len))"

func = eval(gen_random_string)

func # => <function <lambda> at 0x10e19a398>
func(5) # => "A2dEx"
```

在上面的代码中，`gen_random_string`为`lambda`字符串表达式，通过`eval`执行后，就转换为一个函数对象，然后就可以像正常定义的函数一样调用了。

如果你看到这里还没有疑问，那么说明你肯定没有亲自实践。事实上，上面执行`func(5)`的时候并不会返回预期结果，而是会抛出如下异常。

```bash
>>> func(5)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "<string>", line 1, in <lambda>
  File "<string>", line 1, in <genexpr>
NameError: global name 'random' is not defined
```

这是因为，我们在定义的`lambda`函数中，用到了`random`库，而在`lambda`表达式中，我们并没有`import random`。

这下麻烦了，很多时候我们的函数都要用到标准库或者第三方库，而在调用这些库函数之前，我们必须得先`import`。想来想去，这个`import`的操作都没法塞到`lambda`表达式中。

为了解决这个依赖库的问题，我想到两种方式。

第一种方式，在加载`YAML/JSON`用例之前，先统一将测试用例依赖的所有库都`import`一遍。这个想法很快就被否决了，因为这必须要在`ApiTestEngine`框架里面去添加这部分代码，而且每个项目的依赖库不一样，需要`import`的库也不一样，总不能为了解决这个问题，在框架初始化部分将所有的库都`import`吧？而且为了适配不同项目来改动测试框架的代码，也不是通用测试框架应有的做法。

然后我想到了第二种方式，就是在测试用例里面，通过新增一个`requires`模块，罗列出当前测试用例所有需要引用的库，然后在加载用例的时候通过代码动态地进行导入依赖库。

```YAML
- test:
    name: create user which does not exist
    requires:
        - random
        - string
        - hashlib
    function_binds:
        gen_random_string: "lambda str_len: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(str_len))"
        gen_md5: "lambda *str_args: hashlib.md5(''.join(str_args).encode('utf-8'))
    variables:
        - TOKEN: debugtalk
        - random: ${gen_random_string(5)}
        - json: {"name": "user", "password": "123456"}
        - authorization: ${gen_md5($TOKEN, $json, $random)}
```

动态地导入依赖库？其实也没有多玄乎，`Python`本身也支持这种特性。如果你看到这里感觉无法理解，那么我再补充点基础知识。

在`Python`中执行`import`时，实际上等价于执行`__import__`函数。

例如，`import random`等价于如下语句：

```python
random = __import__('random', globals(), locals(), [], -1)
```

其中，`__import__`的函数定义为`__import__(name[, globals[, locals[, fromlist[, level]]]])`，第一个参数为库的名称，后面的参数暂不用管（可直接查看[官方文档][python-functions-import]）。

由于后面的参数都有默认值，通常情况下我们采用默认值即可，因此我们也可以简化为如下形式：

```python
random = __import__('random')
```

执行这个语句的有什么效果呢？

可能这也是大多数`Python`初学者都忽略的一个知识点。在`Python`运行环境中，有一个全局的环境变量，当我们定义一个函数，或者引入一个依赖库时，实际上就是将其对象添加到了全局的环境变量中。

这个全局的环境变量就是`globals()`，它是一个字典类型的数据结构。要验证以上知识点，我们可以在`Python`的交互终端中进行如下实验。

```bash
$ python
>>>
>>> globals()
{'__name__': '__main__', '__doc__': None, '__package__': None, '__loader__': <class '_frozen_importlib.BuiltinImporter'>, '__spec__': None, '__annotations__': {}, '__builtins__': <module 'builtins' (built-in)>}
>>>
>>> import random
>>>
>>> globals()
{'__name__': '__main__', '__doc__': None, '__package__': None, '__loader__': <class '_frozen_importlib.BuiltinImporter'>, '__spec__': None, '__annotations__': {}, '__builtins__': <module 'builtins' (built-in)>, 'random': <module 'random' from '/Users/Leo/.pyenv/versions/3.6.0/lib/python3.6/random.py'>}
```

可以看出，在执行`import random`命令后，`globals()`中就新增了`random`函数的引用。

因此，导入`random`依赖库时，我们采用如下的写法也是等价的。

```python
module_name = ”random“
globals()[module_name] = __import__(module_name)
```

更进一步，`__import__`作为`Python`的底层函数，其实是不推荐直接调用的。要实现同样的功能，推荐使用`importlib.import_module`。替换后就变成了如下形式：

```python
module_name = ”random“
globals()[module_name] = importlib.import_module(module_name)
```

如果理解了以上的知识点，那么再给我们一个依赖库名称（字符串形式）的列表时，我们就可以实现动态的导入（`import`）了。

```python
def import_requires(modules):
   """ import required modules dynamicly
   """
   for module_name in modules:
       globals()[module_name] = importlib.import_module(module_name)
```

在实现了定义`lambda`函数的`function_binds`和导入依赖库的`requires`模块之后，我们就可以在`YAML/JSON`中灵活地描述测试用例了。

还是之前的例子，完整的测试用例描述形式就为如下样子。

```yaml
- test:
    name: create user which does not exist
    requires:
        - random
        - string
        - hashlib
    function_binds:
        gen_random_string: "lambda str_len: ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(str_len))"
        gen_md5: "lambda *str_args: hashlib.md5(''.join(str_args).encode('utf-8')).hexdigest()"
    variables:
        - TOKEN: debugtalk
        - random: ${gen_random_string(5)}
        - data: '{"name": "user", "password": "123456"}'
        - authorization: ${gen_md5($TOKEN, $data, $random)}
    request:
        url: http://127.0.0.1:5000/api/users/1000
        method: POST
        headers:
            Content-Type: application/json
            authorization: $authorization
            random: $random
        data: $data
    validators:
        - {"check": "status_code", "comparator": "eq", "expected": 201}
        - {"check": "content.success", "comparator": "eq", "expected": true}
```

现在我们可以在`YAML/JSON`文本中⎡灵活⎦地定义函数，实现各种功能了。

可是，这真的是我们期望的样子么？

开始的时候，我们想在自动化测试中将`测试数据`与`代码实现`进行分离，于是我们引入了`YAML/JSON`格式的用例形式；为了在`YAML/JSON`文本格式中实现签名校验等计算功能，我们又引入了`function_binds`模块，并通过`lambda`定义函数并与函数名进行绑定；再然后，为了解决定义函数中的依赖库问题，我们又引入了`requires`模块，动态地加载指定的依赖库。

而且即使是这样，这种方式也有一定的局限性，当函数较复杂的时候，我们很难将函数内容转换为`lambda`表达式；虽然理论上所有的函数都能转换为`lamda`表达式，但是实现的难度会非常高。

为了不写代码而人为引入了更多更复杂的概念和技术，这已经不再符合我们的初衷了。于是，我开始重新寻找新的实现方式。

## 方法二：自定义函数模块并进行导入

让我们再回归基础概念，当我们调用一个函数的时候，究竟发生了什么？

简单的说，不管是调用一个函数，还是引用一个变量，都会在当前的运行环境上下文（`context`）中寻找已经定义好的函数或变量。而在`Python`中，当我们加载一个模块（`module`）的时候，就会将该模块中的所有函数、变量、类等对象加载进当前的运行环境上下文。

如果单纯地看这个解释还不清楚，想必大家应该都见过如下案例的形式。假设`moduleA`模块包含如下定义：

```python
# moduleA

def hello(name):
    return "hello, %s" % name

varA = "I am varA"
```

那么，我们就可以通过如下方式导入`moduleA`模块中所有内容，并且直接调用。

```python
from moduleA import *

print(hello("debugtalk")) # => hello, debugtalk
print(varA) # => I am varA
```

明确这一点后，既然我们之前都可以动态地导入（`import`）依赖库，那么我们不妨再进一步，我们同样也可以动态地导入已经定义好的函数啊。

只要我们先在一个`Python`模块文件中定义好测试用例所需的函数，然后在运行测试用例的时候设法将模块中的所有函数导入即可。

于是，问题就转换为，如何在`YAML/JSON`中实现`from moduleA import *`机制。

经过摸索，我发现了`Python`的[`vars`函数][python-functions-vars]，这也是`Python`的`Built-in Functions`之一。

对于`vars`，官方的定义如下：

> Return the `__dict__` attribute for a module, class, instance, or any other object with a `__dict__` attribute.

简言之，就是`vars()`可以将模块（`module`）、类（`class`）、实例（`instance`）或者任意对象的所有属性（包括但不限于定义的方法和变量），以字典的形式返回。

还是前面举例的`moduelA`，相信大家看完下面这个例子就清晰了。

```bash
>>> import moduleA
>>> vars(moduleA)
>>> {'hello': <function hello at 0x1072fcd90>, 'varA': 'I am varA'}
```

掌握了这一层理论基础，我们就可以继续改造我们的测试框架了。

我采取的做法是，在测试用例中新增一个`import_module_functions`模块，里面可填写多个模块的路径。而测试用例中所有需要使用的函数，都定义在对应路径的模块中。

我们再回到之前的案例，在测试用例中需要用到`gen_random_string`和`gen_md5`这两个函数函数，那么就可以将其定义在一个模块中，假设模块名称为`custom_functions.py`，相对于项目根目录的路径为`tests/data/custom_functions.py`。

```python
import hashlib
import random
import string

def gen_random_string(str_len):
    return ''.join(
        random.choice(string.ascii_letters + string.digits) for _ in range(str_len))

def gen_md5(*args):
    return hashlib.md5("".join(args).encode('utf-8')).hexdigest()
```

需要注意的是，这里的模块文件可以放置在系统的任意路径下，但是一定要保证它可作为`Python`的模块进行访问，也就是说在该文件的所有父目录中，都包含`__init__.py`文件。这是`Python`的语法要求，如不理解可查看官方文档。

然后，在`YAML/JSON`测试用例描述的`import_module_functions`栏目中，我们就可以写为`tests.data.custom_functions`。

新的用例描述形式就变成了如下样子。

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

现在函数已经定义好了，那是怎样实现动态加载的呢？

首先，还是借助于`importlib.import_module`，实现模块的导入。

```python
imported = importlib.import_module(module_name)
```

然后，借助于`vars`函数，可以获取得到模块的所有属性，也就是其中定义的方法、变量等对象。

```python
vars(imported)
```

不过，由于我们只需要定义的函数，因此我们还可以通过进行过滤，只获取模块中的所有方法对象。当然，这一步不是必须的。

```python
imported_functions_dict = dict(filter(is_function, vars(imported).items()))
```

其中，`is_function`是一个检测指定对象是否为方法的函数，实现形式如下：

```python
import types

def is_function(tup):
    """ Takes (name, object) tuple, returns True if it is a function.
    """
    name, item = tup
    return isinstance(item, types.FunctionType)
```

通过以上代码，就实现了从指定外部模块加载所有方法的功能。完整的代码如下：

```python

def import_module_functions(self, modules, level="testcase"):
   """ import modules and bind all functions within the context
   """
   for module_name in modules:
       imported = importlib.import_module(module_name)
       imported_functions_dict = dict(filter(is_function, vars(imported).items()))
       self.__update_context_config(level, "functions", imported_functions_dict)
```

结合到实际项目，我们就可以采取这种协作模式：

- 由测试开发或者开发人员将项目中所有依赖的逻辑实现为函数方法，统一放置到一个模块中；
- 在`YAML/JSON`测试用例中，对模块进行引用；（对于测试用例集的模式，只需要引用一次，以后再详细讲解）
- 业务测试人员只需要关注接口的业务数据字段，设计测试用例即可。

可以看出，这也算是软件工程和实际项目中的一种权衡之计，但好处在于能充分发挥各岗位角色人员的职能，有助于接口测试自动化工作的顺利开展。

## 总结

本文介绍了在`YAML/JSON`测试用例中实现`Python`函数定义的两种方法：

- 通过`lambda`实现函数的定义：该种方式适用于函数比较简单的情况，并且函数最好没有依赖库；虽然复杂的函数也能采用这种方式进行定义，但可能会存在一定的局限性，而且看上去也比较累赘。
- 自定义函数模块并进行导入：该种方式通用性更强，所有类型的函数都可以通过这种方式进行定义和引用；但由于需要编写额外的`Python`模块文件，在函数比较简单的情况下反而会显得较为繁琐，此时采用`lambda`形式会更简洁。

到现在为止，我们已经清楚了如何在`YAML/JSON`测试用例中实现函数的定义，但是在`YAML/JSON`文本中要怎样实现函数的调用和传参呢？

```yaml
variables:
   - TOKEN: debugtalk
   - json: {}
   - random: ${gen_random_string(5)}
   - authorization: ${gen_md5($TOKEN, $json, $random)}
```

例如上面的例子（YAML格式），`gen_random_string`和`gen_md5`都是已经定义好的函数，但`${gen_random_string(5)}`和`${gen_md5($TOKEN, $json, $random)}`终究只是文本字符串，程序是如何将其解析为真实的函数和参数，并实现调用的呢？

下篇文章再详细讲解。

## 相关文章

- [《Python的函数式编程--从入门到⎡放弃⎦》][python-functional-programming]
- [《接口自动化测试的最佳工程实践（ApiTestEngine）》][ApiTestEngine-Intro]
- [《ApiTestEngine 演进之路（2）探索优雅的测试用例描述方式》][ApiTestEngine-2]
- [`ApiTestEngine` GitHub源码][ApiTestEngine]

[ApiTestEngine-Intro]: https://debugtalk.com/post/ApiTestEngine-api-test-best-practice/
[ApiTestEngine-2]: https://debugtalk.com/post/ApiTestEngine-2-best-testcase-description/
[python-functional-programming]: https://debugtalk.com/post/python-functional-programming-getting-started/
[ApiTestEngine]: https://github.com/debugtalk/ApiTestEngine
[python-functions-import]: https://docs.python.org/3/library/functions.html#__import__
[python-functions-vars]: https://docs.python.org/3/library/functions.html#vars
