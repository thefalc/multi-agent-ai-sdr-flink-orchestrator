INSERT INTO agent_messages
SELECT 
    CAST(fullDocument._id AS BYTES) AS key,
    CAST(
        ROW(
            fullDocument.company, 
            fullDocument.companyWebsite, 
            fullDocument.email, 
            fullDocument.jobTitle, 
            fullDocument.leadSource, 
            fullDocument.name, 
            fullDocument.projectDescription
        ) 
        AS ROW<
            company_name STRING, 
            company_website STRING, 
            email STRING, 
            job_title STRING, 
            lead_source STRING, 
            name STRING, 
            project_description STRING
        >
    ) AS lead_data,
    CONCAT(
        'Name: ', fullDocument.name, ' | ',
        'Email: ', fullDocument.email, ' | ',
        'Company: ', fullDocument.company, ' | ',
        'Website: ', fullDocument.companyWebsite, ' | ',
        'Lead Source: ', fullDocument.leadSource, ' | ',
        'Job Title: ', fullDocument.jobTitle, ' | ',
        'Project Description: ', fullDocument.projectDescription
    ) AS context
FROM `incoming-leads.stratusdb.leads`
WHERE fullDocument IS NOT NULL AND operationType = 'insert';