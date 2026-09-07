from django.db import models

class Groceries(models.Model):
    item = models.CharField(max_length=100)
    list = models.TextField()

    def __str__(self):
        return self.item


class Favorite(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=255)
    image = models.URLField(max_length=500, blank=True, null=True)
    source_url = models.URLField(max_length=500, blank=True, null=True)
    ingredients = models.JSONField(default=list)
    directions = models.JSONField(default=list)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title
