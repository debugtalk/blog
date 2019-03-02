---
title: 深入浅出 Git 权限校验
permalink: post/head-first-git-authority-verification
date: 2016/06/15
categories:
  - Development
tags:
  - SSH
  - GitHub
  - HTTP(S)
---

借助上次“掉坑”的经历，我对Git权限校验的两种方式重头进行了梳理，形成了这篇总结记录。

在本地计算机与GitHub（或GitLab）进行通信时，传输主要基于两种协议，`HTTPS`和`SSH`，对应的仓库地址就是`HTTPS URLs`和`SSH URLs`。

首先需要强调的是，`HTTPS URLs`和`SSH URLs`对应的是两套完全独立的权限校验方式，主要的区别就是`HTTPS URLs`采用账号密码进行校验，`SSH URLs`采用`SSH`秘钥对进行校验。平时使用的时候我们可以根据实际情况，选择一种即可。

## HTTPS URLs

GitHub官方推荐采用`HTTPS URLs`的方式，因为该种方式适用面更广（即使在有防火墙或代理的情况下也同样适用），使用更方便（配置更简单）。

采用`HTTPS URLs`地址`clone`/`fetch`/`pull`/`push`仓库时，事先无需对本地系统进行任何配置，只需要输入GitHub的账号和密码即可。不过如果每次都要手动输入账号密码，也是一件很繁琐的事情。

好在已经有多个机制可以让操作不用这么麻烦。

在Mac系统中，在启用`Keychain`机制的情况下，首次输入GitHub账号密码后，认证信息就会自动保存到系统的`Keychain`中，下次再次访问仓库时就会自动读取`Keychain`中保存的认证信息。

在非Mac系统中，虽然没有`Keychain`机制，但是Git提供了`credential helper`机制，可以将账号密码以cache的形式在内存中缓存一段时间（默认15分钟），或者以文件的形式存储起来（`~/.git-credentials`）。当然，Mac系统如果不启用`Keychain`机制，也可以采用这种方式。

```sh
# cache credential in memory
$ git config --global credential.helper cache
# store credential in ~/.git-credential
$ git config --global credential.helper store
```

在`credential.helper`设置为`store`的情况下，首次输入GitHub账号密码后，就会自动保存到`~/.git-credentials`文件中，保存形式为`https://user:pass@github.com`；下次再次访问仓库时就会自动读取`~/.git-credentials`中保存的认证信息。

另一个需要说明的情况是，如果在GitHub中开启了`2FA（two-factor authentication）`，那么在本地系统中输入GitHub账号密码时，不能输入原始的密码（即GitHub网站的登录密码），而是需要事先在GitHub网站中创建一个`Personal access token`，后续在访问代码仓库需要进行权限校验的时候，采用`access token`作为密码进行输入。

## SSH URLs

除了`HTTPS URLs`，还可以采用`SSH URLs`的方式访问GitHub代码仓库。

采用`SSH URLs`方式之前，需要先在本地计算机中生成`SSH keypair`（秘钥对，包括私钥和公钥）。默认情况下，生成的秘钥位于`$HOME/.ssh/`目录中，文件名称分别为`id_rsa`和`id_rsa.pub`，通常无需修改，保持默认即可。不过，如果一台计算机中存在多个秘钥对，就需要修改秘钥文件名，名称没有强制的命名规范，便于自己辨识即可。

如下是创建秘钥对的过程。

```bash
➜ ssh-keygen -t rsa -b 4096 -C "mail@debugtalk.com"
Generating public/private rsa key pair.
Enter file in which to save the key (/Users/Leo/.ssh/id_rsa): /Users/Leo/.ssh/debugtalk_id_rsa
Enter passphrase (empty for no passphrase): <myPassphrase>
Enter same passphrase again: <myPassphrase>
Your identification has been saved in /Users/Leo/.ssh/debugtalk_id_rsa.
Your public key has been saved in /Users/Leo/.ssh/debugtalk_id_rsa.pub.
The key fingerprint is:
SHA256:jCyEEKjlCU1klROnuBg+UH08GJ1u252rQMADdD9kYMo mail@debugtalk.com
The key's randomart image is:
+---[RSA 4096]----+
|+*BoBO+.         |
|o=oO=**          |
|++E.*+o.         |
|+ooo +o+         |
|.o. ..+oS. .     |
|  .  o. . o      |
|      .    .     |
|       .  .      |
|        ..       |
+----[SHA256]-----+
```

