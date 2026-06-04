# Usage: python openapi_list.py <filename>
# /app/dept
# /app/info
# Usage: python openapi_list.py <filename> <url_prefix>
# Rest DB API: $URL_PREFIX/app/dept
# Rest Info API: $URL_PREFIX/app/info

import yaml, sys

filename = sys.argv[1];
url_prefix = ""
if len(sys.argv)>2:
  url_prefix = sys.argv[2];

with open(filename, "r") as stream:
    try:
        data = yaml.safe_load(stream)
        for key, value in data["paths"].items():
            if url_prefix != "":
                print("- " + str(value["get"]["summary"]) +": " + url_prefix + str(key))     
            else:
                print(str(key))        
    except yaml.YAMLError as exc:
        print(exc)