---
layout: post
title: Clean, Modern Objective-C
date: 2014-02-20
tags: [objective-c, style, code, programming]
photo-folder: /images/2014-02-20-clean-modern-objective-c
---

Objective-C is far and away my favorite language, and its base syntax lends
itself to cleanliness and readability. Unfortunately, developers who are familiar
with other languages sometimes come in and muck everything up.

These guidelines borrow heavily from [Ash Furrow's *Structuring Modern Objective-C*](http://ashfurrow.com/blog/structuring-modern-objective-c)
and the [New York Times Objective-C Style Guide](https://github.com/NYTimes/objective-c-style-guide).

## 1. No instance variables.

Say you want to have a reference to a button persist throughout your class, but
you don't want to expose a property in the header.
You throw down some curly braces in the implementation and define it, right?

```objective-c
@implementation HHMyClass {
    UIButton *loginButton;
}
```

**No.**

Instead, you should define an *anonymous category* inside your implementation,
like so:

```objective-c
@interface HHMyClass ()

@property (nonatomic) UIButton *loginButton;

@end

@implementation HHMyClass

...

@end
```

On a related note, it's best not to access the `synthesized`
instance variables of your properties, because if you override the setter it
could lead to inconsistent and confusing behavior.
Just always access your properties via `self.property` and you'll always know
the behavior.

## 2. Use consistent spacing and use whitespace liberally.

```objective-c

- (void) doSomethingWithParameter:(NSString*)parameter;

- (void) doSomethingWithParameter:(NSString *)parameter;
//My personal favorite.

- (void)doSomethingWithParameter:(NSString*) parameter;

-(void) doSomethingWithParameter:(NSString*)parameter;

- (void)doSomethingWithParameter:(NSString *) parameter;

- (void)doSomethingWithParameter:(NSString *)parameter;
// Apple's recommendation (thanks, zefhous!)
```
Each of these styles has their own advantages and disadvantages, but whichever
you choose, stick with it throughout the project. And if you're working with a
team, make sure you all agree upon a style.

The positioning of the pointers in the last example brings me to my next point:

## 3. Pointers should hug the variables to which they point.

```objective-c
NSString *title; //Correct.
NSString* title; //Wrong.
```

To illustrate why, I'll give you the example given to me by
[Russ Harmon](http://rus.har.mn)

Consider the following C code:

```c
int* a, b;
```

Now, what is the type of `b`? If you said `int*`, then sorry, you're incorrect.
`b` is just a regular old `int`, because the compiler associates pointers with
the nearest variable.

So given this behavior,

```objective-c
NSString* title;
```

is incorrect, and

```objective-c
NSString *title;
```

is correct.

## 4. Modularize and model.

Classes are great. They store data and routines in neat, discrete compartments
that won't *compile* if they aren't used correctly. Yet, I still see applications
that, say, load data from web APIs that rely on passing `NSDictionaries` around.
Why? It's certainly more convenient, but as the application scales, the dictionary
method seems kludgey at best.

The solution is to modularize and model classes whenever possible. Access the
dictionary one time and set the variables in the class.

A lot of you already know this, but for some developers, especially developers
who are more familiar with C, this is not obvious.

Along this vein...

## 5. Trim your ViewControllers.

It's so easy to throw hundreds of functions, delegates, and protocols into a
ViewController, but that makes maintenance and debugging incredibly difficult.
When your `UIViewController` follows `<UITableViewDelegate, UITableViewDataSource,
UIActionViewDelegate, UIScrollViewDelegate, UIActionSheetDelegate,
UITextFieldDelegate, SomeOtherRandomClassDelegate>`, it becomes increidbly
difficult to keep track of where those methods are. Especially if the developer
isn't using `#pragma mark`s to separate his view controllers.

Speaking of...

## 6. Use pragma marks to split up your code.

Sometimes it's actually negligible to implement a delegate in your ViewController,
like `UIAlertViewDelegate` if you only need `alertView:clickedButtonAtIndex:`.
In that case, you should always separate that delegate with `#pragma`s, like so:

```objective-c
- (void) someInstanceMethod:(id)argument {
    return; // lazy
}

#pragma mark - UIAlertViewDelegate methods

- (void) alertView:clickedButtonAtIndex:(NSInteger)index {
    NSLog(@"Clicked.");
}
```

It has the added benefit of adding to the navigation menu at the top of Xcode.
![Nice, neat navigation]({{page.photo-folder}}/navigation.png)

**Update 1:**

## 7. Use 'Modern Objective-C Syntax'

Objective-C makes heavy use of the `@` operator, which generally denotes
Objective-C objects. For example, `"string"` is a `char*`, while `@"string"` is
an NSString. These have been standard in Objective-C for a long time, but only
recently, in Objective-C 2.0, did Apple add in definitions for NSDictionary,
NSArray, and NSNumber, all using @directives.

```objective-c
NSNumber *number = [NSNumber numberWithInteger:7];
NSNumber *modernNumber = @(7); // or @7

NSArray *array = [NSArray arrayWithObjects:number, modernNumber, nil];
NSArray *modernArray = @[number, modernNumber];

NSDictionary *dictionary = [NSDictionary dictionaryWithObjectsAndKeys:number, @"number"];
NSDictionary *modernDictionary = @{@"number" : number};
```

It's more concise, and still somehow more readable.

## 8. Fruitful functions should be nouns

Fruitful functions (functions that return a value) should be nouns, because the
function signature should describe what it returns. For example:

```objective-c
- (void) doSomething;
// This is good, because it will only do something, so it's like an action.

- (NSArray*) shuffledArray;
// This is also good, because the signature says 'I'm a shuffled array.'

- (NSArray*) shuffleArray;
// This is ambiguous, because we don't know if the action will apply to the object itself or if it will just return a shuffled array.

- (NSArray*) getShuffledArray;
// Needlessly complicated. By sending the message and using the return value, you are implicitly 'getting' the array.
```

I'll periodically amend this with future tips.
Happy coding!
