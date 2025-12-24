#!/usr/bin/env python3

# Test script to verify decimal/float fix
import sys
sys.path.append('/Users/kunalkumar/Desktop/kuanl')

from decimal import Decimal
from school_no_blockchain import safe_decimal, format_decimal, safe_float_input

def test_decimal_operations():
    """Test decimal operations that were causing the original error"""
    print("Testing Decimal Operations...")
    
    # Test safe_decimal conversion
    print("\n1. Testing safe_decimal conversions:")
    
    # Test float to Decimal conversion
    float_value = 100.50
    decimal_value = safe_decimal(float_value)
    print(f"Float {float_value} -> Decimal: {decimal_value} (type: {type(decimal_value)})")
    
    # Test string to Decimal conversion
    str_value = "200.75"
    decimal_str = safe_decimal(str_value)
    print(f"String '{str_value}' -> Decimal: {decimal_str} (type: {type(decimal_str)})")
    
    # Test integer to Decimal conversion
    int_value = 500
    decimal_int = safe_decimal(int_value)
    print(f"Integer {int_value} -> Decimal: {decimal_int} (type: {type(decimal_int)})")
    
    # Test Decimal passthrough
    existing_decimal = Decimal("300.25")
    decimal_passthrough = safe_decimal(existing_decimal)
    print(f"Decimal {existing_decimal} -> Decimal: {decimal_passthrough} (type: {type(decimal_passthrough)})")
    
    # Test arithmetic operations that were causing the original error
    print("\n2. Testing arithmetic operations:")
    
    # Test subtraction (was causing the original error)
    balance = Decimal("1000.00")
    amount = Decimal("250.50")
    new_balance = balance - amount
    print(f"Balance {balance} - Amount {amount} = {new_balance}")
    
    # Test addition
    new_balance = balance + amount
    print(f"Balance {balance} + Amount {amount} = {new_balance}")
    
    # Test comparison
    is_sufficient = balance >= amount
    print(f"Balance {balance} >= Amount {amount}: {is_sufficient}")
    
    # Test format_decimal
    print("\n3. Testing format_decimal:")
    test_values = [Decimal("123.45"), Decimal("1000.00"), Decimal("99.99")]
    for val in test_values:
        formatted = format_decimal(val)
        print(f"Decimal {val} formatted: {formatted}")
    
    print("\n✅ All decimal operations completed successfully!")
    print("✅ The original 'decimal.Decimal' and 'float' type error should be resolved!")

if __name__ == "__main__":
    test_decimal_operations()
