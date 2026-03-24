# core/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from django.utils import timezone
from .models import Conversation, Message, MessageRead
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
            message_content = data.get('message', '')
            metadata = data.get('metadata') or {}
            message_kind = data.get('message_type', 'text')
            
            # Save message to DB
            message = await self.save_message(message_content, message_kind, metadata)
            if not message:
                return

            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message_broadcast',
                    'message_id': message.id if message else None,
                    'message': message.content,
                    'sender': self.user.username,
                    'timestamp': message.timestamp.isoformat(),
                    'message_type': message.message_type,
                    'metadata': message.metadata,
                    'attachments': []
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
        elif message_type == 'mark_messages_as_read':
            message_ids = data.get('message_ids', [])
            if message_ids:
                await self.mark_messages_read(message_ids)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'read_receipts_broadcast',
                        'message_ids': message_ids,
                        'read_by': self.user.username
                    }
                )

    # --- Handlers for group messages ---

    # Receive message from room group and send to WebSocket
    async def chat_message_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message_id': event.get('message_id'),
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
            'message_type': event.get('message_type', 'text'),
            'metadata': event.get('metadata', {}),
            'attachments': event.get('attachments', [])
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

    async def read_receipts_broadcast(self, event):
        await self.send(text_data=json.dumps({
            'type': 'messages_read',
            'message_ids': event['message_ids'],
            'read_by': event.get('read_by')
        }))

    async def reaction_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'reaction_update',
            'message_id': event['message_id'],
            'reactions': event['reactions']
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
    def save_message(self, message_content, message_kind='text', metadata=None):
        """
        Saves a new message to the database.
        """
        try:
            conversation = Conversation.objects.get(pk=self.conversation_id)
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=message_content,
                message_type=message_kind,
                metadata=metadata or {}
            )
            # Mark messages as read for the sender upon sending
            conversation.messages.filter(is_read=False).exclude(sender=self.user).update(is_read=True)
            return message
        except Conversation.DoesNotExist:
            return None

    @sync_to_async
    def mark_messages_read(self, message_ids):
        messages = Message.objects.filter(pk__in=message_ids, conversation_id=self.conversation_id)
        messages.update(is_read=True, read_at=timezone.now())
        MessageRead.objects.bulk_create(
            [MessageRead(message_id=message_id, user=self.user) for message_id in message_ids],
            ignore_conflicts=True
        )

