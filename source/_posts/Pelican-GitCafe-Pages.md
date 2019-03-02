---
title: 使用 Pelican + GitCafe Pages 创建 Blog
permalink: post/Create-Blog-with-Pelican-and-GitCafe-Pages
date: 2013/10/03
categories:
  - 效率工具
tags:
  - Pelican
  - Git
---

## 博客系统的技术实现

博客系统采用 Pelican + GitCafe Pages 的技术架构。

其中，Pelican是一个由Python开发的用于生成静态页面的程序，可以将markdown等格式的文本生成模版格式化的html静态页面；而GitCafe提供的Pages服务可以通过项目的形式对Pelican生成的html文件进行托管，并可通过域名绑定的形式实现独立域名。

这种实现方式与 Jekyll + Github Pages 的实现方式大致相同，差别在于不同的静态页面生成系统和不同的托管平台。而为什么选择GitCafe而非GitHub，是因为GitHub服务器在国外，访问速度较慢，且存在偶尔无法访问的情况。

## 博客系统的初始化

创建 Blog 目录
```shell
mkdir 52test.org
cd 52test.org
```

初始化 Blog
```shell
pelican-quickstart
```

根据提示一步步输入相应的配置项，完成配置后在Blog目录下会生成配置文件pelicanconf.py。但通过pelican-quickstart配置的选项较少，更多的配置选项可以参照Pelican官方网站中的教程对pelicanconf.py进行编辑。

## 配置GitCafe

在使用GitCafe之前，需要对电脑的Git客户端进行配置，使电脑与远程GitCafe服务器完成认证。
通常地，我们采用SSH Key认证方式，这需要我们在使用GitCafe前须先建创自已的SSH key。

**进入SSH目录**

```shell
cd ~/.ssh
```

如果还没有 ~/.ssh 目录的话，请先手工创建一个 `mkdir ~/.ssh`

**生成新的SSH秘钥**

输入下面的代码，将命令中的 YOUR_EMAIL@YOUREMAIL.COM 改为你的Email地址，就可以生成新的key文件。当需要输入文件名的时候，点击回车键，即采用默认设置。
```shell
$ ssh-keygen -t rsa -C "YOUR_EMAIL@YOUREMAIL.COM"
Generating public/private rsa key pair.
Enter file in which to save the key (/Users/your_user_directory/.ssh/id_rsa):<回车就好>
```

然后系统会要输入加密串（Passphrase）
```shell
Enter passphrase (empty for no passphrase):<输入加密串>
Enter same passphrase again:<再次输入加密串>
```

最后看到如下的界面，即表示ssh key成功完成设置。
```shell
Your identification has been saved in /c/Users/your_user_directory/.ssh/id_rsa.
Your public key has been saved in /c/Users/your_user_directory/.ssh/id_rsa.pub.
The key fingerprint is:
15:81:d2:7a:c6:6c:0f:ec:b0:b6:d4:18:b8:d1:41:48 YOUR_EMAIL@YOUREMAIL.COM
```

SSH 秘钥生成结束后，可以在用户目录 (~/.ssh/) 下看到私钥 id_rsa 和公钥 id_rsa.pub 这两个文件，请妥善保管这两个文件。

**添加 SSH 公钥到 GitCafe**

用文本工具打开公钥文件 ~/.ssh/id_rsa.pub ，复制里面的所有内容到剪贴板。
进入 GitCafe->【账户设置】->【SSH 公钥管理】设置项，点击【添加新公钥】按钮，在Title文本框中输入标题，在Key文本框粘贴刚才复制的公钥字符串，输入GitCafe账户密码后按【保存】按钮完成操作。

**测试连接**

以上步骤完成后，就可以通过以下命令来测试是否可以连接 GitCafe 服务器了。
```shell
ssh -T git@gitcafe.com
```

如果是第一次连接的话，会出现以下警告，
```shell
The authenticity of host 'gitcafe.com (50.116.2.223)' can't be established.
#RSA key fingerprint is 84:9e:c9:8e:7f:36:28:08:7e:13:bf:43:12:74:11:4e.
#Are you sure you want to continue connecting (yes/no)?
```

