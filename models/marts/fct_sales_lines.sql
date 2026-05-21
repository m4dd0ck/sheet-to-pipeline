-- One row per real invoice line, priced from the product list in force on the sale date.
with lines as (
    select * from {{ ref('stg_sales_lines') }}
    where not is_repeat_paste
),

products as (
    select * from {{ ref('stg_products') }}
),

reps as (
    select * from {{ ref('stg_reps') }}
)

select
    lines.line_key,
    lines.month,
    lines.sale_date,
    lines.invoice,
    lines.customer,
    lines.product_code,
    products.product_name,
    products.category,
    lines.qty,
    products.unit_price,
    lines.qty * products.unit_price as revenue,
    lines.rep_code,
    reps.rep_name,
    reps.region,
    lines.source,
    lines.source_row
from lines
left join products
    on products.product_code = lines.product_code
    and lines.sale_date >= products.effective_from
    and (products.effective_to is null or lines.sale_date < products.effective_to)
left join reps using (rep_code)
