# STEP2. ORM OBS ADD-ON Deployment Steps <!-- omit from toc -->


Go to the orchestrator [github page](https://github.com/oci-landing-zones/terraform-oci-modules-orchestrator).

At the beginning of the README page, select 'Deploy to Oracle Cloud'. When you click the provided magic button, a new ORM stack will be created. Follow these steps:

1. Accept terms, wait for the configuration to load.
2. Set the working directory to “rms-facade”.
3. Set the stack name you prefer.
4. Set the terraform version to 1.5.x. Click Next.
5. Create you own bucket and upload the JSON files provided in this asset:

* [oci_open_lz_addon_mon_iam_atp.auto.tfvars.json](oci_open_lz_addon_mon_iam_atp.auto.tfvars.json)
* [oci_open_lz_addon_mon_network_atp.auto.tfvars.json](oci_open_lz_addon_mon_network_atp.auto.tfvars.json)

6. Add the files generated as output in the ONE-OE deployment as dependencies.
7. Un-check run apply. Click Create.
8. First, execute a plan job to review all the resources that Terraform will create. Once verified, proceed to run the apply job to initiate the deployment.


# License <!-- omit from toc -->

Copyright (c) 2025 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](/LICENSE) for more details.
