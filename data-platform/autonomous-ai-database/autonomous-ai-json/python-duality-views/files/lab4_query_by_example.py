import oracledb


#connect with thick-client
oracledb.init_oracle_client()

# === PLEASE CHANGE YOUR_PASSWORD  TO A REAL PASSWORD! ===
connection = oracledb.connect(user="myapp",
                              password="YOUR_PASSWORD",
                              dsn="localhost:1521/FREEPDB1")
#auto commit
connection.autocommit = True

#Open collection for hotel reservations
soda = connection.getSodaDatabase()

collection = soda.openCollection("hotel_reservations")


#Get reservations with children
print("\n Reservations with children:")
documents = collection.find().filter({'num_children': {"$gt" : 0}}).getDocuments()
for d in documents:
    content = d.getContent()
    print("Number of children:",content["num_children"],". Contact:",content["guest_contact_info"])


#Look for specific reservation using email
print("\n Reservations found using email:")
documents = collection.find().filter({'guest_contact_info.email': {'$like': 'john%'}}).getDocuments()
for d in documents:
    content = d.getContent()
    print("Reservation number:",content["reservation_id"],". Contact:",content["guest_contact_info"])


#check in specific day
print("\n Reservations found for check in at specific date:")
documents = collection.find().filter({ "checkin_date" : { "$date" : {"$gt":"2023-06-15"} } }).getDocuments()
for d in documents:
    content = d.getContent()
    print("Reservation number:",content["reservation_id"],". Contact:",content["guest_contact_info"])


#look for reservations from Nice and Paris

print("\n Give all the reservations with customers from Malaga and Paris:")
documents = collection.find().filter({'guest_contact_info.address.city': {"$in" : ["Malaga", "Paris"]}}).getDocuments()
for d in documents:
    content = d.getContent()
    print("Reservation number:",content["reservation_id"],". Contact:",content["guest_contact_info"])

