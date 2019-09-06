-- "Duh" hypothesis - a restaurant with a checkered past will be more likely to have problems on a current inspection

select
    inspection_type,
    count(*)
from
    inspection_view
where
    inspection_authority = 'Chicago'
group by
    inspection_type
order by
    count(*) desc;
    
-- Based on this and eye-balling raw data, 'Canvass' appears to be a standard inspection

select
    inspection_type,
    count(*)
from
    inspection_view
where
    inspection_authority = 'New York'
group by
    inspection_type
order by
    count(*) desc;
    
/* Based on this and eye-balling raw data, 'Cycle Inspection / Initial Inspection' appears to be standard inspection.
    You can get an A on your original inspection, but you can't get less than an A. They'll just come back to re-inspect.
    The re-inspection is 'Cycle Inspection / Re-inspection', where you can get less than an A. */
    
with rank_scores as (
    select
        inspection_authority,
        license_id,
        inspection_id,
        case
            when inspection_authority = 'New York' and results = 'A' then 0
            when inspection_authority = 'Chicago' and results = 'Pass' then 0
            else 1
        end as bad,
        case when row_number() over(partition by inspection_authority, license_id order by inspection_date desc) = 1 then 1 else 0 end as most_recent
    from
        inspection_view
    where
        results is not null
        and (inspection_authority = 'Chicago' or results in ('A', 'B', 'C'))
        and inspection_type in ('Canvass', 'Cycle Inspection / Initial Inspection', 'Cycle Inspection / Re-inspection')
)
select
    inspection_authority,
    license_id,
    max(case when most_recent = 1 then bad else null end) as bad_now,
    cast(sum(case when most_recent = 0 then bad else null end) as float) / sum(1.0 - most_recent) as pct_bad_previous
from
    rank_scores
group by
    inspection_authority,
    license_id
having
    sum(1 - most_recent) > 0;
