from django.contrib.auth.models import AbstractUser
from django.db import models
from django import forms


class User(AbstractUser):
    following = models.ManyToManyField("User", related_name="followers")
    pass

    def __str__(self):
        return self.username


class Post(models.Model):
    content = models.TextField(max_length=500, default="empty")
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    posted_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.submitter.username} - {self.content[:20]}"


class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        null=False, related_name="likes")

    def __str__(self):
        return f"{self.user.username} - {self.post.content[:30]}"
