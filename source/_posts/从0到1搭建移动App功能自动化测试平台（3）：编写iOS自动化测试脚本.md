---
title: 从0到1搭建移动App功能自动化测试平台（3）：编写iOS自动化测试脚本
permalink: post/build-app-automated-test-platform-from-0-to-1-write-iOS-testcase-scripts
date: 2016/05/30
categories:
  - Testing
  - 自动化测试
tags:
  - Appium
  - iOS
  - Python
  - Ruby
  - AppiumBooster
---


通过前面三篇文章，我们已经将iOS自动化功能测试的开发环境全部准备就绪，也学习了iOS UI控件交互操作的一般性方法，接下来，就可以开始编写自动化测试脚本了。

在本文中，我将在M项目中挑选一个功能点，对其编写自动化测试脚本，演示编写自动化测试用例的整个流程。

## 语言的选择：Python or Ruby？

之前介绍Appium的时候也提到，Appium采用Client-Server的架构设计，并采用标准的HTTP通信协议；Client端基本上可以采用任意主流编程语言编写测试用例，包括但不限于C#、Ruby、Objective-C、Java、node.js、Python、PHP。

因此，在开始编写自动化测试脚本之前，首先需要选定一门编程语言。

这个选择因人而异，并不涉及到太大的优劣之分，基本上在上述几门语言中选择自己最熟悉的就好。

但对我而言，选择却没有那么干脆，前段时间在Python和Ruby之间犹豫了很久，经过艰难的决定，最终选择了Ruby。为什么不考虑Java？不熟是一方面，另一方面是觉得采用编译型语言写测试用例总感觉太重，这活儿还是解释型语言来做更合适些。

其实，最开始本来是想选择Python的，因为Python在软件测试领域比Ruby应用得更广，至少在国内，不管是公司团队，还是测试人员群体，使用Python的会比使用Ruby的多很多。

那为什么还是选择了Ruby呢？

我主要是基于如下几点考虑的：

