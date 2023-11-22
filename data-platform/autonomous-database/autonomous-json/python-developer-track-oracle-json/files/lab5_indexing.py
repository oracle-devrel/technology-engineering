import oracledb
import json

#connect with thick-client
oracledb.init_oracle_client()
connection = oracledb.connect(user="myapp",
                              password="YOUR_PASSWORD",
                              dsn="localhost:1521/FREEPDB1")
#auto commit
connection.autocommit = True

#Open collection for hotel reservations
soda = connection.getSodaDatabase()

collection = soda.openCollection("hotel_reservations")

#Task1: Create composite index

index_def = {
    'name': 'RESERVATION_INDEX',
    'fields': [
        {
            'path': 'reservation_id',
            'datatype': 'string',
            'order': 'asc'
        },
        {
            'path': 'room_id',
            'datatype': 'string',
            'order': 'asc'
        },

    ]
}
collection.createIndex(index_def)



#Task 2: Search Data Guide 
#text only text. text_value text and numbers
index_search_def ={ 
    "name"      : "SEARCH_AND_DATA_GUIDE_IDX",
    "dataguide" : "on",
    "search_on" : "text" }

collection.createIndex(index_search_def)

documents = collection.find().filter({"$textContains" : "check%"}).getDocuments()
print('\n Found the following documents talking about check:')
for d in documents:
    content = d.getContent()
    print(content)

#task3: Get Data Guide
data_guide= collection.getDataGuide().getContent()
print(json.dumps(data_guide, indent=1))