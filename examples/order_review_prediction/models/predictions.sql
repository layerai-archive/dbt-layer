SELECT
       order_id,
       review_score,
       layer.predict("layer/ecommerce_olist_order_review_score_prediction/models/review_score_predictor_model", ARRAY[days_between_purchase_and_delivery, order_approved_late, actual_delivery_vs_expectation_bucket, total_order_price, total_order_freight, is_multiItems_order, seller_shipped_late]) as review_prediction
FROM
     {{ref('training_data')}}