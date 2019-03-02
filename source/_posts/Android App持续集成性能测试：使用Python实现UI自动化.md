---
title: Android App持续集成性能测试：使用Python实现UI自动化
permalink: post/Android-performance-test-UI-Automation-with-Python
date: 2016/04/17
categories:
  - Testing
tags:
  - Android
  - UI
  - Python
---

在进行Android App持续集成性能测试的时候，需要自动化实现UI层面的一些操作，常见的几种场景包括：

- 测试帧率时，需要模拟滑屏、拖拽操作；
- 初次安装app后启动应用时，需要点击按钮跳过协议页面；
- 从`Android M`(6.0)开始，首次启动应用时会进行系统权限校验，需要勾选checkbox以及点击按钮；
- 模拟点击按钮登录用户账号；

这些场景虽然看上去互不相关，但是从测试的角度，UI层面的操作应该都可以归为两类：控件定位和执行动作。

本文将从测试的角度出发，介绍Android UI实现自动化测试的基本方法，并着重讲解通过Python操作Android UI的一般性流程。后续，我会在单独的博客文章中介绍UI操作在Android App持续集成性能测试中的应用。

## 先说uiautomator

要对Android的UI实现自动化操作，首先想到的就是Google官方的`UI Automator`，通过这个工具，可以很好地实现Android UI自动化。

`UI Automator`是一个从Android 4.3 (API level 18) 引入的测试框架，它提供了一套丰富的API，可以在不依赖于目标app内部实现机制的基础上，方便地创建自动化测试用例，实现用户对Android UI各种界面交互操作的模拟。

对于`UI Automator`的使用介绍，我从创建测试用例和执行测试两部分进行。

首先是创建测试用例，流程大致如下：

- 采用JUnit Library创建Java Project
- 将`Android-sdk`中的`android.jar`和`uiautomator.jar`添加进项目
- 使用`UI Automator`提供的API编写测试用例，实现对UI界面操作的定制场景，例如点击按钮、滑动屏幕等
- 将项目编译生成jar文件，例如memorytest.jar

创建好了测试用例，那要怎样执行呢？

从Android 4.3开始，系统中就自带了`uiautomator`命令，命令的路径为`/system/bin/uiautomator`。

由于`uiautomator`命令是运行在Android设备中的，因此需先要将编译好的jar文件push到Android设备中，导入目录为`/data/local/tmp/`。

~~~shell
➜  adb push memorytest.jar /data/local/tmp/
~~~

完成以上准备工作后，就可以在Android的Terminal中执行了`uiautomator`命令了。

详细的`uiautomator`命令用法可参考官方文档，这里只列出最常用的一种方式：

~~~bash
➜  adb shell
shell@hammerhead:/ $ uiautomator runtest memorytest.jar -c com.uc.util.TestCases#slideScreen -e pkgName com.UCMobile
~~~

在如上示例中，`memorytest.jar`是我们之前编译好的测试用例jar文件名，`com.uc.util.TestCases#slideScreen`是Java工程中的类名和方法名，`-e`后面是传入测试类的`name-value`参数。

这里就不再对`UI Automator`进行过多介绍，后续我会再针对`UI Automator`单独写一篇更加详细的教程。

## Python调用uiautomator

通常，我们的持续集成性能测试代码是采用Python编写的，那如何通过Python调用uiautomator呢？

如果沿用上面介绍的流程，Python调用uiautomator实现自动化测试应该也会采用同样的思路：

首先，需要在Java Project使用`UI Automator API`编写UI测试场景，编译生成jar文件，并将这个文件导入到Python项目中。

然后，在Python测试代码中，调用`uiautomator`命令前需要先将jar文件push到Android设备。

~~~python
jar_file_path = os.path.join(_project_root_path, "resource/jar/memorytest.jar")
cmdexec.push(jar_file_path, '/data/local/tmp/')
~~~

接下来，就可以在Python中组装测试命令，并将命令传到Android设备中进行执行。

~~~python
cmd = "uiautomator runtest memorytest.jar -c com.uc.util.TestCases#slideScreen -e pkgName com.UCMobile"
cmdexec.sendShellCommand(cmd, timeout_time=None)
~~~

