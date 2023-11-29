
package main

import (
	"fmt"
	"log"
	"time"
	"os"
	"flag"	

	g "github.com/gosnmp/gosnmp"
)


var (
	targetPtr    = flag.String("target", "", "target host okv server")
	PortPtr      = flag.Int("Port", 0, "target host snmp port")
	UserNamePtr  = flag.String("UserName", "", "UserName of okv snmp user")
	AuthenticationPassphrasePtr  = flag.String("AuthenticationPassphrase", "", "AuthenticationPassphrase of okv snmp user")
	PrivacyPassphrasePtr  = flag.String("PrivacyPassphrase", "", "PrivacyPassphrase of okv snmp user")
	
	)
	

func main() {

flag.Parse()

if *targetPtr =="" {
    fmt.Printf("Please provide target ip\n")
	fmt.Printf("go run main.go -target=\"\" -Port=161 -UserName=\"\" -AuthenticationPassphrasePtr=\"\" -PrivacyPassphrasePtr=\"\" \n")
	os.Exit(1)
	}
	
if *PortPtr == 0 {
    fmt.Printf("Please provide PortPtr\n")
	os.Exit(1)
	}
	

if *UserNamePtr == "" {
    fmt.Printf("Please provide UserNamePtr\n")
	os.Exit(1)
	}
	
if *AuthenticationPassphrasePtr == "" {
    fmt.Printf("Please provide AuthenticationPassphrasePtr\n")
	os.Exit(1)
	}

if *PrivacyPassphrasePtr == "" {
    fmt.Printf("Please provide PrivacyPassphrasePtr\n")
	os.Exit(1)
	}

	
		


/*
   var values  [] g.SnmpPDU
*/
	// build our own GoSNMP struct, rather than using g.Default
	params := &g.GoSNMP{
		Target:        "10.0.0.190",
		Port:          161,
		Version:       g.Version3,
		SecurityModel: g.UserSecurityModel,
		MsgFlags:      g.AuthPriv,
		Timeout:       time.Duration(30) * time.Second,
		SecurityParameters: &g.UsmSecurityParameters{UserName: *UserNamePtr,
			AuthenticationProtocol:   g.SHA,
			AuthenticationPassphrase: "",
			PrivacyProtocol:          g.AES,
			PrivacyPassphrase:        "",
		},
	}
	
	err := params.Connect()
	if err != nil {
		log.Fatalf("Connect() err: %v", err)
		os.Exit(1)
	}
	defer params.Conn.Close()
	
	// full mib info
	fmt.Printf("An entry containing a process and its statistics.\n")
	err = params.BulkWalk(".1.3.6.1.4.1.2021", printValue)
	fmt.Printf("*------------------------------*\n")
	
	// full prEntry
	fmt.Printf("An entry containing a process and its statistics.\n")
	err = params.BulkWalk(".1.3.6.1.4.1.2021.2.1", printValue)
	fmt.Printf("*------------------------------*\n")
	
	// memory
    fmt.Printf("An entry memory.\n")	
	err = params.BulkWalk(".1.3.6.1.4.1.2021.4", printValue)
	fmt.Printf("*------------------------------*\n")
	
	// An entry containing a disk and its statistics.
    fmt.Printf("An entry containing a disk and its statistics.\n")		
	err = params.BulkWalk(".1.3.6.1.4.1.2021.9.1", printValue)
	fmt.Printf("*------------------------------*\n")
	
	// Load average information.
    fmt.Printf("An entry containing Load average information.\n")	
    err = params.BulkWalk(".1.3.6.1.4.1.2021.10", printValue)
	fmt.Printf("*------------------------------*\n")
	
    // systemmStats
    fmt.Printf("An entry containing systemmStats.\n")	
	err = params.BulkWalk(".1.3.6.1.4.1.2021.11", printValue)
	fmt.Printf("*------------------------------*\n")
	
	// hrSystemUptime Tracks the amount of time that an Oracle Key Vault instance has been running
     fmt.Printf("An entry containing Tracks the amount of time that an Oracle Key Vault instance has been running\n")		
	 err = params.BulkWalk(".1.3.6.1.2.1.25.1.1", printValue)
	fmt.Printf("*------------------------------*\n")
	
	// ifAdminStatus.x Tracks if the Oracle Key Vault network interface (x) are running, not running, or being tested. Values are as follows: 
	 fmt.Printf("Tracks if the Oracle Key Vault network interface (x) are running, not running, or being tested.\n")	
	 err = params.BulkWalk("1.3.6.1.2.1.2.2.1.7", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	// memAvailReal Tracks the available RAM
    fmt.Printf("Tracks the available RAM.\n")		
	err = params.BulkWalk("1.3.6.1.4.1.2021.4.6", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	
     // memTotalReal  	Tracks the total amount of RAM being used
     fmt.Printf("Tracks the total amount of RAM being used\n")	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.4.5", printValue) 
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawIdle For CPU monitoring; tracks the number of ticks (typically 1/100s) spent idle
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent idle\n")	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.53", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawInterrupt For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing hardware interrupts
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing hardware interrupts\n")		 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.56", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawKernel For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing kernel-level code
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing kernel-level code\n")		 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.55", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawNice For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing reduced-priority code
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing reduced-priority code\n")	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.51", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawSystem For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing system-level code
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing system-level code\n")	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.52", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawUser For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing user-level code
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent processing system-level code\n")	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.50", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // ssCpuRawWait For CPU monitoring; tracks the number of ticks (typically 1/100s) spent waiting for input-output (IO)
     fmt.Printf("For CPU monitoring; tracks the number of ticks (typically 1/100s) spent waiting for input-output (IO)\n")	 	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.11.54", printValue)
	fmt.Printf("*------------------------------*\n")
	 
	 // UCD-SNMP-MIB.prTable Tracks the number of processes running under a certain name. Names we monitor are httpd (the http server), kmipd (the kmip daemon), and ora_pmon_dbfwdb (an indicator if the DB is down)
     fmt.Printf("UCD-SNMP-MIB.prTable Tracks the number of processes running under a certain name.\n")	 	 	 
	 err = params.BulkWalk("1.3.6.1.4.1.2021.2", printValue)
	fmt.Printf("*------------------------------*\n")
	 
    // nsExtendOutputFull For monitoring Fast Recovery Area Space utilization; tracks the total limit, space used, and space free. The alert also shows the CA or server certificate expiration date and time (whichever expires sooner) as well as the status of the Oracle Audit Vault agent and the Oracle Audit Vault monitor. For the certificate expiration, the time zone that is shown for the date and time is in UTC. The output may be inconsistent if Oracle Key Vault is in the middle of a certification rotation.
     fmt.Printf("For monitoring Fast Recovery Area Space utilization.\n")	 	 	 	
	 err = params.BulkWalk("1.3.6.1.4.1.8072.1.3.2.3.1.2", printValue)
	fmt.Printf("*------------------------------*\n")

    // sysDescr For including the full name and version identification of the system's hardware.
     fmt.Printf("For including the full name and version identification of the system's hardware..\n")	 	
	 err = params.BulkWalk("1.3.6.1.2.1.1.1", printValue)	
	fmt.Printf("*------------------------------*\n")
	 
	 // sysObjectID Represents the standard identification of the managed system.
     fmt.Printf("Represents the standard identification of the managed system.\n")	 
	 err = params.BulkWalk("1.3.6.1.2.1.1.2", printValue)	
	fmt.Printf("*------------------------------*\n")

	 // sysUpTime Represents the time (in hundredths of a second) since the network management portion of the system was last re-initialized.
     fmt.Printf("Represents the time (in hundredths of a second) since the network management portion of the system was last re-initialized.\n")	 
	 err = params.BulkWalk("1.3.6.1.2.1.1.3", printValue)
	fmt.Printf("*------------------------------*\n")

    // sysName	 Represents an administratively-assigned name. By convention, this is the node's fully-qualified domain name.
     fmt.Printf("Represents an administratively-assigned name. By convention, this is the node's fully-qualified domain name.\n")	 	
	 err = params.BulkWalk("1.3.6.1.2.1.1.5", printValue)	
	fmt.Printf("*------------------------------*\n")
	 
	// sysLocation Represents the physical location of the node, for example, telephone closet, 3rd floor.
     fmt.Printf("Represents the physical location of the node, for example, telephone closet, 3rd floor.\n")	 		
	 err = params.BulkWalk("1.3.6.1.2.1.1.6", printValue)	
	fmt.Printf("*------------------------------*\n")

	// sysServices represents the value that indicates the set of services primarily offered. The value is a sum.
	 fmt.Printf("represents the value that indicates the set of services primarily offered. The value is a sum.\n")	 
	 err = params.BulkWalk("1.3.6.1.2.1.1.7", printValue)	 
	fmt.Printf("*------------------------------*\n")
	 	 	 
	 	 

	if err != nil {
		fmt.Printf("Walk Error: %v\n", err)
		os.Exit(1)
	}
	
	
	
	
}


func printValue(pdu g.SnmpPDU ) error {
	fmt.Printf("Name=> %s = ", pdu.Name)
	

	switch pdu.Type {
	case g.OctetString:
		b := pdu.Value.([]byte)
		fmt.Printf("STRING: %s\n", string(b))
		fmt.Printf("------------\n")
	default:
		fmt.Printf("TYPE %d: %d\n", pdu.Type, g.ToBigInt(pdu.Value))
	}
	return nil
}