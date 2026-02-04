#!/usr/bin/env python3
"""
Mobile WhatsApp-Style Chat Validation Script
Tests the implementation of mobile-optimized chat features
"""

import os
import re
import sys

def check_file_exists(path):
    """Check if a file exists"""
    return os.path.isfile(path)

def read_file(path):
    """Read file contents"""
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except:
        return ""

def validate_implementation():
    """Validate mobile WhatsApp-style implementation"""
    
    errors = []
    warnings = []
    successes = []
    
    print("=" * 60)
    print("MOBILE WHATSAPP-STYLE CHAT VALIDATION")
    print("=" * 60)
    print()
    
    # ==========================================
    # 1. Check Files Exist
    # ==========================================
    print("1. Checking required files...")
    required_files = {
        'chat_routes.py': 'Backend routes',
        'templates/chat.html': 'HTML template',
        'static/css/chat.css': 'Styling'
    }
    
    for file_path, description in required_files.items():
        if check_file_exists(file_path):
            successes.append(f"✓ {file_path} exists ({description})")
        else:
            errors.append(f"✗ {file_path} missing ({description})")
    
    print()
    
    # ==========================================
    # 2. Check CSS Mobile Features
    # ==========================================
    print("2. Checking CSS mobile features...")
    css_content = read_file('static/css/chat.css')
    
    css_checks = {
        '.mobile-status-bar': 'Mobile status bar',
        '.mobile-app-header': 'Mobile app header',
        '.fab': 'Floating Action Button',
        '.bottom-sheet': 'Bottom sheet modal',
        '@media (max-width: 768px)': 'Tablet/mobile breakpoint',
        '@media (max-width: 480px)': 'Small mobile breakpoint',
        'slideUp': 'Slide-up animation',
        'linear-gradient(135deg, #075E54': 'WhatsApp teal gradient'
    }
    
    for pattern, description in css_checks.items():
        if pattern in css_content:
            successes.append(f"✓ CSS: {description}")
        else:
            errors.append(f"✗ CSS: {description} not found")
    
    print()
    
    # ==========================================
    # 3. Check HTML Mobile Elements
    # ==========================================
    print("3. Checking HTML mobile elements...")
    html_content = read_file('templates/chat.html')
    
    html_checks = {
        'mobile-status-bar': 'Mobile status bar HTML',
        'mobile-app-header': 'Mobile app header HTML',
        'id="fabBtn"': 'FAB button element',
        'id="bottomSheet"': 'Bottom sheet element',
        'bottomNewDM': 'New DM option',
        'bottomNewGroup': 'New Group option',
        'Font Awesome': 'Font Awesome icons'
    }
    
    for pattern, description in html_checks.items():
        if pattern in html_content:
            successes.append(f"✓ HTML: {description}")
        else:
            errors.append(f"✗ HTML: {description} not found")
    
    print()
    
    # ==========================================
    # 4. Check JavaScript Functionality
    # ==========================================
    print("4. Checking JavaScript event handlers...")
    
    js_checks = {
        "getElementById('fabBtn')": 'FAB click handler',
        "getElementById('bottomSheet')": 'Bottom sheet handlers',
        "addEventListener('click'": 'Event listeners',
        "isMobileView()": 'Mobile detection function',
        "orientationchange": 'Orientation change handling',
        "updateMobileStatus": 'Online/offline status',
        "touchstart": 'Touch gesture support'
    }
    
    for pattern, description in js_checks.items():
        if pattern in html_content:
            successes.append(f"✓ JS: {description}")
        else:
            warnings.append(f"⚠ JS: {description} not found (may be in external script)")
    
    print()
    
    # ==========================================
    # 5. Check Backend Admin Support
    # ==========================================
    print("5. Checking backend admin integration...")
    routes_content = read_file('chat_routes.py')
    
    backend_checks = {
        'is_user_or_admin': 'Auth function updated',
        'resolve_person_by_public_id': 'Person lookup function',
        'Admin.query': 'Admin table queries',
        '"superadmin"': 'Superadmin role support',
        '"finance_admin"': 'Finance admin role support',
        '"academic_admin"': 'Academic admin role support',
        '"admissions_admin"': 'Admissions admin role support'
    }
    
    for pattern, description in backend_checks.items():
        if pattern in routes_content:
            successes.append(f"✓ Backend: {description}")
        else:
            errors.append(f"✗ Backend: {description} not found")
    
    print()
    
    # ==========================================
    # 6. Check File Sizes
    # ==========================================
    print("6. Checking file sizes...")
    try:
        css_size = os.path.getsize('static/css/chat.css')
        html_size = os.path.getsize('templates/chat.html')
        routes_size = os.path.getsize('chat_routes.py')
        
        print(f"  CSS file: {css_size:,} bytes")
        print(f"  HTML file: {html_size:,} bytes")
        print(f"  Routes file: {routes_size:,} bytes")
        
        if css_size > 2500:  # Expected ~2700+ bytes
            successes.append("✓ CSS file size reasonable")
        else:
            warnings.append("⚠ CSS file smaller than expected (may be missing styles)")
            
        if html_size > 650:  # Expected ~680 bytes
            successes.append("✓ HTML file size reasonable")
        else:
            warnings.append("⚠ HTML file smaller than expected (may be missing elements)")
    except:
        warnings.append("⚠ Could not check file sizes")
    
    print()
    
    # ==========================================
    # Print Results
    # ==========================================
    print("=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print()
    
    if successes:
        print(f"✓ SUCCESSES ({len(successes)}):")
        for msg in successes:
            print(f"  {msg}")
        print()
    
    if warnings:
        print(f"⚠ WARNINGS ({len(warnings)}):")
        for msg in warnings:
            print(f"  {msg}")
        print()
    
    if errors:
        print(f"✗ ERRORS ({len(errors)}):")
        for msg in errors:
            print(f"  {msg}")
        print()
    
    # Summary
    total_checks = len(successes) + len(warnings) + len(errors)
    success_rate = (len(successes) / total_checks * 100) if total_checks > 0 else 0
    
    print("=" * 60)
    print(f"SUMMARY: {len(successes)}/{total_checks} checks passed ({success_rate:.1f}%)")
    print("=" * 60)
    
    if len(errors) == 0:
        print("✓ Mobile WhatsApp-style implementation is COMPLETE!")
        print()
        print("Next steps:")
        print("  1. Test on mobile devices (≤768px screens)")
        print("  2. Test admin chat integration")
        print("  3. Verify responsive breakpoints")
        print("  4. Test touch interactions (swipe, FAB, etc.)")
        print("  5. Monitor performance metrics")
        print()
        return 0
    else:
        print("✗ Implementation has errors. Please review above.")
        print()
        return 1

if __name__ == '__main__':
    sys.exit(validate_implementation())
