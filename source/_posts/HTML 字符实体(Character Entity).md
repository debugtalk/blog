---
title: HTML 字符实体(Character Entity)
permalink: post/html-character-entity
date: 2013/10/04
categories:
  - Development
tags:
  - 字符编码
---

## 字符实体的由来

在HTML源文件中，有些字符（如<，>，&等）作为特殊字符不能直接使用，如果直接使用的话HTML将不能被正确解析。但如果HTML内容中需要展示这些特殊字符时该怎么处理呢？这就需要使用转义字符串来对其进行转义。

转义字符串（Escape Sequence）也称字符实体(Character Entity)。在HTML中，定义转义字符串的原因有两个：

- 第一个原因：像“<”和“>”这类符号已经用来表示HTML标签，因此就不能直接当作文本中的符号来使用。为了在HTML文档中使用这些符号，就需要定义它的转义字符串。当解释程序遇到这类字符串时就把它解释为真实的字符。在输入转义字符串时，要严格遵守字母大小写的规则。
- 第二个原因：有些字符在ASCII字符集中没有定义，因此需要使用转义字符串来表示。

## 转义字符串的组成

转义字符串（Escape Sequence），即字符实体（Character Entity）分成三部分：

- 第一部分是一个&符号，英文叫ampersand；
- 第二部分是字符实体名称（character entity names）或者是#加上实体编号；
- 第三部分是一个分号。

对于实体编号，采用的是字符的Unicode编码序号，并且可以采用其对应的十进制编码或者十六进制编码进行表示，具体形式为`#nnnn`或`#xhhhh`。

例如，要显示小于号（<），如果采用字符实体名称进行表示，就可以写成`&lt;`；如果采用字符实体编号的形式，由于其Unicode编码为60（对应16进制为x3c），因此可以写成`&#60;`或者`&#x3c;`。

同一个符号，可以用“实体名称”和“实体编号”两种方式进行表示，“实体名称”的优势在于便于记忆，但不能保证所有的浏览器都能顺利识别它；而“实体编号”，各种浏览器都能处理，其劣势在于不便于记忆。

提示：实体名称（Entity）是区分大小写的。

如何显示空格？
通常情况下，HTML会自动截去多余的空格，多个空格都将被看做一个空格。为了在网页中增加空格，可以使用`&nbsp;`表示空格。

## HTML Encode & Decode

对于HTML字符实体的Encode和Decode，即是对字符（character）和其对应的字符实体（Character Entity）进行相互转换。

HTML Encode: 字符(Character) => 字符实体(Character Entity)
HTML Decode: 字符实体(Character Entity) => 字符(Character)

例如，对于汉字“测试”，由于其Unicode编码为`\u6D4B\u8BD5`（对应的十进制为`27979 35797`），因此Encode后得到`&#27979;&#35797;`；反向地，对`&#27979;&#35797;`进行Decode后便得到“测试”。当然，对`&#x6D4B;&#x8BD5;`进行Decode同样可以得到“测试”。
