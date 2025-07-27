from django.db import models

class NoticeManager(models.Manager):
    """Custom manager for Notice model with utility methods"""

    def published(self):
        """Return only published notices"""
        return self.filter(published=True)

    def recent_published(self, limit=5):
        """Return recent published notices"""
        return self.published().order_by('-date_created')[:limit]

    def search_published(self, query):
        """Search in published notices by title and content"""
        if not query:
            return self.published()

        return self.published().filter(
            models.Q(title__icontains=query) |
            models.Q(content__icontains=query)
        )