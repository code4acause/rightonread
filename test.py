from database import competitions_collection, books_collection,users_collection



p = books_collection.find()
for comp in p:
    print(comp)

users = users_collection.find()
for u in users:
    print(u)

joined_competitions = competitions_collection.find()
for comp in joined_competitions:
    print(comp['books'])