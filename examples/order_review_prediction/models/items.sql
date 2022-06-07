with items as (

    select * from {{ ref('stg_items') }}

),

final as (

    SELECT
    order_id, 
    sum(price) as total_order_price,
    sum(freight_value) as total_order_freight,
    max(shipping_limit_date) as max_shipping_limit_date,
    CASE
        WHEN count(price) > 1 THEN 1
        ELSE 0
    END as is_multiItems_order

    FROM items
    GROUP BY order_id

)

select * from final