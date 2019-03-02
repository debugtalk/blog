---
title: 打造心目中理想的自动化测试框架（AppiumBooster）
permalink: post/build-ideal-app-automation-test-framework
date: 2016/09/07
categories:
  - Testing
  - 自动化测试
tags:
  - Appium
  - UI
  - AppiumBooster
---

## 前言

做过自动化测试的人应该都会有这样一种体会，要写个自动化demo测试用例很容易，但是要真正将自动化测试落地，对成百上千的自动化测试用例实现较好的可复用性和可维护性就很难了。

基于这一痛点，我开发了[`AppiumBooster`](https://github.com/debugtalk/AppiumBooster)框架。顾名思义，`AppiumBooster`基于`Appium`实现，但更简单和易于使用；测试人员不用接触任何代码，就可以直接采用简洁优雅的方式来编写和维护自动化测试用例。

原型开发完毕后，我将其应用在当前所在团队的项目上，并在使用的过程中，按照自己心目中理想的自动化测试框架的模样对其进行迭代优化，最终打磨成了一个自己还算用得顺手的自动化测试框架。

本文便是对`AppiumBooster`的核心特性及其设计思想进行介绍。在内容组织上，本文的各个部分相对独立，大家可直接选择自己感兴趣的部分进行阅读。

## UI交互基础

UI交互是自动化测试的基础，主要分为三部分内容：定位控件、操作控件、检测结果。

### 控件定位

定位控件时，统一采用元素ID进行定位。这里的ID包括`accessibility_id`或`accessibility_label`，需要在iOS工程项目中预先进行设置。

另外，考虑到控件可能出现延迟加载的情况，定位控件时统一执行`wait`操作；定位成功后会立即返回控件对象，定位失败时会进行等待并不断尝试定位，直到超时（30秒）后抛出异常。

```ruby
wait { id control_id }
```

源码路径：[`AppiumBooster/lib/pages/control.rb`](https://github.com/debugtalk/AppiumBooster/blob/master/lib/pages/control.rb)

### 控件操作

根据实践证明，UI的控件操作基本主要就是点击、输入和滑动，这三个操作基本上可以覆盖绝大多数场景。

- `scrollToDisplay`: 根据指定控件的坐标位置，对屏幕进行`上/下/左/右`滑动操作，直至将指定控件展示在屏幕中
- `click`: 通过控件ID定位到指定控件，并对指定控件进行`click`操作；若指定控件不在当前屏幕中，则先执行`scrollToDisplay`，再执行`click`操作
- `type(text)`: 在指定控件中输入字符串；若指定控件不在当前屏幕中，则先执行`scrollToDisplay`，再执行输入操作
- `tapByCoordinate`: 先执行`scrollToDisplay`，确保指定控件在当前屏幕中；获取指定控件的坐标值，然后对坐标进行`tap`操作
- `scroll(direction)`: 对屏幕进行指定方向的滑动

源码路径：[`AppiumBooster/lib/pages/actions.rb`](https://github.com/debugtalk/AppiumBooster/blob/master/lib/pages/actions.rb)

### 预期结果检查

每次执行一步操作后，需要对执行结果进行判断，以此来确定测试用例的各个步骤是否执行成功。

当前，`AppiumBooster`采用控件的ID作为检查对象，并统一封装到`check_elements(control_ids)`方法中。

在实际使用过程中，需要先确定当前步骤执行完成后的跳转页面的特征控件，即当前步骤执行前不存在该控件，但执行成功后的页面中具有该控件。然后在操作步骤描述的`expectation`属性中指定特征控件的ID。

具体地，在指定控件ID的时候还可以配合使用操作符（`!`,`||`,`&&`），以此实现多种复杂场景的检测。典型的预期结果描述形式如下：

- `A`: 预期控件A存在；
- `!A`: 预期控件A不存在；
- `A||B`: 预期控件A或控件B至少存在一个；
- `A&&B`: 预期控件A和控件B同时存在；
- `A&&!B`: 预期控件A存在，但控件B不存在；
- `!A&&!B`: 预期控件A和控件B都不存在。

源码路径：[`AppiumBooster/lib/pages/inner_screen.rb`](https://github.com/debugtalk/AppiumBooster/blob/master/lib/pages/inner_screen.rb)

## 测试用例引擎（YAML）

对于自动化测试而言，自动化测试用例的组织与管理是最为重要的部分，直接关系到自动化测试用例的可复用性和可维护性。

经过综合考虑，`AppiumBooster`从三个层面来描述测试用例，从低到高分别是`step`、`feature`和`testcase`；描述方式推荐使用`YAML`格式。

### steps（测试步骤描述）

首先是对于单一操作步骤的描述。

从UI层面来看，每一个操作步骤都可以归纳为三个方面：定位控件、操作控件和检查结果。

`AppiumBooster`的做法是，将App根据功能模块进行拆分，每一个模块单独创建一个`YAML`文件，并保存在`steps`目录下。然后，在每个模块中以控件为单位，分别进行定义。

现以如下示例进行详细说明。

```yaml
---
AccountSteps:
  enter Login page:
    control_id: tablecellMyAccountLogin
    control_action: click
    expectation: btnForgetPassword

  input test EmailAddress:
    control_id: txtfieldEmailAddress
    control_action: type
    data: leo.lee@debugtalk.com
    expectation: sectxtfieldPassword

  check if coupon popup window exists(optional):
    control_id: inner_screen
    control_action: has_control
    data: btnViewMyCoupons
    expectation: btnClose
    optional: true
```

其中，`AccountSteps`是steps模块名称，用于区分不同的steps模块，方便在`features`模块中进行引用。

描述单个步骤时，有三项是必不可少的：步骤名称、控件ID（`control_id`）和控件操作方式（`control_action`）。当控件操作方式为输入（`type`）时，则还需指定`data`属性，即输入内容。

在检查步骤执行结果方面，可通过在`expectation`属性中指定控件ID进行实现，前面在`预期结果检查`一节中已经详细介绍了使用方法。该属性可以置空或不进行填写，相当于不对当前步骤进行检测。

另外还有一个`optional`属性，对步骤指定该属性并设置为true时，当前步骤的执行结果不影响整个测试用例。

### features（功能点描述）

各个模块的单一操作步骤定义完毕后，虽然可以直接将多个步骤进行组合形成对测试场景的描述，即测试用例，但是操作起来会过于局限细节；特别是当测试用例较多时，可维护性是一个很大的问题。

`AppiumBooster`的做法是，将App根据功能模块进行拆分，每一个模块单独创建一个`YAML`文件，并保存在`features`目录下。然后，在每个模块中以功能点为单位，通过对steps模块中定义好的操作步骤进行引用并组合，即可实现对功能点的描述。

以`系统登录`功能为例，功能点的描述可采用如下形式。

```yaml
---
AccountFeatures:
  login with valid test account:
    - AccountSteps | enter My Account page
    - AccountSteps | enter Login page
    - AccountSteps | input test EmailAddress
    - AccountSteps | input test Password
    - AccountSteps | login
    - AccountSteps | close coupon popup window(optional)

  login with valid production account:
    - AccountSteps | enter My Account page
    - AccountSteps | enter Login page
    - AccountSteps | input production EmailAddress
    - AccountSteps | input production Password
    - AccountSteps | login
    - AccountSteps | close coupon popup window(optional)

  logout:
    - AccountSteps | enter My Account page
    - SettingsSteps | enter Settings page
    - AccountSteps | logout
```

其中，`AccountFeatures`是features模块名称，用于区分不同的features模块，方便在`testcase`中进行引用。

在引用steps模块的操作步骤时，需要同时指定steps模块名称和操作步骤的名称，并以`|`进行分隔。

### testcases（测试用例描述）

在功能点描述的基础上，`AppiumBooster`就可以在第三个层面，简单清晰地描述测试用例了。

具体做法很简单，针对每个测试用例创建一个`YAML`文件，并保存在`testcases`目录下。然后，通过对features模块中定义好的功能点描述进行引用并组合，即可实现对测试用例的描述。

同样的，在引用features模块的功能点时，也需要同时指定features模块名称和功能点的名称，并以`|`进行分隔。

如下示例便是实现了在商城中购买商品的整个流程，包括切换国家、登录、选择商品、添加购物车、下单完成支付等功能点。

```yaml
---
Buy Phantom 4:
  - SettingsFeatures | initialize first startup
  - SettingsFeatures | Change Country to China
  - AccountFeatures | login with valid account
  - AccountFeatures | Change Shipping Address to China
  - StoreFeatures | add phantom 4 to cart
  - StoreFeatures | finish order
  - AccountFeatures | logout
```

另外，在某些测试场景中可能需要重复进行某一个功能点的操作。虽然可以将需要重复的步骤多写几次，但会显得比较累赘，特别是重复次数较多时更是麻烦。

`AppiumBooster`的做法是，在测试用例的步骤中可指定执行次数，并以`|`进行分隔，如下例所示。

```yaml
---
Send random text messages:
  - SettingsFeatures | initialize first startup
  - AccountFeatures | login with valid test account
  - MessageFeatures | enter follower user message page
  - MessageFeatures | send random text message | 100
```

## 测试用例引擎（CSV）

基本上，`YAML`测试用例引擎已经可以很好地满足组织和管理自动化测试用例的需求。

但考虑到部分用户会偏向于使用表格的形式，因为表格看上去更直观一些，`AppiumBooster`同时还支持`CSV`格式的测试用例引擎。

### testcases（测试用例描述）

采用表格来编写测试用例时，只需要在任意表格工具，包括Microsoft Excel、iWork Numbers、WPS等，按照如下形式对测试用例进行描述。

![AppiumBooster CSV Testcase example](/images/AppiumBooster_CSV_Testcase_example.jpg)

然后，将表格内容另存为`CSV`格式的文件，并放置于`testcases`目录中即可。

可以看出，`CSV`格式的测试用例和`YAML`格式的测试用例是等价的，两者包含的信息内容完全相同。

在具体实现上，`AppiumBooster`在执行测试用例之前，也会将两个测试用例引擎的测试用例描述转换为相同的数据结构，然后再进行统一的操作。

统一转换后的数据结构如下所示：

```json
{
  "testcase_name": "Login and Logout",
  "features_suite": [
    {
      "feature_name": "login with valid account",
      "feature_steps": [
        {"control_id": "btnMenuMyAccount", "control_action": "click", "expectation": "tablecellMyAccountSystemSettings", "step_desc": "enter My Account page"},
        {"control_id": "tablecellMyAccountLogin", "control_action": "click", "expectation": "btnForgetPassword", "step_desc": "enter Login page"},
        {"control_id": "txtfieldEmailAddress", "control_action": "type", "data": "leo.lee@debugtalk.com", "expectation": "sectxtfieldPassword", "step_desc": "input EmailAddress"},
        {"control_id": "sectxtfieldPassword", "control_action": "type", "data": 12345678, "expectation": "btnLogin", "step_desc": "input Password"},
        {"control_id": "btnLogin", "control_action": "click", "expectation": "tablecellMyMessage", "step_desc": "login"},
        {"control_id": "btnClose", "control_action": "click", "expectation": nil, "optional": true, "step_desc": "close coupon popup window(optional)"}
      ]
    },
    {
      "feature_name": "logout",
      "feature_steps": [
        {"control_id": "btnMenuMyAccount", "control_action": "click", "expectation": "tablecellMyAccountSystemSettings", "step_desc": "enter My Account page"},
        {"control_id": "tablecellMyAccountSystemSettings", "control_action": "click", "expectation": "txtCountryDistrict", "step_desc": "enter Settings page"},
        {"control_id": "btnLogout", "control_action": "click", "expectation": "uiviewMyAccount", "step_desc": "logout"}
      ]
    }
  ]
}
```

### 测试用例转换器（`yaml2csv`）

既然`CSV`格式的测试用例和`YAML`格式的测试用例是等价的，那么两者之间的转换也就容易实现了。

当前，`AppiumBooster`支持将`YAML`格式的测试用例转换为`CSV`格式的测试用例，只需要执行一条命令即可。

```bash
$ ruby start.rb -c "yaml2csv" -f ios/testcases/login_and_logout.yml
```

## 过程记录及结果存储

在自动化测试执行过程中，应尽量对测试用例执行过程进行记录，方便后续对问题根据定位和追溯。

### 过程记录方式

当前，`AppiumBooster`已实现的记录形式有如下三种：

- logger模块：可指定日志级别对测试过程进行记录
- 截图功能：测试用例运行过程中，在每个步骤执行完成后进行截图
- DOM source：测试用例运行过程中，在每个步骤执行完成后保存当前页面的DOM内容

### 测试结果存储

由于`Appium`分为Server端和Client端，因此`AppiumBooster`在记录日志的时候也将日志分为了三份：

- `appium_server.log`: Appium Server端的日志，这部分日志是由`Appium框架`打印的
- `appium_booster.log`: 包括测试环境初始化和测试用例执行记录，这部分日志是由`AppiumBooster`中采用logger模块打印的
- `client_server.log`: 同时记录`AppiumBooster`和`Appium框架`的日志，相当于`appium_server.log`和`appium_booster.log`的并集，优点在于可以清晰地看到测试用例执行过程中Client端和Server端的通讯交互过程

另外，当测试用例执行失败时，`AppiumBooster`会将执行失败的步骤截图和日志提取出来，单独保存到`errors`文件夹中，方便问题追溯。

具体地，每次执行测试前，`AppiumBooster`会在指定的`results`目录下创建一个以当前时间（`%Y-%m-%d_%H:%M:%S`）命名的文件夹，存储结构如下所示。

```
2016-08-28_16:28:48
├── appium_server.log
├── appium_booster.log
├── client_server.log
├── errors
│   ├── 16_31_29_btnLogin.click.dom
│   ├── 16_31_29_btnLogin.click.png
│   ├── 16_32_03_btnMenuMyAccount.click.dom
│   └── 16_32_03_btnMenuMyAccount.click.png
├── screenshots
│   ├── 16_30_34_tablecellMyAccountLogin.click.png
│   ├── 16_30_41_txtfieldEmailAddress.type_leo.lee@debugtalk.com.png
│   ├── 16_30_48_sectxtfieldPassword.type_123456.png
│   ├── 16_31_29_btnLogin.click.png
│   └── 16_32_03_btnMenuMyAccount.click.png
└── xmls
    ├── 16_30_34_tablecellMyAccountLogin.click.dom
    ├── 16_30_41_txtfieldEmailAddress.type_leo.lee@debugtalk.com.dom
    ├── 16_30_48_sectxtfieldPassword.type_123456.dom
    ├── 16_31_29_btnLogin.click.dom
    └── 16_32_03_btnMenuMyAccount.click.dom
```

对于每一个测试步骤的截图和DOM，存储文件命名格式为`%H_%M_%S_ControlID.ControlAction`。采用这种命名方式有两个好处：

- 文件通过时间排序，对应着测试用例执行的步骤顺序
- 可以在截图或DOM中直观地看到每一步操作指令对应的执行结果

## 环境初始化

### Appium Server

在执行自动化测试时，某些情况下可能会造成`Appium Server`出现异常情况（e.g. 500 error），并影响到下一次测试的执行。

为了避免这类情况，`AppiumBooster`在每次执行测试前，会强制性地对`Appium Server`进行重启。方式也比较简单暴力，运行测试之前先检查系统是否有`bin/appium`的进程在运行，如果有，则先kill掉该进程，然后再启动`Appium Server`。

需要说明的是，由于`Appium Server`的启动需要一定时间，为了防止运行`Appium Client`时`Appium Server`还未初始化完毕，因此启动`Appium Server`后最好能等待一段时间（e.g. sleep 10s）。

### `iOS/Android`模拟器

在模拟器中运行一段时间后，也会存在缓存数据和文件，可能会对下一次测试造成影响。

为了避免这类情况，`AppiumBooster`在每次执行测试前，会先删除已存在的模拟器，然后再用指定的模拟器配置创建新的模拟器。

对于iOS模拟器，`AppiumBooster`通过调用`xcrun simctl`命令的方式来对模拟器进行操作，基本原理如下所示。

```bash
# delete iOS simulator: xcrun simctl delete device_id
$ xcrun simctl delete F2F53866-50A5-4E0F-B164-5AC1702AD1BD
# create iOS simulator: xcrun simctl create device_type device_type_id runtime_id
$ xcrun simctl create 'iPhone 5' 'com.apple.CoreSimulator.SimDeviceType.iPhone-5' 'com.apple.CoreSimulator.SimRuntime.iOS-9-3'
```

其中，`device_id`/`device_type_id`/`runtime_id`这些属性值可以通过执行`xcrun simctl list`命令获取得到。

```bash
$ xcrun simctl list
== Device Types ==
iPhone 5s (com.apple.CoreSimulator.SimDeviceType.iPhone-5s)
iPhone 6 (com.apple.CoreSimulator.SimDeviceType.iPhone-6)
== Runtimes ==
iOS 8.4 (8.4 - 12H141) (com.apple.CoreSimulator.SimRuntime.iOS-8-4)
iOS 9.3 (9.3 - 13E230) (com.apple.CoreSimulator.SimRuntime.iOS-9-3)
== Devices ==
-- iOS 8.4 --
    iPhone 5s (E1BD9CC5-8E95-408F-849C-B0C6A44D669A) (Shutdown)
-- iOS 9.3 --
    iPhone 5s (BAFEFBE1-3ADB-45C4-9C4E-E3791D260524) (Shutdown)
    iPhone 6 (F23B3F85-7B65-4999-9F1C-80111783F5A5) (Shutdown)
== Device Pairs ==
```

## 增强特性

除了以上基础特性，`AppiumBooster`还支持一些辅助特性，可以增强测试框架的使用体验。

### Data参数化

在某些场景下，测试用例执行时需要动态获取数值。例如，注册账号的测试用例中，每次执行测试用例时需要保证用户名为未注册的，常见的做法就是在注册用户名中包含时间戳。

`AppiumBooster`的做法是，可以在测试步骤的`data`字段中，传入Ruby表达式，格式为`${ruby_expression}`。在执行测试用例时，会先对`ruby_expression`进行`eval`计算，然后用计算得到的值作为实际参数。

回到刚才的注册账号测试用例，填写用户名的步骤就可以按照如下形式指定参数。

```
input test EmailAddress:
  control_id: txtfieldEmailAddress
  control_action: type
  data: ${Time.now.to_i}@debugtalk.com
  expectation: sectxtfieldPassword
```

实际执行测试用例时，`data`就会参数化为`1471318368@debugtalk.com`的形式。

### 全局参数配置

对于某些配置参数，例如系统的登录账号密码等，虽然可以直接填写到测试用例的`steps`中，但是终究不够灵活。特别是当存在多个测试用例引用同一个参数时，涉及到参数改动时就需要同时修改多个地方。

更好的做法是，将此类参数提取出来，在统一的地方进行配置。在`AppiumBooster`中，可以在`config.yml`文件中配置全局参数。

```yaml
---
TestEnvAccount:
  UserName: test@debugtalk.com
  Password: 123456

ProductionEnvAccount:
  UserName: production@debugtalk.com
  Password: 12345678
```

然后，在测试用例的`steps`就可以采用如下形式对全局参数进行引用。

```
---
AccountSteps:
  input test EmailAddress:
    control_id: txtfieldEmailAddress
    control_action: type
    data: ${config.TestEnvAccount.UserName}
    expectation: sectxtfieldPassword

  input test Password:
    control_id: sectxtfieldPassword
    control_action: type
    data: ${config.TestEnvAccount.Password}
    expectation: btnLogin
```

### optional选项

在执行测试用例时，有时候可能会存在这样的场景：某个步骤作为非必要步骤，当其执行失败时，我们并不想将测试用例判定为不通过。

基于该场景，在测试用例设计表格中增加了`optional`参数。该参数值默认不用填写。但如果在某个步骤对应的optional栏填写了true值后，那么该步骤就会作为非必要步骤，其执行结果不会影响整个用例的执行结果。

例如，在电商类APP中，某些账号有优惠券，登录系统后，会弹出优惠券的提示框；而有的账号没有优惠券，登录后就不会有这样的弹框。那么关闭优惠券弹框的步骤就可以将其`optional`参数设置为true。

```yaml
---
AccountSteps:
  close coupon popup window(optional):
    control_id: btnClose
    control_action: click
    expectation: !btnViewMyCoupons
    optional: true
```

## 命令行工具

`AppiumBooster`通过在命令行中进行调用。

```bash
$ ruby start.rb -h
Usage: start.rb [options]
    -p, --app_path <value>           Specify app path
    -t, --app_type <value>           Specify app type, ios or android
    -f, --testcase_file <value>      Specify testcase file(s)
    -d, --output_folder <value>      Specify output folder
    -c, --convert_type <value>       Specify testcase converter, yaml2csv or csv2yaml
        --disable_output_color       Disable output color
```

### 执行测试用例

指定执行测试用例时支持多种方式，常见的几种使用方式示例如下：

```bash
$ cd ${AppiumBooster}
# 执行指定的测试用例文件（绝对路径）
$ ruby run.rb -p "ios/app/test.zip" -f "/Users/Leo/MyProjects/AppiumBooster/ios/testcases/login.yml"

# 执行指定的测试用例文件（相对路径）
$ ruby run.rb -p "ios/app/test.zip" -f "ios/testcases/login.yml"

# 执行所有yaml格式的测试用例文件
$ ruby run.rb -p "ios/app/test.zip" -f "ios/testcases/*.yml"

# 执行ios目录下所有csv格式的测试用例文件
$ ruby run.rb -p "ios/app/test.zip" -t "ios" -f "*.csv"
```

### 测试用例转换

将YAML格式的测试用例转换为CSV格式的测试用例：

```bash
$ ruby start.rb -c "yaml2csv" -f ios/testcases/login_and_logout.yml
```

## 总结

什么才算是心目中理想的自动化测试框架？我也没有确切的答案。

> 为什么要登山？
> 因为山在那里。
