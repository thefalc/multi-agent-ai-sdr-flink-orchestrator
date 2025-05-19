INSERT INTO agent_predictions
SELECT 
    CAST(NULL AS BYTES) AS key,  -- Assign NULL since it's not provided in the source
    lead_data,
    context,
    prediction.response as agent_name
FROM (
    SELECT 
        context, 
        lead_data
    FROM agent_messages
) AS subquery
CROSS JOIN 
    LATERAL TABLE (
        ml_predict('agent_router', context)
    ) AS prediction;
