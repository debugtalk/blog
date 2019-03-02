---
title: 在Pelican中使用多说评论系统
permalink: post/Using-DuoShuo-in-Pelican
date: 2013/10/05
categories:
  - 效率工具
tags:
  - Pelican
---

## 引言

Pelican默认采用的是Disqus评论系统，但由于Disqus附带的Facebook和Twitter社交功能在国内无法使用，因此我们更希望使用一些国内的SNS平台，比如QQ，新浪微博，豆瓣，人人等。在国产的评论系统中，使用较多的有[多说](http://duoshuo.com)、[有言](http://www.uyan.cc/)等，本文将介绍如何在Pelican博客系统中采用多说评论系统。

## 获取多说代码

在[多说首页](http://duoshuo.com)点击【我要安装】，进入创建站点界面；完成站点信息填写后，点击【创建】按钮，即可获得多说代码，大致如下所示。
```javascript
<!-- Duoshuo Comment BEGIN -->
<div class="ds-thread"></div>
<script type="text/javascript">
var duoshuoQuery = {short_name:"leolee"};
    (function() {
        var ds = document.createElement('script');
        ds.type = 'text/javascript';ds.async = true;
        ds.src = 'http://static.duoshuo.com/embed.js';
        ds.charset = 'UTF-8';
        (document.getElementsByTagName('head')[0]
        || document.getElementsByTagName('body')[0]).appendChild(ds);
    })();
</script>
<!-- Duoshuo Comment END -->
```

在上面的代码中，short_name即是注册的多说域名。

## 修改模板系统

获得多说代码后，在博客正文末尾对其进行引用，便可使用多说的评论功能。
由于我们采用的是模板，因此只需要在article模板中添加对多说代码的引用，便可以一劳永逸。
针对Pelican的模板系统，需要修改如下几个地方。

**在 pelicanconf.py 中开启多说评论功能**

模仿Pelican默认的DISQUS，在配置文件pelicanconf.py中添加如下代码。
```python
DUOSHUO_SITENAME = "leolee"
```
需要注意的是，DUOSHUO_SITENAME需要全部字母大写，因为只有这样Pelican才会将其作为全局变量，供其它文件引用。

**添加 DuoShuo_Script.html**

将获取得到的多说代码保存至单个文件中，方便在其它文件中对其进行引用。
```javascript
{% if DUOSHUO_SITENAME %}
<!-- Duoshuo Comment BEGIN -->
<div class="ds-thread"></div>
<script type="text/javascript">
var duoshuoQuery = {short_name:"{{ DUOSHUO_SITENAME }}"};
(function() {
    var ds = document.createElement('script');
    ds.type = 'text/javascript';
    ds.async = true;
    ds.src = 'http://static.duoshuo.com/embed.js';
    ds.charset = 'UTF-8';
    (document.getElementsByTagName('head')[0]
        || document.getElementsByTagName('body')[0]).appendChild(ds);
})();
</script>
<!-- Duoshuo Comment END -->
{% endif %}
```

在该文件中，添加了一个if语句，即只有在pelicanconf.py中对DUOSHUO_SITENAME进行设置后才开启多说评论功能。

**添加 DuoShuo_thread.html**

```html
<noscript>
Please enable JavaScript to view the comments powered by <a href="http://duoshuo.com/">DuoShuo</a>.
</noscript>
```

添加这个文件的作用是，当浏览器禁用Javascript后，用户无法看见评论框，而这个代码便是对用户进行提示。

**修改 article.html**

由于评论功能总是出现在文章末尾，因此应该将评论功能模块放在文章模版末尾，即对article.html进行修改，修改内容如下所示。
```html
{% raw %}
{% extends "base.html" %}
{% block title %}{{ article.title|striptags }}{% endblock %}
{% block content %}
<div>
  <article class="hentry" role="article">
    {% include '_includes/article.html' %}
    <footer>
      {% include '_includes/article_infos.html' %}
    </footer>
  </article>

  {% if DUOSHUO_SITENAME and SITEURL and article.status != "draft" %}
  <section>
    <h1>Comments</h1>
    <div id="DuoShuoComment" aria-live="polite">
      {% include '_includes/DuoShuo_Script.html' %}
      {% include '_includes/DuoShuo_thread.html' %}
    </div>
  </section>
  {% endif %}
</div>
{% endblock %}
{% endraw %}
```

通过以上修改，便可在Pelican博客系统中使用多说评论系统。
