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
