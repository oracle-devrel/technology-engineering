
---------------------------------------------------------------------------------
-- CUSTOMER_HISTORY_SALES_DV - JSON RELATIONAL DUALITY Views 
-- CUSTOMERS, SALES, PRODUCTS relational tables, SH sample schema 
----------------------------------------------------------------------------------

CREATE FORCE NONEDITIONABLE JSON RELATIONAL DUALITY VIEW CUSTOMER_HISTORY_SALES_DV
 AS SELECT JSON {
        'quantitySold' : s.QUANTITY_SOLD,
        'amountSold' : s.AMOUNT_SOLD,
        '_id' : s.SALES_ID,
        'products' : 
            ( SELECT JSON {
                'prodId' : p.PROD_ID,
                'prodName' : p.PROD_NAME,
                'prodDesc' : p.PROD_DESC,
                'prodCategory' : p.PROD_CATEGORY
            }
            FROM PRODUCTS p
             WHERE  p.PROD_ID = s.PROD_ID 
         ),
        'customers' : 
            ( SELECT JSON {
                'custId' : c.CUST_ID,
                'custFirstName' : c.CUST_FIRST_NAME,
                'custLastName' : c.CUST_LAST_NAME,
                'custPostalCode' : c.CUST_POSTAL_CODE,
                'custEmail' : c.CUST_EMAIL WITH UPDATE
            }
            FROM CUSTOMERS c
            WHERE  c.CUST_ID = s.CUST_ID 
         )
    }
    FROM SALES s
;

SELECT  dv.DATA.customers.custId CUST_ID,
        dv.DATA.amountSold AMOUNT_SOLD,
        dv.DATA.customers.custEmail CUST_EMAIL,
        dv.DATA.products.prodId PROD_ID,
        dv.DATA.products.prodDesc PROD_DESC,
        dv.DATA.products.prodCategory CATEGORY
    FROM CUSTOMER_HISTORY_SALES_DV dv
    WHERE dv.DATA.customers.custId = 8696
;
/* 
CUST_ID    AMOUNT_SOLD    CUST_EMAIL                         PROD_ID    PROD_DESC                                    CATEGORY               
__________ ______________ __________________________________ __________ ____________________________________________ ______________________ 
8696       51.97          "Snodgrass@company.example.com"    127        "Genuine Series MIX Wood Bat"                "Baseball"             
8696       1552.83        "Snodgrass@company.example.com"    18         "Lithium Electric Golf Caddy"                "Golf"                 
8696       48.36          "Snodgrass@company.example.com"    42         "New Zealand Cricket Team"                   "Cricket"              
8696       49.66          "Snodgrass@company.example.com"    40         "West Indies Team"                           "Cricket"              
8696       48.36          "Snodgrass@company.example.com"    45         "English Cricket Team"                       "Cricket"              
8696       48.36          "Snodgrass@company.example.com"    41         "South African Team"                         "Cricket"              
8696       54.35          "Snodgrass@company.example.com"    35         "Catchers Mitt"                              "Baseball"             
8696       16.69          "Snodgrass@company.example.com"    125        "Cricket Bucket Hat"                         "Cricket"              
8696       11.38          "Snodgrass@company.example.com"    30         "Cricket Bat - Linseed Oil"                  "Cricket"              
8696       45.71          "Snodgrass@company.example.com"    27         "Bucket of 24 Synthetic Baseballs"           "Baseball"             
8696       9.36           "Snodgrass@company.example.com"    30         "Cricket Bat - Linseed Oil"                  "Cricket"              
8696       53.89          "Snodgrass@company.example.com"    36         "12\" Premium Ser
*/ 

-- SUM sales 
 
WITH CTE as 
(SELECT  dv.DATA.customers.custId CUST_ID,
        dv.DATA.amountSold AMOUNT_SOLD,
        dv.DATA.customers.custEmail CUST_EMAIL,
        dv.DATA.products.prodId PROD_ID,
        dv.DATA.products.prodDesc PROD_DESC,
        dv.DATA.products.prodCategory CATEGORY
FROM CUSTOMER_HISTORY_SALES_DV dv
WHERE dv.DATA.customers.custId = 8696) 
SELECT CUST_ID,CUST_EMAIL,PROD_DESC, SUM(AMOUNT_SOLD), CATEGORY FROM CTE GROUP BY CUST_ID,CUST_EMAIL,PROD_DESC, CATEGORY
;
/*
CUST_ID    CUST_EMAIL                         PROD_DESC                                  SUM(AMOUNT_SOLD) CATEGORY     
__________ __________________________________ _______________________________________ ___________________ ____________ 
8696       "Snodgrass@company.example.com"    "Tennis Balls 12 Pack"                                47.36 "Tennis"     
8696       "Snodgrass@company.example.com"    "Tennis Balls Heavy Duty Felt 3 can"                  20.98 "Tennis"     
8696       "Snodgrass@company.example.com"    "Tennis Strings Natural Gut"                         100.16 "Tennis"     
8696       "Snodgrass@company.example.com"    "West Indies Team"                                    97.59 "Cricket"    
8696       "Snodgrass@company.example.com"    "Wicket Keeper Gloves"                                18.86 "Cricket"    

46 rows selected.
*/