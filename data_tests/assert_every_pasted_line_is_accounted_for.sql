-- Each month: lines pasted = real lines in the fact table + repeats flagged as paste errors.
with pasted as (
    select month, count(*) as pasted, count(*) filter (where is_repeat_paste) as repeats
    from {{ ref('stg_sales_lines') }}
    group by month
),

kept as (
    select month, count(*) as kept
    from {{ ref('fct_sales_lines') }}
    group by month
)

select pasted.month, pasted.pasted, pasted.repeats, kept.kept
from pasted
left join kept using (month)
where pasted.pasted != coalesce(kept.kept, 0) + pasted.repeats
