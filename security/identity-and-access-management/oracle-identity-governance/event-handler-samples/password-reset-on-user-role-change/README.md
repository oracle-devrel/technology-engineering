# Password Reset On User Role Change Event Handler

This asset contains the code and deployment items for an event handler that automatically triggers a password reset flow for a user once a user's role attribute changes.

Note that by "user role" we are reffering to the user's role attribute (also known as "employee type") in this context, not to changes in a user's membership to any particular OIG role.

Developed on and compatible with OIG 11g R2 PS3 and above.

Review Date: 28.10.2024

# When to use this asset?

When there's a need to provide or demonstrate the functionality described above or something similar, which can be adapted from the provided code.

Note that password resets for lifecycle events involving other attribute value changes, such as for example a user's parent Organization, can be easily retrofitted based on the provided sample.

# How to use this asset?

## Building and deployment

Here's a short build and deployment checklist:

1. Generate a jar file containing the sample code.
2. Copy the jar file under the `lib` directory of the provided `plugin` folder structure and create a zip file with the following root structure:
- lib
- META-INF
- plugin.xml
3. Register the plugin zip file to an OIG environment using OIG's plugin registration utility script.

Please see the useful link below for detailed build and deployment steps.

## How do I execute the event handler?

Once registered the code will be run automatically when user lifecycle events occur in the system. Note that password resets will be triggered only when the target attribute value changes (in this sample, the user's role), during modify events.

# Useful Links

[Oracle Identity Governance developer's guide - Developing plugins](https://docs.oracle.com/en/middleware/idm/identity-governance/12.2.1.4/omdev/developing-plug-ins.html#GUID-7F4EE3EA-076C-45DB-B13D-2905AB5AF6CB)

# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