需要说明的是，上面代码中的`cmdexec`是一个封装类的实例，主要实现的是通过adb与Android设备进行交互，例如push/pull文件、执行Android shell命令等。

经过这么一个流程，可能大家都会感觉到实现起来太过复杂。特别地，如果需要增加一个测试场景，就又要到Java项目中添加测试代码，重新编译为jar文件，并将新的jar文件添加到Python项目中，或者替换原有jar文件。这还不算完，同样地，在Python项目中也需要针对新增的测试场景进行相应的编码。

难道就没有更便捷的方式么？

幸运的是，之前已经有人针对这个痛点填了坑，并在GitHub上进行了开源，项目名称是`xiaocong/uiautomator`（为了便于与Google官方的uiautomator进行区分，后面统一采用pyuiautomator进行描述）。它实现的功能很明确，从项目简介就一目了然。

> Python wrapper of Android uiautomator test tool.

该工具以`Python package`的形式存在，可通过`pip`在测试机（PC）上进行安装。

~~~bash
pip install uiautomator
~~~

安装完毕后，无需在Android设备上安装任何东西，只要设备通过adb与主机相连，就可以在主机中通过Python操作Android设备的UI控件。

如下是简单的示例：

~~~python
from uiautomator import device as d

# Turn on screen
d.screen.on()

# press back key
d.press.back()

# click (x, y) on screen
d.click(x, y)

# check unchecked checkbox
checkbox = d(className='android.widget.CheckBox', checked='false')
checkbox.click()

# click button with text 'Next'
d(text="Clock").click()
button = d(className='android.widget.Button', text='Next')
button.click()

# swipe from (sx, sy) to (ex, ey)
d.swipe(sx, sy, ex, ey)
~~~

