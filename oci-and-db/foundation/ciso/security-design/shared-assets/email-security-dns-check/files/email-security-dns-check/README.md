# Email Security DNS Check

Owner: Jacco Steur

## When to use this asset?

This Python tool checks the email security settings of a domain by verifying its SPF, DKIM, and DMARC records. It extracts relevant information from a domain or an `.eml` file, performs validation, and outputs a summary of findings, including policies and IP addresses associated with SPF records. It can also analyze the alignment of sender information for SPF and DKIM, and resolve IP locations.

### Disclaimer

This asset covers the OCI platform as specified in the *CIS Oracle Cloud Infrastructure Foundations Benchmark*, only. Any workload provisioned in Databases, Compute VMs (running any Operating System), the Container Engine for Kubernetes, or in the VMware Solution is *out of scope* of the *OCI Security Health Check*.

This is not an official Oracle application and it is not supported
by Oracle Support.

### Flags and Usage

- `-f --eml-file`: Path to the `.eml` file to analyze.
- `-s --sender-domain`: Specify the sender domain directly.
- `--selector`: DKIM selector for the sender domain, if known.
- `--mx-selector`: DKIM selector for MX domains.
- `-t --txt`: Dump all TXT records for the domain being checked.
- `--resolve-spf`: Resolve all IP addresses in the SPF record and display their geolocation.

### Install the tool

After cloning the repository and cd into the right directory:

```
security/security-design/shared-assets/email-security-dns-check
```
Run the following command in your terminal to initialize your pyhton environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Usage examples 

To check a domain’s SPF, DKIM, and DMARC settings:

```bash
./email_security_check.sh -s oraclecloud.com
```

For a reverse DNS check and geo location check of the mail server use the command as follows:

```bash
./email_security_check.sh -s oraclecloud.com --resolve-spf
```

If you know what the DKIM selector of the sending email domain is, use the tool as follows:

```bash
./email_security_check.sh -s oraclecloud.com --selector selectoridcs-4 
```

If you have a email available from the sending email domain then this can be used to get the DKIM selector:

```bash
./email_security_check.sh -f email.eml 
```
