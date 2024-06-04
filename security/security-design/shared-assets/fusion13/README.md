# SSO configuration for Oracle Fusion ERP, Fusion HCM, or Fusion SCM  

Author: Inge Os

The aim is to show how you may configure SSO between an Oracle Fusion Application instance and an instance of  Oracle OCI IAM Domain.  
In the text below the scope of Oracle Fusion Applications is ERP, HCM and SCM.  

In the context of identity integration two interlinked but distinct concepts arise:  
- Federation, runtime SSO, between a service Provider SP and an Identity provider IdP.  
- Provisioning or user synchronization. A process of create, update activate, deactivate, or delete users in one user store, whit a second user store as master.

In the scope of this example, the following terms are used:
- Oracle OCI IAM, abbreviated form of a  Oracle OCI IAM Domain instance
- IDCS, abbreviation for the older IAM solution, Oracle Identity Cloud Service
- Oracle Fusion Apps, Any of Oracle Fusion ERP, Oracle Fusion SCM or Oracle Fusion HCM

Below it will be demonstrated and shown how to configure Single Sign On, SSO, from Oracle Fusion Apps to IAM Domain, with the SAML 2.0 standard as integration protocol. 
  
From a security point of view, there is several security advantages of linking Oracle Fusion Apps to Oracle OCI IAM:
- Oracle OCI IAM offers dynamic risk assessment of the user, with step up authentication and account lockout, if the risk of the user is calculated to exceed a given level. Risk factors includes number of failed logons, rapid change in IP addresses, just to mention a few.
- Oracle OCI IAM offers multi factor authentication. From comments on the internet, it seems that one major reasons for accounts breach, is bad password hygiene, like reuse of password and stolen password. By enabling multi factor authentication, the risk of account theft or account hijacking is severely reduced.
- Simplified integration with 3. Party IdPs like Entra-ID
- One common user store and authentication mechanism across several Oracle Fusion Apps like oracle Fusion EPM, Oracle Fusion ERP and Oracle Fusion extensions with Visual Builder
- Easy integration with Oracle OCI IaaS/PaaS Cloud Services.
OCI IAM offers different Domain types, and the two most significant in the context of Oracle Fusion Apps are Free and Oracle Apps Premium.  
For the pure SSO scenario, Oracle IAM Domain free type might be sufficient, but for dynamic risk evaluation, provisioning, Just-in-time SSO provisioning, Oracle IAM Domain Apps Premium is recommended. Please refer to the Documentation section at the end for details.  

The workflow outlined here, creates the SAML federation only, provisioning is not in the scope. In case you want to add a provision workflow as well,
you may select the <ins>Oracle Fusion Applications Release 13</ins> from the application catalog. In this example we will use a standard SAML application within Oracle OCI IAM.  


The steps are basically the same for Oracle IDCS and Oracle OCI IAM. There are on subtle difference, in IDCS, you may choose the App Catalog, </ins>Oracle Fusion Applications Release 13</ins>, as it does not mandate configuration of provisioning. The Oracle OCI IAM version of *<ins>Oracle Fusion Applications Release 13</ins> app do mandate that provisioning is configured in addition.

A typical authentication flow for Oracle Fusion Apps is like:
- The user connects the browser to her Oracle Fusion Apps welcome page
- Oracle Fusion Apps, if any SSO token is available it is verified
- If the verification fails, or the token does not exist, the browser is redirected to the IdP, Oracle OCI IAM
- Oracle OCI IAM request the user credentials, and if authentication succeeds, and the user is assigned to the correct application within Oracle OCI IAM, a valid SAML assertion is issued, and the browser is redirected back to Oracle Oracle Fusion Apps
- Oracle Fusion Apps verifies the SAML assertion, and if it succeeds, issues a valid Oracle Fusion Apps token
- A valid session is created for Oracle Fusion Apps  
  
![Overview over authentication](images/fusion13_oiciam_federation_00001.jpg)

Configuration of SSO for Oracle Fusion Apps

The configuration follows a few steps, as outlined below:

1) Oracle OCI IAM: Add a SAML application to the Oracle OCI IAM, added from the app Catalogue in Oracle OCI IAM
2) Download IdP Metadata, for later upload to the Fusion Apps
3) Fusion: Define SAML IdP in the Oracle Fusion Apps security console
4) Fusion: Upload earlier downloaded Oracle OCI IAM metadata
5) Fusion: Download Oracle Fusion Apps metadata to Oracle OCI IAM
6) Oracle OCI IAM Domain: Extract the proper certificate from the Oracle Fusion Apps metadata XML file
7) Oracle OCI IAM Domain: Extract attributes from Oracle Fusion Apps Metadata
8) Oracle OCI IAM Domain: Update Oracle OCI IAM with the extracted values
9) Oracle OCI IAM: Activate the SAML Application and assign users to it
10) Fusion: Test SAML federation with Oracle OCI IAM
11) Fusion: Enable Federation
12) Fusion: Post Configuration of Oracle Fusion Apps


