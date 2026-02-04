# Finance Reports Setup Guide

## Overview
Complete financial reporting system with Daily, Weekly, and Monthly reports with charts and analytics.

## Backend Implementation

### Routes Added
1. **GET `/admin/finance/reports`** - Main reports page
2. **GET `/admin/finance/api/reports/daily`** - Daily report data
3. **GET `/admin/finance/api/reports/weekly`** - Weekly report data
4. **GET `/admin/finance/api/reports/monthly`** - Monthly report data
5. **GET `/admin/finance/api/reports/transactions`** - Transactions API

### Helper Functions
```python
- get_daily_revenue(days=30)          # Daily revenue for last N days
- get_weekly_revenue()                # Current & last week comparison
- get_monthly_revenue(months=12)      # Monthly revenue trend
- get_today_transactions_count()      # Today's transaction count
- get_department_breakdown()          # Revenue by department
- get_financial_summary()             # Overall financial stats
- get_payment_method_breakdown()      # Payment method analysis
- get_top_debtors(limit=20)          # Top debtors list
```

## Frontend Features

### Daily Report Tab
✅ Today's revenue card
✅ Today's transactions count
✅ Average transaction value
✅ Pending approvals count
✅ 30-day revenue trend chart
✅ Today's transactions table with student details

### Weekly Report Tab
✅ Week's total revenue
✅ Weekly transactions count
✅ Best performing day
✅ Week vs Last Week trend indicator
✅ Weekly revenue bar chart
✅ Week-over-week comparison chart
✅ Weekly summary card

### Monthly Report Tab
✅ Current month's revenue
✅ Monthly transactions count
✅ Collection rate percentage
✅ Outstanding balance amount
✅ Monthly revenue trend line chart
✅ Revenue by department pie chart
✅ Month vs Year-to-Date comparison
✅ Detailed monthly breakdown table

## Data Visualization
- **Line Charts**: Revenue trends
- **Bar Charts**: Weekly/daily breakdowns
- **Doughnut/Pie Charts**: Distribution analysis
- **Interactive Tooltips**: Hover for details
- **Responsive Design**: Mobile-friendly
- **Print Support**: Built-in print functionality
- **Export Option**: Download reports

## Key Statistics Tracked
1. Daily Revenue
2. Weekly Revenue & Trends
3. Monthly Revenue & YTD
4. Transaction Count
5. Average Transaction Value
6. Collection Rate
7. Outstanding Balance
8. Payment Methods
9. Top Debtors
10. Department Breakdown

## Database Queries
All functions use SQLAlchemy ORM with proper:
- Date grouping and aggregation
- Filtering by approval status
- Relationship joins
- Error handling and logging

## Error Handling
- Try-catch blocks on all functions
- Graceful fallbacks for missing data
- User-friendly error messages
- Comprehensive logging for debugging

## Security
- @login_required decorator on all routes
- @require_finance_admin permission check
- CSRF protection with meta tag
- Role-based access control

## How to Test

1. Navigate to `/admin/finance/reports`
2. Ensure you have finance admin permissions
3. Click through the three tabs (Daily/Weekly/Monthly)
4. Charts should load dynamically
5. Try the Print and Export buttons
6. Check browser console for any errors

## API Response Format
```json
{
    "success": true,
    "data": [...],
    "total": 0.00,
    "average": 0.00
}
```

## Notes
- All monetary values in GHS (Ghana Cedis)
- Dates are handled with UTC timezone
- Chart.js v3.9.1 for visualization
- Bootstrap 5 for styling
- Responsive grid layout

## Future Enhancements
- PDF export using jsPDF
- Email report scheduling
- Custom date range filtering
- Additional metrics (growth rate, forecasting)
- Real-time websocket updates
- Data caching for performance