- 从Appium的官方文档来看，Appium对Ruby的支持力度，或者说是偏爱程度，貌似会更大些；在[Appium Client Libraries](http://appium.io/downloads.html)列表中将Ruby排在第一位就不说了，在[Appium Tutorials](http://appium.io/tutorial.html?lang=en)中示例语言就只采用了Ruby和Java进行描述。
- [Appium_Console](https://github.com/appium/ruby_lib)是采用Ruby编写的，在Console中执行的命令基本上可直接用在Ruby脚本中。
- 后续打算引入BDD（行为驱动开发）的测试模式，而不管是cucumber还是RSpec，都是采用Ruby开发的。

当然，还有最最重要的一点，身处于珠江三角洲最大的Ruby阵营，周围Ruby大牛云集，公司的好多业务系统也都是采用Rails作为后台语言，完全没理由不选择Ruby啊。

## 第一个测试用例：系统登录

在测试领域中，系统登录这个功能点的地位，堪比软件开发中的`Hello World`，因此第一个测试用例就毫无悬念地选择系统登录了。

在编写自动化测试脚本之前，我们首先需要清楚用例执行的路径，路径中操作涉及到的控件，以及被操作控件的属性信息。

对于本次演示的APP来说，登录时需要先进入【My Account】页面，然后点击【Login】进入登录页面，接着在登录页面中输入账号密码后再点击【Login】按钮，完成登录操作。

![Preview of DebugTalk Plus login](/images/DebugTalk_Plus_Login.jpg)

确定了操作路径以后，就可以在`Appium Ruby Console`中依次操作一遍，目的是确保代码能正确地对控件进行操作。

第一步要点击【My Account】按钮，因此先查看下Button控件属性。要是不确定目标控件的类型，可以直接执行`page`命令，然后在返回结果中根据控件名称进行查找。

```shell
[1] pry(main)> page :button
...（略）
UIAButton
   name, label: My Account
   id: My Account => My Account
nil
```

通过返回结果，可以看到【My Account】按钮的name、label属性就是“My Account”，因此可以通过`button_exact('My Account')`方式来定位控件，并进行点击操作。

```shell
[2] pry(main)> button_exact('My Account').click
nil
```

执行命令后，观察iOS模拟器中APP的响应情况，看是否成功进入“My Account”页面。

第二步也是类似的，操作代码如下：

```shell
[3] pry(main)> button_exact('Login').click
nil
```

进入到登录页面后，再次查看页面中的控件信息：

```shell
[4] pry(main)> page
...（略）
UIATextField
   value: Email Address
   id: Email Address => Email Address
UIASecureTextField
   value: Password (6-16 characters)
   id: Password (6-16 characters) => Password (6-16 characters)
UIAButton
   name, label: Login
   id: Log In => Login
       登录     => Login
...（略）
```

第三步需要填写账号密码，账号密码的控件属性分别是`UIATextField`和`UIASecureTextField`。由于这两个控件的类型在登录页面都是唯一的，因此可以采用控件的类型来进行定位，然后进行输入操作，代码如下：

```shell
[5] pry(main)> tag('UIATextField').type 'leo.lee@debugtalk.com'
""
[6] pry(main)> tag('UIASecureTextField').type '123456'
""
```

执行完输入命令后，在iOS模拟器中可以看到账号密码输入框都成功输入了内容。

最后第四步点击【Login】按钮，操作上和第二步完全一致。

```shell
[7] pry(main)> button_exact('Login').click
nil
```

执行完以上四个步骤后，在iOS模拟器中看到成功完成账号登录操作，这说明我们的执行命令没有问题，可以用于编写自动化测试代码。整合起来，测试脚本就是下面这样。

```ruby
button_exact('My Account').click
button_exact('Login').click
tag('UIATextField').type 'leo.lee@debugtalk.com'
tag('UIASecureTextField').type '12345678'
button_exact('Login').click
```

将以上脚本保存为`login.rb`文件。

但当我们直接运行`login.rb`文件时，并不能运行成功。原因很简单，脚本中的`button_exact`、`tag`这些方法并没有定义，我们在文件中也没有引入相关库文件。

在上一篇文章中有介绍过，通过`arc`启动虚拟机时，会从`appium.txt`中读取虚拟机的配置信息。类似的，我们在脚本中执行自动化测试时，也会加载虚拟机，因此同样需要在脚本中指定虚拟机的配置信息，并初始化`Appium Driver`的实例。

初始化代码可以通过`Appium Inspector`生成，基本上为固定模式，我们暂时不用深究。

添加初始化部分的代码后，测试脚本如下所示。

```ruby
require 'rubygems'
require 'appium_lib'

capabilities = {
  'appium-version' => '1.0',
  'platformName' => 'iOS',
  'platformVersion' => '9.3',
}
Appium::Driver.new(caps: capabilities).start_driver
Appium.promote_appium_methods Object

# testcase: login
button_exact('My Account').click
button_exact('Login').click
tag('UIATextField').type 'leo.lee@debugtalk.com'
tag('UIASecureTextField').type '123456'
button_exact('Login').click

driver_quit
```

## 优化测试脚本：加入等待机制

如上测试脚本编写好后，在Terminal中运行`ruby login.rb`，就可以执行脚本了。

运行命令后，会看到iOS虚拟机成功启动，接着App成功进行加载，然后自动按照前面设计的路径，执行系统登录流程。

但是，在实际操作过程中，发现有时候运行脚本时会出现找不到控件的异常，异常信息如下所示：

```shell
➜ ruby login.rb
/Library/Ruby/Gems/2.0.0/gems/appium_lib-8.0.2/lib/appium_lib/common/helper.rb:218:in `_no_such_element': An element could not be located on the page using the given search parameters. (Selenium::WebDriver::Error::NoSuchElementError)
	from /Library/Ruby/Gems/2.0.0/gems/appium_lib-8.0.2/lib/appium_lib/ios/helper.rb:578:in `ele_by_json'
	from /Library/Ruby/Gems/2.0.0/gems/appium_lib-8.0.2/lib/appium_lib/ios/helper.rb:367:in `ele_by_json_visible_exact'
	from /Library/Ruby/Gems/2.0.0/gems/appium_lib-8.0.2/lib/appium_lib/ios/element/button.rb:41:in `button_exact'
	from /Library/Ruby/Gems/2.0.0/gems/appium_lib-8.0.2/lib/appium_lib/driver.rb:226:in `rescue in block (4 levels) in promote_appium_methods'
	from /Library/Ruby/Gems/2.0.0/gems/appium_lib-8.0.2/lib/appium_lib/driver.rb:217:in `block (4 levels) in promote_appium_methods'
	from login.rb:28:in `<main>'
```

更奇怪的是，这个异常并不是稳定出现的，有时候能正常运行整个用例，但有时在某个步骤就会抛出找不到控件的异常。这是什么原因呢？为什么在`Appium Ruby Console`中单步操作时就不会出现这个问题，但是在执行脚本的时候就会偶尔出现异常呢？

原来，在我们之前的脚本中，两条命令之间并没有间隔时间，有可能前一条命令执行完后，模拟器中的应用还没有完成下一个页面的加载，下一条命令就又开始查找控件，然后由于找不到控件就抛出异常了。

这也是为什么我们在`Appium Ruby Console`中没有出现这样的问题。因为手工输入命令多少会有一些耗时，输入两条命令的间隔时间足够虚拟机中的APP完成下一页面的加载了。

那针对这种情况，我们要怎么修改测试脚本呢？难道要在每一行代码之间都添加休眠（sleep）函数么？

也不用这么麻烦，针对这类情况，`ruby_lib`实现了`wait`机制。将执行命令放入到`wait{}`中后，执行脚本时就会等待该命令执行完成后再去执行下一条命令。当然，等待也不是无休止的，如果等待30秒后还是没有执行完，仍然会抛出异常。

登录流程的测试脚本修改后如下所示（已省略初始化部分的代码）：

```ruby
wait { button_exact('My Account').click }
wait { button_exact('Login').click }
wait { tag('UIATextField').type 'leo.lee@debugtalk.com' }
wait { tag('UIASecureTextField').type '123456' }
wait { button_exact('Login').click }
```

对脚本添加`wait`机制后，之前出现的找不到控件的异常就不再出现了。

## 优化测试脚本：加入结果检测机制

然而，现在脚本仍然不够完善。

我们在`Appium Ruby Console`中手工执行命令后，都是由人工肉眼确认虚拟机中APP是否成功进入下一个页面，或者返回结果是否正确。

但是在执行自动化测试脚本时，我们不可能一直去盯着模拟器。因此，我们还需要在脚本中加入结果检测机制，通过脚本实现结果正确性的检测。

具体怎么做呢？

原理也很简单，只需要在下一个页面中，寻找一个在前一个页面中没有的控件。

例如，由A页面跳转至B页面，在B页面中会存在“Welcome”的文本控件，但是在A页面中是没有这个“Welcome”文本控件的；那么，我们就可以在脚本中的跳转页面语句之后，加入一条检测“Welcome”文本控件的语句；后续在执行测试脚本的时候，如果页面跳转失败，就会因为找不到控件而抛出异常，我们也能通过这个异常知道测试执行失败了。

当然，对下一页面中的控件进行检测时同样需要加入等待机制的。

登录流程的测试脚本修改后如下所示（已省略初始化部分的代码）：

```ruby
wait { button_exact('My Account').click }
wait { text_exact 'System Settings' }

wait { button_exact('Login').click }
wait { button_exact 'Forget password?' }

wait { tag('UIATextField').type 'leo.lee@debugtalk.com' }
wait { tag('UIASecureTextField').type '12345678' }
wait { button_exact('Login').click }
wait { text_exact 'My Message' }
```

至此，系统登录流程的自动化测试脚本我们就编写完成了。

## To be continued ...

在本文中，我们通过系统登录这一典型功能点，演示了编写自动化测试用例的整个流程。

在下一篇文章中，我们还会对自动化测试脚本的结构进行进一步优化，并实现测试代码工程化。
