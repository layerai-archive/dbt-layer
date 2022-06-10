SELECT *
FROM {{ ref('raw_orders') }}
WHERE order_id IS NOT NULL
  and customer_id IS NOT NULL
  and order_status IS NOT NULL
  and order_purchase_timestamp IS NOT NULL
  and order_approved_at IS NOT NULL
  and order_delivered_carrier_date IS NOT NULL
  and order_delivered_customer_date IS NOT NULL
  and order_estimated_delivery_date IS NOT NULL
  and order_status = 'delivered'
  and order_purchase_timestamp < order_approved_at
  and order_approved_at < order_delivered_carrier_date
  and order_delivered_carrier_date < order_delivered_customer_date

