from django.db import models

from apps.account_manager.models.user import User

class Agent(models.Model):
    user = models.OneToOneField(User, related_name='agent', on_delete=models.CASCADE, blank=True, null=True)
    type = models.CharField(max_length=255)

    def __str__(self):
        if self.user:
            return f"{self.user.name}"
        else:
            return f"{self.id}"
        
    class Meta:
        # ordering = ['-created_at']
        verbose_name_plural = "       Agents"
        db_table = 'agents'