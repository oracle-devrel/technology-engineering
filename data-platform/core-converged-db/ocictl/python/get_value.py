import sys, json

data = json.loads(sys.argv[1])['data']

print(data[sys.argv[2]])
