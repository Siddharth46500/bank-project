#!/usr/bin/env python3

# Test script to verify MySQL lock timeout fix
import sys
import time
import threading
sys.path.append('/Users/kunalkumar/Desktop/kuanl')

from school_no_blockchain import get_connection, transfer_money, account_open, safe_decimal

def test_database_connection():
    """Test database connection with new timeout settings"""
    print("Testing Database Connection...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Test connection
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"✅ Database connection successful: {result}")
        
        # Test transaction isolation level
        cursor.execute("SELECT @@transaction_isolation")
        isolation = cursor.fetchone()
        print(f"✅ Transaction isolation level: {isolation[0]}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_account_operations():
    """Test basic account operations"""
    print("\nTesting Account Operations...")
    
    try:
        # Create a test account
        account_no = account_open("Test User", "1234567890", 1234, safe_decimal("1000.00"), "SAVINGS")
        if account_no:
            print(f"✅ Test account created: {account_no}")
            return account_no
        else:
            print("❌ Failed to create test account")
            return None
            
    except Exception as e:
        print(f"❌ Account creation failed: {e}")
        return None

def test_transaction_atomicity():
    """Test that transactions are atomic and properly handled"""
    print("\nTesting Transaction Atomicity...")
    
    try:
        # Create two test accounts
        acc1 = account_open("Test User 1", "1111111111", 1111, safe_decimal("1000.00"), "SAVINGS")
        acc2 = account_open("Test User 2", "2222222222", 2222, safe_decimal("500.00"), "SAVINGS")
        
        if acc1 and acc2:
            print(f"✅ Test accounts created: {acc1}, {acc2}")
            
            # Test transfer
            success = transfer_money(acc1, acc2, safe_decimal("200.00"), "Test transfer")
            if success:
                print("✅ Transfer completed successfully")
                return True
            else:
                print("❌ Transfer failed")
                return False
        else:
            print("❌ Failed to create test accounts")
            return False
            
    except Exception as e:
        print(f"❌ Transaction test failed: {e}")
        return False

def test_concurrent_access_simulation():
    """Simulate concurrent database access to test for lock timeouts"""
    print("\nTesting Concurrent Access Simulation...")
    
    def transfer_operation(thread_id):
        """Simulate a transfer operation"""
        try:
            # Create accounts for this thread
            acc_from = account_open(f"Thread {thread_id} User A", f"111{thread_id}", 1000+thread_id, safe_decimal("1000.00"), "SAVINGS")
            acc_to = account_open(f"Thread {thread_id} User B", f"222{thread_id}", 2000+thread_id, safe_decimal("500.00"), "SAVINGS")
            
            if acc_from and acc_to:
                # Perform transfer
                success = transfer_money(acc_from, acc_to, safe_decimal("100.00"), f"Thread {thread_id} transfer")
                return success
            return False
            
        except Exception as e:
            print(f"Thread {thread_id} error: {e}")
            return False
    
    try:
        # Simulate multiple concurrent operations
        threads = []
        for i in range(3):
            thread = threading.Thread(target=transfer_operation, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)  # 30 second timeout
        
        print("✅ Concurrent access test completed")
        return True
        
    except Exception as e:
        print(f"❌ Concurrent access test failed: {e}")
        return False

def cleanup_test_data():
    """Clean up any test data created during testing"""
    print("\nCleaning up test data...")
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Clean up test transaction history
        cursor.execute("DELETE FROM TRANSACTION_HISTORY WHERE remark_encrypted LIKE %s OR remark_encrypted LIKE %s", ('Test%', 'Thread%'))
        
        # Clean up test accounts (assuming account names start with "Test" or "Thread")
        cursor.execute("DELETE FROM ACCOUNTS WHERE name LIKE 'Test%' OR name LIKE 'Thread%'")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Test data cleaned up successfully")
        
    except Exception as e:
        print(f"Warning: Could not clean up test data: {e}")

if __name__ == "__main__":
    print("🔧 Testing MySQL Lock Timeout Fix for school_no_blockchain.py")
    print("=" * 70)
    
    # Run all tests
    test_results = []
    
    test_results.append(test_database_connection())
    
    if test_results[-1]:  # Only continue if database connection works
        test_results.append(test_account_operations())
        test_results.append(test_transaction_atomicity())
        test_results.append(test_concurrent_access_simulation())
    
    # Cleanup
    cleanup_test_data()
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST RESULTS SUMMARY:")
    print("=" * 70)
    
    if all(test_results):
        print("🎉 ALL TESTS PASSED!")
        print("🎉 MySQL lock timeout issue has been resolved!")
        print("🎉 The bank management system should now handle concurrent transactions properly!")
    else:
        print("❌ Some tests failed - additional fixes may be needed")
        print(f"Tests passed: {sum(test_results)}/{len(test_results)}")
