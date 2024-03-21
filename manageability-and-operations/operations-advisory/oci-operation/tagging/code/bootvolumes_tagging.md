# execute query to get the boot volumes

```csharp
oci search resource structured-search \
--query-text "query   bootvolume resources sorted by timeCreated desc" --limit 1000 | \
jq -r '.data.items[] | "\(."defined-tags")\("|")\(."identifier")\("|")\(."display-name")"' > bootvolumes_info.csv

```



# load this to excel then update the the first column with the below pattern
```csharp
{ "TagNameSpace_1": {  "key1": "v1",  "key2": "v2" }, "TagNameSpace_2": { "key1": "v1" ,"key2": "v2"  } }
```


```csharp
## save end export the file as csv 
## copy the file to the remote linux
## run the below script to remove extra chars
 
sed 's/""/"/g' -i boot_volume_tags.csv
sed 's/,,//g' -i boot_volume_tags.csv
sed 's/,/|/g' -i boot_volume_tags.csv

cat boot_volume_tags.csv
```

# create a free_form tags files definition

```csharp
date_now=$(date +%m-%d-%y-%H-%M)
export date_now
cat<<EOF>free_form.json
{ 
 "updated_from":  "oci_cli",
 "updated_user":  "your_user_name",
 "updated_date": "$date_now" 
}
EOF

cat free_form.json
```



# run the below code to update your boot volume defined and free_form tags


```csharp
input=boot_volume_tags.csv
while IFS= read -r line
do
export DEFINED_TAG=`echo $line | awk -F '|' '{print $1}'`
export DEFINED_TAG=`echo $DEFINED_TAG | sed 's/^"//g' | sed 's/"$//g'`
export BV_OCID=`echo $line | awk -F '|' '{print $2}'`
echo $BV_OCID
echo $DEFINED_TAG
oci bv boot-volume update \
--boot-volume-id $BV_OCID \
--defined-tags $DEFINED_TAG \
--freeform-tags file://free_form.json  \
--force
done<$input

```



