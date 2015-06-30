---
layout: post
title: "Swift and Haskell: `do` or Die"
tags: ["swift", "haskell", "functional"]
---

**Note:** This post requires cursory knowledge of Monads and, ideally, a teensy bit of Haskell. You can probably get away with reading Javier Soto's piece [*Functor and Monad in Swift*](http://www.javiersoto.me/post/106875422394).

Swift 2 introduced a robust error-handling system that abstracts away old Cocoa `NSError **` handling.

In Swift 1.2, using something like `NSJSONSerialization` required a very awkward, pass-by-reference error model, that feels very foreign to Swift.

```swift
func parseJSONData(data: NSData) -> AnyObject {
    var error: NSError?
    let json: AnyObject? = NSJSONSerialization.JSONObjectWithData(data, options: NSJSONReadingOptions.allZeros, error: &error)
    if let error = error {
        println(error) // Error 'handling'
        return nil
    }
    return json
}

func jsonAsDictionary(json: AnyObject, inout error: NSErrorPointer) -> [String: AnyObject]? {
    if let cast = json as? [String: AnyObject] {
        return cast
    }
    error = NSError(domain: "JSONThing", code: 0x22334422, userInfo: nil)
    return nil
}
```

There's a lot of visual noise, and it's hard to pick out the real implementation details buried within the error handling logic.

Swift 2 abstracts `NSError` into a new system that feels like other languages' `try/catch` semantics.

That code, in Swift 2, becomes:

```swift
enum JSONError {
    case Cast
}
func parseJSONData(data: NSData) throws -> AnyObject {
    return try NSJSONSerialization.JSONObjectWithData(data, options: [])
}
func jsonAsDictionary(json: AnyObject) throws -> [String: AnyObject] {
    if let dict = json as? [String: AnyObject] {
        return dict
    }
    throw JSONError.Cast
}
```

The `try` is the key there. By using `try` you're promising either to handle the error, or pass the error onto the caller (which is marked with `throws` in the type signature)

Then we can use multiple of these functions within one `do` block,
and fail into the `catch` when the first one fails.

```swift
do {
    let data = NSData()
    let json = try parseJSONData(data)
    let dict = try jsonAsDictionary(json)
} catch {
    println(error)
}
```

That's the crux of Swift error handling -- at some point in the function's lifetime, some caller has to `catch` the error. If not, it's a compile-time error.

And `catch` isn't some kind of expensive, stack-unwinding Exception. In fact, you can think of `throws` in a type signature as syntactic sugar for some kind of `Either` type.

Let's try de-sugaring the `throws` from the second example, into something that's Swift 2 compatible.

We start by defining an `Either` type. `Either` traditionally holds two values -- `Left`, which contains some kind of error, and `Right`, which contains a valid value.

```swift
enum Either<T> {
    case Left(error: NSError)
    case Right(value: T)
}
```

For an added bonus, we'll implement Monadic bind for our Either type, to make it easier to chain multiple failable expressions.
In this case, if the bound `Either` is `.Left`, we want to ignore the transformation and propagate out the existing error.

However, if the bound `Either` is `.Right`, we want to apply the transformation and return the result.

Since the result is an `Either` as well, you can chain multiple of these `bind`s as much as you want.

```swift
extension Either {
    func bind(transform: T -> Either<T>) -> Either<T> {
        switch (self) {
        case .Left:
            return self
        case .Right(let value):
            return transform(value)
        }
    }
}
```

Now let's define those two functions from earlier, except using our Either type.

```swift
func parseJSONData(data: NSData) -> Either<AnyObject> {
    var error: NSError?
    let json: AnyObject? = NSJSONSerialization.JSONObjectWithData(data, options: NSJSONReadingOptions.allZeros, error: &error)
    if let error = error {
        return .Left(error: error)
    }
    return .Right(value: json!)
}

func jsonAsDictionary(json: AnyObject) -> Either<[String: AnyObject]> {
    if let dict = json as? [String: AnyObject] {
        return .Right(value: dict)
    }
    return .Left(error: NSError(domain: "JSONThing", code: 0x22334422, userInfo: nil))
}

let jsonData = NSData(contentsOfFile: "someFile.json")
parseJSONData(jsonData).bind(jsonAsDictionary)
```

Well, there's even more code, since we still have to live in the old world and now transform it into our new world. But we've

The `throws` example from earlier is very similar behavior to `do` notation in Haskell. `do` notation wraps one or many monadic operations in a way that feels almost imperative.

Say we were interacting with some Swift-Haskell interface. We could work with that parseJSONData using do notation.

```haskell


jsonDictionary = do
    let data = File "someFile.json" :: NSData
    parsedJSON <- parseJSONData data
    jsonAsDictionary parsedJSON
```

Or, by desugaring the do notation,

```haskell
jsonDictionary = parseJSONData json >>= jsonAsDictionary
    where json :: NSData
          json = File "someFile.json"
```

They follow very similar semantics, by abstracting away and propagating failures throughout the sugared syntax.

This is, of course, an oversimplifcation of both technologies, but it's exciting to see functional concepts at the very core of Swift, and shaping its future.
