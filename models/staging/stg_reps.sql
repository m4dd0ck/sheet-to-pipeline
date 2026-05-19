select rep_code, name as rep_name, region
from {{ source('raw', 'reps') }}
