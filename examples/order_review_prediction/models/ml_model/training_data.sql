SELECT orders.order_id,
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
       stg_reviews.review_score
FROM {{ ref('orders') }} LEFT JOIN {{ ref('items') }}
ON orders.order_id = items.order_id
    LEFT JOIN {{ ref ('stg_reviews') }} ON orders.order_id = stg_reviews.order_id