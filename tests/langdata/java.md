# Java documentation is important

That's a language still. Here's a java codeblock:

```java
public class MyUnit {
    public String concatenate(String one, String two){
      return one + two;
    }
}
```

And since we have that class, let's test it

```java
import org.junit.Test;
import static org.junit.Assert.*;

public class MyUnitTest {

    @Test
    public void testConcatenate() {
        MyUnit myUnit = new MyUnit();

        String result = myUnit.concatenate("one", "two");

        assertEquals("onetwo", result);

    }
}

```
