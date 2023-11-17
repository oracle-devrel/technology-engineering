import oracledb

#thick mode for SODA
oracledb.init_oracle_client()

#connection details
connection = oracledb.connect(user="myapp",password="PassworD123##",dsn="localhost:1521/FREEPDB1")

#connect, create and list collections
soda = connection.getSodaDatabase()
collection1 =soda.createCollection("my_first_collection")
collection2= soda.createCollection("my_second_collection")
list=soda.getCollectionNames()
print(list)

#delete one collection
collection2.drop()

list=soda.getCollectionNames()
print(list)