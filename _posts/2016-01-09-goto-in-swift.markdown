---
layout: post
title: goto in Swift
date: 2016-01-09
tags: [swift, programming, goto, fail]
---

`Goto` is a statement in the C programming language that, despite its usefulness
and flexibility, is somewhat despised among modern-day programmers. 

`goto` is a holdover from Assembly programming, where all control flow is
explicitly transferred between memory locations. You label the beginning of a
set of statements (usually referred to as a 'Basic Block') and transfer
execution using some kind of branch or jump statement.

For example (in MIPS32 assembly)

```asm
        syscall                 # assume we've just executed a syscall
        move $t0, $v0           # copy the return value of the syscall
        beq $t0, $zero, is_zero # if $t0 == 0, jump to is_zero, else is is_one
is_not_zero:
        # This will only be executed if the result of the syscall is not zero
        j end
is_zero:
        # This will only be executed if the result of the syscall is zero
        j end
end:
        jr $ra
```

*Whew.* That was a mouthful. Essentially, we're checking the result of a
syscall and jumping to a different execution location based on it. Roughly, in
C, this would translate to

```c
    int syscall_ret = syscall() // assume this works ... 
    if (syscall_ret == 0) goto is_zero;

is_not_zero:
    // This will only be executed if the result of the syscall is not zero
    goto end;

is_zero:
    // This will only be executed if the result of the syscall is zero
    goto end;

end:
    return;
```

Again, a very roundabout way of writing an if-statement.

There's a very common usage pattern for this in languages like C which
have fussy ownership rules. Sometimes it's necessary to run many tasks and
perform the same cleanup once that's done, no matter what happens. It's a
primitive form of error-handling when nothing else exists.

In fact, in `AssertMacros.h`, Apple defines a set of macros to facilitate this
error handling scheme.

From [AssertMacros.h](https://opensource.apple.com/source/CarbonHeaders/CarbonHeaders-18.1/AssertMacros.h)

```
require(assertion, exceptionLabel)
    In production builds, if the assertion expression evaluates to false, goto exceptionLabel
```

Using these macros, you can safely clean up after many statements. We can't
`return` when there's an error, because otherwise the file would remain
unclosed.

```c
    int retval = 0;
    int err = 0;
    FILE *file = fopen("file.txt", "rw");
    err = readfile(file);
    require(err == 0, fail);
    err = processfile(file);
    require(err == 0, fail);
    err = do_another_thing(file);
    require(err == 0, fail);
    err = do_a_third_thing(file);
    require(err == 0, fail);
    goto cleanup; // skip `fail`.
fail:
    retval = err;
cleanup:
    fclose(file);
    return retval;
```

In this example, there are many tasks that need to happen to the file, and the
function needs to exit early if any of them go wrong. Of course, in Swift, we
have a comprehensive and very nice error handling mechanism.

```swift
do {
  let file = fopen("file.txt", "rw")
  defer { fclose(file) }

  let contents = try file.read()
  try processFile(file)
  try doAnotherThing(file)
  try doAThirdThing(file)
} catch {
  print(error)
}
```

The `defer` statement will ensure the file is closed if an error happens.

# Implementing `goto` in Swift  

Swift, by design, abstracts away the notion of instructions or semi-predictable
instruction locations, and has never implemented any kind of explicit control
flow jumping. This is a *fantastic decision* because it eliminates [classes of
bugs in production.](https://nakedsecurity.sophos.com/2014/02/24/anatomy-of-a-goto-fail-apples-ssl-bug-explained-plus-an-unofficial-patch/)

However, Swift does offer a few methods of selective control flow: `if`
statements, `switch` statements, and function calls. We can replicate the
style of the goto from before using a switch statement with string cases:

```swift
var x = 4
let label = x == 4 ? "isFour" : "isNotFour"
switch label {
  case "isFour":
    print("It's four!")
  case "isNotFour":
    print("It's not four.")
  default: break // We need this because switches with strings can never be exhaustive.
}
```

However, this doesn't give us a way to change execution to another label.
This really only buys us the ability to jump to an execution location from
within an existing location. E.g. there is no `reswitch` statement.

We can, however, take advantage of three features of Swift: inner functions,
recursion, and closures.

Because functions are closures in Swift, inner functions wrap references to
variables within the containing scope. We can use this to pretend the inner
function is just part of the function body. If we declare it right, we can
recurse into the inner function with a different label and effectively alter
the execution location.

Imagine this function, which prints all numbers from 1 to 50:

```swift
func main() {
  var value = 0
  while value < 50 {
    value += 1
    print(value)
  }
}
```

We can reimplement it using an inner `goto` function, like so:

```swift
func main() {
  var value = 0
  func goto(label: String) {
    switch label {
      case "cond":
        goto(x < 50 ? "body" : "end")
      case "body":
        value += 1
        print(value)
        goto("cond")
      case "end": break
      default: break
    }
  }
  goto("cond")
}
```

By recursing into `goto`, we cause another run of the switch statement with a
different label. We can do any kind of control flow this way.

However, this isn't a very extensible solution. There's a lot of boilerplate. 
We need to declare the `goto` inner function within any function that wants to
use it, and the switch statement. It's kinda hard to visualize the control flow
(well, it's always hard with `goto`) with all the `switch` noise.

We can define a struct that wraps scoped gotos, that maps strings to closures.

```swift
struct Goto {
    typealias Closure = () -> Void
    var closures = [String: Closure]()
    mutating func set(label: String, closure: Closure) {
        closures[label] = closure
    }
    func call(label: String) {
        closures[label]?()
    }
}
```

And we can define a handy operator to avoid writing `goto.call("label")`

```swift
infix operator • { associativity left precedence 140 }
func •(goto: Goto, label: String) {
    goto.call(label)
}
```

And then we can get started using it! We define multiple blocks within the
`goto` we declare, and call into that goto struct from within those blocks.

```swift
var x = 0

var goto = Goto()
goto.set("cond") {
    goto • (x < 50 ? "body" : "end")
}
goto.set("body") {
    x += 1
    print(x)
    goto • "cond"
}
goto.set("end") {}

goto • "cond"
```

It's incredibly bug-prone, fragile, and easy to mess up.

C'est la `goto`.


[Goto.swift](https://github.com/harlanhaskins/Goto.swift) is available in the Swift Package Manager.
