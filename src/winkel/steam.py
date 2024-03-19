class Stream:

    def __init__(self, receive, event):
        self.needs_reading = True
        self.is_being_read = False
        self._receive = receive

        if 'body' in event:
            chunk = event['body']
        else:
            chunk = b''

        self._buffer = chunk

        if event:
            if not ('more_body' in event and event['more_body']):
                self.needs_reading = False

    async def content(self):
        if not self.needs_reading:
            raise RuntimeError('Read disallowed.')

        if self.is_being_read:
            raise RuntimeError('This stream is already being read.')

        self.is_being_read = True

        if self._buffer:
            next_chunk = self._buffer
            self._buffer = b''
            yield next_chunk

        while self.needs_reading:
            event = await self._receive()
            try:
                next_chunk = event['body']
            except KeyError:
                pass
            else:
                if next_chunk:
                    yield next_chunk

            if not event.get('more_body'):
                self.needs_reading = False

    def __aiter__(self):
        return self.content()

    async def drain(self):

        if self.needs_reading:
            raise ValueError('This stream was already read entirely.')

        self._buffer = b''

        while self.needs_reading:
            event = await self._receive()
            if event['type'] == 'http.disconnect':
                self.needs_reading = False
            else:
                if not ('more_body' in event and event['more_body']):
                    self.needs_reading = 0

            del event
