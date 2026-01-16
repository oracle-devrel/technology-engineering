import random
import array
 
# declare arrays of the character that we need in out password
# Represented as chars to enable easy string concatenation
DIGITS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
LOCASE_VOYELS = ['a', 'e', 'i', 'o', 'u', 'y']
LOCASE_CONSONANT = [ 'b', 'c', 'd', 'f', 'g', 'h', 'j', 'k', 'm', 'n', 'p', 'q', 'r', 's', 't', 'v', 'w', 'x', 'z']
UPCASE_VOYELS = ['A', 'E', 'I', 'O', 'U', 'Y']
UPCASE_CONSONANT = [ 'B', 'C', 'D', 'F', 'G', 'H', 'J', 'K', 'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'X', 'Z']
# Only special characters supported by DB System
SYMBOLS = ['#', '_', '-']
 
# combines all the character arrays above to form one array
COMBINED_LIST = DIGITS + UPCASE_VOYELS + UPCASE_CONSONANT + LOCASE_VOYELS + LOCASE_CONSONANT + SYMBOLS
 
# Combine the character randomly selected above
# We want a 14-character password
p =  random.choice(LOCASE_CONSONANT) + random.choice(LOCASE_VOYELS) + random.choice(LOCASE_CONSONANT) + random.choice(LOCASE_VOYELS) + random.choice(LOCASE_CONSONANT) + random.choice(LOCASE_VOYELS) 
p += random.choice(UPCASE_CONSONANT) + random.choice(UPCASE_VOYELS) + random.choice(UPCASE_CONSONANT) + random.choice(UPCASE_VOYELS)
p += random.choice(DIGITS) + random.choice(DIGITS)  
p += random.choice(SYMBOLS) + random.choice(SYMBOLS) 
       
# print out password
print(p)