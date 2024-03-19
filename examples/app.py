from winkel.asgi import ASGIApp, Response


app = ASGIApp()

@app.router.register('/')
async def my_handler(scope):
    return Response(200, b'I was handled.')


app.finalize()