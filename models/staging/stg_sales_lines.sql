-- One row per pasted line. An exact repeat of a line within the same month's paste is kept but
-- flagged: invoice lines are unique in the order system, so a repeat can only be a paste error.
with source as (
    select * from {{ source('raw', 'sales_lines') }}
),

keyed as (
    select
        *,
        md5(concat_ws('|', invoice, product_code, qty, sale_date, customer, rep_code)) as line_key
    from source
)

select
    line_key,
    month,
    source,
    source_row,
    sale_date,
    invoice,
    customer,
    product_code,
    qty,
    rep_code,
    row_number() over (partition by month, line_key order by source_row) > 1 as is_repeat_paste
from keyed
