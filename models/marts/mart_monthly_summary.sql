-- The workbook's Summary tab, rebuilt: same columns, same month labels, computed from the
-- corrected lines.
with lines as (
    select * from {{ ref('fct_sales_lines') }}
),

by_rep as (
    select month, rep_name, sum(revenue) as rep_revenue
    from lines
    group by month, rep_name
),

top_reps as (
    select month, arg_max(rep_name, rep_revenue) as top_rep
    from by_rep
    group by month
)

select
    lines.month,
    strftime(min(lines.sale_date), '%b %Y') as month_label,
    round(sum(lines.revenue), 2) as revenue,
    sum(lines.qty) as units,
    count(distinct lines.invoice) as invoices,
    round(sum(lines.revenue) / count(distinct lines.invoice), 2) as avg_invoice,
    round(sum(lines.revenue) filter (where lines.region = 'North'), 2) as north,
    round(sum(lines.revenue) filter (where lines.region = 'South'), 2) as south,
    round(sum(lines.revenue) filter (where lines.region = 'Central'), 2) as central,
    any_value(top_reps.top_rep) as top_rep
from lines
inner join top_reps using (month)
group by lines.month
order by lines.month
