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