The diagrams below visualize the process 

![Diagram 1](images/fusion13_oiciam_federation_00002.jpg)  
![Diagram 2](images/fusion13_oiciam_federation_00003.jpg)  
![Diagram 3](images/fusion13_oiciam_federation_00004.jpg)  

# Full outline

The process is a little bit back and forth between Oracle OCI IAM console and Oracle Fusion Apps Security Console, for a smooth experience open two incognito windows,
one for each. The test stage, step 10 requires a clean sheet.  

## 1) Oracle OCI IAM Domain: Add a SAML application to the Oracle OCI IAM Domain, added from the app Catalogue in Oracle OCI IAM Domain

First navigate to the applicable Oracle OCI IAM Domain, and select <ins>Integrated Applications</ins>  
  
![Integrated Applications menu](images/fusion13_oiciam_federation_00006.jpg)  
  
Select <ins>SAML application</ins> tab and launch the workflow

![Select SAML](images/fusion13_oiciam_federation_00007.jpg)  
  
![Click Launch workflow](images/fusion13_oiciam_federation_00008.jpg)  

You have now entered the main screens for IDP configuration, do not leave the screens before it is completed.
Without valid values for mandatory fields like <ins>Entity ID</ins>, the configuration will not be saved.  
Enter a descriptive name and some meaningful descriptions

![Adding name and description](images/fusion13_oiciam_federation_00009.jpg)  

## 2) Download IdP Metadata, for later upload to the Oracle Fusion Apps

The next step is to download the metadata to a XML file, for later upload to Oracle Fusion Apps. Do not click finish. You may, in the continuation, jump between this screen and the previous screen.  

![fusion13_oiciam_federation_00011.jpg](images/fusion13_oiciam_federation_00011.jpg)  

## 3) Fusion: Define SAML IdP in the Oracle Fusion Apps security console

Sign-on to Fusion with an account with access to the <ins>Security Console</ins>  

![fusion13_oiciam_federation_00013.jpg](images/fusion13_oiciam_federation_00013.jpg)  

![fusion13_oiciam_federation_00014.jpg](images/fusion13_oiciam_federation_00014.jpg)  
  
  Navigate to tools, <ins>Security Console</ins>  

![security console](images/fusion13_oiciam_federation_00015.jpg)  

Select <ins>Single Sign-on</ins>

![fusion13_oiciam_federation_00016.jpg](images/fusion13_oiciam_federation_00016.jpg)  
  
and <ins>Create Identity provider</ins>  

![fusion13_oiciam_federation_00017.jpg](images/fusion13_oiciam_federation_00017.jpg)  

## 4) Fusion: Upload earlier downloaded Oracle OCI IAM Domain metadata

Select <ins>Edit</ins> to start configuration

![images/fusion13_oiciam_federation_00019.jpg](images/fusion13_oiciam_federation_00019.jpg)  

Select upload and upload the XML file downloaded earlier. Oracle Fusion Apps will sanity check the XML file, and when accepted the fie name will be shown in the screen.  

![Click upload](images/fusion13_oiciam_federation_00020.jpg)  
  
![Select file from filesystem](images/fusion13_oiciam_federation_00021.jpg)  
  
![fusion13_oiciam_federation_00022.jp](images/fusion13_oiciam_federation_00022.jpg)  
  
Select <ins>Done<ins>, to save the configuration  

![fusion13_oiciam_federation_00023.jpg](images/fusion13_oiciam_federation_00023a.jpg)  

## 5) Fusion: Download Oracle Fusion Apps metadata to Oracle OCI IAM Domain

Download and save the metadata XML file by click on the download symbol.    
![fusion13_oiciam_federation_00023.jpg](images/fusion13_oiciam_federation_00023b.jpg)  

## 6) Oracle OCI IAM Domain: Extract the proper certificate from the Oracle Fusion Apps metadata XML file
  
OCI IAM does not have a feature to upload a metadata file directly and automatically extract the values.  
This is a bit of minor work. You need to download the Oracle Fusion Apps metadata file and open it in a tool like Visual Code, Crome or Firefox, to be able to search for the correct attributes. 

Create an empty text file with the following text:  
``
-----BEGIN CERTIFICATE-----
-----END CERTIFICATE-----
``


