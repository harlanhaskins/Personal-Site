---
layout: post
title: "Building a Compiler in Swift with LLVM, Part 3: Code Generation to LLVM IR"
date: 2017-01-11
tags: [swift, llvm, compilers, parsers]
---

If you've gotten this far in the tutorial, then you'll have built a Lexer and
Parser for the
[Kaleidoscope](http://llvm.org/docs/tutorial/index.html) programming language.
If you haven't read those, I'd strongly recommend reading [Part 1](https://harlanhaskins.com/2017/01/08/building-a-compiler-with-swift-in-llvm-part-1-introduction-and-the-lexer.html) and [Part 2](https://harlanhaskins.com/2017/01/09/building-a-compiler-with-swift-in-llvm-part-2-ast-and-the-parser.html) first. This time we'll be turning this parser into a proper compiler by turning the
parsed code into
[LLVM Intermediate Representation (LLVM IR)](http://llvm.org/docs/LangRef.html#introduction).

> This is the third part in a 4-part series where we'll build a compiler for the
> basic form of the [Kaleidoscope sample language](http://llvm.org/docs/tutorial/index.html).
>
> Quick Links
>
> - [Part 1: Introduction and the Lexer](https://harlanhaskins.com/2017/01/08/building-a-compiler-with-swift-in-llvm-part-1-introduction-and-the-lexer.html)
> - [Part 2: AST and the Parser](https://harlanhaskins.com/2017/01/09/building-a-compiler-with-swift-in-llvm-part-2-ast-and-the-parser.html)

## How does LLVM IR Work?

LLVM IR is a high-level assembly language with a suite of backends that can
generate machine code for many different target architectures. High-level
assembly language, while oxymoronic, means that LLVM is semantically similar to
assembly while adding higher-level abstractions. These abstractions make it
possible to generate code without having to consider things like calling
conventions, nuances of pointer arithmetic, register allocation, and stack
management.

IR is also strongly typed, which means you can think about structured types and
don't have to worry much about manipulating raw data and thinking in terms of
bits and bytes.

IR is represented in [Static Single Assignment](https://en.wikipedia.org/wiki/Static_single_assignment_form)
form, which means that programs have access to an infinite number of "registers"
that can only be assigned once. Consider the tree-shaped Kaleidoscope AST:

```swift
indirect enum Expr {
    case number(Double)
    case variable(String)
    case binary(Expr, BinaryOperator, Expr)
    case call(String, [Expr])
    case ifelse(Expr, Expr, Expr)
}
```

Notice that `.binary` has two `Expr`s inside it, as subexpressions. We'd say
that a binary operator has two _dependencies_ that must be generated before we
can generate the necessary code for the operator itself. So to generate a binary
operator expression, we generate the code for the left-hand side, then the
right-hand side. Then we can use the values in each of those new registers
as the parameters to the math instruction.

## Generating IR in Swift

Almost all of the LLVM project is implemented in C++, including all the
libraries and APIs. Unfortunately, Swift does not interoperate directly with
C++ like it does Objective-C. Because many more languages can interoperate with
C than C++, the LLVM project includes a comprehensive set of C bindings
into the LLVM libraries.

However, as with any C interop, it's cumbersome and easy to introduce subtle
bugs from Swift. Using the C API, you frequently have to make use of the
`UnsafeMutableBufferPointer` APIs, which (while convenient) are less than
ideal:

```swift
let function = LLVMGetNamedFunction(module, "puts")
var args = [/* ... llvm values ... */]
args.withUnsafeMutableBufferPointer { buf in
  LLVMBuildCall(builder, function, buf.baseAddress, UInt32(buf.count), "")
}
```

Fortunately, I've been working on a library that wraps the LLVM API in a much
more friendly, Swifty interface. It does away with all the unsafe code and
exposes native Swift types that represent the underlying LLVM types. It's called
[LLVMSwift](https://github.com/harlanhaskins/LLVMSwift).

## Using LLVMSwift

Let's say we want to emit Hello, World as LLVM IR.

First, we want to create a `Module`. Think of an LLVM module as everything that
would reside in a single `.o` file from `clang` or `gcc`. It includes all the
function declarations, global variables, and metadata. You can give it
whatever name you'd like.

```swift
import LLVM

let module = Module(name: "main")
```

Next, we'll want to make an `IRBuilder` that will handle generating all the
individual IR statements, functions, and global variables. A builder builds
code into a specific `Module`, so you need to create it with the particular
module you just created.

```swift
let builder = IRBuilder(module: module)
```

Now you're ready to start adding functions.

```swift
let mainType = FunctionType(args: [],
                            returnType: VoidType())
let main = builder.addFunction("main",
                               type: mainType)

// declare void @main()
```

In this case, `main` is a reference to an LLVM `Function`. You can pass this
`Function` object into the `IRBuilder`'s `buildCall` method to build a call
instruction.

### Functions

A `Function` is comprised of one or more `BasicBlock`s. A `BasicBlock` is a
grouping of instructions that has an entry point that an instruction can jump
to. Consider this assembly code:

```assembly
exec_syscall:
        # assume we've just executed a syscall
        syscall

        # copy the return value of the syscall
        move $t0, $v0

        # if $t0 == 0, jump to is_zero, otherwise to is_one
        beq $t0, $zero, is_zero

is_not_zero:
        # This will only be executed if the result of the syscall is not zero
        j end

is_zero:
        # This will only be executed if the result of the syscall is zero
        j end

end:
        jr $ra
```

This example has four basic blocks: `exec_syscall`, `is_not_zero`, `is_zero`,
and `end`. Every basic block in this example ends with a `jump` instruction
that transfers execution to the basic block that's specified. This is not
necessary in assembly, because if those don't end in a jump, they will just
fall through to the next basic block. LLVM enforces that basic blocks must
end in a terminator -- either a branch to another basic block, a return from
the function, or something that will terminate the program. This helps ensure
that the programmer always moves execution to the place they intend.

The first `BasicBlock` in an LLVM `Function` is special -- no other basic blocks
are allowed to branch to it, and it is jumped to immediately upon execution
of the function. This is called the `entry` block. Let's give our main an entry
block and move the builder to the end of that block so it will start inserting
instructions there:

```swift
let entry = main.appendBasicBlock(named: "entry")
builder.positionAtEnd(of: entry)
```

Now our LLVM looks like this:

```llvm
; ModuleID = 'main'
source_filename = "main"

define void @main() {
entry:
}
```

Simple enough! Now we'll need to add a global string to store
`"Hello, world!\n"`, which is easy:

```swift
let helloWorld = builder.buildGlobalStringPtr(name: "hello-world",
                                              value: "Hello, world!\n")
```

Now there is a global variable called `hello-world` that looks like this in IR:

```llvm
@hello-world = private unnamed_addr constant [15 x i8] c"Hello, world!\0A\00"
```

That `\0A\00` at the end are hexadecimal ASCII character escapes for the newline
and the `NUL` terminator, respectively.. The string is an `Array` of 15 `i8`s,
or 8-bit integers.

Now we can use this global to build a call to `puts`, which takes a string and
returns an `i32`.

```swift
let putsType = FunctionType(args: [PointerType(pointee: IntType.int8)],
                            returnType: IntType.int32)
let puts = builder.addFunction("puts", type: putsType)
```

Now we can build a call to `puts` with our global variable.

```swift
builder.buildCall(puts, args: [helloWorld])
```

We've built this call, and that's all we intend for this program to do. Because
all basic blocks need to end in a terminator, then we need to build a `ret`
instruction to finish the function.

```swift
builder.buildRetVoid()
```

Now the whole module looks like this:

```llvm
; ModuleID = 'main'
source_filename = "main"

@hello-world = private unnamed_addr constant [15 x i8] c"Hello, world!\0A\00"

declare i32 @puts(i8*)

define void @main() {
entry:
  %0 = call i32 (i8*) @puts(i8* getelementptr inbounds ([15 x i8], [15 x i8]* @hello-world, i32 0, i32 0))
  ret void
}
```

And we're done! This is a full LLVM program that will print "Hello, world!" to
stdout. You can verify this by saving it to a file, `hello.ll`, and using the
command-line tool `lli`, the LLVM interpreter, to run this file:

```
lli hello.ll
```

## Compiling Kaleidoscope to LLVM IR

Okay, now that you've been given a brief introduction to LLVM IR and the
LLVMSwift library, we're ready to write the code generation pass for the
Kaleidoscope compiler!

Remember what we said earlier -- that expressions are dependent on their
subexpressions? This is important to how we think about code generation to
LLVM IR. You'll want to have, at a minimum, one function that knows how to
emit the appropriate code for each data structure in your AST.

Let's make another class to encapsulate all the code generation. Let's name it
`IRGenerator`.

```swift
class IRGenerator {
    let module: Module
    let builder: IRBuilder
    let file: File

    init(file: File) {
        self.module = Module(name: "main")
        self.builder = IRBuilder(module: module)
        self.file = file
    }
}
```

### Prototypes

So far so good. Let's start with the simple case: emitting prototypes. Recall
that a prototype is a function name and its arguments' names.

That's easy enough to create using the builder, so let's do that (comments
inline.)

```swift
@discardableResult
func emitPrototype(_ prototype: Prototype) -> Function {
    // If there is already a function with that name, then return
    // the existing function.
    if let function = module.function(named: prototype.name) {
        return function
    }

    // Otherwise, construct a new function with same number of parameters
    // all of which are `double`s, returning a `double`.
    let argTypes = [IRType](repeating: FloatType.double,
                            count: prototype.params.count)
    let funcType = FunctionType(argTypes: argTypes,
                                returnType: FloatType.double)

    let function = builder.addFunction(prototype.name, type: funcType)

    // Set the names of all the parameters to the names we parsed
    for (var param, name) in zip(function.parameters, prototype.params) {
        param.name = name
    }

    return function
}
```

Okay, so we can declare the existence of a function without giving it a body.
This is all we need for `extern` declarations, which are represented as
`Prototype`s.

### Expressions

Next, we'll write the code to generate an expression. This is going to be the
most complicated, so I'll explain it in pieces. First, the signature:

```swift
func emitExpr(_ expr: Expr) throws -> IRValue
```

Next, we're going to switch over the cases. First, `.number`:

```swift
switch expr {
case .number(let value):
  return FloatType.double.constant(value)
```

Simple -- just make a constant value of `FloatType.double`, which is an LLVM
built-in type.

Next, function calls. This is more interesting because it's the first time we've
encountered something that could fail. What if the user called a function that
didn't exist? What if the user called a function with the wrong number of
arguments?

> Note: Real compilers split the semantic analysis into a separate pass that
> happens before code generation. We're doing them together for brevity.

Well, this is where we should start defining some errors. We want an error for
each case -- either the function doesn't exist, or it had an arity mismatch
(arity meaning the number of arguments).

```swift
enum IRError: Error {
    case unknownFunction(String)
    case arityMismatch(String, expected: Int, got: Int)
}
```

We also need a way to look up a prototype from the list of prototypes in the
`File` declaration. Add the following to the declaration of `File`:

```swift
private let prototypeMap: [String: Prototype]

func prototype(named: String) -> Prototype? {
    return prototypeMap[name]
}
```

This means that `File` will now keep track of a mapping of names to their
corresponding prototypes. We can ask the `File` declaration for a prototype
by name and then throw an error if the function didn't exist.

```swift
case .call(let name, let args):
    // Ask the module for a function with the same name.
    // If there wasn't one, then throw an error.
    guard let prototype = file.prototype(named: name) else {
        throw IRError.unknownFunction(name)
    }
    // Now make sure the call has the same number of arguments as the
    // function itself. If not, throw the other error.
    guard prototype.params.count == args.count else {
        throw IRError.arityMismatch(name,
                                    expected: prototype.params.count,
                                    got: args.count)
    }

    // Emit the function, or grab the existing function with that name
    let function = emitPrototype(prototype)

    // Emit all of the arguments from left to right
    let callArgs = try args.map(emitExpr)

    // Now build a call to that function.
    return builder.buildCall(function, args: callArgs)
```

We're making progress! There are two cases left: variables and binary operators.

There's another possible error here: What if we try to reference a variable
that doesn't exist yet? Well, we'll need a way to keep track of the parameters
of a function while we're emitting its expression. Let's add a new
property to `IRGenerator`:

```swift
private var parameterValues = [String: IRValue]()
```

We'll populate this array later, once we're emitting code for functions. For
now, assume this will be filled with the function's parameters that we can look
up by name when we reference them.

Let's add another case to the error enum:

```swift
case unknownVariable(String)
```

Now we can emit the code for `.variable` declarations.

```swift
case .variable(let name):
    guard let param = parameterValues[name] else {
        throw IRError.unknownVariable(name)
    }
    return param
```

Great! That was easy. If we didn't find the binding, then throw an
error. Otherwise, return it.

Next we'll handle `.ifelse` expressions. These are interesting in that one of
the cases of the if expression won't be executed. This means that we'll need
to make some more `BasicBlock`s and jump to a specific one if the condition
is true. Fortunately, LLVM's `br` instruction allows for a condition.

So we'll make a basic block for the true case, a basic block for the false case,
and then a `merge` basic block that they'll both jump to once they're done.

In the `merge` block, we'll use what's called a `PHI` node in LLVM. A `PHI` node
is a special instruction that changes its value based on where we *came from*.

So consider this `PHI` node:

```
%3 = phi double [ %1, %then ],
                [ %2, %else ]
```

You can read this as "if we just came from the block `%then`, then it'll have
the value in `%1`. If you came from the block `%else`, then it'll have the value
%2".

We'll make a phi node to combine the values from the two new blocks we'll create,
like so:

```swift
case .ifelse(let cond, let thenExpr, let elseExpr):
  // Create a `not-equal` comparison
  let checkCond = builder.buildFCmp(try emitExpr(cond),
                                    FloatType.double.constant(0.0),
                                    .orderedNotEqual)

  // Create a basic block to execute in the true or false cases,
  // and a block to jump to after.
  let thenBB = builder.currentFunction!.appendBasicBlock(named: "then")
  let elseBB = builder.currentFunction!.appendBasicBlock(named: "else")
  let mergeBB = builder.currentFunction!.appendBasicBlock(named: "merge")

  // Create a conditional branch instruction that will branch to the
  // `then` block if the condition is true, and the `else` block if false.
  builder.buildCondBr(condition: checkCond, then: thenBB, else: elseBB)

  // Position the builder at the end of the `then` block and emit the expressions
  builder.positionAtEnd(of: thenBB)
  let thenVal = try emitExpr(thenExpr)
  builder.buildBr(mergeBB)

  // Do the same for the else block
  builder.positionAtEnd(of: elseBB)
  let elseVal = try emitExpr(elseExpr)
  builder.buildBr(mergeBB)

  // Move to the merge block
  builder.positionAtEnd(of: mergeBB)

  // Make a phi node of type double
  let phi = builder.buildPhi(FloatType.double)

  // Add the two incoming blocks to the phi node.
  phi.addIncoming([(thenVal, thenBB), (elseVal, elseBB)])

  return phi
```

The last expression type, `.binary`, is straightforward. Emit the code for
the left-hand side, then the right-hand side. Once we do that, emit the
instruction corresponding to the mathematical operation in the operator.

```swift
case let .binary(lhs, op, rhs):
    let lhsVal = try emitExpr(lhs)
    let rhsVal = try emitExpr(rhs)
    switch op {
    case .plus:
        return builder.buildAdd(lhsVal, rhsVal)
    case .minus:
        return builder.buildSub(lhsVal, rhsVal)
    case .divide:
        return builder.buildDiv(lhsVal, rhsVal)
    case .times:
        return builder.buildMul(lhsVal, rhsVal)
    case .mod:
        return builder.buildRem(lhsVal, rhsVal)
```

Now the last binary operator: equals.

And we're done with `emitExpr()`!

### Definitions

Now the last piece of the puzzle: Function definitions. Recall that a function
is comprised of a prototype and a single expression for the body. We're going
to need to do one special thing: populate the `parameterValues` with the parameters
of this function: when we begin working with the function, register the parameters
with the `parameterValues`. When you're done, remove them all!

```swift
@discardableResult
func emitDefinition(_ definition: Definition) throws -> Function {
  // Lazily emit the function prototype
  let function = emitPrototype(definition.prototype)

  // Register each of the parameters' underlying LLVM values
  for (idx, arg) in definition.prototype.params.enumerated() {
    let param = function.parameter(at: idx)!
    parameterValues[arg] = param
  }

  // Create the entry basic block
  let entryBlock = function.appendBasicBlock(named: "entry")
  builder.positionAtEnd(of: entryBlock)

  // Emit the underlying expression
  let expr = try emitExpr(definition.expr)

  // Build a return of the expression
  builder.buildRet(expr)

  // Now remove the parameter values.
  parameterValues.removeAll()

  return function
}
```

### Wrapping It All Together

A binary file isn't actually executable unless we have a `main` function.
Our main function will just execute each file-level expression and print its
value. To do that, we'll loop through all the expressions and make a call to
`printf` with the format string `"%f\n"`.

```swift
func emitPrintf() -> Function {
  if let function = module.function(named: "printf") { return function }

    // Printf's C type is `int printf(char *, ...)`
  let printfType = FunctionType(argTypes: [PointerType(pointee: IntType.int8)],
                                returnType: IntType.int32,
                                isVarArg: true)

  // Add a declaration of printf
  return builder.addFunction("printf", type: printfType)
}

func emitMain() throws {
  // Our main function will take no arguments and return void.
  let mainType = FunctionType(argTypes: [], returnType: VoidType())
  let function = builder.addFunction("main", type: mainType)

  // Make an entry block
  let entry = function.appendBasicBlock(named: "entry")
  builder.positionAtEnd(of: entry)

  // Make a global string containing the format string
  let formatString = builder.buildGlobalStringPtr("%f\n")
  let printf = emitPrintf()

  // Emit each expression along with a call to printf with that
  // format string.
  for expr in file.expressions {
    let val = try emitExpr(expr)
    builder.buildCall(printf, args: [formatString, val])
  }

  // Return void
  builder.buildRetVoid()
}
```

The last thing we need is have one more function to emit everything declared
at file level. Let's make a function that just emits all `extern` definitions,
function definitions, and the main function:

```swift
func emit() throws {
  for extern in file.externs {
    emitPrototype(extern)
  }
  for definition in file.definitions {
    try emitDefinition(definition)
  }
  try emitMain()
}
```

And that's it! We've just built a compiler that can lex, parse, and compile
any Kaleidoscope program!

Let's write a small `main.swift` that will read a file from disk and compile it!

```swift
import Foundation

guard CommandLine.arguments.count > 1 else {
    print("usage: Kaleidoscope <file>")
    exit(-1)
}

do {
    let file = try String(contentsOfFile: CommandLine.arguments[1])
    let lexer = Lexer(input: file)
    let parser = Parser(tokens: lexer.lex())
    let file = try parser.parseFile()
    let irGen = IRGenerator(file: file)
    try irGen.emit()
    irGen.module.dump()
    try irGen.module.verify()
} catch {
    print("error: \(error)")
}
```

It works! We can see the IR that's emitted for any valid Kaleidoscope program
we write.

In Part 4, we're going to built a Just-In-Time compiler using LLVM's JIT that
allows you to execute Kaleidoscope programs from a REPL.

### Code Listing

The code for this depends on LLVMSwift, so we cannot link it in a single gist.
It's available as a Swift Package Manager project
[on GitHub here](https://github.com/harlanhaskins/Kaleidoscope-Swift).
