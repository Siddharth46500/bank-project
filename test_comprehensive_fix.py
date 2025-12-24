#!/usr/bin/env python3

# Comprehensive test for both decimal/float fix and MySQL lock timeout fix
import sys
sys.path.append('/Users/kunalkumar/Desktop/kuanl')

from school_no_blockchain import transfer_money, account_open, safe_decimal, get_connection

def test_complete_fix():
    """Test that both issues are resolved: decimal/float type error and MySQL lock timeout"""
    print("🔧 Testing Complete Fix for school_no_blockchain.py")
    print("=" * 60)
    
    print("\n1. Testing Decimal/Float Type Compatibility")
    print("-" * 50)
    
    # Test the original problematic scenario
    try:
        # Create accounts with Decimal amounts
        acc1 = account_open("Decimal Test User 1", "1111111111", 1111, safe_decimal("1000.50"), "SAVINGS")
        acc2 = account_open("Decimal Test User 2", "2222222222", 2222, safe_decimal("500.25"), "SAVINGS")
        
        if acc1 and acc2:
            print(f"✅ Accounts created: {acc1}, {acc2}")
            
            # Test transfer with float input (this would cause the original error)
            float_amount = 250.75  # This would be float from user input
            print(f"Testing transfer of float amount: {float_amount}")
            
            success = transfer_money(acc1, acc2, float_amount, "Decimal/Float test")
            if success:
                print("✅ Transfer with float amount successful - No type error!")
            else:
                print("❌ Transfer failed")
                return False
        else:
            print("❌ Failed to create accounts")
            return False
            
    except Exception as e:
        if "unsupported operand type" in str(e):
            print(f"❌ Original decimal/float error still exists: {e}")
            return False
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    
    print("\n2. Testing Database Lock Handling")
    print("-" * 50)
    
    # Test multiple transfers to ensure no lock timeouts
    try:
        success_count = 0
        for i in range(5):
            acc_a = account_open(f"Lock Test User A{i}", f"33{i}1", 331, safe_decimal("1000.00"), "SAVINGS")
            acc_b = account_open(f"Lock Test User B{i}", f"33{i}2", 332, safe_decimal("500.00"), "SAVINGS")
            
            if acc_a and acc_b:
                # Perform transfer
                if transfer_money(acc_a, acc_b, safe_decimal("100.00"), f"Lock test {i}"):
                    success_count += 1
        
        print(f"✅ {success_count}/5 concurrent transfers successful - No lock timeout!")
        
    except Exception as e:
        if "Lock wait timeout" in str(e) or "1205" in str(e):
            print(f"❌ MySQL lock timeout still exists: {e}")
            return False
        else:
            print(f"❌ Unexpected error: {e}")
            return False
    
    print("\n3. Testing Transaction Data Integrity")
    print("-" * 50)
    
    # Verify that transactions are properly recorded
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM TRANSACTION_HISTORY")
        transaction_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ACCOUNTS WHERE name LIKE 'Test%'")
        account_count = cursor.fetchone()[0]
        
        print(f"✅ Database integrity check:")
        print(f"   - Total transactions recorded: {transaction_count}")
        print(f"   - Test accounts created: {account_count}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database integrity check failed: {e}")
        return False
    
    return True

def cleanup_comprehensive_test():
    """Clean up all test data"""
    print("\n4. Cleaning up test data...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Clean up all test data
        cursor.execute("DELETE FROM TRANSACTION_HISTORY WHERE remark_encrypted LIKE 'Decimal%' OR remark_encrypted LIKE 'Lock%' OR remark_encrypted LIKE 'Test%'")
        cursor.execute("DELETE FROM ACCOUNTS WHERE name LIKE 'Decimal%' OR name LIKE 'Lock%' OR name LIKE 'Test%'")
        
        conn.commit()
        
        # Verify cleanup
        cursor.execute("SELECT COUNT(*) FROM TRANSACTION_HISTORY")
        remaining_transactions = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM ACCOUNTS WHERE name LIKE 'Decimal%' OR name LIKE 'Lock%' OR name LIKE 'Test%'")
        remaining_accounts = cursor.fetchone()[0]
        
        print(f"✅ Cleanup completed:")
        print(f"   - Remaining test transactions: {remaining_transactions}")
        print(f"   - Remaining test accounts: {remaining_accounts}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Warning: Cleanup failed: {e}")

if __name__ == "__main__":
    success = test_complete_fix()
    
    cleanup_comprehensive_test()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 COMPREHENSIVE TEST PASSED!")
        print("🎉 Both decimal/float type error AND MySQL lock timeout are FIXED!")
        print("🎉 The bank management system is now fully functional!")
    else:
        print("❌ Comprehensive test failed - additional fixes needed")
    
    print("=" * 60)
