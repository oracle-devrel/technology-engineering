# Access Extension Notification Scheduled Task

This asset contains the code and deployment items for a scheduled task designed to notify users of any expiring access and to allow them to extend expiration dates by a set number of days. This is achieved by including unique actionable links in the notification emails.

The scheduled task needs to be used in conjunction with the Extend Access WebService in order to provide the end-to-end access extension functionality.

Developed on and compatible with OIG 11g R2 PS3 and above.

Review Date: 13.11.2023

# When to use this asset?

When there's a need to provide or demonstrate the functionality described above or something similar, which can be adapted from the provided code.

# How to use this asset?

## Pre-requisites and dependencies

The scheduled task uses the `javax.mail` interface in order to send emails, and also parts of the `jaxb-api` interface for generating UUIDs.

As such, the following jar files are required as dependencies and need to be used during the build process, **and also uploaded as third party jars** to the OIM deployment node:
- javax.mail.jar
- jaxb-api-2.3.1.jar

## Building and deployment

Here's a short build and deployment checklist:

1. Use an SQL client, such as SQLDeveloper, to connect to the OIM DB schema (e.g. DEV_OIM) and execute `EXTEND_ACCESS.sql` to create the required data table
2. Import any additional artifacts using deployment manager, such as the `Access_Extension_Template.xml` file
3. Generate a jar file containing the sample code.
4. Upload the jar file to an OIG environment using OIG's command line "Jar Upload" utility. Also remember to upload the dependencies as "3. ThirdParty" jars.
5. Use the Enterprise Manager web interface to upload the scheduled task metadata/definition into the MDS repository.
6. Create a scheduled task in OIG based on the uploaded definition.

Please see the useful link below for detailed build and deployment steps.

## Executing the scheduled task

The following items need to be populated as part of the scheduled job parameters:
- Days Before Expiration: Number of days before the email is sent, e.g. 7
- Extension Days: Extension days to be added to existing end dates, e.g. 60
- Extension Link Text: Text to be included part of the actionable extension links, e.g. Click here to extend access
- REST WS Endpoint URL: Endpoint URL for the access extension REST webservice, e.g. http://127.0.0.1:14000/extend_access/rest
- Email Template Name: Email template name for the email, e.g. Access_Extension_Template
- SMTP Mail Server Hostname: Hostname of the SMTP Mail server, e.g. localhost
- SMTP Mail Server TLS: Enable or disable SMTP TLS, e.g. No
- SMTP Mail Server Port: Port of the SMTP Mail server, e.g. 25

[Consult this section](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omusg/managing-jobs-1.html#GUID-71BB3623-AEE2-4F64-BBD4-D921DCA39D7C) on how to manually start or schedule a job.

# Useful Links

[Oracle Identity Governance developer's guide - Developing scheduled tasks](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omdev/developing-scheduled-tasks.html#GUID-F62EF833-1E70-41FC-9DCC-C1EAB407D151)

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
