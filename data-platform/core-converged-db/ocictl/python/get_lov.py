import sys, json

data = json.loads(sys.argv[1])['data']

for c in data:
    print(c[sys.argv[2]])