在创建秘钥的过程中，系统还建议创建一个名为`passphrase`的东西，这是用来干嘛的呢？

> 首先，单独采用密码肯定是不够安全的。如果密码太简单，那么就很容易被暴力破解，如果密码太复杂，那么用户就很难记忆，记录到小本子里面更不安全。

> 因此，`SSH keys`诞生了。`SSH`秘钥对的可靠性非常高，被暴力破解的可能性基本没有。不过，这要求用户非常谨慎地保管好私钥，如果别人使用你的计算机时偷偷地将你的私钥拷走了，那么就好比是别人拿到了你家里的钥匙，也能随时打开你家的门。

> 基于以上情况，解决办法就是在`SSH keys`之外再增加一个密码，即`passphrase`。只有同时具备`SSH private key`和`passphrase`的情况下，才能通过`SSH`的权限校验，这就大大地增加了安全性。当然，这个`passphrase`也不是必须的，在创建秘钥对时也可以不设置`passphrase`。

> 另外，如果每次权限校验时都要输入`passphrase`，这也是挺麻烦的。好在我们不用再担心这个问题，因为`ssh-agent`可以帮我们记住`passphrase`，Mac系统的Keychain也可以记住`passphrase`，这样我们在同一台计算机中就不用重新输入密码了。

秘钥对创建好以后，私钥存放于本地计算机（`~/.ssh/id_rsa`），将公钥（`~/.ssh/id_rsa.pub`）中的内容添加至GitHub账户。

```sh
# copy the contents of id_rsa.pub to the clipboard
➜ pbcopy < ~/.ssh/id_rsa.pub

# paste to GitHub
# Login GitHub, 【Settings】->【SSH and GPG keys】->【New SSH Key】
```

不过，如果此时检测本地计算机与GitHub的连接状态，会发现系统仍提示权限校验失败。

```bash
➜ ssh -T git@github.com
Permission denied (publickey).
```

这是因为在本地计算机与GitHub建立连接的时候，实际上是本机计算机的`ssh-agent`与GitHub服务器进行通信。虽然本地计算机有了私钥，但是`ssh-agent`并不知道私钥存储在哪儿。因此，要想正常使用秘钥对，需要先将私钥加入到本地计算机的`ssh-agent`中（添加过程中需要输入`passphrase`）。

```bash
# start ssh-agent in the background
➜ eval "$(ssh-agent -s)"
Agent pid 78370

➜ ssh-add ~/.ssh/id_rsa
Enter passphrase for /Users/Leo/.ssh/id_rsa: <myPassphrase>
Identity added: /Users/Leo/.ssh/id_rsa (/Users/Leo/.ssh/id_rsa)
```

添加完成后，就可以查看到当前计算机中存储的密钥。

```bash
➜ ssh-add -l
4096 SHA256:xRg49AgTxxxxxxxx8q2SPPOfxxxxxxxxRlBY /Users/Leo/.ssh/id_rsa (RSA)
```

再次检测本地计算机与GitHub的连接状态，校验就正常通过了。

```bash
➜ ssh -T git@github.com
Hi leolee! You've successfully authenticated, but GitHub does not provide shell access.
```

后续再进行`clone`/`fetch`/`pull`/`push`操作时，就可以正常访问GitHub代码仓库了，并且也不需要再重新输入账号密码。

而且，将私钥加入`ssh-agent`后，即使删除私钥文件，本地计算机仍可以正常访问GitHub代码仓库。

```bash
➜ rm -rf ~/.ssh
➜ ssh-add -l
4096 SHA256:xRg49AgTxxxxxxxx8q2SPPOfxxxxxxxxRlBY /Users/Leo/.ssh/id_rsa (RSA)
➜ ssh -T git@github.com
The authenticity of host 'github.com (192.30.252.130)' can't be established.
RSA key fingerprint is SHA256:nThbg6kXUpJWGl7E1IGOCspRomTxdCARLviKw6E5SY8.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added 'github.com,192.30.252.130' (RSA) to the list of known hosts.
Hi leolee! You've successfully authenticated, but GitHub does not provide shell access.
```

