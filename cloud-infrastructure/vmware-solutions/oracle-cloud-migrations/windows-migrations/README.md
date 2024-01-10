# Windows Migrations

## Operating system preparations

In order to successfully migrate source environments based on the Microsoft Windows operating system you need to prepare the source environment.
Microsoft Windows instances run on OCI Compute shapes using Paravirtualized drivers (VirtIO) for the Storage and Network interfaces. The drivers for these devices are by default not present and need to be installed before the migration to OCI in the source environment. If this is not done, the migrate instance will boot in OCI and fail with an “inaccessible boot device error” (Bluescreen error)
and/or no networking interfaces presence.

### Installing the Oracle Paravirtualized drivers
You can download the Oracle VirtIO drivers for Windows for oracle's e-delivery site:
https://docs.oracle.com/en/operating-systems/oracle-linux/kvm-virtio/

**IMPORTANT**: Use the new VirtIO 2.0.1 or 2.1.0 Drivers, as the previous version (2.0) will result
in an inaccessible boot device error.

### Replication issues with source instances running Microsoft Windows
On every replication cycle, the OCM service will try to create a snapshot on the source
virtual machine. The VMware environment will try to make the snapshot using filesystem
and application aware quiescing. 

There are sometimes issues where the VMware platform is not able to quiesce the filesystem properly, 
resulting in an replication error. The error could be something like: failed to open Virtual Disk. Open virtual Disk failed. 
The error code is 1. (Error code 1 means an unkown VMware error)

You can disable the application level quiescing, but be aware that the final replication cycle needs to
be then run with a powered off source VM, else there could be a possibility of corrupted data.

### How to disable application level quiescing during snapshots of virtual machines
https://kb.vmware.com/s/article/2146204

Disable VSS application quiescing using the VMware Tools configuration:
- Open the file C:\ProgramData\VMware\VMware Tools\Tools.conf file using a text editor.
- If the file does not exist at the location mentioned above, create it.
- Add these entries to the file:
```
[vmbackup]
vss.disableAppQuiescing = true
```
- Save and close the file.
- Restart the VMware Tools Service.
- Click Start > Run, type services.msc, and click OK.
- Right-click the VMware Tools Service and click Restart.