First step is to create a proper CER file for upload to Oracle OCI IAM 
Locate the <md:KeyDescriptor use="signing"> XML element, and find <dsig:X509Certificate>  
From the md:IDPSSODescriptor element  copy/paste between <dsig:X509Certificate> and </dsig:X509Certificate>  

![Certificate to be extracted](images/fusion13_oiciam_federation_00026.jpg)  
  
Copy the value into the editor:  
``
-----BEGIN CERTIFICATE-----
MIIEDzCCYDVQQDExBZjANBYDVQQDExw0BAYDVQQDExSgwJgYDVQQDEx91Y2YzLXpYDVQQDEx
-----END CERTIFICATE-----
``
and save to a .cer file



## 7) Oracle OCI IAM Domain: Extract attributes from Oracle Fusion Apps Metadata

The values you will need to extract from the Oracle Fusion Apps metadata file are:  
  
|OCI IAM Attribute| XML Path |Attribute name|Example value|
|-----------------|---------|--------------|-------------|
|Relay State|md:SPSSODescriptor/md:AssertionConsumerService|Location|https://login-esss-saas1.ds-fa.oraclepdemos.com/oam/server/fed/sp/sso|
|Enity ID|md:EntityDescriptor|entityID|https://login-esss-saas1.ds-fa.oraclepdemos.com/oam/server/fed/sp/sso|
|AssertionConsumerURL|md:SPSSODescriptor/md:AssertionConsumerService|Location|https://login-esss-saas1.ds-fa.oraclepdemos.com/oam/server/fed/sp/sso|
|SingleLogoutURL|md:SPSSODescriptor/md:SingleLogoutService|Location|https://login-essss-saas1.ds-fa.oraclepdemos.com/oamfed/sp/samlv20|
|LogoutResponseURL|md:SPSSODescriptor/md:SingleLogoutService|ResponseLocation|https://login-essss-saas1.ds-fa.oraclepdemos.com/oamfed/sp/samlv20|

An example table of attributes required by Oracle OCI IAM:  

![Attribute table](images/fusion13_oiciam_federation_00029)  

<ins>Entity ID</ins> location within Oracle Fusion Apps metadata  
![Entry of entity ID](images/fusion13_oiciam_federation_00030.jpg)  

<ins>AssertionConsumerUR</ins>L and <ins>SingleLogoutURL</ins> location within Oracle Fusion Apps metadata  
![AssertionConsumerURL](images/fusion13_oiciam_federation_00031.jpg)  

<ins>ResponseLocatio</ins>n Attribute    
![Entry of ResponseLocation Attribute](images/fusion13_oiciam_federation_00032.jpg)  

## 8) Oracle OCI IAM Domain: Update with the extracted values

Navigate back to the first page in the workflow of creating a SAML application within Oracle OCI IAM, click <ins>Next</ins>, all configurations will be on this page  
![IDP configuration startpage](images/fusion13_oiciam_federation_00035.jpg)   

In the general page add 
EntityId and Assertion consumer URL  
Leave the default values for Name ID format and Name ID value  
![Enter values](images/fusion13_oiciam_federation_00036.jpg)  

Upload the previously created certificate file .cer file  
![Upload .cer file](images/fusion13_oiciam_federation_00037.jpg)  
  
![fusion13_oiciam_federation_00038.jpg](images/fusion13_oiciam_federation_00038.jpg)  

Finally add values for Single logout URL and Logout response URL  
![Add Single logout URL and Logout response URL](images/fusion13_oiciam_federation_00040.jpg)  

## 9) Oracle OCI IAM Domain: Activate the SAML Application and assign users to it

The integrated application needs to be activated before any SAML requests are accepted, and only users (or via groups) assigned to the integrated application will be authenticated against it.  

First activate the application  

![Activate IdP](images/fusion13_oiciam_federation_00042.jpg)  
  
![Activate IdP](images/fusion13_oiciam_federation_00043.jpg)  

Assign users, when it is active  

![Assign users](images/fusion13_oiciam_federation_00044.jpg)  
  
![Verification of user assignment](images/fusion13_oiciam_federation_00045.jpg)  

## 10) Fusion: Test SAML federation with Oracle OCI IAM Domain
  
Oracle Fusion Apps will not allow the SSO to be activated before it is tested and the test is successful. The task is undertaken in the Federation configuration screen.  

As a preliminary step, you may open, in a different browser session (incognito window) a separate session and turn on Oracle OCI IAM Diagnostics  
The diagnostic can be useful if the Oracle Fusion Apps to Oracle OCI IAM test fails. 
    