只有执行`ssh-add -D`或`ssh-add -d pub_key`命令，将私钥从`ssh-agent`删除后，认证信息才会失效。

```bash
➜ ssh-add -d ~/.ssh/id_rsa.pub
Identity removed: /Users/Leo/.ssh/id_rsa.pub (mail@debugtalk.com)
➜ ssh-add -l
The agent has no identities.
➜ ssh -T git@github.com
Permission denied (publickey).
```

## 同时使用多个GitHub账号

熟悉了`HTTPS URLs`和`SSH URLs`这两种校验方式之后，我们再来看之前遇到的问题。要想在一台计算机上同时使用多个GitHub账号访问不同的仓库，需要怎么做呢？

为了更好地演示，现假设有两个GitHub账号，`debugtalk`和`leolee`，在两个账号中各自有一个仓库，`debugtalk/DroidMeter`和`DebugTalk/MobileStore`（公司私有库）。

前面已经说过，`HTTPS URLs`和`SSH URLs`对应着两套独立的权限校验方式，因此这两套方式应该是都能单独实现我们的需求的。

不过在详细讲解Git权限校验的问题之前，我们先来回顾下Git配置文件的优先级。

### Git配置存储位置及其优先级

`Unix-like`系统中，保存Git用户信息的主要有3个地方（Mac系统多一个`Keychain`）：

- `/etc/gitconfig`：存储当前系统所有用户的git配置信息，使用带有`--system`选项的`git config`时，配置信息会写入该文件；
- `~/.gitconfig`或`~/.config/git/config`：存储当前用户的git配置信息，使用带有`--global`选项的`git config`时，配置信息会写入该文件；
- `Keychain Access`：在开启`Keychain`机制的情况下，进行权限校验后会自动将账号密码保存至`Keychain Access`。
- 仓库的Git目录中的config文件（即`repo/.git/config`）：存储当前仓库的git配置信息，在仓库中使用带有`--local`选项的`git config`时，配置信息会写入该文件；

在优先级方面，以上4个配置项的优先级从上往下依次上升，即`repo/.git/config`的优先级最高，然后`Keychain Access`会覆盖`~/.gitconfig`中的配置，`~/.gitconfig`会覆盖`/etc/gitconfig`中的配置。

### 基于`SSH`协议实现多账号共存

先来看下如何采用`SSH URLs`实现我们的需求。

在处理多账号共存问题之前，两个账号均已分别创建`SSH`秘钥对，并且`SSH-key`均已加入本地计算机的`ssh-agent`。

```bash
➜ ssh-add -l
4096 SHA256:lqujbjkWM1xxxxxxxxxxG6ERK6DNYj9tXExxxxxx8ew /Users/Leo/.ssh/debugtalk_id_rsa (RSA)
4096 SHA256:II2O9vZutdQr8xxxxxxxxxxD7EYvxxxxxxbynx2hHtg /Users/Leo/.ssh/id_rsa (RSA)
```

在详细讲解多账号共存的问题之前，我们先来回想下平时在Terminal中与GitHub仓库进行交互的场景。

```zsh
➜  DroidMeter git:(master) git pull
Already up-to-date.
➜  DroidMeter git:(master) touch README.md
➜  DroidMeter git:(master) ✗ git add .
➜  DroidMeter git:(master) ✗ git commit -m "add README"
➜  DroidMeter git:(master) git push
Counting objects: 3, done.
Delta compression using up to 4 threads.
Compressing objects: 100% (2/2), done.
Writing objects: 100% (3/3), 310 bytes | 0 bytes/s, done.
Total 3 (delta 0), reused 0 (delta 0)
To git@debugtalk:debugtalk/DroidMeter.git
   7df6839..68d085b  master -> master
```

在操作过程中，本地计算机的`ssh-agent`与GitHub服务器建立了连接，并进行了账号权限校验。

当本地计算机只有一个GitHub账号时，这个行为并不难理解，系统应该会采用这个唯一的GitHub账号进行操作。那如果本地计算机中有多个Github账号时，系统是根据什么来判断应该选择哪个账号呢？

实际情况是，系统没法进行判断。系统只会有一个默认的账号，然后采用这个默认的账号去操作所有的代码仓库，当账号与仓库不匹配时，就会报权限校验失败的错误。

