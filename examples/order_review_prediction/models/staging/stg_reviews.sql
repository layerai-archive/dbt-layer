SELECT order_id,
       max(review_score) as review_score
FROM {{ ref('raw_reviews') }}
GROUP BY order_id