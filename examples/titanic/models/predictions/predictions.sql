SELECT
       PassengerId,
       layer.predict("layer/titanic/models/survival_model:4.8",ARRAY[Pclass, Sex, Age, SibSp, Parch, Fare])
FROM
     {{ref('passenger_features')}}
