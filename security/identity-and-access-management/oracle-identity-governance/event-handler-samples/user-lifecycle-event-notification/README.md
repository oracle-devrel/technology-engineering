# User Lifecycle Event Notification Event Handler

This asset contains the code and deployment items for an event handler that sends notifications during user lifecycle events. The targeted event is configured during deployment. It uses standard OIG APIs to handle email composition and dispatch (tcEmailNotificationUtil).

Developed on and compatible with OIG 11g R2 PS3 and above.

Review Date: 22.02.2024

# When to use this asset?

When there's a need to provide or demonstrate the functionality described above or something similar, which can be adapted from the provided code.

Note that OIG already provides native notification capabilities for most (but not all) user lifecycle events. Only use this approach if the out of the box functionality proves insufficient.

# How to use this asset?

## Building and deployment

Here's a short build and deployment checklist:

1. Import any additional artifacts using deployment manager, such as the `User_Lifecycle_Event_Notification_Template_And_Lookup.xml` file.
2. Generate a jar file containing the sample code.
3. Copy the jar file under the `lib` directory of the provided `plugin` folder structure and create a zip file with the following root structure:
- lib
- META-INF
- plugin.xml
4. Configure the type of user lifecycle event you want to send notifications for, by editing the value of the `operation` parameter inside `META-INF/EventHandlers.xml`. The provided sample file is configured to target user disable lifecycle events.
5. Log into the OIM administration console and adjust the event handler functionality as needed by editing the values stored in the `Lookup.Sample.LifecycleNotification` Lookup, which was imported during step 1.
6. Use the OIM administration console to also adjust the `User Lifecycle Event Notification` notification template content to your liking, if needed.
7. Register the plugin zip file to an OIG environment using OIG's plugin registration utility script.

Please see the useful link below for detailed build and deployment steps.

## How do I execute the event handler?

Once registered the code will be run automatically when the configured lifecycle events occur in the system.

# Useful Links

[Oracle Identity Governance developer's guide - Developing plugins](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omdev/developing-plug-ins.html#GUID-7F4EE3EA-076C-45DB-B13D-2905AB5AF6CB)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
