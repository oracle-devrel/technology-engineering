# Region

region              = "eu-frankfurt-1"
#region              = "eu-amsterdam-1"
compartment_name    = "Ralf_Lange"       # must exist
bucket_name         = "InstanceScripts"  # will be created. Fails if created outside of Terraform
vcn_name            = "OSManagementHub"  # will be created
public_subnet_name  = "public"           # will be created
command_server_name = "frankfurt"

instances = {
    "crashandburn" = { os =  "OracleLinux10", arch= "arm", osmh=false, phase="production"}
    "ol8arm-pilot"   = { os="OracleLinux8", arch="arm", osmh=true, phase="pilot"}
    "ol9arm-pilot"   = { os="OracleLinux9", arch="arm", osmh=true, phase="pilot"}
    "ol10arm-pilot"  = { os="OracleLinux10",arch="arm", osmh=true, phase="pilot"}
    "ol8arm-prod"    = { os="OracleLinux8", arch="arm", osmh=true, phase="production"}
    "ol9arm-prod"    = { os="OracleLinux9", arch="arm", osmh=true, phase="production"}
    "ol10arm-prod"   = { os="OracleLinux10",arch="arm", osmh=true, phase="production"}
##osmh    "ol8amd-pilot"   = { os="OracleLinux8", arch="amd", osmh=true, phase="pilot"}
##osmh    "ol9amd-pilot"   = { os="OracleLinux9", arch="amd", osmh=true, phase="pilot"}
##osmh    "ol10amd-pilot"  = { os="OracleLinux10",arch="amd", osmh=true, phase="pilot"}
##osmh    "ol8amd-prod"    = { os="OracleLinux8", arch="amd", osmh=true, phase="production"}
##osmh    "ol9amd-prod"    = { os="OracleLinux9", arch="amd", osmh=true, phase="production"}
##osmh    "ol10amd-prod"   = { os="OracleLinux10",arch="amd", osmh=true, phase="production"}
##osmh    "ol8x86-pilot"   = { os="OracleLinux8", arch="x86", osmh=true, phase="pilot"}
##osmh    "ol9x86-pilot"   = { os="OracleLinux9", arch="x86", osmh=true, phase="pilot"}
##osmh    "ol10x86-pilot"  = { os="OracleLinux10",arch="x86", osmh=true, phase="pilot"}
##osmh    "ol8x86-prod"    = { os="OracleLinux8", arch="x86", osmh=true, phase="production"}
##osmh    "ol9x86-prod"    = { os="OracleLinux9", arch="x86", osmh=true, phase="production"}
##osmh    "ol10x86-prod"   = { os="OracleLinux10",arch="x86", osmh=true, phase="production"}
###    "ol9x86-01" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-02" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-03" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-04" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-05" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-06" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-07" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-08" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-09" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
###    "ol9x86-10" = { os="OracleLinux9",arch="x86", osmh=false, phase="pilot"}
##    "ol9arm" = { os="OracleLinux9",arch="arm", osmh=true, phase="pilot"}
##    "ol9amd" = { os="OracleLinux9",arch="amd", osmh=true, phase="pilot"}
##    "ol9x86" = { os="OracleLinux9",arch="x86", osmh=true, phase="pilot"}
##    "ol8arm" = { os="OracleLinux8",arch="arm", osmh=true, phase="pilot"}
##    "ol8amd" = { os="OracleLinux8",arch="amd", osmh=true, phase="pilot"}
##    "ol8x86" = { os="OracleLinux8",arch="x86", osmh=true, phase="pilot"}
}
