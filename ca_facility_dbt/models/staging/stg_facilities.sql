-- stg_facilities.sql
-- Cleans and standardizes the raw facility locations data

with source as (
    select * from public.raw_facility_locations
),

cleaned as (
    select
        facid                                    as facility_id,
        facname                                  as facility_name,
        fac_type_code                            as facility_type,
        trim(lower(county_name))                 as county,
        zip                                      as zip_code,
        city                                     as city,
        address                                  as address,
        county_code                              as county_code,
        district_name                            as district_name,
        licensed_certified                       as license_status,
        capacity                                 as capacity,
        npi                                      as npi,
        contact_phone_number                     as phone,
        loaded_at

    from source
    where facid is not null
)

select * from cleaned