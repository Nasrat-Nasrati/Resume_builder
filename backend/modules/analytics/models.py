from django.db import models


class PageViewDaily(models.Model):
    page_date = models.DateField()
    path = models.CharField(max_length=32)
    view_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["page_date", "path"], name="unique_daily_public_page_views")]
        indexes = [models.Index(fields=["page_date", "path"], name="daily_page_view_date_idx")]
