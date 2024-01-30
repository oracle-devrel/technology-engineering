import sys, json

data = json.load(sys.stdin)['data']

for c in data:
        fsize = round(c['size']/(1024),3)
        print (c['name'].ljust(30,' ')+" "+c['time-modified'][:19].ljust(25,' ')+f'{fsize:.3f}'.rjust(10)+" KB")



