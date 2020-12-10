from django.contrib import admin

from .models import User, Post, Like


class PostAdmin(admin.ModelAdmin):
    display = ("content", "submitter", "posted_on")


class LikeAdmin(admin.ModelAdmin):
    display = ("user", "post")


admin.site.register(User)
admin.site.register(Post, PostAdmin)
admin.site.register(Like, LikeAdmin)
