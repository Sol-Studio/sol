import asyncio
import websockets
from pytz import timezone
from datetime import datetime

chat = [
    {
        "id":"공지",
        "time": "공지",
        "content": "server started"
    }
]
def get_log_date():
    dt = datetime.now(timezone("Asia/Seoul"))
    log_date = dt.strftime("%Y%m%d_%H:%M:%S")
    return log_date

async def accept(websocket, path):
    while True:
        try:
            data = await websocket.recv()
            print("receive : " + data)
            if data[0] == "l":
                data = eval(data[1:])
                room = data["room"]
                id_ = data["id"]
                try:
                    rd = chat[id_]
                    if data["userid"] == rd["id"]:
                        z = "msg-self"
                    else:
                        z = ""

                    

                    await websocket.send(
                        """<article class="msg-container %s">
                            <div class="msg-box">
                                <div class="flr">
                                    <div class="messages">
                                        <p class="msg">%s</p>
                                    </div>
                                    <span class="timestamp">
                                        <span class="username">%s</span>&bull;
                                        <span class="posttime">%s</span>
                                    </span>
                                </div>
                            </div>
                            </article>""" % (z, rd["content"], rd["id"], rd["time"]))

                except IndexError as e:
                    await websocket.send("fail")


            elif data[0] == "s":
                data1 = eval(data[1:])
                chat.append({
                    "id": data1["userid"],
                    "time": get_log_date(),
                    "content": data1["content"]
                })

    
        except KeyboardInterrupt:
            exit()
        
        except Exception as e:
            break

start_server = websockets.serve(accept, "0.0.0.0", 2000)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()


