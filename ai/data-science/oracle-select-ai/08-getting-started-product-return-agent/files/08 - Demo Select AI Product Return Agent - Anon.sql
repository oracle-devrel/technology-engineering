-- Copyright (c) 2026, Oracle and/or its affiliates.  All rights reserved.
-- This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

/*
Select AI - Create a Product Return Agent with Built-In Tools
*/


/*
Pre-Requisites - Configuring Select AI
*/


/*
Note: Please refer to "00 - Setup Select AI - Anon" for all pre-requisites on granting permissions to Packages, LLMs, Authentication and for Setting Up Credentials.
*/


/*
Create a Product Return Agent with Built-In Tools
*/


/*
This example shows how you can create a multi-turn conversational agent using Select AI Agent. In this example, you set up a customer-service agent that handles product returns and updates the return status in your database.

Create an Agent

You create an agent called Customer_Return_Agent with a profile and role to manage return requests.

Create Tools

You then create an agent tool named Update_Order_Status_Tool to update the status of the order in your database.

Create Task

You create a task called Handle_Product_Return_Task to guide the flow: ask for the reason (no longer needed, arrived too late, box broken, or defective). Proceed with a defective return flow.

Create Team

You create an agent team called Return_Agency_Team with Customer_Return_Agent as the agent and set it as an active team.

Run the Select AI Agent Team

You now run the agent team by using select ai agent as a prefix to your prompts.
*/


/*
Drop Tables
*/


-- Drop Demo Tables If Exists
DROP TABLE IF EXISTS DEMO_AGENTS_CUSTOMERS;
DROP TABLE IF EXISTS DEMO_AGENTS_CUSTOMER_ORDER_STATUS;


/*
Create Tables & Insert Records
*/


-- Create Sample Customer Data
CREATE TABLE DEMO_AGENTS_CUSTOMERS (
    customer_id  NUMBER(10) PRIMARY KEY,
    name         VARCHAR2(100),
    email        VARCHAR2(100),
    phone        VARCHAR2(20),
    state        VARCHAR2(2),
    zip          VARCHAR2(10)
);

INSERT INTO DEMO_AGENTS_CUSTOMERS (customer_id, name, email, phone, state, zip) VALUES
(1, 'Alice Thompson', 'alice.thompson@example.com', '555-1234', 'NY', '10001'),
(2, 'Bob Martinez', 'bob.martinez@example.com', '555-2345', 'CA', '94105'),
(3, 'Carol Chen', 'carol.chen@example.com', '555-3456', 'TX', '73301'),
(4, 'David Johnson', 'david.johnson@example.com', '555-4567', 'IL', '60601'),
(5, 'Eva Green', 'eva.green@example.com', '555-5678', 'FL', '33101');

-- Create Sample Customer Order Status
CREATE TABLE DEMO_AGENTS_CUSTOMER_ORDER_STATUS (
    customer_id     NUMBER(10),
    order_number    VARCHAR2(20),
    status          VARCHAR2(30),
    product_name    VARCHAR2(100)

);

INSERT INTO DEMO_AGENTS_CUSTOMER_ORDER_STATUS (customer_id, order_number, status, product_name) VALUES
(2, '7734', 'delivered', 'smartphone charging cord'),
(1, '4381', 'pending_delivery', 'smartphone protective case'),
(2, '7820', 'delivered', 'smartphone charging cord'),
(3, '1293', 'pending_return', 'smartphone stand (metal)'),
(4, '9842', 'returned', 'smartphone backup storage'),
(5, '5019', 'delivered', 'smartphone protective case'),
(2, '6674', 'pending_delivery', 'smartphone charging cord'),
(1, '3087', 'returned', 'smartphone stand (metal)'),
(3, '7635', 'pending_return', 'smartphone backup storage'),
(4, '3928', 'delivered', 'smartphone protective case'),
(5, '8421', 'pending_delivery', 'smartphone charging cord'),
(1, '2204', 'returned', 'smartphone stand (metal)'),
(2, '7031', 'pending_delivery', 'smartphone backup storage'),
(3, '1649', 'delivered', 'smartphone protective case'),
(4, '9732', 'pending_return', 'smartphone charging cord'),
(5, '4550', 'delivered', 'smartphone stand (metal)'),
(1, '6468', 'pending_delivery', 'smartphone backup storage'),
(2, '3910', 'returned', 'smartphone protective case'),
(3, '2187', 'delivered', 'smartphone charging cord'),
(4, '8023', 'pending_return', 'smartphone stand (metal)'),
(5, '5176', 'delivered', 'smartphone backup storage');


