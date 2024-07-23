import os
import time

print('Hello World!\n')

time.sleep(3)

print(f'Hello {os.environ.get('TEST_NAME', 'UNKNOWN')}')

time.sleep(3)

print('Job Done!')