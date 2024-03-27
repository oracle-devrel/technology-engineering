# Run plan

This utility has been made to run benchmarks against Autonomous Databases. It could be easily adapted to run against any Oracle Database.

Create a JSON file describing your test plan, and run it against ADB.

A test plan is made of runs and steps.
Each test plan has 1-N runs.
Each run has 1..M steps.

When you run your test plan, each run is executed sequentially. In each run, the steps are run sequentially or in parallel.
For example, consider the following test plan

{
    "IDPLAN": "B2-UNIT",
    "PlanDesc": "B2 unitary con 4-8 ocpu",
    "version": 1.0,
    "releaseDate": "2020-10-13T00:00:00.000Z",
    "runs": 
    [
        {
          "name": "Run1",
          "Label": "RUN1",
      "ocpu": "4",
      "storageTB": "5",
      "parallel": "Y",
          "steps": 
      [
        {
          "name": "ScaleUpAdw",
          "type": "SCALE",
          "command": "/home/opc/PPL/scale-ADW.sh"
        },
        {
          "name": "CollectAWR",
          "type": "AWR",
          "command": "/home/opc/PPL/create-AWR-snapshot.sh"
        },
        {
          "name": "step1",
          "type": "SH",
          "command": "/home/opc/PPL/run.B2.DM_CONFIG0.sh"
        },
        {
          "name": "Waiting",
          "type": "WAIT",
          "command": "/home/opc/PPL/check-for-completion.sh"
        },
        {
          "name": "CollectAWR",
          "type": "AWR",
          "command": "/home/opc/PPL/create-AWR-snapshot.sh"
        }
      ]
        },
        {
          "name": "Run2",
          "Label": "RUN2",
      "ocpu": "8",
      "storageTB": "5",
      "parallel": "Y",
          "steps": 
      [
        {
          "name": "ScaleUpAdw",
          "type": "SCALE",
          "command": "/home/opc/PPL/scale-ADW.sh"
        },
        {
          "name": "CollectAWR",
          "type": "AWR",
          "command": "/home/opc/PPL/create-AWR-snapshot.sh"
        },
        {
          "name": "step1",
          "type": "SH",
          "command": "/home/opc/PPL/run.B2.DM_CONFIG0.sh"
        },
        {
          "name": "Waiting",
          "type": "WAIT",
          "command": "/home/opc/PPL/check-for-completion.sh"
        },
        {
          "name": "CollectAWR",
          "type": "AWR",
          "command": "/home/opc/PPL/create-AWR-snapshot.sh"
        }
      ]
        },
    ]
  }

This plan is named B2-UNIT and has 2 runs:
  Run1 will do the following:
    Scale ADB to 4 OCPU
    Create an AWR snapshot
    Execute "/home/opc/PPL/run.B2.DM_CONFIG0.sh"
    Wait until completion
    Create an AWR snapshot and generate the AWR report
    
  Run2 will do the following:
    Scale ADB to 8 OCPU
    Create an AWR snapshot
    Execute "/home/opc/PPL/run.B2.DM_CONFIG0.sh"
    Wait until completion
    Create an AWR snapshot and generate the AWR report

At the end of all the runs, a notification will be sent to a topic in OCI. If this topic is associated to anemail address, you'll receive somnething like this:

"As of 20/12/2022-10h19mn02s, plan with ID B1-IB.Consulta88.20221220101727 completed with the following results:
 
Now starting plan B1-IB.Consulta88 at 20221220101727
Plan description: Consulta88 4 ocpu
 
/home/opc/PPL/log/B1-IB.Consulta88.20221220101727.RUN1.step1.4.10.ADMIN.log:Elapsed: 00:01:08.30 ("Consulta88")
Now scaling down to 4 ocpu.
No need to scale ...
Plan B1-IB.Consulta88 completed.
 
Please review file /home/opc/PPL/log/B1-IB.Consulta88.20221220101727.log for detailed information.
 
Kind regards,"

So this tool enables to automate long test plans and run them unattented.


# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.

See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
