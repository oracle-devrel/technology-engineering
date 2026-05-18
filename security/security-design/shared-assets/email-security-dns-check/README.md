## Purpose of the email security DNS check

Oracle requires that certain records are added to a customers DNS to allow Oracle's email delivery service to send emails on the customers behalf. This prevents the customers emails from being flagged as spoofed. 

### Disclaimer

This asset uses a rest API to make it possible to show the geo-locations of the email servers in the SPF DNS records. This is done by making an HTTP request to the ip-api.com service.

The requests to ip-api.com are done in a anonymous way. The privacy policy at ip-api.com mentions that they do not track or analyse access or use in any manner. No cookies are placed during use.

To protect and rate-limit the API the network IP address of the client is stored in memory (RAM) for up to 1 minute.
Any other information provided is discarded after the request is answered. Requests are not logged. 
The usage of the ip-api.com rest API is free for non-commercial use.

For more detail on the privacy policy, please visit [https://ip-api.com/privacy](https://ip-api.com/privacy).

This is not an official Oracle application and it is not supported by Oracle Support.

## Understanding SPF, DKIM, and DMARC

First a high level overview of the different protocols.

### SPF (Sender Policy Framework)

SPF  is an email authentication protocol that allows a domain to specify which mail servers are authorized to send emails on its behalf. It works by publishing DNS records that define the authorized IP addresses. This helps prevent email spoofing.

### DKIM (DomainKeys Identified Mail)

DKIM is an email authentication method that adds a digital signature to email headers. This signature is linked to the domain and verified by the receiving server using a DKIM public key published in the sender’s DNS records.

### DMARC (Domain-based Message Authentication, Reporting, and Conformance)

DMARC builds on SPF and DKIM by specifying how the recipient should handle emails that fail SPF or DKIM checks. It provides reporting capabilities to monitor the domain’s email authentication.

### Email Authentication Flow with SPF, DKIM, and DMARC

Following diagram shows the flow through the different protocols:

```
[ Sender's Email System ]
    |
    |-- Email sent with DKIM Signature
    |
[ Internet ]
    |
    v
[ Recipient's Email Server ]
    |
    |-- Step 1: SPF Check
    |     - Is the sending IP authorized?
    |
    |-- Step 2: DKIM Verification
    |     - Is the signature valid?
    |
    |-- Step 3: DMARC Policy Lookup
    |     - What is the sender's DMARC policy?
    |     - Do SPF/DKIM results align with the 'From' domain?
    |
    |-- Step 4: Apply DMARC Policy
    |     - Deliver, Quarantine, or Reject
    v
[ Recipient's Inbox or Spam Folder ]
```

The following links provide documentation for diferent Oracle products referencing these settings for SPF, DKIM and DMARC. 

### Resources

- [SPF settings in Email Delivery on OCI](https://docs.oracle.com/en-us/iaas/Content/Email/Tasks/configurespf.htm)
- [DKIM settings in Email Delivery on OCI](https://docs.oracle.com/en-us/iaas/Content/Email/Tasks/configure-dkim-using-the-console.htm)
- [Setting up an Email Domain with DKIM](https://docs.oracle.com/en-us/iaas/Content/Email/Tasks/managing_dkim-setup_email_domain_with_dkim.htm)
- [Configuring Email Authentication Settings for SPF and DKIM on OCI IAM](https://docs.oracle.com/en-us/iaas/Content/Identity/notifications/configure-email-auth-spf-dkim.htm)
- [Configure Email Security on Fusion Cloud Applications](https://docs.oracle.com/en/cloud/saas/applications-common/24d/facia/configure-email-security.html)
