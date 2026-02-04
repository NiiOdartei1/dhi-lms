"""Test script to verify finance_routes fixes"""

import sys
sys.path.insert(0, 'c:/Users/lampt/Desktop/LMS')

try:
    print("Testing finance_routes fixes...\n")
    
    # Test 1: Import modules
    print("✅ Test 1: Importing modules...")
    from models import StudentFeeBalance, StudentFeeTransaction, User, StudentProfile
    from finance_routes import (
        get_financial_summary,
        get_payment_method_breakdown,
        get_daily_revenue,
        get_weekly_revenue,
        get_monthly_revenue
    )
    print("   Successfully imported all functions\n")
    
    # Test 2: Check StudentFeeBalance fields
    print("✅ Test 2: Checking StudentFeeBalance model...")
    print(f"   Fields: {[col.name for col in StudentFeeBalance.__table__.columns]}")
    print(f"   Has 'balance' field: {'balance' in [col.name for col in StudentFeeBalance.__table__.columns]}")
    print(f"   Has 'amount_due' field: {'amount_due' in [col.name for col in StudentFeeBalance.__table__.columns]}")
    print(f"   Has 'amount_paid' field: {'amount_paid' in [col.name for col in StudentFeeBalance.__table__.columns]}\n")
    
    # Test 3: Test financial summary (should not error)
    print("✅ Test 3: Testing get_financial_summary()...")
    try:
        summary = get_financial_summary()
        print(f"   Result: {summary}\n")
    except Exception as e:
        print(f"   ERROR: {e}\n")
    
    # Test 4: Test payment method breakdown
    print("✅ Test 4: Testing get_payment_method_breakdown()...")
    try:
        methods = get_payment_method_breakdown()
        print(f"   Result type: {type(methods)}")
        print(f"   Result length: {len(methods)}")
        if methods:
            print(f"   First method type: {type(methods[0])}")
            print(f"   First method: {methods[0]}\n")
        else:
            print(f"   No payment methods found (this is OK if database is empty)\n")
    except Exception as e:
        print(f"   ERROR: {e}\n")
    
    print("✅ All tests completed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
