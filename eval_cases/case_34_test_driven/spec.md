# Test-Driven Development: Make Tests Pass

You're given a test file with 10 failing tests. Your task is to implement the code that makes all tests pass.

## The Test File

This `test_calculator.py` defines what you need to build:

```python
"""
Tests for a Calculator class.
Your task: Create calculator.py that makes ALL these tests pass.
"""
import unittest

# This import should work after you create calculator.py
from calculator import Calculator, CalculatorError


class TestCalculator(unittest.TestCase):
    
    def setUp(self):
        """Create a fresh calculator for each test."""
        self.calc = Calculator()
    
    def test_initial_value_is_zero(self):
        """Calculator starts at zero."""
        self.assertEqual(self.calc.value, 0)
    
    def test_add_positive_numbers(self):
        """Can add positive numbers."""
        self.calc.add(5)
        self.assertEqual(self.calc.value, 5)
        self.calc.add(3)
        self.assertEqual(self.calc.value, 8)
    
    def test_add_negative_numbers(self):
        """Can add negative numbers."""
        self.calc.add(-5)
        self.assertEqual(self.calc.value, -5)
    
    def test_subtract(self):
        """Can subtract numbers."""
        self.calc.add(10)
        self.calc.subtract(3)
        self.assertEqual(self.calc.value, 7)
    
    def test_multiply(self):
        """Can multiply."""
        self.calc.add(5)
        self.calc.multiply(3)
        self.assertEqual(self.calc.value, 15)
    
    def test_divide(self):
        """Can divide."""
        self.calc.add(20)
        self.calc.divide(4)
        self.assertEqual(self.calc.value, 5)
    
    def test_divide_by_zero_raises_error(self):
        """Dividing by zero raises CalculatorError."""
        self.calc.add(10)
        with self.assertRaises(CalculatorError):
            self.calc.divide(0)
    
    def test_clear_resets_to_zero(self):
        """Clear resets value to zero."""
        self.calc.add(100)
        self.calc.clear()
        self.assertEqual(self.calc.value, 0)
    
    def test_chain_operations(self):
        """Operations can be chained fluently."""
        # add(5).multiply(2).subtract(3) = 7
        result = self.calc.add(5).multiply(2).subtract(3)
        self.assertEqual(result.value, 7)
        self.assertIs(result, self.calc)  # Returns self
    
    def test_memory_store_and_recall(self):
        """Can store and recall memory."""
        self.calc.add(42)
        self.calc.memory_store()
        self.calc.clear()
        self.assertEqual(self.calc.value, 0)
        self.calc.memory_recall()
        self.assertEqual(self.calc.value, 42)


if __name__ == '__main__':
    unittest.main()
```

## Your Task

1. Create `calculator.py` with:
   - `Calculator` class with all required methods
   - `CalculatorError` exception class
   - All methods should support chaining (return self)
   - Memory store/recall functionality

2. All 10 tests must pass when running:
   ```
   python -m pytest test_calculator.py -v
   ```
   or
   ```
   python -m unittest test_calculator.py -v
   ```

## Requirements

- `Calculator` class with `value` property (starts at 0)
- Methods: `add()`, `subtract()`, `multiply()`, `divide()`, `clear()`
- Methods return `self` for chaining
- `CalculatorError` raised on divide by zero
- `memory_store()` and `memory_recall()` methods
- Python stdlib only

## Deliverables

1. `calculator.py` - Your implementation
2. `test_calculator.py` - Copy of the test file (unchanged)

## Evaluation

All 10 tests must pass. Partial credit for passing some tests.
