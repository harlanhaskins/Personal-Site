---
layout: post
title: "Building a Compiler in Swift with LLVM, Part 2: AST and the Parser"
date: 2017-01-09
tags: [swift, llvm, compilers, parsers]
---

In [Part 1 of this tutorial](https://harlanhaskins.com/2017/01/08/building-a-compiler-with-swift-in-llvm-part-1-introduction-and-the-lexer.html),
we built a lexer in Swift that can tokenize the
[Kaleidoscope language](http://llvm.org/docs/tutorial). Now we're going to write
a parser that can turn code from this language into an Abstract Syntax Tree,
or AST.

> This is the second part in a 4-part series where we'll build a compiler for the
> basic form of the [Kaleidoscope sample language](http://llvm.org/docs/tutorial/index.html).
>
> Quick Links
>
> - [Part 1: Introduction and the Lexer](https://harlanhaskins.com/2017/01/08/building-a-compiler-with-swift-in-llvm-part-1-introduction-and-the-lexer.html)

## AST Structure

An AST represents the structure of your program as it was written in the source
text. ASTs usually have different data structures for the different kinds of
declarations, statements, and expressions in the language. In Kaleidoscope,
we're going to have three kinds of structures.

### Prototypes

A function prototype includes the name of the function and the names of
the function's parameters.

For example, in the function definition:

```
def foo(a, b, c) 0
```

the prototype will have the name `"foo"`, and the parameters `["a", "b", "c"]`.

We'll make it a struct that includes both of those values:

```swift
struct Prototype {
    let name: String
    let params: [String]
}
```

This means we can use this prototype as both the prototype of an `extern`
declaration and inside a function definition. Speaking of...

### Externs and Definitions

Kaleidoscope allows the programmer to specify existing named functions in the
C standard library without having to implement those functions.

For example, if I want to use the `math.h` function:

```
double sqrt(double n);
```

then I can declare its existence in Kaleidoscope as:

```
extern sqrt(n)
```

Because Kaleidoscope only has Double-typed numbers, we can get away with not
specifying types in the declaration. All parameters are implicitly `double`, and
all functions return `double`.

A Kaleidoscope function definition has two parts: a prototype and an expression.
The expression will have variables that reference the parameters given to the
function when it's called.

We can represent it with another struct, this time called `Definition`:

```swift
struct Definition {
    let prototype: Prototype
    let expr: Expr
}
```

### Expressions

There are a few different kinds of expressions in the Kaleidoscope language.
You have:

- Numbers, which have a Double as a value
- Variables
- Binary operators, which have two subexpressions and an operator
- Function Calls, which have a name and an array of expressions.

Because there is a small set of cases, we can represent the expressions with
another Swift enum:

```swift
indirect enum Expr {
    case number(Double)
    case variable(String)
    case binary(Expr, BinaryOperator, Expr)
    case call(String, [Expr])
}
```

## Parser

Kaleidoscope has a simple grammar that can be represented in [Backus-Naur
Form](https://en.wikipedia.org/wiki/Backus–Naur_form):

```
<prototype>  ::= <identifier> "(" <params> ")"
<definition> ::= "def" <prototype> <expr>
<extern>     ::= "extern" <prototype>
<operator>   ::= "+" | "-" | "*" | "/" | "%"
<expr>       ::= <binary> | <call> | <identifier> | <number>
               | "(" <expr> ")"
<binary>     ::= <expr> <operator> <expr>
<call>       ::= <identifier> "(" <arguments> ")"
<arguments>  ::= <expr>
               | <expr> "," <arguments>
```

The names on the left of the `::=` are called "terms", and the values on
the right are the possible values that may represent these terms.

In this form, each term can be substituted with the value to the right.

We'll be building a [recursive descent parser](https://en.wikipedia.org/wiki/Recursive_descent_parser) in Swift that can turn tokens emitted by [our Lexer](https://harlanhaskins.com/2017/01/08/building-a-compiler-with-swift-in-llvm-part-1-introduction-and-the-lexer.html)
into the AST we declared earlier.

### A Note on Recursive Descent Parsers

Notice in the grammar above that `<expr>` has `<binary>` as a case, and that
`<binary>` has two `<expr>`s inside. That's where the "recursive" comes in.
The parsers for `<expr>` and `<binary>` are going to call into each other.

### Kaleidoscope's Parser

First, begin with a class definition for our Parser. It needs to keep a list of
tokens and a current index into that list.

```swift
class Parser {
    let tokens: [Token]
    var index = 0

    init(tokens: [Token]) {
        self.tokens = tokens
    }
}
```

Next, just like our Lexer, we're going to want some abstractions that make it
easier to parse each of the terms. Let's define those in the class:

```swift
var currentToken: Token? {
    return index < tokens.count ? tokens[index] : nil
}

func advance(n: Int = 1) {
    index += n
}

/// Eats the specified token if it's the currentToken,
/// otherwise throws an error.
func parse(_ token: Token) throws {
    guard let tok = currentToken else {
        throw ParseError.unexpectedEOF
    }
    guard token == tok else {
        throw ParseError.unexpectedToken(token)
    }
    advance()
}
```

We'll also use a ParseError enum that specifies a few errors our parser can
throw:

```swift
enum ParseError: Error {
    case unexpectedToken(Token)
    case unexpectedEOF
}
```

Okay, now we're going to parse each term we use in the grammar. We can combine
some terms that are only used in one place. First, we'll want a function that
parses a single identifier. We need to ensure that the current token is
an `.identifier` token, and extract the name from it.

```swift
func parseIdentifier() throws -> String {
    guard let token = currentToken else {
        throw ParseError.unexpectedEOF
    }
    guard case .identifier(let name) = token else {
        throw ParseError.unexpectedToken(token)
    }
    advance()
    return name
}
```

Once we have this, we can make use of it inside the parsers for other terms.

Next, we'll write the parser for `Prototype`s. We'll want to parse:

- a single identifier, then
- a left paren, then
- a comma-separated list of identifiers, and finally
- a right paren.

But wait — we've seen this pattern before in the grammar. Left paren,
comma-separated list, then right paren... that's very similar to the grammar for
function call arguments! The only difference is the function call arguments
contain a list of expressions instead of a list of identifiers.

Because we dislike code duplication, we can use some more advanced Swift
features to reuse the logic: generics and higher-order functions.

Let's make a function:

```swift
func parseCommaSeparated<TermType>(_ parseFn: () throws -> TermType) throws -> [TermType]
```

This function is generic, which means it will collect whatever type the
passed-in function returns into a list.

```swift
func parseCommaSeparated<TermType>(_ parseFn: () throws -> TermType) throws -> [TermType] {
    try parse(.leftParen)
    var vals = [TermType]()
    while let tok = currentToken, tok != .rightParen {
        let val = try parseFn()
        if case .comma? = currentToken {
            try parse(.comma)
        }
        vals.append(val)
    }
    try parse(.rightParen)
    return vals
}
```

Doing this, our parser for the prototype term is simple:

```swift
func parsePrototype() throws -> Prototype {
    let name = try parseIdentifier()
    let params = try parseCommaSeparated(parseIdentifier)
    return Prototype(name: name, params: params)
}
```

And now the way we parse `extern` definitions is simple, just parse the
`.extern` token, then return a prototype:

```swift
func parseExtern() throws -> Prototype {
    try parse(.extern)
    return try parsePrototype()
}
```

### Expressions

Parsing expressions is slightly more complicated. Since there are different
kinds of expressions, we'll have to switch on the token to determine which
term we're going to parse.

It'll look like this:

- If we see a left paren, then we're going to eat it, recurse to parse the inner
  expression, then eat the right paren.
- If we see a number, then we can eat it and make a `.number` expression.
- If we see an identifier, then we can eat it.
    - If after that we see a left paren, then we can parse the arguments to
      a function call and make a `.call` expression
    - Otherwise, make a `.variable` expression.
- If we see any other token, throw an error.

We keep track of this expression, then check for an operator token.

- If we see an operator token, then eat it and recurse to parse another
  expression. We then package these two expressions into a `.binary` expression.
- Otherwise, return the first expression we parsed.

The full code for this is attached at the bottom.

### Definitions

We're almost done!

The last thing we need to parse are function definitions. Recall that a function
definition includes a prototype and an expression for the body.
We already have parsers for both of those terms, so we can just re-use those
parsers and be done.

```swift
func parseDefinition() throws -> Definition {
    try parse(.def)
    let prototype = try parsePrototype()
    let expr = try parseExpr()
    return Definition(prototype: prototype, expr: expr)
}
```

### All Together Now

Now that we have parsers for each of the terms in the language, we can make a
struct that holds all the top-level declarations in the program. The only
top-level declarations we support right now are extern declarations and
function definitions.

We just switch over the current token until we have no more tokens left.
If the code was malformed during the parsing, it will throw an error
and we will bubble it up to the caller.

If the code was correct, then we just read until there are no more tokens and
return a `TopLevel` struct with the top-level definitions.

```swift
func parseTopLevel() throws -> TopLevel {
    var externs = [Prototype]()
    var definitions = [Definition]()
    while let tok = currentToken {
        switch tok {
        case .extern:
            externs.append(try parseExtern())
        case .def:
            definitions.append(try parseDefinition())
        default:
            throw ParseError.unexpectedToken(tok)
        }
    }
    return TopLevel(externs: externs, definitions: definitions)
}
```

## Let's Give It a Shot!

```swift
let toks = Lexer(input: "extern sqrt(n)\ndef foo(n) (n * sqrt(n * 200) + 57 * n % 2)").lex()
let topLevel = try Parser(tokens: toks).parseTopLevel()
print(topLevel)
// TopLevel(externs: [Prototype(name: "sqrt", params: ["n"])], definitions: [Definition(prototype: Prototype(name: "foo", params: ["n"]), expr: Expr.binary(Expr.variable("n"), BinaryOperator.times, Expr.binary(Expr.call("sqrt", [Expr.binary(Expr.variable("n"), BinaryOperator.times, Expr.number(200.0))]), BinaryOperator.plus, Expr.binary(Expr.number(57.0), BinaryOperator.times, Expr.binary(Expr.variable("n"), BinaryOperator.mod, Expr.number(2.0))))))])
```

It works!

Now we have a parser and syntax tree. The next step is to generate LLVM IR for
this code and then we'll have a real functioning compiler!


## Code Listing

The full code for the tutorial so far is listed below and available
[as a gist](https://gist.github.com/harlanhaskins/0254261ff193502c8b19917f41102c47):

<script src="https://gist.github.com/harlanhaskins/0254261ff193502c8b19917f41102c47.js"></script>
