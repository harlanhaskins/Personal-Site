---
layout: post
title: "BogoSort: An Analysis of Random"
date: 2014-02-18
tags: [bogosort, bogo, sorting, c, python, algorithm, efficiency]
photo-folder: /images/2014-02-18-bogosort-an-analysis-of-random
---

I’ve become weirdly fascinated with BogoSort, the worst sorting algorithm ever.

## What is BogoSort?

* Check if the list is sorted.
* If it is, return. Else, shuffle the list and go back to step one.

It’s fairly inefficient.

My intrigue began in an intro to Computer Science class, when discussing sorting algorithms. Someone mentioned BogoSort (or ShotgunSort as some call it) and I whipped up a quick Python BogoSort implementation.

## Python

```
python3 bogoSort.py
How many items would you like in your list? 10
[66, 14, 71, 47, 74, 36, 80, 60, 30, 26]
[14, 26, 30, 36, 47, 60, 66, 71, 74, 80]
It took me 0:00:20.794921 to BogoSort this list.
I shuffled it 1,998,740 times.
```

## C

```
./BogoSort -s -n 10
[20, 78, 67, 84, 57, 46, 27, 58, 44, 51]
[20, 27, 44, 46, 51, 57, 58, 67, 78, 84]
It took me 00:00:0.5199 to BogoSort this list.
I shuffled it 2,073,394 times.
```

The C implementation is significantly faster than Python, but we all knew that.

Python’s BogoSort averages ~~40,000~~ **100,000** shuffles per second. C manages around 4,000,000 shuffles per second, which is ~~98~~ **40** times faster than Python.
Update: Apparemtly `random` has a shuffle function, which is a lot faster than mine. Numbers have been updated to reflect that.

With this information, I decided to write a **BogoSort Data Aggregation Tool**, which will collect data from repeated BogoSorts over a variety of list-lengths.

It's called as such:

```c
BogoSort -t 10 -e 6
// Will run from a list of 1 item to a list of 6 items, 10 times each.
```

where `-t` specifies the number of times to run each sort, and `-e` specifies the highest list length it will test.

When it's done, it throws the results into a CSV file in the BogoSortResults folder, where one can analyze them using a spreadsheet program.

*Which is exactly what I did.*

![Charts]({{ page.photo-folder }}/chart.png)

You can find all of my code [on my GitHub](http://github.com/harlanhaskins/Bogo-Sort). Try it for yourself!
