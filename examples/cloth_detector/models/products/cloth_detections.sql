SELECT
       id,
       layer.predict("layer/clothing/models/objectdetection", ARRAY[image])
FROM
     {{ ref("products") }}
