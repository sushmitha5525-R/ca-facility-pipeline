-- mart_facility_access.sql
-- Counts facilities by county and type, calculates compliance rate

with facilities as (
    select * from {{ ref('stg_facilities') }}
),

county_summary as (
    select
        county,
        facility_type,
        count(*)                                              as total_facilities,
        count(case when license_status = 'LICENSED' 
              then 1 end)                                     as licensed_count,
        round(
            count(case when license_status = 'LICENSED' 
                  then 1 end) * 100.0 / count(*), 2
        )                                                     as compliance_rate_pct
    from facilities
    where county is not null
    group by county, facility_type
)

select * from county_summary
order by county, total_facilities desc