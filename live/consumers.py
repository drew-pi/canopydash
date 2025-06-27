from channels.generic.websocket import AsyncWebsocketConsumer

import json

class ProgressConsumer(AsyncWebsocketConsumer):

    # Called when a client establishes a WebSocket connection
    async def connect(self):
        # extract task ID from the URL route ( /ws/progress/<task_id>/)
        self.task_id = self.scope["url_route"]["kwargs"]["task_id"]

        # create group name unique to this task ID
        self.group   = f"progress_{self.task_id}"

        # register this socket connection (self.channel_name) with the group
        await self.channel_layer.group_add(self.group, self.channel_name)

        # accepts the WebSocket connection (just the required handshake step)
        await self.accept()

    # called when websocket disconnects (tab closed)
    async def disconnect(self, close_code):

        # remove from group to clean up
        await self.channel_layer.group_discard(self.group, self.channel_name)

    # custom handler for messages sent to the group with type='update' (i.e used by celery)
    async def update(self, event):

        # send the event data (progress percent and status)
        await self.send(text_data=json.dumps(event["data"]))