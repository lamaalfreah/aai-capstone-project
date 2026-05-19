from django.db import models


class ChatSession(models.Model):
    title = models.CharField(max_length=100, default="محادثة جديدة")
    session_key = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
        null=True,
        blank=True
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField(blank=True)
    attachment = models.FileField(upload_to='chat_uploads/', blank=True, null=True)
    learning_style = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Stores generated files/images/audio paths and service information.
    metadata = models.JSONField(default=dict, blank=True)

    # True when this message contains transformed educational content.
    # The assessment button appears only for this type of message.
    is_learning_output = models.BooleanField(default=False)
    
    class Meta:
            ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"