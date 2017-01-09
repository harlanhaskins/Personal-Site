---
layout: post
title: "Building a Compiler in Swift with LLVM, Part 1: Introduction and the Lexer"
date: 2017-01-08
tags: [swift, llvm, compilers, parsers]
---

Compilers are some of the most fascinating programs because they touch every
aspect of Computer Science, from CLI and API design to calling conventions and
platform-specific optimizations. Yet, many developers have a fearful reverence
for them that makes them seem unapproachable. I think this is unnecessary.

Difficulties in compiler development arise mainly because of human concerns:
semantic correctness and following a strict standard. Those concerns are easier
to satisfy when designing a new language, as the standard is usually malleable.

> This is the first part in a 4-part series where we'll build a compiler for the
> basic form of the [Kaleidoscope sample language](http://llvm.org/docs/tutorial/index.html).


## Introduction to LLVM

Traditional compilers handle every part of the compilation process themselves.
After lexing, parsing, and semantic analysis, they branch out into code
generation paths for all the different target architectures they
support. This means that the compiler has to duplicate optimizations and
code generation logic, and that every compiler needs its own bespoke
register allocator, optimizer, code generator, etc. for x86, ARM, PowerPC, and
so on. Gross.

#### Enter LLVM

LLVM (the 'Low Level Virtual Machine') is a suite of tools that facilitate
development of compilers. These tools are all packaged into individual libraries
so it's easier to integrate them into other projects.

At the heart of the LLVM project is one specific tool: a programming language
called LLVM Intermediate Representation — abbreviated LLVM IR.
Instead of writing new code generation for every architecture, compiler
engineers can lower their language to LLVM IR and get fantastic code generation
and optimizations for free.

LLVM IR is a typed assembly language with support for high-level
features like functions (with different calling conventions), named types, and
abstractions for gritty details like pointer arithmetic.
What’s more, LLVM IR is a very simple language. It’s easy to get started
emitting basic IR, and later, when you need it, to opt in to more advanced
features and optimizations.

## Kaleidoscope

Kaleidoscope is a simple imperative language that's used in [the official LLVM tutorial](http://www.llvm.org/docs/tutorial/).
It has floating-point numbers and supports functions, recursion, and
binary operator math.

We can define functions like this:

```
def foo(n) (n * 100.34)
```

And we can scale up to more complex expressions and definitions like so:

```
extern sqrt(n)

def foo(n) (n * sqrt(n * 200) + 57 * n % 2)
```

## The Lexer

The first step in programming language development is reading in the source text
and translating it to a stream of manipulatable tokens. These tokens are usually
one of a set of values, some of which might have extra data attached. Naturally,
a Swift `enum` makes the most sense for a token.

We'll want a specific case for each bit of syntax exposed in that grammar, so it
should look something like this:

```swift
enum Token {
    case leftParen, rightParen, def, extern, comma
    case identifier(String)
    case number(Double)
    case `operator`(BinaryOperator)
}
```

That `BinaryOperator` there corresponds to this simple enum:

```swift
enum BinaryOperator: UnicodeScalar {
    case plus = "+"
    case minus = "-"
    case times = "*"
    case divide = "/"
    case mod = "%"
}
```

Once we define this, we can write a small Lexer that will deconstruct the source
text into a list of these tokens, while ignoring whitespace.

First, we want to define a class called `Lexer` that holds an array of
`UnicodeScalar`s. I usually prefer using `UnicodeScalar`s when I'm not
concerned with Unicode correctness. This language will be ASCII-only, so we're
safe using UnicodeScalar.

```swift
class Lexer {
    let input: [UnicodeScalar]
    var index = 0

    init(input: String) {
        self.input = Array(input.unicodeScalars)
    }
}
```

Once we do that, we'll want a method that reads in characters until it can
spit out a token. We'll call it `advanceToNextToken()`. The full code is
attached at the bottom of the post, but `advanceToNextToken` basically does
this, in order:

- Skip whitespace by advancing the index while the current character is a space.
- Check if the non-whitespace character is one of the single-character tokens.
    - If it is, then return that token.
- Otherwise, read an identifier.
    - If that identifier is an integer or decimal number, then return the number token.
    - Check if it's one of the two word tokens, `def` or `extern`.
        - If it is, return it.
    - Return a generic identifier token.

With this, we can take input from the programmer and read it out into a series of tokens that we can pass to the parser. Add one more method, `lex()` that
reads all available tokens from the input and returns a list.

```swift
func lex() -> [Token] {
    var toks = [Token]()
    while let tok = advanceToNextToken() {
        toks.append(tok)
    }
    return toks
}
```

## Let's give it a shot!

```swift
let toks = Lexer(input: "def foo(n) (n * 100.35)").lex()
print(toks)
// [Token.def, Token.identifier("foo"), Token.leftParen, Token.identifier("n"), Token.rightParen, Token.leftParen, Token.identifier("n"), Token.operator(BinaryOperator.times), Token.number(100.34), Token.rightParen]
```

It works!

Hopefully you're now aware how simple it can be to write a lexer for a fairly
feature-rich little toy language. In later parts we'll [parse these tokens into
an AST](https://harlanhaskins.com/2017/01/09/building-a-compiler-with-swift-in-llvm-part-2-ast-and-the-parser.html) then generate the LLVM IR for them using a library I'm working on,
[LLVMSwift](https://github.com/harlanhaskins/LLVMSwift).

Happy compiling!

## Code Listing

The full code is listed below and available [as a gist](https://gist.github.com/harlanhaskins/1d14f1ab048256d8dfa2f875f893b30d):

<script src="https://gist.github.com/harlanhaskins/1d14f1ab048256d8dfa2f875f893b30d.js"></script>
