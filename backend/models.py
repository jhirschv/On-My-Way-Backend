from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from PIL import Image

# Create your models here.

class User(AbstractUser):
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    guest = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.profile_picture:
            img_path = self.profile_picture.path
            img = Image.open(img_path)
            if img.height != img.width:
                size = min(img.size)  # Ensuring the image is square
                left = (img.width - size) / 2
                top = (img.height - size) / 2
                right = (img.width + size) / 2
                bottom = (img.height + size) / 2
                img = img.crop((left, top, right, bottom))
                img.save(img_path)

    def __str__(self):
        return self.username
    
class ChatSession(models.Model):
    participants = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='chats', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatSession {self.pk}"

class Message(models.Model):
    chat_session = models.ForeignKey(ChatSession, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender} on {self.timestamp}"