-- COMMIT
COMMIT;


/*
Define OCI API Credential
*/


-- Drop Credential
BEGIN
    DBMS_CLOUD.DROP_CREDENTIAL('<enter-oci-api-credential-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Credential does not exist.');
END;
/


-- Create Credentials for OCI API Key
BEGIN                                                                          
	DBMS_CLOUD.CREATE_CREDENTIAL
        (  
		    	credential_name => '<enter-oci-api-credential-name>',
			 	user_ocid 		=> '<enter-user-ocid>',
		        tenancy_ocid    => '<enter-tenancy-ocid>',
		        private_key     => '<enter-private-key-value>',
		        fingerprint     => '<enter-private-key-fingerprint>'       
        );                                                                           
END;                                                                           
/


/*
Define AI Profile
*/


-- Drop AI Profile
BEGIN
    DBMS_CLOUD_AI.DROP_PROFILE('<enter-ai-profile-name>');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Profile does not exist.');
END;
/


-- Create AI Profile
BEGIN                                                                          
	DBMS_CLOUD_AI.CREATE_PROFILE
        (                                                
		        profile_name => '<enter-ai-profile-name>'
		    ,   attributes   => '{
                                        "provider"          : "oci"
		                            ,   "object_list"       : 
                                                                [
                                                                        {"owner": "<enter-schema-name>", "name": "DEMO_AGENTS_CUSTOMERS"}
                                                                    ,   {"owner": "<enter-schema-name>", "name": "DEMO_AGENTS_CUSTOMER_ORDER_STATUS"}
                                                                ]
                                    ,   "credential_name"   : "<enter-oci-api-credential-name>"
                                    ,   "model"             : "<enter-model-name-id>"
                                    ,   "oci_compartment_id": "<enter-compartment-ocid>"
                                    ,   "region"            : "<enter-region-identifier>"
                                    ,   "comments"          : "true"
                                    ,   "conversation"      : "true"
                                }'
        );
END;                                                                           
/


/*
Define PL/SQL Function to Update Order Status
*/


-- Drop PL/SQL Function that will be used to update order status
DROP FUNCTION IF EXISTS UPDATE_CUSTOMER_ORDER_STATUS;

-- A Function returns something, Procedure doesn't

--Create a update customer order status function
CREATE OR REPLACE FUNCTION UPDATE_CUSTOMER_ORDER_STATUS (
    p_customer_name IN VARCHAR2,
    p_order_number  IN VARCHAR2,
    p_status        IN VARCHAR2
) RETURN VARCHAR2 IS

    -- Global variables
    v_customer_id  DEMO_AGENTS_CUSTOMERS.customer_id%TYPE;
    v_row_count    NUMBER;

BEGIN
    -- Find customer_id from customer_name
    SELECT customer_id
    INTO v_customer_id
    FROM DEMO_AGENTS_CUSTOMERS
    WHERE name = p_customer_name;
    
    UPDATE DEMO_AGENTS_CUSTOMER_ORDER_STATUS
    SET status = p_status
    WHERE customer_id = v_customer_id
      AND order_number = p_order_number;

    v_row_count := SQL%ROWCOUNT;

    IF v_row_count = 0 THEN
        RETURN 'No matching record found to update.';
    ELSE
        RETURN 'Update successful.';
    END IF;
EXCEPTION
    WHEN OTHERS THEN
        RETURN 'Error: ' || SQLERRM;
END;


/*
View Record
*/


-- Preview an example record
 SELECT * FROM DEMO_AGENTS_CUSTOMER_ORDER_STATUS WHERE CUSTOMER_ID = 3 AND ORDER_NUMBER = '2187';


/*
Test PL/SQL Function
*/


-- Test PL/SQL Function Defined Above
DECLARE
    v_result VARCHAR2;
BEGIN
    v_result := UPDATE_CUSTOMER_ORDER_STATUS('Carol Chen', '2187', 'no longer needed');

    DBMS_OUTPUT.PUT_LINE(v_result);
END;
/


/*
View Record
*/


-- Preview updated record
 SELECT * FROM DEMO_AGENTS_CUSTOMER_ORDER_STATUS WHERE CUSTOMER_ID = 3 AND ORDER_NUMBER = '2187';


