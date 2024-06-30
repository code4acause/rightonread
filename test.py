from database import competitions_collection, books_collection

#joined_competitions = competitions_collection.find()
#for comp in joined_competitions:
#    print(comp)

p = books_collection.find()
for comp in p:
    print(comp)