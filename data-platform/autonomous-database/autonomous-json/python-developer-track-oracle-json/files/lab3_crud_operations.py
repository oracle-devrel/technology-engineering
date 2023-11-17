import oracledb


#connect with thick-client
oracledb.init_oracle_client()
connection = oracledb.connect(user="myapp",
                              password="PassworD123##",
                              dsn="localhost:1521/FREEPDB1")

#auto commit
connection.autocommit = True

#Create new collection for hotel reservations
soda = connection.getSodaDatabase()
collection = soda.createCollection("hotel_reservations")
collection = soda.openCollection("hotel_reservations")

#Task 1: insertDocument
collection.insertOne(
{
    "reservation_id": "1",
    "hotel_id": "123",
    "room_id": "105",
    "checkin_date": "2023-06-03",
    "checkout_date": "2023-06-07",
    "num_adults": 2,
    "num_children": 0,
    "guest_name": {
      "first_name": "Maria",
      "last_name": "Rodriguez"
    },
    "guest_contact_info": {
      "email": "mrodriguez@example.com",
      "phone": "777-4231",
      "address": {
        "city": "Paris",
        "country": "France"
      }
    },
    "total_cost": 650.00,
    "payment_status": "paid"
  })

#Task2: Insert one and get Key
content = {
    "reservation_id": "2",
    "hotel_id": "123",
    "room_id": "315",
    "checkin_date": "2023-06-15",
    "checkout_date": "2023-06-17",
    "num_adults": 1,
    "num_children": 0,
    "guest_name": {
      "first_name": "Ethan",
      "last_name": "Lee"
    },
    "guest_contact_info": {
      "email": "ethan.lee@example.com",
      "phone": "123-8106",
      "address": {
        "city": "Madrid",
        "country": "Spain"
      }
    },
    "total_cost": 350.00,
    "payment_status": "paid"
  }

document = collection.insertOneAndGet(content)
key = document.key
print('\n The key of the document is: ', key)



#Task 3: fetch by key
document = collection.find().key(key).getOne() 
content = document.getContent()                
print('\n The document is:')
print(content)

#Task 4: insertMany

all_documents=[
    {
    "reservation_id": "3",
    "hotel_id": "123",
    "room_id": "207",
    "checkin_date": "2023-06-25",
    "checkout_date": "2023-06-30",
    "num_adults": 2,
    "num_children": 0,
    "guest_name": {
      "first_name": "Olivia",
      "last_name": "Johnson"
    },
    "guest_contact_info": {
      "email": "olivia.johnson@example.com",
      "phone": "987-1890",
      "address": {
        "city": "Barcelona",
        "country": "Spain"
      }
    },
    "total_cost": 932.00,
    "payment_status": "pending"
  }
,

{
    "reservation_id": "4",
    "hotel_id": "123",
    "room_id": "222",
    "checkin_date": "2023-06-07",
    "checkout_date": "2023-06-17",
    "num_adults": 2,
    "num_children": 0,
    "guest_name": {
      "first_name": "Liam",
      "last_name": "Patel"
    },
    "guest_contact_info": {
      "email": "liam.patel@example.com",
      "phone": "123-8106",
      "address": {
        "city": "Malaga",
        "country": "Spain"
      }
    },
    "total_cost": 350.00,
    "payment_status": "paid"
  }

,

{
    "reservation_id": "5",
    "hotel_id": "123",
    "room_id": "101",
    "checkin_date": "2023-06-01",
    "checkout_date": "2023-06-05",
    "num_adults": 2,
    "num_children": 1,
    "guest_name": {
      "first_name": "John",
      "last_name": "Smith"
    },
    "guest_contact_info": {
      "email": "john.smith@example.com",
      "phone": "555-1234",
      "address": {
        "city": "Lyon",
        "country": "France"
      }
    },
    "additional_requests": [
      {
        "type": "extra_bed",
        "quantity": 1
      },
      {
        "type": "late_checkout",
        "details": "Please arrange for a 2pm checkout"
      }
    ],
    "total_cost": 800.00,
    "payment_status": "paid"
  }
  ,
    {
    "reservation_id": "6",
    "hotel_id": "123",
    "room_id": "305",
    "checkin_date": "2023-06-04",
    "checkout_date": "2023-06-20",
    "num_adults": 2,
    "num_children": 0,
    "guest_name": {
      "first_name": "Marcus",
      "last_name": "Wong"
    },
    "guest_contact_info": {
      "email": "marcus.wong@example.com",
      "phone": "123-1234",
      "address": {
        "city": "Nice",
        "country": "France"
      }
    },
    "total_cost": 1350.00,
    "payment_status": "cancelled"
  }
    
]
result_docs = collection.insertManyAndGet(all_documents)

#Task5: count all documents

total = collection.find().count()
print('\n My hotel has', total, 'reservations')


#Task 6: Find customers who didn't pay
documents = collection.find().filter({'payment_status': "pending"}).getDocuments()
print('\n Customers who didn\'t pay:')
for d in documents:
    content = d.getContent()
    print(content["guest_contact_info"])


#Task 7: Replace pending to paid 

new_content = {
    "reservation_id": "3",
    "hotel_id": "123",
    "room_id": "207",
    "checkin_date": "2023-06-25",
    "checkout_date": "2023-06-30",
    "num_adults": 2,
    "num_children": 0,
    "guest_name": {
      "first_name": "Olivia",
      "last_name": "Johnson"
    },
    "guest_contact_info": {
      "email": "olivia.johnson@example.com",
      "phone": "987-1890",
      "address": {
        "city": "Barcelona",
        "country": "Spain"
      }
    },
    "total_cost": 932.00,
    "payment_status": "paid"
    
  } 

to_modify_doc = collection.find().filter({'payment_status': "pending"}).getOne()
key=to_modify_doc.key
collection.find().key(key).replaceOne(new_content)

#Task 8: delete a cancelled reservation

deleted = collection.find().filter({'payment_status': "cancelled"}).remove()
print('\n Deleted', deleted, 'documents')