/*
Define Update Order Status Tool
*/


-- Drop Agent Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TOOL('UPDATE_ORDER_STATUS_TOOL');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Tool does not exist.');
END;
/


--Create Agent Tool
BEGIN
    DBMS_CLOUD_AI_AGENT.CREATE_TOOL(
        tool_name => 'UPDATE_ORDER_STATUS_TOOL',
        attributes => '{"instruction": "This tool updates the database to reflect return status change. Always confirm user name and order number with user before updating status",
                        "function" : "UPDATE_CUSTOMER_ORDER_STATUS"}',
        description => 'Tool for updating customer order status in database table.'
    );
END;
/


/*
Define Handle Product Return Task
*/


-- Drop Agent Task
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TASK('HANDLE_PRODUCT_RETURN_TASK');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Task does not exist.');
END;
/


-- Create Agent Task
BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_TASK(
    task_name => 'HANDLE_PRODUCT_RETURN_TASK',
    attributes => '{"instruction": "Process a product return request from a customer: {query}' || 
                    '1. Ask customer the order reason for return (no longer needed, arrived too late, box broken, or defective)' || 
                    '2. If no longer needed:' ||
                    '   a. Inform customer to ship the product at their expense back to us.' ||
                    '   b. Update the order status to return_shipment_pending using UPDATE_ORDER_STATUS_TOOL.' ||
                     '3. If it arrived too late:' ||
                    '   a. Ask customer if they want a refund.' ||
                    '   b. If the customer wants a refund, then confirm refund processed and update the order status to refund_completed' || 
                    '4. If the product was defective or the box broken:' ||
                    '   a. Ask customer if they want a replacement or a refund' ||
                    '   b. If a replacement, inform customer replacement is on its way and they will receive a return shipping label for the defective product, then update the order status to replaced' ||
                    '   c. If a refund, inform customer to print out the return shipping label for the defective product, return the product, and update the order status to refund' ||
                    '5. After the completion of a return or refund, ask if you can help with anything else.' ||
                    '   End the task if user does not need help on anything else",
                    "tools": ["UPDATE_ORDER_STATUS_TOOL"]}'
  );
END;
/


/*
Define Customer Return Agent
*/


-- Drop Agent
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_AGENT('CUSTOMER_RETURN_AGENT');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Agent does not exist.');
END;
/


-- Create Agent
BEGIN
  DBMS_CLOUD_AI_AGENT.CREATE_AGENT(
    agent_name => 'CUSTOMER_RETURN_AGENT',
    attributes => '{"profile_name": "<enter-ai-profile-name>",
                    "role": "You are an experienced customer return agent who deals with customers return requests."}');
END;
/
 

/*
Define Return Agency Team
*/


-- Drop Agent Team
BEGIN
    DBMS_CLOUD_AI_AGENT.DROP_TEAM('RETURN_AGENCY_TEAM');
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Agent Team does not exist.');
END;
/


-- Create Agent Team
BEGIN                                                                
  DBMS_CLOUD_AI_AGENT.CREATE_TEAM( 
    team_name  => 'RETURN_AGENCY_TEAM',                                                            
    attributes => '{"agents": [{"name":"CUSTOMER_RETURN_AGENT","task" : "HANDLE_PRODUCT_RETURN_TASK"}],
                    "process": "sequential"}');                                                                
END;                                                                      
/


/*
Set & Validate Agent Team is in Session
*/


-- Set Agent Team
EXEC DBMS_CLOUD_AI_AGENT.SET_TEAM('RETURN_AGENCY_TEAM');


-- Validate Agent Team is Set
SELECT DBMS_CLOUD_AI_AGENT.GET_TEAM FROM DUAL;


/*
Interact with Agent Team
*/


-- Interact with Agent Team
select ai agent I want to return a smartphone case;


-- Interact with Agent Team
select ai agent the item is defective;


-- Interact with Agent Team
select ai agent I will need a replacement;


-- Interact with Agent Team
select ai agent Im Bob Martinez and my order number is 7820;


-- Interact with Agent Team
select ai agent No, Im all set. Thanks;


/*
Validate Updated Record
*/


-- Preview updated record
 SELECT * FROM DEMO_AGENTS_CUSTOMER_ORDER_STATUS WHERE ORDER_NUMBER = '7820';


/*
End of Notebook
*/

