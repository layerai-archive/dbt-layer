with source as (

    select * from {{ ref('raw_reviews') }}

),

final as (

    SELECT 
    order_id,
    max(review_score) as review_score
    FROM source
    GROUP BY order_id

)

select * from final