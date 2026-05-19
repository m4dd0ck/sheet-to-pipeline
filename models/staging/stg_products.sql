-- Price list with validity windows: a new row for a code replaces the previous price from its
-- effective date. VLOOKUP ignored this; the pipeline does not.
select
    code as product_code,
    name as product_name,
    category,
    unit_price,
    effective_from,
    lead(effective_from) over (partition by code order by effective_from) as effective_to
from {{ source('raw', 'products') }}
