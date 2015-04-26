---
layout: post
title: On Opinionated Tools
tags: ["Programming"]
---

I've recently begun a love affair with Haskell that's caused me to rethink
how I approach problem solving at a fundamental level.

Haskell, for those uninitiated, is a functional programming language that
looks, reads, and behaves like pure mathematics. This rigid, well-defined
structure has, in some ways, caused me to rethink my stance on the standard
ways people try to decrease development time.

Programmers are lazy. It's core to how we can effectively do our jobs,
because we've always got efficiency on the mind. However, this means our
decision-making process errs on what *we think* will lead to the least
work.

Think of it as a greedy approach to problem solving -- that is, we tend
to prefer the solution that will get in our way the least *right now*,
but neglect that the composition of many such soltions becomes a liability
itself.

*We trade convenience now for inconvenience later.*

## Programming Language Design

Some languages allow for ultimate flexibility when writing. They allow for
very rapid development without handling edge cases right away. This can be
really useful when prototyping or writing simple, one-off programs.

This convenience breaks down when running in production.

Let's look at some examples. Say, for example, you're writing an integer
arithmetic library. Dynamic languages like Python mean you can get started
really quickly!

```python
def add(first, second):
    return first + second

def multiply(first, second):
    return first * second

def modulo(first, second):
    return first % second
```

Great! These functions work as intended when given two integers. However,
you have experience writing libraries. You know that you need to handle
cases where misuse might cause a nondescript error, and you need to handle
those cases within your library.

For example, Python will not complain when writing this code.

```python
import arithmetic
import random

if random.randint(1, 3) == 2:
    arithmetic.add(4, 'hello!')
```

The code above has a 33% chance of failing miserably. Worse, the error
is tied to the internal implementation.

```
Traceback (most recent call last):
  File "arithmetic.py" line 1, in arithmetic
  File "<stdin>", line 1, in add
TypeError: unsupported operand type(s) for +: 'int' and 'str'
```

So since you cannot stop your users from misusing your library,
you make sure that your clients get descriptive errors if they do.

```python
def add(first, second):
    if first is None or second is None:
        raise ValueError('Cannot add None')

    if not isinstance(first, int) or not isinstance(second, int):
        raise ValueError(('Cannot add two non-integer types." +
                          'Expected (<type \'int\', \'int\'>), got ' +
                          '(%s, %s)') % (type(first), type(second)))

    return first + second

def multiply(first, second):
    if first is None or second is None:
        raise ValueError('Cannot multiply None')

    if not isinstance(first, int) or not isinstance(second, int):
        raise ValueError(('Cannot multiply two non-integer types." +
                          'Expected (<type \'int\', \'int\'>),' +
                          'got (%s, %s)') % (type(first), type(second)))

    return first * second

def modulo(first, second):
    if first is None or second is None:
        raise ValueError('Cannot take remainder of None')

    if not isinstance(first, int) or not isinstance(second, int):
        raise ValueError(('Cannot take remainder of two non-integer' +
                          'types. Expected (<type \'int\', \'int\'>),' +
                          'got (%s, %s)') % (type(first), type(second))))

    return first % second
```


***Yikes.***

And of course, you have to write the requisite unit tests to make sure
the library gracefully and descriptively handles the errors.

In order to ensure safety and correctness, your codebase explodes in
complexity.

Even worse, your library now does not work with `float`s, `str`s, or
anything else that would respond to `add`, `multiply`, and `modulo`.

Compare that to the compatible Haskell implementation (with type
signatures, too! Sorry, no point-free here.)

```haskell
add :: Num a => a -> a -> a
add x y = x + y

multiply :: Num a => a -> a -> a
multiply x y = x * y

modulo :: Integral a => a -> a -> a
modulo x y = x `mod` y
```

Let's consider what we didn't have to do:

* Check for `None` or `null`.
    Haskell's type system is such that the non-existence of a value
    is expressed at the type level. There is a type, `Maybe`, that
    encompasses the possibility of not having a value. As such, handling
    `None` is always explicit, and completely ignorable unless necessary.

    Apple has also shown support for this kind of type-level safety.
    Swift's type system is a dramatic improvement over Objective-C, and
    it enables you to write incredibly expressive and safe code, much
    easier.

* Check the type of the inputs.
    This is a gimme: Haskell is a (very) strictly typed language, and
    typeclasses like `Num` and `Integral` allow us to write incredibly
    generic implementations that work on a wide variety of types.

* Write unit tests.
    Our implementations are mathematically provably correct. There is no
    chance for side-effects. In the Python example, invalid values break
    control flow! They must be handled by the API client, with all manner
    of `try`/`except`/`finally` clauses. In Haskell, any side-effects are,
    like `null`, handled at the type level.

### 'Garbage in, garbage out.'

Unopinionaed languages handle this by accepting all sorts of garbage --
and letting the requisite garbage flow in response.

Opinionated languages stop the garbage from getting in.

## Databases

I've been working with MongoDB for a while, and, while I really appreciate
the ability to reason with the database as JSON, I've really come to
despise the lack of schema validation. When writing an API around MongoDB,
the work of validating the data falls on either the server or the
individual clients. This leads to repeated work on many different
platforms, to ensure data consistency throughout. It also leads to
programmers making *assumptions* about the available data. When values
can come back `null` in JSON, and that behavior is not explicitly defined
at the database-level, that leads to hundreds of `null` checks in each of
the clients.

Sure, it's more flexible to just throw data into a Mongo document, and in
some unfortunate cases, that may be completely required, but the lack of
schema validation does little more than cause crashes, UI inconsistency,
and silent-failures months down the line. In production.

Again, ***garbage in, garbage out.***

Opinionated tools, though inconvenient, allow the programmers to focus on
correctness of their implementation, not extra code to handle invalid
input.
