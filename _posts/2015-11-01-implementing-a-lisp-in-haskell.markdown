---
layout: post
title: "Implementing a LISP-y Language in Haskell: Part 1"
tags: ['haskell', 'lisp', 'programming']
date: 2015-11-02
---

LISP is widely considered by academic-types as the original basis of
good programming language design. It's deceptively simple -- nested
expressions that recursively reduce to a value.

In my
[Programming Language Concepts](https://www.cs.rit.edu/~scj/plc_20151.html)
class at RIT, we spent time implementing common algorithms in a LISP-y language
called Impcore, made by [Norman Ramsey](http://www.cs.tufts.edu/~nr/), as a
teaching tool.

I really appreciate LISP, and had a lot of fun looking through the Impccore
source and textbooks learning the syntax and operational semantics of Impcore.

So I decided to implement my own, called Letter, in a language that's very
well suited to recursive data structures: Haskell.

For reference, here is a simple factorial implementation in Letter:

```lisp
(def fact(n)
  (if (= n 0)
    1
    (* n (fact (- n 1))))

(do
    (let x (fact 8))
    (print x)
    (print (fact 10)))
```

## Grammar

Like any good language designer, I started by defining a grammar. Luckily,
Impcore has a very understandable grammar, so I borrowed heavily from their
language definition.

The grammar I settled on is:

```haskell
exp        ::= (<exp-body>)             ; A parenthesized expression
             | <num>
             | <id>
exp-body   ::= let <id> <exp>           ; A 'let' expression
             | do <exp>+                ; A 'do' expression
             | <id> <exp>*              ; A function call
fun-def    ::= (def <id> (<id>*) <exp>)
num        ::= 0-9
alpha      ::= a-z | A-Z
id         ::= <id-char>+
id-char    ::= ? | ^ | * | + | = | <alpha>
             | < | > | - | _ | <num>
```

## Operational Semantics

Next, we need to define some kind of operational semantics for the possible
permutations of elements in out language. Like any bad language designer, I did
not do any mathematics or formalization of any operational semantics. Instead,
I made an informal list of rules.

* The only type in Letter is machine integer.
* All expressions reduce to a numeric value.
* A `def` statement:
    * Declares an n-ary function with bindings to formal parameters.
    * Must have one (and only one) expression inside.
    * Is only valid at file scope.
* A `do` statement:
    * Wraps multiple expressions into one expression.
    * Allows side-effects through the `print` statement.
    * Evaluates to the result of the last expression.
    * Opens a new context for local variables. These variables are
      destroyed when the do statement is left.
* A `let` statement:
    * Yields the value from the expression it binds.
    * Adds a binding to the enclosing environment.
* A `print` statement:
    * Evaluates its argument and prints it to `stdout`.
    * Yields the value from the expression it prints.
* A function call:
    * Looks up the function definition from the environment, throwing
      an error if it's not found.
    * Adds bindings in the environment in the order specified by the
      formal parameters of the definition.

Now that we have these semantics defined, we can implement the evaluation
routines.

## Syntax

To represent our program, we'll need a data structure to represent the
language's Abstract Syntax Tree. Since Letter is a nested language, we can
easily represent it using a nested Haskell data structure.

```haskell
data Exp = NExp Int
         | Do [Exp]
         | Var String
         | Let String Exp
         | FunCall String [Exp]
         deriving Show
```

You can see that this definition follows very closely to the grammar we defined
earlier. That's no accident -- Haskell (really, ML)'s data type syntax is
influenced by formal grammar definition.

Because Letter only has integer types, all expressions will reduce down to
a `NExp`, which is the simplest expression which is still an `Exp`. This is
useful, because we can pass variable bindings directly into functions by
ensuring all parameters are `Exp`s in some form.

Next, we'll need to determine a representation for functions. A function is
essentially just a single expression that has parameters that differ between
calls. We can implement this behavior by using `Var`s inside the function
body and adding the relevant bindings when the function is called.

Functions are made by composing multiple other functions together.
Still, I need a way to give the language some basic functions that
can be used inside user-defined functions. To achieve this, I made a
`FunDef` type that has two possible cases.

```
data FunDef = UserFun [String] Exp
            | BuiltinFun Int (Env -> [Exp] -> IO Exp)
```

First, a `UserFun`. A `UserFun` is exactly what we just described: A list of
formal parameters (`[String]`), and a single expression that it evaluates to.

Then, a `BuiltinFun`, which contains:
* an arity so we know how many arguments are required
* a Haskell function that takes in an `Env` (more on that later) and a list of
expressions for arguments, and yields an expression in the IO Monad (ignore
that, for now).

Now that we've discussed how the syntax is represented, let's move on to how
the language is evaluated.

## Evaluation

Remember that, in our semantics, all expressions are evaluated to a single
integer? There are many places in the `Exp` definition for nesting to happen,
so our evaluation function is necessarily going to be recursive.

Because Haskell is declarative, our recursive evaluation function essentially
reads like the informal semantics defined above. Before I explain the details,
I need to take a step back and talk about the Environment.

### The `Env`ironment.

We need some context that stores the variables and functions that have been
previously defined, so that newer expressions can use the previously declared
values.

To do this, we need an environment that's passed throughout the
evaluation system that holds references to global variables.

```haskell
data Env = Env
         { functions :: M.Map String FunDef
         , globals   :: M.Map String Exp
         } deriving Show
```

The environment has two `Map`s (Haskell's fast hash table library) that store
functions and global expressions with `String` keys. Thus, a variable reference
is just a single lookup, and a function call just means looking up the relevant
`FunDef` from the environment's function table and executing it with the
provided arguments.

With that in mind, we can now start evaluating expressions. In Letter,
evaluation is a two step process: First we reduce the expression to an `NExp`,
then we extract the Int inside.

Note: All these computations need to be wrapped in the IO Monad because one
function, the `print` function, needs to be able to perform IO.

With that, let's define the `eval` function, which reduces and unwraps:

```haskell
eval :: Env -> Exp -> IO Int
eval env (NExp n) = return n
eval env e        = reduce env e >>= eval env
```

You can see that the recursive base case, the NExp, is just a simple pattern
match that pulls out an Int, and the main case first reduces the expression
then recurses with that reduced value.

The `reduce` function contains all of the heavy lifting of Letter.

First, like before, define the base case. `NExp`s pass through the function
unchanged.
```haskell
reduce env n@(NExp _)                       = return n
```
Then we'll handle each part of the `Exp` definition.

### `do` and `let`

Remember that `do` statements create a new scope and
wrap a list of expressions. To emulate this 'new scope', we just insert the
new binding into the environment and pass it along through the rest of the `do`
statement whenever we hit a 'let' statement.

Similarly, we have two possible cases for 'do' statements. Either you have one
expression inside or multiple expressions inside. If there's just one
expression, then we evaluate that expression with the current environment, and
the `do` is over. If there's multiple, then we'll evaluate the statement and
throw away its value, then recurse and evaluate the rest of the expressions
inside the `do`.

```haskell
reduce (Env fs gs) (Do ((Let id e):exps))  = reduce (Env fs (M.insert id e gs)) (Do exps)
reduce env (Do [exp])                      = reduce env exp
reduce env (Do (exp:exps))                 = do
    _ <- reduce env exp
    reduce env (Do exps)
```

#### Scoping
Because Haskell is an immutable language, all the recursive calls to `reduce`
make a *copy* of the environment. Thus, when I say that I'm 'adding' a
definition to the environment, what I'm really saying is that nested
expressions will have this definition inside their environment. However, the
beauty of this construct is that once a `do` has been evaluated, its
environment is destroyed, and the outer environment remains unmodified. Thus,
scoping to functions and do statements happens _for free_.

### `Var`

Variable lookups are very easy. Attempt to look up the given expression in the
environment. If it's found, then that's the expression you're looking for; just
recurse with it. Otherwise, stop the program and print an error.

```haskell
reduce env@(Env _ gs) (Var id)           = do
    let exp = M.lookup id gs
    case exp of
        Nothing  -> error "Use of undeclared identifier \"" ++ id ++ "\""
        (Just e) -> reduce env e
```

### `FunCall`

Function calls are another beast entirely. First, lookup the function just like
a variable lookup, except in the function table in the environment. Then we'll
need to handle both types of function definitions. To do so, I defined a 'call'
function:

```haskell
reduce env@(Env fs _) (FunCall id args) = do
    let exp = M.lookup id fs
    case exp of
        Nothing -> error $ "Use of undeclared function \"" ++ id ++ "\""
        (Just e) -> call env id e args

call :: Env -> String -> FunDef -> [Exp] -> IO Exp
call env n (BuiltinFun arity f) args
    | (length args) == arity = f env args
    | otherwise = argsError n arity (length args)
call env@(Env fs gs) n (UserFun ns e) args
    | length args == length ns = do
        vals <- mapM (reduce env) args
        let formals = M.fromList (zip ns vals)
        reduce (Env fs (M.union formals gs)) e
    | otherwise = argsError n (length ns) (length args)

argsError id f a = error $
                   "Invalid number of arguments to function \""
                   ++ id ++ "\". Expected " ++ show f
                   ++ ", got " ++ show a ++ "."
```

If you're dealing with a builtin function, then make sure the arity matches
the arguments they gave, and if so, just call the wrapped function.

If it's a user-defined function, verify the arity by comparing the length of
the formal parameters with the supplied arguments, and if they match, add
bindings for those formal parameters into the environment and reduce the
expression inside the function. The expression's variable bindings will now
resolve to `NExp`s, and the function will execute successfully.

### Builtin functions

Now that we have the evaluation semantics locked down, we'll create an initial
environment that all the functions can have access to.

To do that, I'll make a wrapper function that transforms functions over `Int`
to be over `Exp` instead.

```haskell
binaryFun :: (Int -> Int -> Int) -> FunDef
binaryFun f = BuiltinFun 2 $ \env (e1:e2:_) -> do
    a <- eval env e1
    b <- eval env e2
    return (NExp $ f a b)
```

This means that I'll be able to seed Letter with builtin functions that
behave exactly like native Haskell functions.

I'll also create functions for defining `if`, `print`, and `check-expect`.

```
ifDef :: Env -> [Exp] -> IO Exp
ifDef env (e1:e2:e3:_) = do
    a <- eval env e1
    if a /= 0
    then reduce env e2
    else reduce env e3

printDef :: Env -> [Exp] -> IO Exp
printDef env (e:_) = do
    val <- eval env e
    print val
    return (NExp val)

checkExpectDef :: Env -> [Exp] -> IO Exp
checkExpectDef env (e1:e2:_) = do
    a <- eval env e1
    b <- eval env e2
    if a == b
    then do
        putStrLn $ "check-expect passed."
        return $ NExp 0
    else do
        putStrLn $ "check-expect failed. Expected \"" ++ show a ++ "\", got \"" ++ show b ++ "\""
        return $ NExp 0

boolify :: (Int -> Int -> Bool) -> (Int -> Int -> Int)
boolify f = \a b -> if f a b then 1 else 0

builtinFuns = M.fromList
              [ ("+", binaryFun (+))
              , ("*", binaryFun (*))
              , ("-", binaryFun (-))
              , ("/", binaryFun div)
              , ("=", binaryFun (boolify (==)))
              , (">", binaryFun (boolify (>)))
              , ("<", binaryFun (boolify (<)))
              , (">=", binaryFun (boolify (>=)))
              , ("<=", binaryFun (boolify (<=)))
              , ("/=", binaryFun (boolify (/=)))
              , ("mod", binaryFun mod)
              , ("if", BuiltinFun 3 ifDef)
              , ("print", BuiltinFun 1 printDef)
              , ("check-expect", BuiltinFun 2 checkExpectDef)
              ]
```

Now users have access to a nice 'standard library' of functions at their
disposal.

If you'd like to take a look beforehand, you can check out the
[Repo on GitHub](https://github.com/harlanhaskins/Letter/). The whole project
is up there.

Next week I'll tackle parsing the language and wrapping things up in a nice
CLI.
