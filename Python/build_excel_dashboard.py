import pandas as pd
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.worksheet.table import Table, TableStyleInfo

FONT_NAME = "Arial"
HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF", size=11)
TITLE_FONT = Font(name=FONT_NAME, bold=True, size=16, color="1F4E78")
SUBTITLE_FONT = Font(name=FONT_NAME, italic=True, size=10, color="595959")
KPI_LABEL_FONT = Font(name=FONT_NAME, size=10, color="595959")
KPI_VALUE_FONT = Font(name=FONT_NAME, bold=True, size=18, color="1F4E78")
BOLD = Font(name=FONT_NAME, bold=True)
NORMAL = Font(name=FONT_NAME, size=10)
thin = Side(style="thin", color="D9D9D9")
BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
KPI_FILL = PatternFill("solid", fgColor="F2F7FC")

customers = pd.read_csv("data/customers.csv")
products = pd.read_csv("data/products.csv")
orders = pd.read_csv("data/orders.csv", parse_dates=["order_date", "ship_date"])

merged = (
    orders.merge(customers, on="customer_id", how="left")
          .merge(products[["product_id", "product_name", "category"]], on="product_id", how="left")
)
merged = merged[[
    "order_id", "order_date", "customer_id", "customer_name", "region", "segment",
    "product_id", "product_name", "category", "quantity", "unit_price", "discount_pct",
    "gross_revenue", "discount_amount", "net_revenue", "total_cost", "profit",
    "ship_date", "shipping_type",
]].sort_values("order_date").reset_index(drop=True)

N = len(merged)                 # 6000
FIRST_ROW = 2
LAST_ROW = FIRST_ROW + N - 1    # 6001

wb = Workbook()

# =====================================================================
# Sheet: Orders (raw data)
# =====================================================================
ws = wb.active
ws.title = "Orders"
headers = ["Order ID", "Order Date", "Customer ID", "Customer Name", "Region", "Segment",
           "Product ID", "Product Name", "Category", "Quantity", "Unit Price", "Discount %",
           "Gross Revenue", "Discount Amount", "Net Revenue", "Total Cost", "Profit",
           "Ship Date", "Shipping Type"]
ws.append(headers)
for c in range(1, len(headers) + 1):
    cell = ws.cell(row=1, column=c)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal="center")

for row in merged.itertuples(index=False):
    ws.append(list(row))

# number formats
date_cols = [2, 18]
money_cols = [11, 13, 14, 15, 16, 17]
pct_cols = [12]
for r in range(FIRST_ROW, LAST_ROW + 1):
    for c in date_cols:
        ws.cell(row=r, column=c).number_format = "yyyy-mm-dd"
    for c in money_cols:
        ws.cell(row=r, column=c).number_format = "$#,##0.00"
    for c in pct_cols:
        ws.cell(row=r, column=c).number_format = "0%"

