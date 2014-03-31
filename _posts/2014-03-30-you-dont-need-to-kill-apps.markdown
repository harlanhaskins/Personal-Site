---
layout: post
title: You Don't Need To Kill Your Apps
date: 2014-03-30
---
I frequently see people talking erroneously about the 'need' to kill all apps. As
an iOS developer, this worries me, because it means caching, downloads, and any
sort of tidying up upon standby is interrupted completely.

I thought I'd expand to non-developers how the standby procedure works,
why **nobody needs to kill all of their running apps** and how
**it is detrimental to the functionality of the apps to kill them when exiting**.

Some of you may recognize this post. It's a cross post from my Reddit.

---

Apple designed the multitasking system to be unobtrusive and not require the
user to think about 'managing free memory' or anything, because the system is
**supposed** to fill up as much memory as possible. Android's multitasking
works fairly similarly, but with much less control by the system.

When an app is paused, a series of calls are dispatched to the app.

'Clean up your memory.' 'Pause whatever's going on.' (It's in iOS apps as a
method called `applicationWillResignActive:` is called, and then
`applicationDidEnterBackground:`.)

When the system encounters a lack of memory for a new app to open, all of the
currently running apps are sent a few other messages. First, they're sent a
careful message

'Hey, I'm getting a memory warning. Could you please please remove some things
from memory please?' (This is called both in the `AppDelegate` as
`applicationDidReceiveMemoryWarning:` and in the currently presented
view controller as `didReceiveMemoryWarning`, basically telling the developer
to get rid of some things that can be redownloaded or cached to the disk.)

If after that call to all running apps still hasn't freed enough, it calls all
the apps, starting from the oldest, and says 'Alright, you've gotta close now.
Pack up and go home.' (This is the killing process: `applicationWillTerminate:`)

So closing your apps interrupts that whole incredibly calculated song and dance
and can actually be detrimental to performance, as apps now need to reopen from
cold every single time you open them again.

**TL;DR: You do not need to kill all of your apps, because iOS has an incredibly
complicated system that relies on full-memory situations.**

**EDIT 1**: (from [binders\_of\_women\_](http://reddit.com/u/binders\_\of\_\women_)) "Additional TL; DR - it
takes more battery to quit and restart your apps than it does to let them run in
the background."
