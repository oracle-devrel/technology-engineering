# Autonomous Database Serverless
 
Oracle Cloud provides a set of data management services built on self-driving Oracle Autonomous Database technology to deliver automated patching, upgrades, and tuning, including performing all routine database maintenance tasks while the system is running, without human intervention.

Reviewed: 23.10.2024
 
# Table of Contents
 
1. [Team Publications](#team-publications)
2. [Useful Links](#useful-links)
3. [LiveLabs](#livelabs)
 
# Team Publications
 
- [How to rotate Oracle Autonomous Wallets with a Grace Period](https://medium.com/@javidelatorre/how-to-rotate-oracle-autonomous-wallets-with-a-grace-period-8cf3a75e2ac6)
    - Step-by-step blog article explaining how to rotate the wallet.
 
- [4 ways to connect to Autonomous Database on a Private Network](https://blogs.oracle.com/datawarehousing/post/4-ways-to-connect-to-autonomous-database-on-a-private-network)
    - Learn how to connect to Autonomous Database when is on a private network.

- [Develop over a full database managed service on your laptop](https://dev.to/javierdelatorre/develop-over-a-full-database-managed-service-on-your-laptop-20pg)
    - Learn how to create an Autonomous Database on your laptop.
      
- [How to use Terraform to automate Oracle Autonomous Database deployments](https://blogs.oracle.com/datawarehousing/post/how-to-use-terraform-to-automate-oracle-autonomous-database-deployments)
    - Learn how to use Terraform to automate Oracle Autonomous Database deployments.

- [Recently announced Autonomous Database container image](https://www.linkedin.com/posts/manuela-mitu-1119a3259_adb-activity-7112093727061340161-L8L1)
    - Learn how to download and run an Autonomous Database Free container image.

- [Recently announced Autonomous Database container image](https://www.linkedin.com/posts/manuela-mitu-1119a3259_autonomousdatabase-activity-7117196782438076416-YHBt)
    - Access built-in database tools and load data.

- [Autonomous Database only - Geocode with managed reference data](https://www.youtube.com/watch?v=yCxlNBjtoNE)
    - Geocoding is the conversion of an address or place name into geographic coordinates. With Oracle Autonomous Database Serverless you can now geocode (and reverse geocode) with managed reference data.
 
- [Disaster Recovery with Autonomous Data Guard Serverless](https://www.youtube.com/watch?v=h4wkXh7dWe4)
    - The disaster Recovery solution for the Autonomous Database Serverless (RTO/RPO, local and remote cross-region, etc).
      
- [How to create Autonomous Database Notifications in Slack](https://blogs.oracle.com/datawarehousing/post/how-to-create-autonomous-database-notifications-in-slack)
    - Step-by-step blog article explaining how to send an alert message, triggered by an Autonomous Database event, into a slack channel using a webhook link.
    
- [Oracle Database Vault on the Autonomous Database](https://www.youtube.com/watch?v=d5c2QAPrX1o)
    - How to configure and implement Oracle Database Vault on the Autonomous Database. Use cases.
      
- [Switching from Oracle-Managed to Customer-Managed Keys in Autonomous Database Serverless](https://medium.com/@mmy0utu8e/switching-from-oracle-managed-to-customer-managed-keys-in-autonomous-database-serverless-b1c24d107a8f)
    - How to switch from Oracle-Managed to Customer-Managed Keys in Autonomous Database Serverless.

- [Capture-Replay Workloads between non-Autonomous and Autonomous Databases](https://www.youtube.com/watch?v=cWZ9MPBZemc)
    - How to Capture and Replay Workloads between non-Autonomous and Autonomous Databases.
      
- [The Oracle Autonomous Database You Can Get for Free](https://medium.com/@mmy0utu8e/oracle-autonomous-database-for-free-f93174bdb7ed)
    - Free Autonomous Database options description

- [Capture-Replay Workloads between Autonomous Databases](https://www.youtube.com/watch?v=JXpQe7zUFs8)
    - How to Capture and Replay Workloads between Autonomous Databases.

 - [Enable SQL Trace on Autonomous Database](https://blogs.oracle.com/datawarehousing/post/enable-sql-trace-on-autonomous-database)
    - Step-by-step blog article explaining how to collect a sql trace from Autonomous Database.
  
 - [ADB-S Top 3 Announcements for Autonomous in Cloud World 2024](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-data-ai-activity-7242082377458429952-GXeQ?utm_source=share&utm_medium=member_desktop)
    - ADB-S Top 3 Announcements for Autonomous.

 - [Protecting the Autonomous Database from runaway queries](https://medium.com/@adrian.capitanu/protecting-the-autonomous-database-from-runaway-queries-eba925112bbb)
    - Step-by-step blog article explaining how to protect the ADB from runaway queries and controlling resource usage

 - [The Oracle Data Marketplace](https://medium.com/@mmy0utu8e/the-oracle-data-marketplace-ddbf4ac92b87)
    - How to share/consume data using Data Marketplace on the Autonomous Database
      
 - [Using the new graphical interface for Database Replay to test new patches on Autonomous Database](https://medium.com/@adrian.capitanu/using-database-replay-to-test-new-patches-on-autonomous-database-6701ed9def6e)
    - How to automate testing of new patches before implementing them in a Production Autonomous Database
   
## Tip of the Day
 
- [Tip 1](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7104394940436164609-LSa-?)
    - Query different databases using direct query.

- [Tip 2](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7104746581991563264-ONHG?)
    - Which types of Autonomous databases can I provision?

- [Tip 3](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7105106822885224448-NkPN?)
    - Autonomous is self-securing.

- [Tip 4](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7105457134749777920-hiGQ?)
    - Improve security with Data Safe.

- [Tip 5](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7105858237802962944-IicY?)
    - Automatic backups.

- [Tip 6](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7106932008630517760-7SO0?)
    - Create Autonomous Databases from Azure.

- [Tip 7](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7107272409954590721-wgkk?)
    - Configure Autonomous CPU autoscaling.

- [Tip 8](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7107662131604418561-GsqH?)
    - Configure Autonomous storage autoscaling.

- [Tip 9](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7108015244769136640-3QVI?)
    - Automatic Indexing.

- [Tip 10](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7108380970751303682-yE0n?)
    - Configure disaster recovery.

- [Tip 11](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7109470994955710464-YaUH?)
    - Clone production databases.

- [Tip 12](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7109853287725621249-jn9y?)
    - Use JSON with an Autonomous Database.

- [Tip 13](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7110214198017560576-Ucd7?)
    - Become an expert data scientist.

- [Tip 14](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7110526745765720064-dpWI?)
    - Use time travel to query historical data.

- [Tip 15](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7110892721266905088-z23o?)
    - Data Sharing.

- [Tip 16](https://www.linkedin.com/posts/javier-de-la-torre-medina_oracle-autonomousdatabase-tipoftheday-activity-7112001307946725378-grDm?)
    - Elastic Resource Pools.

- [Tip 17](https://www.linkedin.com/posts/javier-de-la-torre-medina_data-oracle-autonomousdatabase-activity-7112353730464821248-7w38?)
    - Data Studio.

- [Tip 18](https://www.linkedin.com/posts/javier-de-la-torre-medina_data-oracle-autonomousdatabase-activity-7112743945121492993-geuf?)
    - MongoDB API.

- [Tip 19](https://www.linkedin.com/posts/javier-de-la-torre-medina_data-softwareengineering-innovation-activity-7113069715228405762-0lWO?)
    - Autonomous Container image.

- [Tip 20](https://www.linkedin.com/posts/javier-de-la-torre-medina_data-softwareengineering-innovation-activity-7113425224850653184-PTZd?)
    - Select AI.
    
# Useful Links
 
- [Autonomous Database Serverless documentation](https://docs.oracle.com/en/cloud/paas/autonomous-database/shared/index.html)
    - Full documentation about Oracle Autonomous Database Serverless.
      
- [Whats new?](https://docs.oracle.com/en/cloud/paas/autonomous-database/serverless/adbsb/whats-new-adwc.html#ADBSN-GUID-F31A86F8-012B-4235-A0BE-4ABF75164853)
    - What is new in Autonomous Database Serverless.

- [In-Memory is Now Available on Oracle Autonomous](https://blogs.oracle.com/datawarehousing/post/database-inmemory-is-now-available-on-oracle-autonomous-database-serverless)
    - In-Memory with Autonomous Database Serverless.
      
- [Select AI for Synthetic Data Generation](https://blogs.oracle.com/datawarehousing/post/announcing-select-ai-for-synthetic-data-generation-adb)
    - Using Select AI for Synthetic Data Generation.
 
## LiveLabs
 
- [Manage and Monitor Autonomous Database](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=553&clear=RR,180)
    - Complete the course about how to administrate an Autonomous Database.
  
- [Chat with your Data in Autonomous Database using Generative AI](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3831&clear=RR,180&session=6652951814948)
    - Lab on how to use Generative AI.
      
- [Develop Apps using GenAI, Autonomous Database and React](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3910&clear=RR,180&session=116856248894781)
    - Lab on how to develop Apps using GenAI, Autonomous Database and React.
      
- [.NET development with Oracle Autonomous Database Quick Start](https://apexapps.oracle.com/pls/apex/r/dbpm/livelabs/view-workshop?wid=3359&clear=RR,180&session=111609839150181)
    - Lab on how to develop .NET Apps with Oracle Autonomous Database.
      

# License
 
Copyright (c) 2025 Oracle and/or its affiliates.
 
Licensed under the Universal Permissive License (UPL), Version 1.0.
 
See [LICENSE](https://github.com/oracle-devrel/technology-engineering/blob/main/LICENSE) for more details.