widths = [11, 12, 12, 16, 10, 14, 11, 22, 16, 9, 11, 10, 13, 14, 12, 11, 10, 11, 13]
for i, w in enumerate(widths, start=1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"

tab = Table(displayName="OrdersTable", ref=f"A1:S{LAST_ROW}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium9", showRowStripes=True)
ws.add_table(tab)

# Column letters for reference elsewhere
COL = {name: get_column_letter(i + 1) for i, name in enumerate(headers)}
# COL: Order Date=B, Region=E, Segment=F, Category=I, Net Revenue=O, Profit=Q, Discount%=L

ORD = "Orders"
RNG = lambda col: f"{ORD}!${COL[col]}${FIRST_ROW}:${COL[col]}${LAST_ROW}"

print("Column map:", COL)

# =====================================================================
# Sheet: Product Summary (helper — SUMIF rollups + rank, feeds Top-10 chart)
# =====================================================================
ps = wb.create_sheet("Product Summary")
ps.append(["Product Name", "Category", "Net Revenue", "Units Sold", "Rank (by Revenue)"])
for c in range(1, 6):
    cell = ps.cell(row=1, column=c)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL

prod_list = products[["product_name", "category"]].drop_duplicates().sort_values("product_name")
PFIRST, PLAST = 2, 1 + len(prod_list)
for i, r in enumerate(prod_list.itertuples(index=False), start=PFIRST):
    ps.cell(row=i, column=1, value=r.product_name)
    ps.cell(row=i, column=2, value=r.category)
    ps.cell(row=i, column=3, value=f"=SUMIF({RNG('Product Name')},A{i},{RNG('Net Revenue')})")
    ps.cell(row=i, column=4, value=f"=SUMIF({RNG('Product Name')},A{i},{RNG('Quantity')})")
    ps.cell(row=i, column=3).number_format = "$#,##0.00"

for i in range(PFIRST, PLAST + 1):
    ps.cell(row=i, column=5, value=f"=RANK(C{i},$C${PFIRST}:$C${PLAST},0)")

ps.column_dimensions["A"].width = 26
ps.column_dimensions["B"].width = 18
ps.column_dimensions["C"].width = 14
ps.column_dimensions["D"].width = 12
ps.column_dimensions["E"].width = 16

PS = "'Product Summary'"

# =====================================================================
# Sheet: Customers (raw reference data — enables clean distinct-customer counts)
# =====================================================================
cs = wb.create_sheet("Customers")
cs.append(["Customer ID", "Customer Name", "Region", "Segment", "Signup Date"])
for c in range(1, 6):
    cell = cs.cell(row=1, column=c)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
CFIRST = 2
for i, r in enumerate(customers.itertuples(index=False), start=CFIRST):
    cs.cell(row=i, column=1, value=r.customer_id)
    cs.cell(row=i, column=2, value=r.customer_name)
    cs.cell(row=i, column=3, value=r.region)
    cs.cell(row=i, column=4, value=r.segment)
    cs.cell(row=i, column=5, value=r.signup_date)
    cs.cell(row=i, column=5).number_format = "yyyy-mm-dd"
CLAST = CFIRST + len(customers) - 1
for i, w in enumerate([12, 16, 10, 14, 12], start=1):
    cs.column_dimensions[get_column_letter(i)].width = w
CUST_SEG_RNG = f"Customers!$D${CFIRST}:$D${CLAST}"

# =====================================================================
# Sheet: Dashboard
# =====================================================================
db = wb.create_sheet("Dashboard", 0)  # make it the first/active sheet
db.sheet_view.showGridLines = False

db["B2"] = "E-Commerce Sales Performance Dashboard"
db["B2"].font = TITLE_FONT
db["B3"] = "Jan 2024 – Dec 2025  |  Source: Orders sheet (6,000 orders, 500 customers, 31 SKUs)"
db["B3"].font = SUBTITLE_FONT

# ---- KPI cards ----
kpis = [
    ("Total Net Revenue", f"=SUM({RNG('Net Revenue')})", "$#,##0"),
    ("Total Profit", f"=SUM({RNG('Profit')})", "$#,##0"),
    ("Total Orders", f"=COUNTA({RNG('Order ID')})", "#,##0"),
    ("Avg Order Value", f"=SUM({RNG('Net Revenue')})/COUNTA({RNG('Order ID')})", "$#,##0.00"),
    ("Overall Profit Margin", f"=SUM({RNG('Profit')})/SUM({RNG('Net Revenue')})", "0.0%"),
]
kpi_col_start = 2  # column B
kpi_row_label, kpi_row_value = 5, 6
for i, (label, formula, fmt) in enumerate(kpis):
    col = kpi_col_start + i * 3
    for rr in (kpi_row_label, kpi_row_value):
        for cc in (col, col + 1):
            db.cell(row=rr, column=cc).fill = KPI_FILL
    lbl = db.cell(row=kpi_row_label, column=col, value=label)
    lbl.font = KPI_LABEL_FONT
    val = db.cell(row=kpi_row_value, column=col, value=formula)
    val.font = KPI_VALUE_FONT
    val.number_format = fmt
    db.merge_cells(start_row=kpi_row_label, start_column=col, end_row=kpi_row_label, end_column=col + 1)
    db.merge_cells(start_row=kpi_row_value, start_column=col, end_row=kpi_row_value, end_column=col + 1)

for i in range(1, 18):
    db.column_dimensions[get_column_letter(i)].width = 11

# ---- Table 1: Revenue & Profit by Category ----
cat_row0 = 9
db.cell(row=cat_row0, column=2, value="Revenue & Profit by Category").font = BOLD
hdr = cat_row0 + 1
for j, h in enumerate(["Category", "Net Revenue", "Profit", "Margin %"]):
    cell = db.cell(row=hdr, column=2 + j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
categories = sorted(products["category"].unique())
for i, cat in enumerate(categories, start=hdr + 1):
    db.cell(row=i, column=2, value=cat)
    db.cell(row=i, column=3, value=f"=SUMIF({RNG('Category')},B{i},{RNG('Net Revenue')})").number_format = "$#,##0"
    db.cell(row=i, column=4, value=f"=SUMIF({RNG('Category')},B{i},{RNG('Profit')})").number_format = "$#,##0"
    db.cell(row=i, column=5, value=f"=D{i}/C{i}").number_format = "0.0%"
cat_last = hdr + len(categories)

# ---- Table 2: Revenue by Region ----
reg_row0 = cat_last + 3
db.cell(row=reg_row0, column=2, value="Revenue by Region").font = BOLD
hdr2 = reg_row0 + 1
for j, h in enumerate(["Region", "Net Revenue", "Orders", "Avg Order Value"]):
    cell = db.cell(row=hdr2, column=2 + j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
regions = sorted(customers["region"].unique())
for i, reg in enumerate(regions, start=hdr2 + 1):
    db.cell(row=i, column=2, value=reg)
    db.cell(row=i, column=3, value=f"=SUMIF({RNG('Region')},B{i},{RNG('Net Revenue')})").number_format = "$#,##0"
    db.cell(row=i, column=4, value=f"=COUNTIF({RNG('Region')},B{i})").number_format = "#,##0"
    db.cell(row=i, column=5, value=f"=C{i}/D{i}").number_format = "$#,##0.00"
reg_last = hdr2 + len(regions)

# ---- Table 3: Customer Segment Performance ----
seg_row0 = reg_last + 3
db.cell(row=seg_row0, column=2, value="Customer Segment Performance").font = BOLD
hdr3 = seg_row0 + 1
for j, h in enumerate(["Segment", "Net Revenue", "Orders", "Customers", "Revenue / Customer"]):
    cell = db.cell(row=hdr3, column=2 + j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
segments = sorted(customers["segment"].unique())
for i, seg in enumerate(segments, start=hdr3 + 1):
    db.cell(row=i, column=2, value=seg)
    db.cell(row=i, column=3, value=f"=SUMIF({RNG('Segment')},B{i},{RNG('Net Revenue')})").number_format = "$#,##0"
    db.cell(row=i, column=4, value=f"=COUNTIF({RNG('Segment')},B{i})").number_format = "#,##0"
    db.cell(row=i, column=5, value=f"=COUNTIF({CUST_SEG_RNG},B{i})").number_format = "#,##0"
    db.cell(row=i, column=6, value=f"=C{i}/E{i}").number_format = "$#,##0"
seg_last = hdr3 + len(segments)

# ---- Table 4: Discount Tier Impact ----
disc_row0 = seg_last + 3
db.cell(row=disc_row0, column=2, value="Discount Tier Impact on Margin").font = BOLD
hdr4 = disc_row0 + 1
for j, h in enumerate(["Discount Tier", "Orders", "Net Revenue", "Avg Margin %"]):
    cell = db.cell(row=hdr4, column=2 + j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
tiers = ["0% (no discount)", "1-10%", "11%+"]
# helper column T on Orders sheet computes the tier per row (keeps Dashboard formulas simple & robust)
ws.cell(row=1, column=20, value="Discount Tier").font = HEADER_FONT
ws.cell(row=1, column=20).fill = HEADER_FILL
for r in range(FIRST_ROW, LAST_ROW + 1):
    ws.cell(row=r, column=20,
             value=f'=IF(L{r}=0,"0% (no discount)",IF(L{r}<=0.1,"1-10%","11%+"))')
ws.column_dimensions["T"].width = 16
TIER_RNG = f"{ORD}!$T${FIRST_ROW}:$T${LAST_ROW}"
for i, tier in enumerate(tiers, start=hdr4 + 1):
    db.cell(row=i, column=2, value=tier)
    db.cell(row=i, column=3, value=f"=COUNTIF({TIER_RNG},B{i})").number_format = "#,##0"
    db.cell(row=i, column=4, value=f"=SUMIF({TIER_RNG},B{i},{RNG('Net Revenue')})").number_format = "$#,##0"
    db.cell(row=i, column=5, value=f"=SUMIF({TIER_RNG},B{i},{RNG('Profit')})/D{i}").number_format = "0.0%"
disc_last = hdr4 + len(tiers)

# ---- Table 5: Monthly Revenue Trend (24 months) ----
month_row0 = 9
month_col0 = 8  # column H, to the right of the tables above
db.cell(row=month_row0, column=month_col0, value="Monthly Net Revenue & Profit Trend").font = BOLD
hdr5 = month_row0 + 1
for j, h in enumerate(["Month", "Net Revenue", "Profit"]):
    cell = db.cell(row=hdr5, column=month_col0 + j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
months = pd.date_range("2024-01-01", "2025-12-01", freq="MS")
for i, m in enumerate(months, start=hdr5 + 1):
    start_d = m.date()
    end_d = (m + pd.offsets.MonthBegin(1)).date()
    c_month = db.cell(row=i, column=month_col0, value=start_d)
    c_month.number_format = "mmm-yyyy"
    db.cell(row=i, column=month_col0 + 1,
             value=f'=SUMIFS({RNG("Net Revenue")},{RNG("Order Date")},">="&{get_column_letter(month_col0)}{i},{RNG("Order Date")},"<"&DATE({end_d.year},{end_d.month},{end_d.day}))').number_format = "$#,##0"
    db.cell(row=i, column=month_col0 + 2,
             value=f'=SUMIFS({RNG("Profit")},{RNG("Order Date")},">="&{get_column_letter(month_col0)}{i},{RNG("Order Date")},"<"&DATE({end_d.year},{end_d.month},{end_d.day}))').number_format = "$#,##0"
month_last = hdr5 + len(months)

# ---- Table 6: Top 10 Products by Net Revenue ----
top_row0 = month_last + 3
db.cell(row=top_row0, column=month_col0, value="Top 10 Products by Net Revenue").font = BOLD
hdr6 = top_row0 + 1
for j, h in enumerate(["Rank", "Product Name", "Net Revenue"]):
    cell = db.cell(row=hdr6, column=month_col0 + j, value=h)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
for i, rnk in enumerate(range(1, 11), start=hdr6 + 1):
    db.cell(row=i, column=month_col0, value=rnk)
    db.cell(row=i, column=month_col0 + 1,
             value=f"=INDEX({PS}!$A${PFIRST}:$A${PLAST},MATCH({get_column_letter(month_col0)}{i},{PS}!$E${PFIRST}:$E${PLAST},0))")
    db.cell(row=i, column=month_col0 + 2,
             value=f"=INDEX({PS}!$C${PFIRST}:$C${PLAST},MATCH({get_column_letter(month_col0)}{i},{PS}!$E${PFIRST}:$E${PLAST},0))").number_format = "$#,##0"
top_last = hdr6 + 10

for i in range(1, 18):
    db.column_dimensions[get_column_letter(i)].width = 15
db.column_dimensions["A"].width = 3

# =====================================================================
# Charts
# =====================================================================

def style_chart(chart, title, height=8, width=16):
    chart.title = title
    chart.style = 10
    chart.height = height
    chart.width = width
    chart.y_axis.majorGridlines = None

# Chart 1: Revenue & Profit by Category (bar)
c1 = BarChart()
c1.type = "col"
c1.grouping = "clustered"
data = Reference(db, min_col=3, max_col=4, min_row=hdr, max_row=cat_last)
cats = Reference(db, min_col=2, min_row=hdr + 1, max_row=cat_last)
c1.add_data(data, titles_from_data=True)
c1.set_categories(cats)
c1.y_axis.scaling.min = 0
style_chart(c1, "Revenue & Profit by Category")
db.add_chart(c1, f"B{cat_last + 2}")

# Chart 2: Revenue by Region (bar)
c2 = BarChart()
c2.type = "col"
data = Reference(db, min_col=3, max_col=3, min_row=hdr2, max_row=reg_last)
cats = Reference(db, min_col=2, min_row=hdr2 + 1, max_row=reg_last)
c2.add_data(data, titles_from_data=True)
c2.set_categories(cats)
c2.y_axis.scaling.min = 0
style_chart(c2, "Net Revenue by Region")
db.add_chart(c2, f"B{reg_last + 2}")

# Chart 3: Monthly Revenue & Profit Trend (line)
c3 = LineChart()
data = Reference(db, min_col=9, max_col=10, min_row=hdr5, max_row=month_last)
cats = Reference(db, min_col=8, min_row=hdr5 + 1, max_row=month_last)
c3.add_data(data, titles_from_data=True)
c3.set_categories(cats)
for s in c3.series:
    s.smooth = False
    s.marker.symbol = "circle"
    s.marker.size = 5
style_chart(c3, "Monthly Net Revenue & Profit Trend", height=8, width=22)
db.add_chart(c3, f"H{month_last + 2}")

# Chart 4: Top 10 Products by Revenue (bar)
c4 = BarChart()
c4.type = "bar"  # horizontal bars read better for long product names
data = Reference(db, min_col=10, max_col=10, min_row=hdr6, max_row=top_last)
cats = Reference(db, min_col=9, min_row=hdr6 + 1, max_row=top_last)
c4.add_data(data, titles_from_data=True)
c4.set_categories(cats)
c4.y_axis.delete = False
style_chart(c4, "Top 10 Products by Net Revenue", height=9, width=22)
db.add_chart(c4, f"H{top_last + 2}")

# Chart 5: Discount Tier Impact (bar)
c5 = BarChart()
c5.type = "col"
data = Reference(db, min_col=5, max_col=5, min_row=hdr4, max_row=disc_last)
cats = Reference(db, min_col=2, min_row=hdr4 + 1, max_row=disc_last)
c5.add_data(data, titles_from_data=True)
c5.set_categories(cats)
c5.y_axis.scaling.min = 0
style_chart(c5, "Avg Profit Margin % by Discount Tier")
db.add_chart(c5, f"B{disc_last + 2}")

# =====================================================================
# Sheet: Read Me
# =====================================================================
rm = wb.create_sheet("Read Me")
rm.sheet_view.showGridLines = False
rm["B2"] = "E-Commerce Sales Dashboard — Read Me"
rm["B2"].font = TITLE_FONT
lines = [
    "",
    "PURPOSE",
    "This workbook analyzes 2 years (2024-2025) of e-commerce order data: 6,000 orders,",
    "500 customers, and 31 SKUs across 5 categories.",
    "",
    "HOW IT'S BUILT",
    "- 'Orders' holds the raw, transaction-level data (one row per order) as an Excel Table.",
    "- 'Customers' and 'Product Summary' are reference/helper sheets the dashboard formulas pull from.",
    "- 'Dashboard' contains only live formulas (SUMIF/SUMIFS/COUNTIF/INDEX-MATCH/RANK) — nothing",
    "  is hardcoded, so every KPI, table, and chart recalculates automatically if you edit or",
    "  extend the Orders data.",
    "",
    "HOW TO EXTEND IT",
    "- Add new rows to the bottom of the Orders table; formulas reference a fixed range",
    "  (rows 2-6001) — extend the ranges in Dashboard / Product Summary if you add rows.",
    "- Add a new product to 'Product Summary' and it will automatically be eligible for the",
    "  Top-10 ranking.",
    "",
    "COMPANION SQL ANALYSIS",
    "See /sql in the project repo for deeper analysis this workbook doesn't cover:",
    "RFM customer segmentation, at-risk/churn-candidate customers, new-vs-returning revenue",
    "split, and month-over-month growth rates.",
]
for i, line in enumerate(lines, start=3):
    cell = rm.cell(row=i, column=2, value=line)
    if line.isupper() and line:
        cell.font = BOLD
    else:
        cell.font = NORMAL
rm.column_dimensions["B"].width = 95

wb.move_sheet("Read Me", offset=-(wb.sheetnames.index("Read Me")))
wb.active = wb.sheetnames.index("Dashboard")

wb.save("excel/Ecommerce_Sales_Dashboard.xlsx")
print("All tables + charts + Read Me written. cat_last", cat_last, "reg_last", reg_last, "seg_last", seg_last,
      "disc_last", disc_last, "month_last", month_last, "top_last", top_last)
