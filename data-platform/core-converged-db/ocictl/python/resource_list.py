import sys, json

data = json.load(sys.stdin)['data']

for c in data:
        if (len(sys.argv) == 1 or sys.argv[1] == "--long" ):
                print(c['display-name']+":"+c['lifecycle-state']+":"+c['id'])
        elif (sys.argv[1] == "--names" ):
                print(c['display-name'])
        else:
                print(c['id'])

