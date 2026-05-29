# Payroll Reconciliation Tool - Process Guide

## Overview

The **Payroll Reconciliation Tool** helps organizations verify that their payroll payments match their accounting records. Think of it like balancing your bank statement—we're checking that all the money paid out in salaries actually matches what the system recorded.

---

## Step-by-Step Process (From Start to End)

### **Step 1: Upload Your Payroll File**
**What Happens:** You select an Excel file containing your payroll data

**Why:** The tool needs your raw payroll information to work with. This is your source data.

**What We Achieve:**
- System recognizes and loads your file
- Makes the file ready for analysis

---

### **Step 2: Select Which Worksheet to Use**
**What Happens:** You choose which sheet within your Excel file to analyze (many Excel files have multiple sheets)

**Why:** Your Excel file might contain different types of payroll data (regular payroll, bonuses, tax adjustments) on different sheets. We need to know which one to use.

**What We Achieve:**
- Identifies all available sheets in your file
- Loads the selected sheet's preview so you can see what you're working with

---

### **Step 3: Specify the Header Row**
**What Happens:** You tell the system which row contains your column names (headers)

**Why:** Not all Excel files have headers in row 1. Some have titles or blank rows at the top. We need to know where the actual column names are.

**Example:** 
- Row 1 might say "CONFIDENTIAL PAYROLL DATA"
- Row 2 might be blank
- Row 3 might have your actual column names: "Employee ID", "Pay Date", "Salary", etc.

**What We Achieve:**
- Correctly identifies what each column represents
- Properly loads all your data

---

### **Step 4: Load and Preview Your Data**
**What Happens:** The system reads all the data from your sheet and shows you what was loaded

**Why:** This is a sanity check—you want to confirm that the data looks correct before we process it.

**What We Achieve:**
- Shows you how many rows were loaded
- Displays a preview of the data
- Lists all available columns you can work with

---

### **Step 5: Configure Total Tax Column (Optional)**
**What Happens:** If you want, you can create a "Total Tax" column by adding up multiple tax columns

**Why:** Sometimes payroll has different tax types (federal, state, local, FICA, etc.) spread across multiple columns. It's easier to reconcile if we combine them.

**Example:**
- Your file has: Federal_Tax, State_Tax, Local_Tax
- You can create: Total_Tax = Federal_Tax + State_Tax + Local_Tax

**What We Achieve:**
- Creates a single tax column for easier reconciliation
- Makes the final report cleaner and easier to read

---

### **Step 6: Select Your Reconciliation Period**
**What Happens:** You choose the date range you want to reconcile (e.g., April 2025 to March 2026)

**Why:** Payroll records typically need to be reconciled for a specific fiscal year or accounting period, not all data at once.

**What We Achieve:**
- Filters data to only include payroll from your selected period
- Shows how many rows match your date range

---

### **Step 7: Enable Accrued Payroll Mode (Optional, Advanced)**
**What Happens:** You can choose to add an extra month of data for accrued payroll accounting

**Why:** This is for complex accounting situations:
- Sometimes payroll is accrued (recorded) in one month but paid in the next
- When reconciling an accounting period (e.g., April 2025—March 2026), you might need to include payroll accruals from April 2026 that relate to March 2026
- This mode automatically includes that extra month and separates the accrued portions

**Accrued Mode Does Two Things:**
1. **Normal Payroll:** Shows payroll that should be recognized in your selected period
2. **Accrued Payroll:** Shows payroll that relates to your period but was paid/recorded outside it

**What We Achieve:**
- Properly accounts for payroll that spans accounting periods
- Creates separate reports for accounting and accrual purposes
- Ensures GL codes (accounting codes) are correctly assigned

---

### **Step 8: Select How to Group Your Data**
**What Happens:** You configure which columns to group by and which to sum

**Configuration:**
- **Group By Pay Date Column:** Which column has the payment dates (e.g., "Pay Date")
- **Group By Period Begin/End:** The date range the payroll covers (e.g., "Period Start Date", "Period End Date")
- **Columns to Sum (Aggregate):** Which columns should be added together (e.g., "Gross Pay", "Net Pay", "Tax")
- **Additional Fields to Keep:** Other columns you want in the report but not summed (e.g., "Department", "Employee Count")

**Why:** This tells the system how to organize and summarize your payroll data. Different organizations need different groupings.

**Example:**
```
Raw Data (5 rows):
Pay Date    | Gross Pay | Department
2025-04-15  | $5,000    | Sales
2025-04-15  | $3,000    | Sales
2025-04-15  | $2,000    | Engineering

After grouping by Pay Date and summing Gross Pay:
Pay Date    | Gross Pay | Department
2025-04-15  | $10,000   | Sales (first one kept)
```

**What We Achieve:**
- Consolidates multiple individual pay records into summary rows
- Creates a clean, organized report grouped by dates
- Sums up all amounts for easier reconciliation with accounting records

---

### **Step 9: Generate the Reconciliation Report**
**What Happens:** The system processes your data based on all your settings and creates a grouped report

