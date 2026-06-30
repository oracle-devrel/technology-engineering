# How to create a Postman Collection for OCI Audit Logs

To do this, you need to first prepare your Postman to make calls against OCI. You can follow this link to configure it.

How to use OCI API’s with Postman

On my previous post I have showcased how to use Identity Domains API’s in Postman.

learnoci.cloud

After you have prepared the environment for the OCI API calls, you need to Export and import the Logging Search API Collection.

Search response list is being retrieved. | Oracle Cloud Infrastructure REST APIs | Postman API…

Edit description

www.postman.com

![Picture 12](./images/image-01.png)

![Picture 11](./images/image-02.png)

Next you duplicate the Collection and you rename it Audit API:

![Picture 10](./images/image-03.png)

You leave the variables as the ones from Logging Search, and you go to OCI Logging → Audit:

![Picture 9](./images/image-04.png)

In your browser open Developer Tools(Menu →More Tools →Developer Tools):

![Picture 7](./images/image-05.png)

Clear the data, and do a search in OCI Audit:

![Picture 6](./images/image-06.png)

![Picture 5](./images/image-07.png)

In the right, you will see the Search Payload:

![Picture 4](./images/image-08.png)

Right click on the Payload and copy the value:

![Picture 3](./images/image-09.png)

Paste it in the Body of Search logs POST Request in Postman and press Send(Change the TimeStart and TimeEnd values based on your requirement):

![Picture 2](./images/image-10.png)

Congratulation! You have created your own OCI audit API call.

![Picture 1](./images/image-11.png)