那要怎样才能让系统正确区分账号呢？这就需要我们手动进行配置，配置文件即是`~/.ssh/config`。

创建`~/.ssh/config`文件，在其中填写如下内容。

```bash
# debugtalk
Host debugtalk
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_rsa

# DT
Host leolee
    HostName github.com
    User git
    IdentityFile ~/.ssh/dt_id_rsa
```

要理解以上配置文件的含义并不难，我们可以对比看下两个项目的`SSH URLs`：

```
git@github.com:debugtalk/DroidMeter.git
git@github.com:DTSZ/Store_Android.git
```

其中，`git`是本地`ssh-agent`与GitHub服务器建立`SSH`连接采用的用户名（即`User`），`github.com`是GitHub服务器的主机（即`HostName`）。

可以看出，如果采用原始的`SSH URLs`，由于`User`和`HostName`都相同，本地计算机并不知道应该采用哪个`SSH-key`去建立连接。

因此，通过创建`~/.ssh/config`文件，在`Host`中进行区分，然后经过`CNAME`映射到`HostName`，然后分别指向不同的`SSH-key`，即`IdentityFile`。由于`HostName`才是真正指定GitHub服务器主机的字段，因此这么配置不会对本地`ssh-agent`连接GitHub主机产生影响，再加上`Host`别名指向了不同的`SSH-key`，从而实现了对两个GitHub账号的分离。

配置完毕后，两个GitHub账号就可以通过`Host`别名来进行区分了。后续再与GitHub服务器进行通信时，就可以采用`Host`别名代替原先的`github.com`。例如，测试本地`ssh-agent`与GitHub服务器的连通性时，可采用如下方式：

```bash
➜ ssh -T git@debugtalk
Hi debugtalk! You have successfully authenticated, but GitHub does not provide shell access.
➜ ssh -T git@leolee
Hi leolee! You have successfully authenticated, but GitHub does not provide shell access.
```

可以看出，此时两个账号各司其职，不会再出现混淆的情况。

不过，我们还遗漏了很重要的一点。在本地代码仓库中执行`push`/`pull`/`fetch`等操作的时候，命令中并不会包含`Host`信息，那系统怎么知道我们要采用哪个GitHub账号进行操作呢？

答案是，系统还是没法判断，需要我们进行配置指定。

显然，不同的仓库可能对应着不同的GitHub账号，因此这个配置不能配置成全局的，而只能在各个项目中分别进行配置，即`repo/.git/config`文件。

配置的方式如下：

在`debugtalk/DroidMeter`仓库中：

```bash
➜ git remote add origin git@debugtalk:debugtalk/DroidMeter.git
```

在`DebugTalk/MobileStore.git`仓库中：

```bash
➜ git remote add origin git@leolee:DebugTalk/MobileStore.git
```

配置的原理也很容易理解，就是将仓库的`Host`更换为之前设置的别名。添加完毕后，后续再在两个仓库中执行任何`git`操作时，系统就可以选择正确的`SSH-key`与GitHub服务器进行交互了。

### 基于`HTTPS`协议实现多账号共存

再来看下如何采用`HTTPS URLs`实现我们的需求。

有了前面的经验，我们的思路就清晰了许多。采用`HTTPS URLs`的方式进行Git权限校验后，系统会将GitHub账号密码存储到`Keychain`中（Mac系统），或者存储到`~/.git-credentials`文件中（`Git credential helper`）。

不管是存储到哪里，我们面临的问题都是相同的，即如何在代码仓库中区分采用哪个GitHub账号。

配置的方式其实也很简单：

在`debugtalk/DroidMeter`仓库中：

```bash
➜ git remote add origin https://debugtalk@github.com/debugtalk/DroidMeter.git
```

在`DebugTalk/MobileStore.git`仓库中：

```bash
➜ git remote add origin https://leolee@github.com/DebugTalk/MobileStore.git
```

配置的原理也很容易理解，将GitHub用户名添加到仓库的Git地址中，这样在执行git命令的时候，系统就会采用指定的GitHub用户名去`Keychain`或`~/.git-credentials`中寻找对应的认证信息，账号使用错乱的问题也就不复存在了。

`Done!`