![Navigate to diagnostics page](images/fusion13_oiciam_federation_00052.jpg)  
  
![OCI IAM Diagnostic enablement page](images/fusion13_oiciam_federation_00053.jpg)  
  
To enable federation from Oracle Fusion Apps, you need to run a successful test, from the same browser session.  
Edit the Oracle Fusion Apps SSO configuration  
  
![Edit SSO configuration](images/fusion13_oiciam_federation_00047.jpg)  
  

  
<ins>Select Diagnostics and activation</ins>   
![fusion13_oiciam_federation_00048.jpg](images/fusion13_oiciam_federation_00048.jpg)  

Select <ins>test</ins>. The test will bring up a new tab in your current browser window.  
![Click test button](images/fusion13_oiciam_federation_00049.jpg)  

  
![fusion13_oiciam_federation_00050.jpg](images/fusion13_oiciam_federation_00050.jpg)  
  
![fusion13_oiciam_federation_00051.jpg](images/fusion13_oiciam_federation_00051.jpg) 
  
If SSO is correctly configured it will open a new page in the current browser. The current browser shall not have any valid IDCS or Oracle OCI IAM session.  
You need to have the username with the same userid predefined in both Oracle OCI IAM and Oracle Fusion Apps, and the user needs to be either in a assigned group or signed-on directly to the integrated application.  If the userids on both sides of the federation don't match, the federation will fail.  

![OCI IAM Logon page](images/fusion13_oiciam_federation_00054.jpg)  

The status screen returned should look like this, with **Authentication Successful**
![Success page](images/fusion13_oiciam_federation_00055.jpg)  

When the tab is closed, the status field in the Oracle Fusion Apps configuration screen is updated, and the SSO federation can be activated.  
![Success set in Oracle Fusion Apps Configuration screen](images/fusion13_oiciam_federation_00056.jpg)  


## 11) Fusion: Enable Federation
  
Click <ins>Edit</ins> in the Oracle Fusion Apps configuration page, to enable federation  
  
![fusion13_oiciam_federation_00058.jpg](images/fusion13_oiciam_federation_00058.jpg)  
    
Check the flag <ins>Enable identity provider</ins>  
  
![fusion13_oiciam_federation_00059.jpg](images/fusion13_oiciam_federation_00059.jpg)  
  
Save the change  

![fusion13_oiciam_federation_00060.jpg](images/fusion13_oiciam_federation_00060.jpg)  

## 12) Fusion: Post Configuration of Oracle Fusion Apps 

The final step is to decide if SSO shall be visible, label <ins>Company Single Sign-on</ins>, and to decide if SAML federation is the only option.

First add Company Single Sign-on to the logon page   

Navigate to the Single Sign-on configuration page  
![SSO configuration page](images/fusion13_oiciam_federation_00062.jpg)  

Select <ins>edit</ins>, and check Enable Chooser Login Page, and save   
![fusion13_oiciam_federation_00063.jpg](images/fusion13_oiciam_federation_00063.jpg)   

Then select the Identity provider defined earlier  

![fusion13_oiciam_federation_00064.jpg](images/fusion13_oiciam_federation_00064)  

Select <ins>Edit</ins>  
![fusion13_oiciam_federation_00065.jpg](images/fusion13_oiciam_federation_00065)  

If the default identity provider box is checked, the logon page will not be displayed and only federated sign-on is allowed.  

![fusion13_oiciam_federation_00066.jpg](images/fusion13_oiciam_federation_00066)  
  
  
**Piece of advice, keep an independent browser window open, signed-on and open the security center, so the configuration can be reverted before it is put in production.**  


# Documentation Links

Oracle OCI IAM Domain, license types
[](https://docs.oracle.com/en-us/iaas/Content/Identity/sku/overview.htm)  
  
Oracle OCI IAM Domain, App catalog
[](https://docs.oracle.com/en-us/iaas/Content/Identity/applications/add-app-catalog-application.htm)  
[](https://docs.oracle.com/en/cloud/paas/identity-cloud/idcsc/toc.htm)  
  
Oracle OCI IAM Domain, SAML configuration  
[](https://docs.oracle.com/en-us/iaas/Content/Identity/applications/add-saml-application.htm)  
  
Oracle Fusion SSO Configuration
[](https://docs.oracle.com/en/cloud/saas/human-resources/24b/ochus/oracle-applications-cloud-as-the-single-sign-on-sso-service.html#s20069736)



# License

Copyright (c) 2024 Oracle and/or its affiliates.

Licensed under the Universal Permissive License (UPL), Version 1.0.
