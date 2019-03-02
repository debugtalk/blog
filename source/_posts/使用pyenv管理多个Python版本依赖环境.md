---
title: 使用 pyenv 管理多个 Python 版本依赖环境
permalink: post/use-pyenv-manage-multiple-python-virtualenvs
date: 2017/03/25
categories:
  - Development
tags:
  - Python
  - pyenv
---

## 背景

从接触Python以来，一直都是采用[`virtualenv`](https://virtualenv.pypa.io/en/stable/)和[`virtualenvwrapper`](https://pypi.python.org/pypi/virtualenvwrapper)来管理不同项目的依赖环境，通过`workon`、`mkvirtualenv`等命令进行虚拟环境切换，很是愉快。

然而，最近想让项目能兼容更多的Python版本，例如至少同时兼容`Python2.7`和`Python3.3+`，就发现采用之前的方式行不通了。

最大的问题在于，在本地计算机同时安装`Python2.7`和`Python3`后，即使分别针对两个Python版本安装了`virtualenv`和`virtualenvwrapper`，也无法让两个Python版本的`workon`、`mkvirtualenv`命令同时生效。另外一方面，要想在本地计算机安装多个Python版本，会发现安装的成本都比较高，实现方式也不够优雅。

幸运地是，针对该痛点，已经存在一个比较成熟的方案，那就是[`pyenv`](https://github.com/pyenv/pyenv)。

如下是官方的介绍。

> pyenv lets you easily switch between multiple versions of Python. It's simple, unobtrusive, and follows the UNIX tradition of single-purpose tools that do one thing well.

> This project was forked from [rbenv](https://github.com/rbenv/rbenv) and [ruby-build](https://github.com/rbenv/ruby-build), and modified for Python.

本文就针对`pyenv`最核心的功能进行介绍。

## 基本原理

如果要讲解`pyenv`的工作原理，基本上采用一句话就可以概括，那就是：修改系统环境变量`PATH`。

对于系统环境变量`PATH`，相信大家都不陌生，里面包含了一串由冒号分隔的路径，例如`/usr/local/bin:/usr/bin:/bin`。每当在系统中执行一个命令时，例如`python`或`pip`，操作系统就会在`PATH`的所有路径中从左至右依次寻找对应的命令。因为是依次寻找，因此排在左边的路径具有更高的优先级。

而`pyenv`做的，就是在`PATH`最前面插入一个`$(pyenv root)/shims`目录。这样，`pyenv`就可以通过控制`shims`目录中的Python版本号，来灵活地切换至我们所需的Python版本。

如果还想了解更多细节，可以查看[`pyenv`](https://github.com/pyenv/pyenv)的文档介绍及其源码实现。

## 环境初始化

`pyenv`的安装方式包括多种，重点推荐采用[`pyenv-installer`](https://github.com/pyenv/pyenv-installer)的方式，原因主要有两点：

- 通过`pyenv-installer`可一键安装`pyenv`全家桶，后续也可以很方便地实现一键升级；
- `pyenv-installer`的安装方式基于`GitHub`，可保证总是使用到最新版本的`pyenv`，并且`Python`版本库也是最新最全的。

### install && config

通过如下命令安装`pyenv`全家桶。

```bash
$ curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash
```

内容除了包含`pyenv`以外，还包含如下插件：

- `pyenv-doctor`
- `pyenv-installer`
- `pyenv-update`
- `pyenv-virtualenv`
- `pyenv-which-ext`

安装完成后，`pyenv`命令还没有加进系统的环境变量，需要将如下内容加到`~/.zshrc`中，然后执行`source ~/.zshrc`。

```
export PATH=$HOME/.pyenv/bin:$PATH
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

完成以上操作后，`pyenv`就安装完成了。

```bash
$ pyenv -v
pyenv 1.0.8
```

如果不确定`pyenv`的环境是否安装正常，可以通过`pyenv doctor`命令对环境进行检测。

```text
$ pyenv doctor
Cloning /Users/Leo/.pyenv/plugins/pyenv-doctor/bin/.....
Installing python-pyenv-doctor...

BUILD FAILED (OS X 10.12.3 using python-build 20160602)

Last 10 log lines:
checking for memory.h... yes
checking for strings.h... yes
checking for inttypes.h... yes
checking for stdint.h... yes
checking for unistd.h... yes
checking openssl/ssl.h usability... no
checking openssl/ssl.h presence... no
checking for openssl/ssl.h... no
configure: error: OpenSSL development header is not installed.
make: *** No targets specified and no makefile found.  Stop.
Problem(s) detected while checking system.
```

通过检测，可以发现本地环境可能存在的问题，例如，从以上输出可以看出，本地的`OpenSSL development header`还没有安装。根据提示的问题，逐一进行修复，直到检测不再出现问题为止。

### update

通过`pyenv update`命令，可以更新`pyenv`全家桶的所有内容。

```text
$ pyenv update
Updating /Users/Leo/.pyenv...
From https://github.com/yyuu/pyenv
 * branch            master     -> FETCH_HEAD
Already up-to-date.
Updating /Users/Leo/.pyenv/plugins/pyenv-doctor...
From https://github.com/yyuu/pyenv-doctor
 * branch            master     -> FETCH_HEAD
Already up-to-date.
Updating /Users/Leo/.pyenv/plugins/pyenv-installer...
From https://github.com/yyuu/pyenv-installer
 * branch            master     -> FETCH_HEAD
Already up-to-date.
Updating /Users/Leo/.pyenv/plugins/pyenv-update...
From https://github.com/yyuu/pyenv-update
 * branch            master     -> FETCH_HEAD
Already up-to-date.
Updating /Users/Leo/.pyenv/plugins/pyenv-virtualenv...
From https://github.com/yyuu/pyenv-virtualenv
 * branch            master     -> FETCH_HEAD
Already up-to-date.
Updating /Users/Leo/.pyenv/plugins/pyenv-which-ext...
From https://github.com/yyuu/pyenv-which-ext
 * branch            master     -> FETCH_HEAD
Already up-to-date.
```

## pyenv的核心使用方法

`pyenv`的主要功能如下：

```text
$ pyenv -h
Usage: pyenv <command> [<args>]

Some useful pyenv commands are:
   commands    List all available pyenv commands
   local       Set or show the local application-specific Python version
   global      Set or show the global Python version
   shell       Set or show the shell-specific Python version
   install     Install a Python version using python-build
   uninstall   Uninstall a specific Python version
   rehash      Rehash pyenv shims (run this after installing executables)
   version     Show the current Python version and its origin
   versions    List all Python versions available to pyenv
   which       Display the full path to an executable
   whence      List all Python versions that contain the given executable

See `pyenv help <command>' for information on a specific command.
For full documentation, see: https://github.com/yyuu/pyenv#readme
```

### 查看所有可安装的`Python`版本

```text
$ pyenv install --list
Available versions:
  2.1.3
  ...
  2.7.12
  2.7.13
  ...
  3.5.3
  3.6.0
  3.6-dev
  3.6.1
  3.7-dev
```

需要注意的是，如果是采用`brew`命令安装的`pyenv`，可能会发现`Python`版本库中没有最新的`Python`版本。所以建议还是通过`GitHub`源码方式安装`pyenv`。

### 安装指定版本的`Python`环境

```text
$ pyenv install 3.6.0
Downloading Python-3.6.0.tar.xz...
-> https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tar.xz
Installing Python-3.6.0...
Installed Python-3.6.0 to /Users/Leo/.pyenv/versions/3.6.0
```

### 查看当前系统中所有可用的`Python`版本

```text
$ pyenv versions
* system (set by /Users/Leo/.pyenv/version)
  2.7.13
  3.6.0
```

### 切换`Python`版本

`pyenv`可以从三个维度来管理`Python`环境，简称为：`当前系统`、`当前目录`、`当前shell`。这三个维度的优先级从左到右依次升高，即`当前系统`的优先级最低、`当前shell`的优先级最高。

如果想修改系统全局的Python环境，可以采用`pyenv global PYTHON_VERSION`命令。该命令执行后会在`$(pyenv root)`目录（默认为`~/.pyenv`）中创建一个名为`version`的文件（如果该文件已存在，则修改该文件的内容），里面记录着系统全局的Python版本号。

```bash
$ pyenv global 2.7.13
$ cat ~/.pyenv/version
2.7.13
$ pyenv version
2.7.13 (set by /Users/Leo/.pyenv/version)

$ pyenv global 3.6.0
$ cat ~/.pyenv/version
3.6.0
$ pyenv version
3.6.0 (set by /Users/Leo/.pyenv/version)
```

通常情况下，对于特定的项目，我们可能需要切换不同的Python环境，这个时候就可以通过`pyenv local PYTHON_VERSION`命令来修改`当前目录`的Python环境。命令执行后，会在当前目录中生成一个`.python-version`文件（如果该文件已存在，则修改该文件的内容），里面记录着当前目录使用的Python版本号。

```bash
$ cat ~/.pyenv/version
2.7.13
$ pyenv local 3.6.0
$ cat .python-version
3.6.0
$ cat ~/.pyenv/version
2.7.13
$ pyenv version
3.6.0 (set by /Users/Leo/MyProjects/.python-version)
$ pip -V
pip 9.0.1 from /Users/Leo/.pyenv/versions/3.6.0/lib/python3.6/site-packages (python 3.6)
```

可以看出，当前目录中的`.python-version`配置优先于系统全局的`~/.pyenv/version`配置。

另外一种情况，通过执行`pyenv shell PYTHON_VERSION`命令，可以修改`当前shell`的Python环境。执行该命令后，会在当前`shell session`（Terminal窗口）中创建一个名为`PYENV_VERSION`的环境变量，然后在`当前shell`的任意目录中都会采用该环境变量设定的Python版本。此时，`当前系统`和`当前目录`中设定的Python版本均会被忽略。

```bash
$ echo $PYENV_VERSION

$ pyenv shell 3.6.0
$ echo $PYENV_VERSION
3.6.0
$ cat .python-version
2.7.13
$ pyenv version
3.6.0 (set by PYENV_VERSION environment variable)
```

顾名思义，`当前shell`的Python环境仅在当前shell中生效，重新打开一个新的shell后，该环境也就失效了。如果想在`当前shell`中取消shell级别的Python环境，采用`unset`命令重置`PYENV_VERSION`环境变量即可。

```bash
$ cat .python-version
2.7.13
$ pyenv version
3.6.0 (set by PYENV_VERSION environment variable)

$ unset PYENV_VERSION
$ pyenv version
2.7.13 (set by /Users/Leo/MyProjects/.python-version)
```

## 管理多个依赖库环境

经过以上操作，我们在本地计算机中就可以安装多个版本的`Python`运行环境，并可以按照实际需求进行灵活地切换。然而，很多时候在同一个`Python`版本下，我们仍然希望能根据项目进行环境分离，就跟之前我们使用`virtualenv`一样。

在`pyenv`中，也包含这么一个插件，[`pyenv-virtualenv`](https://github.com/pyenv/pyenv-virtualenv)，可以实现同样的功能。

使用方式如下：

```bash
$ pyenv virtualenv PYTHON_VERSION PROJECT_NAME
```

其中，`PYTHON_VERSION`是具体的Python版本号，例如，`3.6.0`，`PROJECT_NAME`是我们自定义的项目名称。比较好的实践方式是，在`PROJECT_NAME`也带上Python的版本号，以便于识别。

现假设我们有`XDiff`这么一个项目，想针对`Python 2.7.13`和`Python 3.6.0`分别创建一个虚拟环境，那就可以依次执行如下命令。

```bash
$ pyenv virtualenv 3.6.0 py36_XDiff
$ pyenv virtualenv 2.7.13 py27_XDiff
```

创建完成后，通过执行`pyenv virtualenvs`命令，就可以看到本地所有的项目环境。

```bash
$ pyenv virtualenvs
  2.7.13/envs/py27_XDiff (created from /Users/Leo/.pyenv/versions/2.7.13)
* 3.6.0/envs/py36_XDiff (created from /Users/Leo/.pyenv/versions/3.6.0)
  py27_XDiff (created from /Users/Leo/.pyenv/versions/2.7.13)
  py36_XDiff (created from /Users/Leo/.pyenv/versions/3.6.0)
```

通过这种方式，在同一个Python版本下我们也可以创建多个虚拟环境，然后在各个虚拟环境中分别维护依赖库环境。

例如，`py36_XDiff`虚拟环境位于`/Users/Leo/.pyenv/versions/3.6.0/envs`目录下，而其依赖库位于`/Users/Leo/.pyenv/versions/3.6.0/lib/python3.6/site-packages`中。

```bash
$ pip -V
pip 9.0.1 from /Users/Leo/.pyenv/versions/3.6.0/lib/python3.6/site-packages (python 3.6)
```

后续在项目开发过程中，我们就可以通过`pyenv local XXX`或`pyenv activate PROJECT_NAME`命令来切换项目的`Python`环境。

```bash
➜  MyProjects pyenv local py27_XDiff
(py27_XDiff) ➜  MyProjects pyenv version
py27_XDiff (set by /Users/Leo/MyProjects/.python-version)
(py27_XDiff) ➜  MyProjects python -V
Python 2.7.13
(py27_XDiff) ➜  MyProjects pip -V
pip 9.0.1 from /Users/Leo/.pyenv/versions/2.7.13/envs/py27_XDiff/lib/python2.7/site-packages (python 2.7)
```

可以看出，切换环境后，`pip`命令对应的目录也随之改变，即始终对应着当前的Python虚拟环境。

对应的，采用`pyenv deactivate`命令退出当前项目的`Python`虚拟环境。

如果想移除某个项目环境，可以通过如下命令实现。

```bash
$ pyenv uninstall PROJECT_NAME
```

以上便是日常开发工作中常用的`pyenv`命令，基本可以满足绝大多数依赖库环境管理方面的需求。
