# Access Termination Notification Scheduled Task

This asset contains the code and deployment items for a scheduled task designed to notify users and their managers of any expiring access. It uses standard OIG APIs to handle email composition and dispatch (tcEmailNotificationUtil).

In case access extensions or a more complex handling of email contents are also required, please refer to the [Access Extension Notification Scheduled Task](https://github.com/oracle-devrel/technology-engineering/tree/main/security/identity-and-access-management/oracle-identity-governance/scheduled-task-samples/access-extension-notification).

Developed on and compatible with OIG 11g R2 PS3 and above.

## When to use this asset?

When there's a need to provide or demonstrate the functionality described above or something similar, which can be adapted from the provided code.

## How to use this asset?

### Building and deployment

Here's a short build and deployment checklist:

1. Import any additional artifacts using deployment manager, such as the `Access_Termination_Template.xml` file
2. Generate a jar file containing the sample code.
3. Upload the jar file to an OIG environment using OIG's command line "Jar Upload" utility. Also remember to upload the dependencies as "3. ThirdParty" jars.
4. Use the Enterprise Manager web interface to upload the scheduled task metadata/definition into the MDS repository.
5. Create a scheduled task in OIG based on the uploaded definition.

Please see the useful link below for detailed build and deployment steps.

### Executing the scheduled task

The following items need to be populated as part of the scheduled job parameters:
- Days Before Expiration: Number of days before the email is sent, e.g. 7
- Email Template Name: Email template name for the email, e.g. Access_Termination_Template

[Consult this section](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omusg/managing-jobs-1.html#GUID-71BB3623-AEE2-4F64-BBD4-D921DCA39D7C) on how to manually start or schedule a job.

## Useful Links

[Oracle Identity Governance developer's guide - Developing scheduled tasks](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omdev/developing-scheduled-tasks.html#GUID-F62EF833-1E70-41FC-9DCC-C1EAB407D151)

# License

Copyright (c) 2023 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
