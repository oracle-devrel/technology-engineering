# ExaCC Status & Maintenance Reports

Many large ExaDB-C@C customers have several ExaDB-C@C instances and desire a single report that lists all these instances. All information is already available on a per ExaDB-C@C basis but large customer installations benefit from all instances in a single report. 

## ExaCC Status Monitoring

This project contains a sample configuration of certain OCI services that allow a customer to monitor the status of their pre-existing Exadata Cloud at Customer (ExaDB-C@C) instances. 
The functionality is provided by configuring OCI Functions, OCI Events, OCI Email Delivery, and OCI SDK for Python and these examples guide the use of these services to generate reports detailing the status and maintenance state of a customer’s ExaDB-C@C instances in their own tenancy. 
This configuration gathers information already available to any ExaDB-C@C customer and aggregates it to form a report. The information gathered is standard metrics and events available to any ExaDB-C@C customer. 
