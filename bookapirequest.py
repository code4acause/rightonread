import requests

def list_bookshelf_volumes(bookshelf_id):
    url = f"https://www.googleapis.com/books/v1/users/[enteruserhere]/bookshelves/1018/volumes?source=1080/"
    params = { "maxResults": 200 }
    response = requests.get(url, params=params)
    volumes = response.json().get("items", [])
    for volume in volumes:
        print(volume["volumeInfo"]["title"])

list_bookshelf_volumes('1018')
