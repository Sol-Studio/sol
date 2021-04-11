import asyncio
import websockets
from pytz import timezone
from datetime import datetime
from pymongo import MongoClient
import time

client = MongoClient("mongodb://localhost:27017/")
people = 0

def get_log_date():
    dt = datetime.now(timezone("Asia/Seoul"))
    log_date = dt.strftime("%Y/%m/%d_%H:%M:%S")
    return log_date

async def accept(websocket, path):
    global people
    people += 1
    info = await websocket.recv()
    data = eval(info)
    i = 0
    while True:
        try:
            d = await websocket.recv()
            if d == "l":
                await websocket.send("%d" % people)
                try:
                    rd = list(client["chat"][data["room"]].find())[i]
                    if data["userid"] == rd["id"]:
                        z = "msg-self"
                    else:
                        z = ""

                    
                    await websocket.send("""<article class="msg-container %s"><div class="msg-box"><div class="flr"><div class="messages"><p class="msg">%s</p></div><span class="timestamp"><span class="username">%s</span>&bull;<span class="posttime">%s</span></span></div></div></article>""" % (z, rd["content"], rd["id"], rd["time"]))
                    
                    i += 1

                except IndexError:
                    await websocket.send("fail")

            else:
                d = eval(d)
                if d["content"] == "#command : !clear!":
                    client["chat"][data["room"]].delete_many({})
                
                else:
                    client["chat"][data["room"]].insert_one({
                        "id": data["userid"],
                        "time": get_log_date(),
                        "content": d["content"]
                    })
    
        except KeyboardInterrupt:
            exit()
        
        except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosedError):
            people -= 1
            break

start_server = websockets.serve(accept, "0.0.0.0", 2000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
