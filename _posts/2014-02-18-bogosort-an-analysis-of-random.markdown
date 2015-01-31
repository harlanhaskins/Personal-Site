---
layout: post
title: "BogoSort: An Analysis of Random"
date: 2014-02-18
tags: [bogosort, bogo, sorting, c, python, algorithm, efficiency]
photo-folder: /post\_images/2014/02/18/bogosort-an-analysis-of-random
---

I’ve become weirdly fascinated with BogoSort, the worst sorting algorithm
ever.

## What is BogoSort?

* Check if the list is sorted.
* If it is, return. Else, shuffle the list and go back to step one.

It’s fairly inefficient.

My intrigue began in an intro to Computer Science class, when discussing
sorting algorithms. Someone mentioned BogoSort (or ShotgunSort as
some call it) and I whipped up a quick Python BogoSort implementation.

## Python

```
python main.py -n 10 -s
[67, 17, 36, 26, 59, 55, 33, 10, 20, 2]
[2, 10, 17, 20, 26, 33, 36, 55, 59, 67]
It took me 0:00:00.689806 to BogoSort this list.
I shuffled it 1,620,424 times.
That's 2349101.05 shuffles per second.
```

## C

```
./BogoSort -n 10 -s
[5, 31, 79, 84, 0, 16, 40, 66, 30, 3]
[0, 3, 5, 16, 30, 31, 40, 66, 79, 84]
It took me 00:00:0.235736 to BogoSort this list.
I shuffled it 3,336,619 times.
That's 14154049.45 shuffles per second.
```

The C implementation is significantly faster than Python, but we all knew
that.

Python’s BogoSort averages **235,000** shuffles per second with 10 items.
C manages around **13,000,000** shuffles per second, which is 55x faster
than Python.

With this information, I decided to write a **BogoSort Data Aggregation Tool**, which will collect data from repeated BogoSorts over a variety of list-lengths.

It's called as such:

```c
BogoSort -t 10 -e 6
// Will run from a list of 1 item to a list of 6 items, 10 times each.
```

where `-t` specifies the number of times to run each sort, and `-e`
specifies the highest list length it will test.

When it's done, it throws the results into a CSV file in the
BogoSortResults folder, where one can analyze them using a spreadsheet
program.

*Which is exactly what I did.*

![Charts]({{ page.photo-folder }}/chart.png)

You can find all of my code
[on my GitHub](http://github.com/harlanhaskins/Bogo-Sort).
Try it for yourself!
