from pymongo import MongoClient 
import time   
import sys

client = MongoClient("mongodb://localhost:27017/")
database = client["sol"]
posts = database["posts"]  






num = 100

for i in range(num):
    print(posts.count())
    x = posts.insert_one(
        {
            "title": "program wrote" + str(posts.estimated_document_count() + 1),
            "author": "program",
            "content": "test",
            "url": posts.estimated_document_count() + 1,
            "time": time.strftime('%c', time.localtime(time.time())),
            "ip": "console"
        }
    )
client.close()
