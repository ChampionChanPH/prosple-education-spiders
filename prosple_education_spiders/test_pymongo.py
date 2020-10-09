from fuzzywuzzy import process, fuzz
from mongodb import get_terms

term = get_terms()
print(term)
print("Count: " + str(len(term)))

ratio = process.extract('early education teaching', term, limit=3, scorer=fuzz.token_sort_ratio)
print(ratio)