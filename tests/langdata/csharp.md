# dotNet is still a thing

What if you could provide a code sample here?

```cs
public void Sum(int a, int b)
{
      return a + b;
}
```

And we know that it is testable.

```csharp
[Testclass]
public class UnitTest1
{
    [TestMethod]
    public void TestMethod1()
    {
        //Arrange
        ApplicationToTest.Calc ClassCalc = new ApplicationToTest.Calc();
        int expectedResult = 5;

        //Act
        int result = ClassCalc.Sum(2,3);

        //Assert
        Assert.AreEqual(expectedResult, result);
    }
}
```

Actually checking and running these tests, that's a different matter.
