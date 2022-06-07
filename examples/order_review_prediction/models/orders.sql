with orders as (

    select * from {{ ref('stg_orders') }}

),

final as (

    SELECT order_id, order_delivered_carrier_date,
    date_diff(order_delivered_customer_date, order_purchase_timestamp, day) as days_between_purchase_and_delivery,

    CASE
        WHEN date_diff(order_approved_at, order_purchase_timestamp, day) = 0 THEN 0
        ELSE 1
    END as order_approved_late,

    CASE
        WHEN date_diff(order_estimated_delivery_date, order_delivered_customer_date, day) <=0 THEN -1
        WHEN date_diff(order_estimated_delivery_date, order_delivered_customer_date, day) <=7 THEN 1
        WHEN date_diff(order_estimated_delivery_date, order_delivered_customer_date, day) <=14 THEN 2
        ELSE 3
    END as actual_delivery_vs_expectation_bucket

    FROM orders

)

select * from final