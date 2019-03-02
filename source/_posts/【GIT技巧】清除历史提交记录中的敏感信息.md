---
title: 【GIT技巧】清除历史提交记录中的敏感信息
permalink: post/clean-sensitive-data-from-git-history-commits
date: 2017/03/17
categories:
  - Development
tags:
  - Git
  - GitHub
---

![](../images/GitHub_hacker.jpg)

## 背景介绍

在使用GitHub的过程中，假如某次提交代码时不小心将密码或`SSH-key`提交进了公共仓库。当然，希望这种事情永远也不会发生，但是如果真遇到了，该怎么办呢？

如果发现得及时，本地提交后还没有推送到GitHub远程仓库的话，这种情况还好处理，直接修改代码后通过`git commit --amend`即可。

但如果发现时已经推送到了GitHub远程仓库，或者已过了许久，后续有了很多新的`commits`，这种情况就会比较复杂了。

错误的方式是，直接在当前代码中去除敏感信息，然后再提交到代码仓库中。这样的做法只能在最新的代码中去除了敏感信息，在git历史记录中仍然保存着敏感信息。

当然，也可以选择直接将整个仓库删除了。不过，看着昔日精心提交的代码记录，实在是难以下手。

要是可以只删除敏感信息部分，而不影响到其它提交记录就好了。事实上，`GIT`的确支持这种操作。

## 处理方式

实现的方式有两种，一是通过`git filter-branch`命令，另一种是采用一款开源的工具，`BFG Repo-Cleaner`。前者是`GIT`官方的实现方法，后者是一款采用`Scala`编写的工具，号称比`git filter-branch`更简单、更快捷。

### git filter-branch

先来看下[`git filter-branch`](https://help.github.com/articles/removing-sensitive-data-from-a-repository/)这种方式。假设要在所有历史提交记录中删除文件`PATH-TO-YOUR-FILE-WITH-SENSITIVE-DATA`，那么就可以采用如下命令：

```bash
$ git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch PATH-TO-YOUR-FILE-WITH-SENSITIVE-DATA' \
--prune-empty --tag-name-filter cat -- --all

> Rewrite 48dc599c80e20527ed902928085e7861e6b3cbe6 (266/266)
> Ref 'refs/heads/master' was rewritten
```

正常情况下，通过执行上面的命令，就可以在所有历史提交记录中彻底删除指定文件。如果要进一步确定的话，可以在`.git`目录中进行全局搜索，确保已彻底清理干净。

然后，就可以通过如下命令将本地代码推送到`GitHub`上，并强制覆盖掉所有历史记录。

```bash
$ git push origin --force --all
```

可以看出，采用`git filter-branch`的操作命令十分复杂（复杂到我也不想理会每个参数的具体含义），这还只是选择粗暴地将整个文件进行删除的情况。如果不想删除文件，而是单独修改特定文件特定内容的话，操作会更加复杂，如有兴趣可查看[`git官方文档`](https://git-scm.com/docs/git-filter-branch)。

### BFG Repo-Cleaner

估计也是因为官方的`git filter-branch`太过复杂，于是`Roberto Tyley`开发了[`BFG Repo-Cleaner`](https://rtyley.github.io/bfg-repo-cleaner/)这款工具。该工具是专门针对移除历史记录的需求而产生的，这可以从其简介中看出来。

> Removes large or troublesome blobs like git-filter-branch does, but faster. And written in Scala

使用`BFG Repo-Cleaner`之前，需要先下载[`BFG's jar`](https://rtyley.github.io/bfg-repo-cleaner/#download)(requires Java 7 or above)。

如果想实现前面例子中同样的功能，删除文件`PATH-TO-YOUR-FILE-WITH-SENSITIVE-DATA`，可以通过如下命令实现：

```bash
$ java -jar bfg.jar --delete-files PATH-TO-YOUR-FILE-WITH-SENSITIVE-DATA my-repo.git
```

如果不想删除文件，而是单独修改特定文件特定内容的话，就可以通过如下命令实现：

```
$ java -jar bfg.jar --replace-text replacements.txt my-repo.git
```

在`replacements.txt`文件中，应包含所有需要替换的内容，格式如下（不包含注释内容）：

```bash
PASSWORD1                       # Replace with '***REMOVED***' (default)
PASSWORD2==>examplePass         # replace with 'examplePass' instead
PASSWORD3==>                    # replace with the empty string
regex:password=\w+==>password=  # Replace, using a regex
regex:\r(\n)==>$1               # Replace Windows newlines with Unix newlines
```

通过执行上述命令，`BFG Repo-Cleaner`就会扫描代码仓库的所有历史提交记录，并按照`replacements.txt`文件中的映射进行替换操作。

通过对比可以看到，`BFG Repo-Cleaner`的确是更加简洁，这也是`GitHub`官方推荐的方式。不过，在`BFG Repo-Cleaner`的介绍文档中也说了，该工具的优势在于简单和快捷，从功能强大的角度来讲，它是比不上`git-filter-branch`的，有些操作也只能通过`git-filter-branch`完成。

如需了解`BFG Repo-Cleaner`的更多用法，可详细阅读其[文档](https://rtyley.github.io/bfg-repo-cleaner/)。

## 写在末尾

不要问我为啥写了这么一篇博客，让我再哭一会儿。我也真心地希望大家永远不会用到这些工具。

小心驶得万年船，共勉！

## 阅读更多

- https://rtyley.github.io/bfg-repo-cleaner/
- https://git-scm.com/docs/git-filter-branch
- https://help.github.com/articles/removing-sensitive-data-from-a-repository/
- http://www-cs-students.stanford.edu/~blynn/gitmagic/ch05.html#_8230_and_then_some
