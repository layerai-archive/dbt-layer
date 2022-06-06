SELECT PassengerId,
       Pclass,
       SibSp,
       Parch,
       Fare,
       Survived,
       case
           when Sex = 'female' then 0
           when Sex = 'male' then 1
           else 0
           end
           as Sex,
       case
           when Age is not null then Age
           when pclass = 1 then 37
           when pclass = 2 then 29
           else 24
           end
           as Age
FROM {{ref('passengers')}}
