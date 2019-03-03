---
title: GitHub 权限校验失败给我的启发
permalink: post/trap-in-GitHub-authority-verification
date: 2016/06/14
categories:
  - Development
tags:
  - SSH
  - GitHub
  - HTTP(S)
---

## 背景描述

众所周知，在GitHub中，每个仓库都有两个地址，分别基于`HTTPS`协议和`SSH`协议，两个协议对应的URL地址（repository_url）形式如下所示：

```bash
# HTTPS
https://github.com/XY/MobileStore.git
# SSH
git@github.com:XY/MobileStore.git
```

正常情况下，只要在本地正确地配置好了`git`账号，采用这两个地址中的任意一个，都可以通过`git clone repository_url`获取代码。

但最近我在Macbook Air中`clone`公司托管在GitHub私有库中的代码时，发现无法通过`HTTPS`协议的地址`clone`代码，始终提示`remote: Repository not found.`的错误。

```bash
➜ git clone https://github.com/XY/MobileStore.git
Cloning into 'MobileStore'...
remote: Repository not found.
fatal: repository 'https://github.com/XY/MobileStore.git/' not found
```

首先，这个代码仓库是确实存在的，而且地址肯定也是没有问题的，通过URL地址也能在浏览器中访问到对应的GitHub仓库页面。

其次，在本地对`git`的配置也是没有问题的，通过`SSH`协议的地址是可以正常`clone`代码的。

```bash
➜ git clone git@github.com:XY/MobileStore.git
Cloning into 'MobileStore'...
Warning: Permanently added the RSA host key for IP address '192.30.252.131' to the list of known hosts.
remote: Counting objects: 355, done.
remote: Compressing objects: 100% (3/3), done.
```

并且，如果在`HTTPS`协议的URL地址中加上GitHub账号，也是可以正常`clone`代码的。

```bash
➜ git clone https://leolee@github.com/XY/MobileStore.git
Cloning into 'MobileStore'...
remote: Counting objects: 355, done.
remote: Compressing objects: 100% (3/3), done.
```

更奇怪的是，在我的另一台Mac Mini中，采用同样的账号配置，两种协议的URL地址却都能正常`clone`代码，仔细地对比了两台电脑的`git`配置，都是一样的。

```bash
➜ cat ~/.git-credentials
https://leolee:340d247cxxxxxxxxf39556e38fe2b0baxxxxxxxx@github.com
➜
➜ cat ~/.gitconfig
[credential]
	helper = store
```

那问题出在哪儿呢？

## 定位分析

通过Google得知，产生`remote: Repository not found.`报错的原因主要有两个，一是仓库地址错误，二是权限校验不通过。显然，第一个原因可以直接排除，在Macbook Air中出现该问题应该就是账号权限校验失败造成的。

对背景描述中的现象进行整理，重点关注两个疑点：

- 通过`HTTPS`协议的URL地址进行`git clone`时，系统没有提示让输入用户名密码，就直接返回权限校验失败的异常；
- 在`HTTPS`协议的URL地址中加上GitHub用户名，就可以正常`clone`，而且，系统也没有提示输入密码。

这说明，在系统中的某个地方，应该是保存了GitHub账号密码的，所以在未指定账号的情况下，`git clone`时系统就不再要求用户输入账号密码，而是直接读取那个保存好的账号信息；但是，那个保存的GitHub账号密码应该是存在问题的，这就造成采用那个账号信息去GitHub校验时无法通过，从而返回异常报错。

基于以上推测，寻找问题根源的当务之急是找到保存GitHub账号密码的地方。

通过查看Git官方文档，存储Git用户信息的地方有三个：

- `/etc/gitconfig`：存储当前系统所有用户的git配置信息；
- `~/.gitconfig`或`~/.config/git/config`：存储当前用户的git配置信息；
- 仓库的Git目录中的config文件（即`repo/.git/config`）：存储当前仓库的git配置信息。

这三个配置项的优先级从上往下依次上升，即`repo/.git/config`会覆盖`~/.gitconfig`中的配置，`~/.gitconfig`会覆盖`/etc/gitconfig`中的配置。

回到当前问题，由于还没有进入到具体的Git仓库，因此`repo/.git/config`可直接排除；然后是查看当前用户的git配置，在当前用户HOME目录下没有`~/.config/git/config`文件，只有`~/.gitconfig`，不过在`~/.gitconfig`中并没有账号信息；再去查看系统级的git配置信息，即`/etc/gitconfig`文件，但发现当前系统中并没有该文件。

找遍了Git用户信息可能存储的地方，都没有看到账号配置信息，那还可能存储在哪儿呢？

这时基本上是毫无思路了，只能靠各种胡乱猜测，甚至尝试采用Wireshark分别在两台Mac上对`git clone`的过程进行抓包，对比通讯数据的差异，但都没有找到答案。

最后，无意中想到了Mac的`Keychain`机制。在Mac OSX的`Keychain`中，可以保存用户的账号密码等`credentials`，那git账号会不会也保存到`Keychain`中了呢？

在Macbook Air中打开`Keychain Access`应用软件，搜索`github`，果然发现存在记录。

![Mac Keychain of GitHub](/images/Mac_Keychain_GitHub.jpg)

而且，`github.com`这一项还存在两条记录。一条是我的个人账号`debugtalk`，另一条是公司的工作账号`leolee`。

**至此，真相大白！！！**

在我的Macbook Air中，`Keychain Access`中保存了我的GitHub个人账号（`debugtalk`），该账号是没有权限访问公司私有仓库的。但是在Terminal中执行`git clone`命令时，系统优先读取了我的个人账号，并用该账号向GitHub发起校验请求，从而造成读取公司私有仓库时权限校验失败。然而，在`HTTPS`协议的URL地址中加上GitHub工作账号（`leolee`）时，由于此时指定了账号名称，因此在`Keychain`中读取账号信息时就可以找到对应账号（包含密码），并且在无需输入密码的情况下就能成功通过GitHub的权限校验，进而成功`clone`得到代码。

原因弄清楚之后，解决方式就很简单了，在`Keychain`中删除个人账号，然后就正常了。

## 总结回顾

但是，问题真的解决了么？

并没有！

简单粗暴地在Keychain中将个人GitHub账号删除了，虽然再次访问公司代码仓库时正常了，那我要再访问个人仓库时该怎么办呢？

貌似并没有清晰的思路。虽然网上也有不少操作指导教程，但是对于操作背后的原理，还是有很多不清晰的地方。

再回到前面的背景描述，以及定位问题的整个过程，不由地悲从中来。使用GitHub好歹也有好几年了，但是连最基本的概念都还一头雾水，所以遇到问题后只能靠瞎猜，东碰西撞，最后瞎猫碰到死耗子。

GitHub的`HTTPS`协议和`SSH`协议，这本来就对应着两套完全独立的权限校验方式，而我在`HTTPS`协议不正常的情况下还去查看`SSH`协议，这本来就实属多余。

借助这次“掉坑”的经历，我对`Git`权限校验的两种方式重头进行了梳理，并单独写了一篇博客，《深入浅出Git权限校验》，虽然花了些时间，但总算是扫清了萦绕多年的迷雾，感觉倍儿爽！

如果你也对`Git的权限校验`没有清晰的了解，遇到权限校验出错时只能“换一种方法试试”，也不知道怎么让一台计算机同时支持多个GitHub账号，那么也推荐看下那篇博客。

在微信公众号`debugtalk`中输入`Git权限校验`，获取《深入浅出Git权限校验》。
