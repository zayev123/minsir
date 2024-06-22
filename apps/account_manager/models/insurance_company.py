from django.db import models

class InsuranceCompany(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    address_area = models.TextField()
    rating = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    class Meta:
        # ordering = ['-created_at']
        verbose_name_plural = "       Insurance Companies"
        db_table = 'insurance_companies'