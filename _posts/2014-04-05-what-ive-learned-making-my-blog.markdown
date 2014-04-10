---
layout: post
title: What I've Learned Making My Blog
date: 2014-04-05
tags: ['vps', 'nginx', 'digitalocean']
---

I've owned [harlanhaskins.com](http://harlanhaskins.com) for three years, and
I've gone through 4 registrars. First, I went to GoDaddy, because I was ignorant.

Oh the folly of youth.

Next was [iPage](http://ipage.com), with whom I stuck for a year. They
weren't a bad registrar. I was a bad customer. They got too expensive for
15-year-old me, so I switched to [NixiHost](http://nixihost.com).

I stayed with NixiHost for two years, once using an incredibly terrible site
I designed when I was learning HTML, and then using two different
[WordPress](http://wordpress.com) blogs. I eventually switched to
[Gandi](http://gandi.net) because I learned that **NixiHost stored my site
administration login in plain text.**

Also Gandi gave me a free SSL certificate for a year.

After spending a lot of time with a friend of mine,
[Mihir Singh](http://citruspi.io), I decided that it was time to move on and set
up a VPS to host my new site, a simple blog that wasn't difficult to work with.

## Enter DigitalOcean

[DigitalOcean](http://digitalocean.com) is fantastic. I bought access to their
lowest-tier VPS (512MB RAM, 2.0GHz single-core CPU, 20GB storage) with the option
to scale it as I need. So far, since I don't get *crazy* amounts of traffic, base
tier is enough.

I chose to install CentOS, because RHEL-based Linux distributions tend to be very
stable and I don't need more downtime than is absolutely necessary.

## I have a VPS. Now what?

Next step: Install an HTTP server.

I had two major choices, nginx, lighttpd, or Apache. I picked nginx because,
though it has fewer features than Apache, its implementation of the features I
really need are **very** fast.

## But I just wanted to blog!

My next step was to set up my blogging platform. First, I tried
[Ghost](http://ghost.org), which was really great. Ghost is a very simple
and minimalistic blogging platform that lets you write posts in Markdown with a
really nice, live-updating preview of your posts.

My ultimate issue with Ghost is that it was written in node.js, which puts a lot
of strain on my server. Any popular-enough post could slow down my page loads
dramatically.

Mihir recommended I try out [Jekyll](http://jekyllrb.com), which is what I'm
currently using. Jekyll is a static site generator, meaning that I really only
need to worry about my posts--Jekyll will handle the rest.

I still write my posts in Markdown (in [vim](http://vim.sexy) too!), but Jekyll
'compiles' my Markdown-formatted files into HTML using a very simple inheritance
structure. Posts inherit from Page which inherits from Default.

I found a nice theme called [Vapor](http://sethlilly.com) which was originally
made for Ghost, but was ported to Jekyll by
[Luca Foschini](https://github.com/LucaFoschini/jekyll-vapor)

Jekyll's pages are completely static. To display my blog posts requires no server
or client side execution, beyond sending static files. Code syntax highlgihting
uses Pygments, which requires just CSS. Seriously. Inspect the code snippet below
and see for yourself:

```python
def checkItOut():
    yeah = lookAtThis()
    for syntax in yeah:
        highlight(syntax)
```

Some of the more keen readers may have noticed my site is not JavaScript-free. I am
using Google Analytics and Disqus. The point still stands that blog content requires
no JavaScript.

## SSL

As I stated above, Gandi gave me a free SSL certificate for a year. I'm serving up
a static site with no user data storage or transmission of sensitive material,
I still wanted to set up SSL because there was no reason not to.

I followed [this](https://benjeffrey.com/posts/setting-up-gandi-ssl-on-nginx) tutorial
because it was essentially everything I wanted to do, and I was able to get SSL
working in about a half hour.

**TL;DR**: Nginx is really good, Jekyll is wonderful and super easy, and SSL is great
even when unnecessary. Not bad for haveing never set up a server.
