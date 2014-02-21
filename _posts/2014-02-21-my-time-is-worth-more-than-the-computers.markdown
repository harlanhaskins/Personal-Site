---
layout: post
title: My Time is Worth More Than the Computer's
date: 2014-02-21
tags: [efficiency, code, simplicity, maintainability, optimization]
---

I live on a [Computer Science-oriented dorm floor](http://csh.rit.edu), and
too often I hear people seriously investigating and recommending infinitely
more complicated systems in the name of "efficiency".

In fact, earlier today, I had this conversation when discussing RESTful APIs:

```
Me: I'm trying to switch from PHP to Python, because Python is so much easier to maintain.

Him: Oh, you should use Haskell. We converted our whole web stack to Haskell.
```

And a few weeks ago, with the same person, discussing Objective-C

```
Me: Right here I have a block that gets called whe-

Him: You're using blocks? You're dirty. The compiler can't optimize that. You shouldn't be using that.
```

I'm going to say something controversial.

>*Efficiency is unimportant until there is a tangible performance hit.*

There. I said it. But accepting this fact leads to some happy consequences.

Wanna make a web server in Ruby? Go for it. As long as doing so makes you more
comfortable and the code is cleaner, absolutely!

* Wanna traverse a deep tree recursively? Memory is cheap! Go for it!

* Wanna use a block instead of a complicated delegate/protocol pattern? Go for it!
blocks are cleaner anyway.

The most important thing when coding is your time. When you stop focusing on
minor inefficiencies, you can go back to solving real problems.
