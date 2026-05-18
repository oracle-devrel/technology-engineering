import ujson as json
import ast
'''
@author jasperan
this script reads finance_data.json, and changes the format to 
adapt to what OCI Generative AI Service expects, an object with type
{
    'prompt': str(),
    'completion': str(),
    'url': str()
}
'''

# this list will store all objects before writing into the output file.
json_list = list()

with open('../data/finance_data.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

    for x in data:
        # this is the new structure we want to use for OCI Generative AI Service
        new_object =  {
            "prompt": x['instruction'].replace("""'""", """""").strip(),
            "completion": x['output'].replace("""'""", """""").strip()     
        }
        json_list.append(new_object)

print('Converting {} prompt-response pairs'.format(len(json_list)))
# for every element in json_list, write everything into a txt file line by line
with open('../data/output.jsonl', 'w', encoding='utf-8') as output_file:
    for x in json_list:
        # avoid those elements with non-utf8 characters. e.g. 🐥
        # we have a huge dataset so these cases are not that important.
        try:
            output_file.write("{}\n".format(json.dumps(x)))
        except Exception as e:
            print(e)
            pass