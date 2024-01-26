SELECT
    * EXCEPT(type)
FROM ${project_id}.simulation.params
WHERE params.type = _type