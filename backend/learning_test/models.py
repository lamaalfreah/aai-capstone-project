from django.db import models

class LearningTestSession(models.Model):
    AGE_CHOICES = [
        ('under15', 'أصغر من 15'),
        ('15plus', 'أكبر من 15'),
    ]

    age_group = models.CharField(max_length=20, choices=AGE_CHOICES, blank=True)
    learning_style = models.CharField(max_length=50, blank=True)
    ai_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.learning_style or "Running"} - {self.created_at:%Y-%m-%d}'

class LearningAnswer(models.Model):
    session = models.ForeignKey(LearningTestSession, on_delete=models.CASCADE, related_name='answers')
    question_order = models.PositiveIntegerField()
    question_text = models.TextField()
    answer = models.CharField(max_length=20)

    class Meta:
        ordering = ['question_order']
        unique_together = ('session', 'question_order')
