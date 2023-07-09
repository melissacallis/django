from django.db import models

class Groceries(models.Model):
    item = models.CharField(max_length=100)
    list = models.TextField()

    def __str__(self):
        return self.item
