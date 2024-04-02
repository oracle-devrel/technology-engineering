import sys, json

data = json.load(sys.stdin)

for c in data:
        if (len(sys.argv) == 1 or sys.argv[1] == "--long" ):
                print(c['displayName']+":"+c['lifecycleState']+":"+c['id'])
        elif (sys.argv[1] == "--names" ):
                print(c['display-name'])
        else:
                print(c['id'])

