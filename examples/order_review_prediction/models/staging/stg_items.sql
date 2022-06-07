with source as (

    select * from {{ ref('raw_items') }}

),

renamed as (

    SELECT order_id, shipping_limit_date, price, freight_value
    FROM source
    WHERE 
    order_id IS NOT NULL and
    shipping_limit_date IS NOT NULL and
    price IS NOT NULL and
    freight_value IS NOT NULL and
    price >= 0 and
    freight_value >= 0

)

select * from renamed