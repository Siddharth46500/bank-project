#!/usr/bin/env python3

# Check the actual table structure in the database
import sys
sys.path.append('/Users/kunalkumar/Desktop/kuanl')

from school_no_blockchain import get_connection

def check_table_structure():
    """Check the actual structure of TRANSACTION_HISTORY table"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check ACCOUNTS table structure
        print("ACCOUNTS table structure:")
        cursor.execute("DESCRIBE ACCOUNTS")
        accounts_columns = cursor.fetchall()
        for col in accounts_columns:
            print(f"  {col[0]}: {col[1]}")
        
        print("\nTRANSACTION_HISTORY table structure:")
        cursor.execute("DESCRIBE TRANSACTION_HISTORY")
        transaction_columns = cursor.fetchall()
        for col in transaction_columns:
            print(f"  {col[0]}: {col[1]}")
            
        # Check if table exists and has data
        cursor.execute("SELECT COUNT(*) FROM TRANSACTION_HISTORY")
        count = cursor.fetchone()
        print(f"\nTRANSACTION_HISTORY has {count[0]} rows")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error checking table structure: {e}")

if __name__ == "__main__":
    check_table_structure()
