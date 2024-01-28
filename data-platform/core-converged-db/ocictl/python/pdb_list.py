import sys, json

data = json.load(sys.stdin)['data']

for c in data:
        print (" db: "+c['pdb-name']+":"+c['open-mode']+":"+c['connection-strings']['pdb-default'].split("/",1)[1])
        print (" id: "+c['id'])
        print ("")



