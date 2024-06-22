from django.db import models

class ClauseCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
    class Meta:
        # ordering = ['-status_changed_at']
        verbose_name_plural = "       Clause Categories"
        db_table = 'clause_categories'