更详细的使用方法可参考[项目文档](https://github.com/xiaocong/uiautomator)。

通过这种方式，我们就可以极大地简化Python操作UI控件的方式，不用再对照着`UI Automator API`使用Java编写测试用例，也不用再反复编译jar文件，省去了同一个测试场景需要维护两套代码的麻烦，整个过程也更加Pythonic。

当然，`pyuiautomator`也并非完美，毕竟它不是Google官方维护的，从我实际使用的经历来看，有时候也会存在一些问题。这里先不展开，后续会单独写一篇博客。不过，总的来说，`pyuiautomator`还是非常值得使用的，它的确可以大大简化测试工作量。

现在继续本文的主题，我们怎么采用`pyuiautomator`来进行UI控件操作呢？

其实从上面的示例代码中就可以看到，UI控件的操作分为两步，首先是对目标控件进行定位，然后是对定位的控件执行动作。

## 定位控件

在UI中，每个控件都有许多属性，例如`class`、`text`、`index`等等。我们要想对某一个控件进行操作，必然需要先对目标控件进行选择。

在上面的`pyuiautomator`用法示例中，已经包含了控件选择的代码：

~~~python
checkbox = d(className='android.widget.CheckBox', checked='false')
button = d(className='android.widget.Button', text='Next')
~~~

在这两行代码中，分别实现了对checkbox和button的选择。基本原则就是，通过指定的控件属性，可以唯一确定目标控件。

那么，我们怎么知道目标控件有哪些属性，以及对应的属性值是什么呢？

Google官方提供了两个工具，`hierarchyviewer`和`uiautomatorviewer`，这两个工具都位于`<android-sdk>/tools/`目录下。关于这两个工具的区别及其各自的特点，本文不进行详细介绍，我们当前只需要知道，在查看控件属性方面，这两个工具实现的功能完全相同，界面也完全相同，我们任选其一即可。

{: .center}
![uiautomatorviewer](/images/uiautomatorviewer.png)

通过这个工具，我们可以查看到当前设备屏幕中的UI元素信息：

- 当前Android设备屏幕中显示的UI元素的详细属性信息
- 当前Android设备屏幕中所有UI元素的层级关系结构

需要强调的是，工具每执行一次dump，获取到的UI信息仅限于当前屏幕中前端（foreground）显示的内容。

获得UI元素的信息后，由于UI控件是以树形结构进行存储，而且每个控件都存在index属性值，因此，理论上讲，通过层级结构和index属性就能唯一指定任意UI控件。

然而，这并不是最佳实践。因为通常情况下，UI布局的树形结构层级较多，通过层级关系进行指定时会造成书写极为复杂，而且从代码中很难一眼看出指定的是哪个控件。不信？看下这个例子就能体会了。如下代码对应的就是上图中红色方框的控件，可以看出，要是寻找每个控件都要从顶级节点开始，要将根节点到目标控件的路径找出来，这也是一个很大的工作量，而且很容易出错。

~~~
d(className='android.widget.FrameLayout')
  .child(className='android.widget.LinearLayout')
  .child(className='android.widget.FrameLayout')
  .child(className='android.widget.FrameLayout')
  .child(className='android.widget.FrameLayout')
  .child(className='android.widget.FrameLayout')
  .child(className='android.widget.FrameLayout')
  .child(className='android.view.View')
  .child(className='android.widget.FrameLayout')
  .child(className='android.widget.FrameLayout')
  .child(className='android.view.View')
  .child(className='android.widget.FrameLayout')
  .child(className='android.widget.TextView')
~~~

在实际应用中，我们更多地是采用控件的属性信息来定位控件，一般情况下，采用属性值`text`就能唯一确定目标控件了。例如同样是对上图中的红色方框进行定位，如下代码就足够了。

~~~
d(text='UC头条有新消息，点击刷新')
~~~

不过，经常会出现目标控件的`text`属性值为空的情况，这个时候我们一般就会采用`class`属性和部分层级关系组合的方式。同样是上图中的红色方框，我们也可以使用如下方式进行定位。

~~~
d(className='android.widget.FrameLayout').child(className='android.widget.TextView')
~~~

可以看出，同一个控件，我们可以采用多种方式进行定位。具体选择何种定位方式，可以参考如下准则：

- 定位方式应保证定位准确
- 定位方式应尽可能简洁
- 定位方式应尽可能稳定，即使屏幕界面出现变化，定位方式也不会失效

这里说到了定位方式的准确性，那要如何进行验证呢？技巧是，采用`.count`和`.info`属性值即可。

~~~python
>>> d(text='UC头条有新消息，点击刷新').count
1
>>> d(text='UC头条有新消息，点击刷新').info
{u'contentDescription': None, u'checked': False, u'clickable': True, u'scrollable': False, u'text': u'UC\u5934\u6761\u6709\u65b0\u6d88\u606f\uff0c\u70b9\u51fb\u5237\u65b0', u'packageName': u'com.UCMobile.projectscn1098RHEAD', u'selected': False, u'enabled': True, u'bounds': {u'top': 1064, u'left': 42, u'right': 1038, u'bottom': 1136}, u'className': u'android.widget.TextView', u'focusable': False, u'focused': False, u'checkable': False, u'resourceName': None, u'longClickable': False, u'visibleBounds': {u'top': 1064, u'left': 42, u'right': 1038, u'bottom': 1136}, u'childCount': 0}
~~~

当`.count`属性值为1，`.info`属性值的内容与目标控件的属性值一致时，就可以确定我们采用的定位方式是准确的。

## 控件操作

定位到具体的控件后，操作就比较容易了。

在`pyuiautomator`中，对`UI Automator`的UI操作动作进行了封装，常用的操作动作有：

- .click()
- .long_click()
- .swipe
- .drag

更多的操作可根据我们测试场景的实际需求，查询`pyuiautomator`文档找到合适的方法。

## 总结

看到这里，相信大家对Android UI自动化测试已经有了基本的认识。由于篇幅关系，我没有将所有内容都包含进来，而是打算后续分多个专题以单独博文的形式进行展开（不知不觉就给自己埋下了坑^_^）。

## 参考文档

- http://developer.android.com/tools/testing-support-library/index.html#UIAutomator
- https://github.com/xiaocong/uiautomator
