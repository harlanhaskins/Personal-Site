I’ve become weirdly fascinated with BogoSort, the worst sorting algorithm ever.

## What is BogoSort?

* Check if the list is sorted.
* If it is, return. Else, shuffle the list and go back to step one.

It’s fairly inefficient.

My intrigue began in an intro to Computer Science class, when discussing sorting algorithms. Someone mentioned BogoSort (or ShotgunSort as some call it) and I whipped up a quick Python BogoSort implementation.

## Python

    How many items would you like in your list? 10
    [65, 44, 88, 22, 87, 14, 69, 82, 65, 16]
    [14, 16, 22, 44, 65, 65, 69, 82, 87, 88]
    It took me 0:02:41.514186 to BogoSort this list.
    I shuffled it 6,856,771 times.

## C

    How many items would you like in your list? 10
    [48, 14, 25, 64, 51, 62, 99, 6, 30, 73]
    [6, 14, 25, 30, 48, 51, 62, 64, 73, 99]
    It took me 00:00:1.4526 to BogoSort this list.
    I shuffled it 6,092,336 times.

The C implementation is significantly faster than Python, but we all knew that.

Python’s BogoSort averages 42,454 shuffles per second. C manages 4,194,090 shuffles per second, which is 98 times faster than Python.

You can find all of my code [on my GitHub](http://github.com/harlanhaskins/Bogo-Sort).
