SELECT order_id,
       layer.automl('regressor',ARRAY[days_between_purchase_and_delivery, order_approved_late,
                    actual_delivery_vs_expectation_bucket, total_order_price, total_order_freight, is_multiItems_order,
                    seller_shipped_late],review_score)
FROM {{ ref('training_data') }}