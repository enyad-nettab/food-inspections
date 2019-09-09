create table chicago_inspections (
    inspection_id bigint primary key,
    dba_name text,
    aka_name text,
    license_number bigint,
    facility_type text,
    risk text,
    address text,
    city text,
    state text,
    zip text,
    inspection_date date,
    inspection_type text,
    results text,
    latitude float,
    longitude float
);

create table chicago_violations (
    inspection_id bigint references chicago_inspections,
    violation_code int,
    violation_description text,
    violation_comments text
);

create table nyc_inspections (
    inspection_id bigint primary key,
    camis text,
    dba_name text,
    borough text,
    building text,
    street text,
    zip text,
    phone_number text,
    cuisine_type text,
    inspection_date date,
    action text,
    score int,
    grade text,
    grade_date date,
    record_date date,
    inspection_type text,
    latitude float,
    longitude float
);

create table nyc_violations (
    inspection_id bigint references nyc_inspections,
    violation_code text,
    violation_description text,
    critical_flag text
);

drop view if exists
    inspection_view;

create view
    inspection_view
as select
    'Chicago' as inspection_authority,
    cast(license_number as text) as license_id,
    inspection_id,
    dba_name,
    aka_name,
    address,
    city,
    state,
    zip,
    inspection_date,
    inspection_type,
    null as score,
    results,
    latitude,
    longitude
from
    chicago_inspections
where
    facility_type = 'Restaurant'
    
union all

select
    'New York' as inspection_authority,
    camis,
    inspection_id,
    dba_name,
    null,
    street,
    'New York',
    'New York',
    zip,
    inspection_date,
    inspection_type,
    score,
    case
        when grade is not null then grade
        when inspection_type != 'Cycle Inspection / Initial Inspection' then grade
        when score <= 13 then 'A'
        when score <= 27 then 'B'
        else 'C'
    end as results,
    latitude,
    longitude
from
    nyc_inspections;
    
drop view if exists
    violation_view;

create view
    violation_view
as select
    'Chicago' as inspection_authority,
    inspection_id,
    cast(violation_code as text) as violation_code,
    violation_description
from
    chicago_violations
where
    inspection_id in (
        select
            inspection_id
        from
            chicago_inspections
        where
            facility_type = 'Restaurant'
    )
    
union all
    
select
    'New York' as inspection_authority,
    inspection_id,
    violation_code,
    violation_description
from
    nyc_violations;