**The Report Includes:**
- **Grouped Payroll Report:** Your payroll data organized and summed up according to your grouping rules
- **Accrued Payroll (if enabled):** Separate section showing accrued amounts with GL codes
- **Review Checks:** Validation checks to ensure data integrity

**Special Processing (if Accrued Mode is On):**
The system classifies each payroll run into categories:
1. **Normal Payroll** - Fully within your reconciliation period
2. **Prior Year Paid This Year** - From prior year but paid in current year
3. **Current Year Paid Next Year** - From current year but paid in next year
4. **Split Beginning of Year** - Spans the period start date
5. **Split End of Year** - Spans the period end date

For split payroll, the system calculates what portion belongs to each period (using working days), ensuring accurate accounting.

**What We Achieve:**
- Organized, summarized payroll report
- Proper classification of complex payroll scenarios
- Accrued portions separated for accounting GL posting
- Foundation for financial reconciliation

---

### **Step 10: Review and Adjust Order (Optional)**
**What Happens:** You can edit the report to reorder rows if needed

**Why:** The system sorts alphabetically or by date, but you might want a custom order for your accounting team.

**What We Achieve:**
- Allows manual customization of the report layout
- Makes it easier for accountants to use the report

---

### **Step 11: Verify Data Integrity with Review Checks**
**What Happens:** The system runs validation checks on your data

**Checks Include:**
- **Row Counts:** Original rows vs. grouped rows (should match or decrease when grouping)
- **Amount Validation:** Total amounts in source data vs. grouped data (should match perfectly)
- **Accrued Validation:** If accrued mode is on, checks that amounts balance across normal and accrued portions

**Why:** This catches errors early:
- If totals don't match, something went wrong during grouping
- If row counts are wrong, we might have lost data
- For accrued mode, this ensures no amounts were lost when splitting

**What We Achieve:**
- Confirms data integrity
- Alerts you if something needs investigation
- Gives confidence that your report is accurate

---

### **Step 12: Download Your Report**
**What Happens:** You download an Excel file containing your reconciliation report

**What's in the Excel File:**
- **Grouped Payroll Sheet:** Your organized payroll data
- **Accrued Payroll Sheet:** (if applicable) Separated accrued amounts with GL codes
- **Review Checks Sheet:** All validation checks and their results
- **Summary Information:** Configuration details and totals

**What We Achieve:**
- Creates an auditable record of your reconciliation
- Provides a format your accounting system can use
- Documents everything for compliance and audit purposes

---

## Key Concepts Explained Simply

### **Grouping/Aggregation**
Instead of showing 500 individual paycheck records, we group them by pay date and sum the amounts. This makes reconciliation easier.

### **Proration (in Accrued Mode)**
When payroll covers multiple months (e.g., a paycheck for April 15–May 15), we split it proportionally between months based on working days. If 60% falls in April and 40% in May, we split the amounts accordingly.

### **GL Code 2157**
This is the accounting code for "Accrued Payroll Liability"—it's where accountants record payroll that's been earned but not yet paid.

### **Accrued vs. Normal**
- **Normal:** Payroll that matches your accounting period exactly
- **Accrued:** Payroll that relates to your period but was earned or paid in a different period

---

## What Success Looks Like

✅ **All review checks pass** - Totals match, row counts are correct  
✅ **No data is lost** - Amount totals stay the same through grouping  
✅ **Report is organized** - Data is logically grouped by pay date  
✅ **Easy to reconcile** - Accountants can quickly match to GL accounts  
✅ **Auditable** - Complete record of what was grouped and how  

---

## Common Questions

**Q: Why does my row count decrease?**  
A: Because we're grouping multiple rows into one. Five paychecks with the same pay date become one line item.

**Q: When should I use Accrued Mode?**  
A: When payroll dates span your accounting period boundaries, or when your accounting system requires accrual entries.

**Q: What if the review checks show a difference?**  
A: It usually means there's a data quality issue (missing dates, invalid amounts, or wrong column selections). The difference amount points you to what's wrong.

**Q: Can I adjust the report after downloading?**  
A: Yes, it's an Excel file. But changes won't carry back into this tool—they're manual adjustments to the exported report.

---

## Technical Notes

- **Date Format:** All dates are normalized to remove time components (e.g., 2025-04-15 12:30 becomes 2025-04-15)
- **Missing Data:** Rows with missing pay dates are excluded
- **Working Days:** Proration calculations use Monday–Friday working days only
- **Numeric Handling:** All amounts are converted to numbers; non-numeric values treated as 0
- **Grouping:** Composite keys (pay date + period dates) ensure accurate grouping

---

## Summary

This tool automates the tedious work of organizing, grouping, and validating payroll data for reconciliation. By following these steps, you:

1. **Load** your payroll data
2. **Configure** how it should be organized
3. **Generate** a professional reconciliation report
4. **Validate** that all amounts are correct
5. **Download** an auditable Excel file

The result is a clean, verified payroll reconciliation ready for your accounting team to match against GL accounts.
