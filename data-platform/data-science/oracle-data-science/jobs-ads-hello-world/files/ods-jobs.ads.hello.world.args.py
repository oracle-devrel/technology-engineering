import time
import argparse

# Read in command line argument
parser = argparse.ArgumentParser()
parser.add_argument('-g', '--greeting', required=False, default='Mystery Person')
args = parser.parse_args()


print(f'Hello {args.greeting}!\n')

time.sleep(3)

print('Job Done!\n')