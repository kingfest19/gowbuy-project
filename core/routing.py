# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import Conversation, Message
from authapp.models import CustomUser

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        # Check if the user is authenticated and part of the conversation
        if self.user.is_anonymous or not await self.is_user_participant():
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Broadcast that this user is now online
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': self.user.username,
                'is_online': True
            }
        )

    async def disconnect(self, close_code):
        # Broadcast that this user has gone offline
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'username': self.user.username,
                'is_online': False
            }
        )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'chat_message':
            message_content = data['message']
            
            # Save message to DB
            message = await self.save_message(message_content)

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message': message.content,
                    'sender': self.user.username,
                    'timestamp': message.timestamp.isoformat()
                }
            )
        elif message_type == 'typing':
            # Broadcast typing status
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_status',
                    'username': self.user.username,
                    'is_typing': data['is_typing']
                }
            )

    # --- Handlers for group messages ---

    # Receive message from room group and send to WebSocket
    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))

    # Receive typing status from room group
    async def typing_status(self, event):
        # Don't send typing notification to the user who is typing
        if event['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'username': event['username'],
                'is_typing': event['is_typing']
            }))

    # Receive user online/offline status from room group
    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'username': event['username'],
            'is_online': event['is_online']
        }))

    # --- Database Helpers ---

    @sync_to_async
    def is_user_participant(self):
        """
        Checks if the user in scope is a participant of the conversation.
        """
        try:
            conversation = Conversation.objects.get(pk=self.conversation_id)
            return conversation.participants.filter(pk=self.user.pk).exists()
        except Conversation.DoesNotExist:
            return False

    @sync_to_async
    def save_message(self, message_content):
        """
        Saves a new message to the database.
        """
        try:
            conversation = Conversation.objects.get(pk=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=message_content
            )
            # Mark messages as read for the sender upon sending
            conversation.messages.filter(is_read=False).exclude(sender=self.user).update(is_read=True)
            return message
        except Conversation.DoesNotExist:
            return None

