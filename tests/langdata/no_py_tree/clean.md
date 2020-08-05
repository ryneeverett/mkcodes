# Cleanliness

If there are no python files in a directory, we don't need to add an __init__.py file to that directory. Sure, they don't hurt, but having them where they aren't needed isn't very tidy and might be confusing.

Speaking of confusing, lets test javascript
```js
function assert(condition, message) {
    if (!condition) {
        message = message || "Assertion failed";
        throw new Error(message);
    }
}

assert([]+[]=="", "very sensible, adding arrays is a string")
assert({}+[]==0, "of course adding a dict to an array is 0")
```
