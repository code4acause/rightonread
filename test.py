from database import competitions_collection

joined_competitions = competitions_collection.find()
for comp in joined_competitions:
    print(comp)