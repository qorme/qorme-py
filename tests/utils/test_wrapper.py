import unittest

from qorme.utils.wrapper import AlreadyWrappedError, DuplicateWrapperError, Wrapper, WrappingError


class Person:
    def __init__(self, name: str, age: int) -> None:
        self.name = name
        self.age = age

    def __str__(self) -> str:
        return f"{self.name}: {self.age} years old."

    def who_are_you(self) -> str:
        return f"I am {self}"

    @classmethod
    def who_are_they(cls, name: str, *, age: int) -> str:
        return f"{name} is {age} years old says {cls.__name__}"

    @staticmethod
    def who_am_i(language: str = "Python") -> str:
        return f"You are likely a {language} developer."


class TestWrapper(unittest.TestCase):
    def setUp(self):
        super().setUp()
        self.wrapper = Wrapper()
        self.person = Person("Anta", 63)

    def tearDown(self):
        super().tearDown()
        self.wrapper.clear()

    def test_wrap_unwrap_method(self):
        to_wrap = self.person.who_are_you

        def wrapper(wrapped, instance, args, kwargs):
            self.assertEqual(wrapped, to_wrap)
            self.assertIs(instance, self.person)
            return f"wrapped: {wrapped(*args, **kwargs)}"

        self.wrapper.wrap(self.person, "who_are_you", wrapper)
        self.assertEqual(self.person.who_are_you(), "wrapped: I am Anta: 63 years old.")

        self.assertTrue(self.wrapper.unwrap(self.person, "who_are_you"))
        self.assertEqual(self.person.who_are_you(), "I am Anta: 63 years old.")

    def test_wrap_unwrap_method_from_class(self):
        def wrapper(wrapped, instance, args, kwargs):
            # self.assertEqual(wrapped, to_wrap)
            self.assertIs(instance, self.person)
            return f"wrapped: {wrapped(*args, **kwargs)}"

        self.wrapper.wrap(Person, "who_are_you", wrapper)
        self.assertEqual(self.person.who_are_you(), "wrapped: I am Anta: 63 years old.")

        self.assertTrue(self.wrapper.unwrap(Person, "who_are_you"))
        self.assertEqual(self.person.who_are_you(), "I am Anta: 63 years old.")

    def test_wrap_unwrap_classmethod(self):
        to_wrap = Person.who_are_they

        def wrapper(wrapped, instance, args, kwargs):
            self.assertEqual(wrapped, to_wrap)
            self.assertIs(instance, Person)
            return f"wrapped: {wrapped(*args, **kwargs)}"

        self.wrapper.wrap(Person, "who_are_they", wrapper)
        self.assertEqual(
            Person.who_are_they("Anta", age=63), "wrapped: Anta is 63 years old says Person"
        )

        self.assertTrue(self.wrapper.unwrap(Person, "who_are_they"))
        self.assertEqual(Person.who_are_they("Anta", age=63), "Anta is 63 years old says Person")

    def test_wrap_unwrap_staticmethod(self):
        to_wrap = Person.who_am_i

        def wrapper(wrapped, instance, args, kwargs):
            self.assertEqual(wrapped, to_wrap)
            # Static methods are not bound to any instance
            self.assertIsNone(instance)
            return f"wrapped: {wrapped(*args, **kwargs)}"

        self.wrapper.wrap(Person, "who_am_i", wrapper)
        self.assertEqual(Person.who_am_i(), "wrapped: You are likely a Python developer.")

        self.assertTrue(self.wrapper.unwrap(Person, "who_am_i"))
        self.assertEqual(Person.who_am_i(), "You are likely a Python developer.")

    def test_wrap_unwrap_not_owned(self):
        self.person.get_age = to_wrap = lambda: self.person.age

        def wrapper(wrapped, instance, args, kwargs):
            self.assertEqual(wrapped, to_wrap)
            self.assertIsNone(instance)
            return f"Age = {wrapped(*args, **kwargs)}"

        self.wrapper.wrap(self.person, "get_age", wrapper)
        self.assertEqual(self.person.get_age(), "Age = 63")

        self.assertTrue(self.wrapper.unwrap(self.person, "get_age"))
        self.assertEqual(self.person.get_age(), 63)

    def test_duplicate_wrapper(self):
        def wrapper(): ...

        self.wrapper.wrap(Person, "who_are_you", wrapper)
        with self.assertRaises(DuplicateWrapperError):
            self.wrapper.wrap(Person, "who_are_you", wrapper)

    def test_already_wrapped(self):
        def wrapper_1(): ...

        def wrapper_2(): ...

        self.wrapper.wrap(Person, "__str__", wrapper_1)
        with self.assertRaises(AlreadyWrappedError):
            self.wrapper.wrap(Person, "__str__", wrapper_2)

    def test_wrapping_error(self):
        def wrapper(): ...

        with self.assertRaises(WrappingError):
            self.wrapper.wrap(Person, "how_are_you", wrapper)

    def test_unwrap_unexisting(self):
        self.assertFalse(self.wrapper.unwrap(Person, "who_are_you"))

        self.wrapper.wrap(Person, "who_am_i", lambda: None)

        self.assertFalse(self.wrapper.unwrap(Person, "who_are_you"))

    def test_clear(self):
        def wrapper(wrapped, instance, args, kwargs):
            return f"wrapped: {wrapped(*args, **kwargs)}"

        self.wrapper.wrap(Person, "who_are_they", wrapper)
        self.wrapper.wrap(Person, "who_are_you", wrapper)

        self.assertEqual(
            self.person.who_are_they("Anta", age=63), "wrapped: Anta is 63 years old says Person"
        )
        self.assertEqual(self.person.who_are_you(), "wrapped: I am Anta: 63 years old.")

        self.wrapper.clear()

        self.assertEqual(
            self.person.who_are_they("Anta", age=63), "Anta is 63 years old says Person"
        )
        self.assertEqual(self.person.who_are_you(), "I am Anta: 63 years old.")

    def test_wrap_temp(self):
        def wrapper(wrapped, instance, args, kwargs):
            return f"wrapped: {wrapped(*args, **kwargs)}"

        with self.wrapper.wrap_temp(self.person, "who_are_you", wrapper):
            self.assertEqual(self.person.who_are_you(), "wrapped: I am Anta: 63 years old.")

        self.assertEqual(self.person.who_are_you(), "I am Anta: 63 years old.")

    def test_iter(self):
        wrappers = [lambda: None for _ in range(3)]
        self.wrapper.wrap(Person, "who_am_i", wrappers[0])
        self.wrapper.wrap(Person, "who_are_you", wrappers[1])
        self.wrapper.wrap(Person, "who_are_they", wrappers[2])

        for i, _wrapper in enumerate(self.wrapper):
            self.assertIs(_wrapper, wrappers[i])

        self.assertEqual(len(self.wrapper), 3)
