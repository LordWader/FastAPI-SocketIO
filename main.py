import base64

import cv2
import uvicorn
import socketio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse


fast_app = FastAPI()
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*'
)
app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=fast_app,
    static_files={'/': './static/simple.html'}
)

rooms = set()
path_to_video = 'path/to/video'


async def background_task(room):
    """Example of how to send server generated events to clients."""
    cap = cv2.VideoCapture(path_to_video)
    while 1:
        ret, frame = cap.read()
        resized = cv2.resize(frame, (640, 480), interpolation = cv2.INTER_AREA)
        cnt = cv2.imencode('.jpg', frame)[1].tobytes()
        stringData = base64.b64encode(cnt).decode('utf-8')
        b64_src = 'data:image/jpg;charset=utf-8;base64,'
        stringData = b64_src + stringData
        await sio.emit('cv-data', {
            'image': stringData,
            'text': "img"}, room=room)


@sio.event
def connect(sid, environ):
    print("connect ", sid, environ)


@sio.event
async def join(sid, message):
    sio.enter_room(sid, message['room'])
    await sio.emit('my_response', {'data': 'Entered room: ' + str(message['room'])},
                   room=sid)
    if message['room'] != "2" and message['room'] not in rooms:
        rooms.add(message['room'])
        sio.start_background_task(background_task, message['room'])


@sio.event
async def chat_message(sid, data):
    print("message ", data)
    await sio.emit('reply', room=sid)


@sio.event
def disconnect(sid):
    print('disconnect ', sid)


@fast_app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return "Run!"


if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0", port=8000
    )
