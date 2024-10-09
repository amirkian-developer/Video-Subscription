from datetime import timedelta,datetime
from django.db import models
from django.contrib.auth.models import User




class VideoUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone   = models.CharField(max_length=15)
    balance = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)

    def __str__(self) -> str:
        return self.user.username


class License(models.Model):
    user = models.ForeignKey(VideoUser, on_delete=models.CASCADE, related_name='licenses')
    title = models.CharField(max_length=255)
    duration = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self) -> str:
        return self.user.user.username + " - " + self.title



class Subscription(models.Model):
    user = models.ForeignKey(VideoUser, on_delete=models.CASCADE, related_name='subscriptions')
    license = models.ForeignKey(License, on_delete=models.CASCADE, related_name='licensed')
    duration = models.PositiveIntegerField()
    start_date = models.DateField(auto_now_add=True)
    end_date   = models.DateField(null=True, blank=True)
    is_active  = models.BooleanField(default=True)

    def is_active(self):
        # return False
        if datetime.today().date() > self.end_date:
            return False
        return True

    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = datetime.today().date()
        self.end_date = self.start_date + timedelta(days=self.duration)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.user.__str__() + " - " + self.license.user.__str__()



class Video(models.Model):
    user = models.ForeignKey(VideoUser, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=255)
    description = models.TextField()
    file_url = models.URLField(null=True, blank=True)
    category = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_hide = models.BooleanField(default=False)

    def __str__(self):
        return self.user.__str__()+" - "+self.title



class WatchHistory(models.Model):
    user = models.ForeignKey(VideoUser, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    watched_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.__str__()+" - "+self.video.title



class Comment(models.Model):
    user = models.ForeignKey(VideoUser, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    text = models.TextField()


class Rate(models.Model):
    user = models.ForeignKey(VideoUser, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    rate = models.PositiveIntegerField()

    class Meta:
        unique_together = ('user', 'video')
