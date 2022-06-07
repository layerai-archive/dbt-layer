with orders as (

    select * from {{ ref('orders') }}

),

items as (

    select * from {{ ref('items') }}

),

reviews as (

    select * from {{ ref('stg_reviews') }}

),

final as (

    SELECT 
    orders.order_id,
    orders.days_between_purchase_and_delivery,
    orders.order_approved_late,
    orders.actual_delivery_vs_expectation_bucket,
    items.total_order_price,
    items.total_order_freight,
    items.is_multiItems_order,
    CASE
        WHEN date_diff(order_delivered_carrier_date, max_shipping_limit_date, day) > 0 THEN 1
        ELSE 0
    END as seller_shipped_late,
    reviews.review_score
    FROM
    orders JOIN items ON orders.order_id = items.order_id
    JOIN reviews ON orders.order_id = reviews.order_id

)

select * from final