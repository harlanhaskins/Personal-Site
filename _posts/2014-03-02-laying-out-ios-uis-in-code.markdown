---
layout: post
title: Laying Out iOS UIs in Code
date: 2014-03-02
tags: ['ios', 'ui', 'design', 'frame']
photo-folder: /images/2014/03/02/laying-out-ios-uis-in-code
---

For most iOS developers, Interface Builder is an incredibly easy WYSIWYG,
drag-and-drop editor to lay out UIs. For many, however, Auto Layout (or the
springs and struts of yore) only provide a cursory amount of control over
placement.

For about a year, I've been laying out all of my UIs purely in code. The benefits
are tremendous.

Before I go on, I'd like to preface this by saying that I would **highly**
recommend using a category to make positioning in code much easier.

I use [`UIView+Positioning`](http://github.com/freak4pc/UIView-Positioning),
which exposes `x`, `y`, `width`, `height`, `right`, `bottom`, `centerX`, and
`centerY` as both setters and getters. Seriously, you will ~~never~~ seldom
touch CGRects again.

## You have ultimate control over your positioning.
With Interface Builder and Auto Layout, you're basically restricted to point-based
layouts.
![Point-based constraints]({{page.photo-folder}}/pointconstraint.png)

You are required to layout your views through their points, so no matter what
device is rendering your view, every position is absolute.

You can also define your constraints relative to the containing view, but again
those numbers are absolute.

When you lay out UIs in code, you can lay them out relative to each other using
percentages and whatever other crazy math you want, to maintain a more consistent
and proportional UI between devices.

```objective-c
button.x = self.view.width  * 0.2; // Position the inset at 20% of the width.
button.y = self.view.height * 0.2; // Position the inset at 20% of the height.
```

## Layouts are more explicitly defined in code.
Many people have had issues with Interface Builder's hundreds of check boxes that
seem to have no default pattern.

For instance, `UIWebView` defaults to detecting Phone Numbers, but not Links or
Addresses, whereas `UITextView` defaults to detecting only Links.

When you define these in code, these defaults are more explicit.

```objective-c
[webView setDataDetectorTypes:UIDataDetectorTypeAll];
```

## IBOutlets are too tightly coupled.
If you create lots of small helper views like I do, you have to connect their
`IBOutlets` individually to all of your classes that need access to their
properties.

And lord help you if you try to delete an `IBOutlet` declaration
before clearing out the `IBOutlets` in Interface Builder. The compiler frowns on
that.

## Version Control with `nib`s is nigh-impossible.
Since Apple moved to the new `xib` format, version control has improved
dramatically, but it's still very difficult.

Interface Builder documents are now stores as straight XML data, which includes
unnecessary data like window positioning, for some reason. This has the weird
side-effect of **altering the file upon viewing** which is some quantum
insanity that I don't fully understand. This makes version control especially
difficult, because that means some innocuous action like looking up a view's
positioning makes uncommitted changes to your `xib` file.

When you lay out your UIs in code, UI changes are just regular old code changes,
which makes `git` very happy.

## Interface Builder is ***slow***
Everyone who's dealt with Interface Builder understands this one. Just opening a
xib takes at least 5 seconds and completely halts Xcode until it's loaded.

I'd estimate I've spent an hour of my life waiting for Interface Builder to load.

Even worse is when you accidentally click on a xib when you mean to click a class.
Loading the class takes a quarter of a second, but now you must stop what you're
doing and wait for Xcode to load that xib before you can click the class.

It's even worse with storyboards, because that means it has to load the xibs for
**an entire application's View Controller hierarchy.**

## Programmatically laying out UIs is not difficult.
It'll take a little bit of practice laying out a few UIViews, watching how
their properties interact, before it becomes second-nature. There are a few small
quirks, though.

* The main `view` property of `UIViewController` is not final in `viewDidLoad`.
    - You'll need to adjust frames in the ViewController's  `viewDidLayoutSubviews` method.
* In iOS 7, the navigation bar no longer adjusts the frame of the main `view`
property.
    - You'll need to look for the `topLayoutGguide` and `bottomLayoutGuide`
properties on UIViewController. They have a property called `length` that will
tell you (in `viewDidLayoutSubviews`) where the bottom of the navigation bar (or
top of the tab bar) is. So lay out your views relative to [top | bottom]LayoutGuide.length
instead of `0.0`.
* Make heavy use of `siteToFit` on UIViews.
    - This will resize your UIViews to just enclose their subviews, no matter
what. This is incredibly convenient for positioning views with multiple subviews
and making sure they're entirely consistent.

I'm confident that once you make one programmatically-laid-out UI, you won't want
to touch Interface Builder again.