正常情况下，显示的RSA key fingerprint应该与GitCafe提供的公钥一致，即84:9e:c9:8e:7f:36:28:08:7e:13:bf:43:12:74:11:4e。

如果没有问题，输入yes按回车就可以了，中间会提示输入 passphrase 口令。

最后，如果连接成功的话，会出现以下信息。
```shell
Hi USERNAME! You've successfully authenticated, but GitCafe does not provide shell access.
```

测试通过后，就可以通过Git客户端向GitCafe服务器上传博客内容了。

## 撰写文章

在 content 目录下用 Markdown 语法来写一篇文章，格式大致如下所示，文件保存后缀为`.md`。
```markdown
Title: My First Blog #标题
Date: 2013-10-05 #日期
Tags: test, blog #标签
Slug: my-first-post #URL

文章内容
```

## 生成html静态页面

创建输出目录
```shell
mkdir leolee
```

生成页面
```shell
pelican -s pelicanconf.py content -o leolee
```

## 上传到 GitCafe

先到 GitCafe 上创建一个与用户名相同的项目，例如GitCafe帐号名称为leolee，则创建一个名为leolee的项目。

进入静态页面输出目录
```shell
cd leolee
```

初始化 git 仓库
```shell
git init
```

创建一个gitcafe-pages的分支，并切换到该分支
```shell
git checkout -b gitcafe-pages
```

添加所有文件
```shell
git add .
```

提交
```shell
git commit -m "init"
```

添加远程仓库
```shell
git remote add origin git@gitcafe.com:leolee/leolee.git
```

push 到 GitCafe 仓库
```shell
git push -u origin gitcafe-pages
```

完成
push 完成以后就可以在访问 GitCafe Pages 地址了。 http://leolee.gitcafe.com

注：不要用 make html 来构建 Blog ，它会删除输出目录后重新生成 Blog ，这意味着会删除 .git 库。

## 更新博客

为了方便更新博客，可以创建了一个shell脚本，放置在Blog根目录下。在此创建的脚本名称为publish.sh，其内容如下所示。
```shell
pelican -s pelicanconf.py content -o leolee
cd leolee
git add .
git commit -m "Update"
git push
cd ../
```

更新博客时，只需要将新增博客的markdown文件放入content目录中，然后运行如下命令。
```shell
$ ./publish.sh
```

当然，在正式发布前通常会先利用本地服务器进行预览，确定没问题后再进行正式发布。

Makefile的内容如下所示：
```makefile
PY=python
PELICAN=pelican
BASEDIR=$(CURDIR)
INPUTDIR=$(BASEDIR)/content
OUTPUTDIR=$(BASEDIR)/output
CONFFILE=$(BASEDIR)/pelicanconf.py
PELICANOPTS=

help:
    @echo 'Makefile for a pelican Web site                                      '
    @echo '                                                                     '
    @echo 'Usage:                                                               '
    @echo '   make clean                Empty the OUTPUTDIR                     '
    @echo '   make generate             Generate static files for the web site  '
    @echo '   make serve                Serve site at http://localhost:8000     '

clean:
    @echo -n 'Cleaning Output folder..............'
    @rm -rf $(OUTPUTDIR)/*
    @echo ''
    @echo 'Done'

generate: clean
    $(PELICAN) $(INPUTDIR) -o $(OUTPUTDIR) -s $(CONFFILE) $(PELICANOPTS)

serve: generate
    cd $(OUTPUTDIR) && $(PY) -m pelican.server

.PHONY: help clean generate serve
```

要预览时，只需要输入如下命令：
```shell
$ make serve
```

然后在浏览器中访问 http://localhost:8000 即可进行本地预览。

## 参考文章
```url
[1]: http://riku.gitcafe.com/pelican-gitcafe.html
[2]: https://gitcafe.com/GitCafe/Help/wiki/%E5%A6%82%E4%BD%95%E5%AE%89%E8%A3%85%E5%92%8C%E8%AE%BE%E7%BD%AE-Git#wiki
```
