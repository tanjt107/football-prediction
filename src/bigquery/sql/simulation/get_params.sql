SELECT
    topic,
    league,
    rule,
    team_no_ko,
    params.groups,
    ko_matchups,
    corrections
FROM `${project_id}.simulation.params` params
WHERE params.type = _type