from django.contrib import admin

from .models import Post, Comment, PostLike, CommentLike

# Register your models here.


class PostAdmin(admin.ModelAdmin):
    list_display = ['author', 'caption', 'create_time', 'update_time']
    search_fields = ['caption', ]
    list_filter = ['author', 'create_time', 'update_time']


admin.site.register(Post, PostAdmin)
admin.site.register(Comment)
admin.site.register(PostLike)
admin.site.register(CommentLike)