-- The summary's revenue and units are exactly the sum of the lines behind them.
with lines as (
    select month, round(sum(revenue), 2) as revenue, sum(qty) as units
    from {{ ref('fct_sales_lines') }}
    group by month
)

select summary.month
from {{ ref('mart_monthly_summary') }} as summary
inner join lines using (month)
where summary.revenue != lines.revenue
   or summary.units != lines.units
   or round(summary.north + summary.south + summary.central, 2) != summary.revenue
