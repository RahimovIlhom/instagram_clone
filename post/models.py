from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import FileExtensionValidator, MaxLengthValidator
from django.db.models import UniqueConstraint

from shared.models import BaseModel


User = get_user_model()


class Post(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    image = models.ImageField(upload_to='post_images/', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])
    ])
    caption = models.TextField(validators=[MaxLengthValidator(1000)])

    class Meta:
        db_table = 'posts'

    def __str__(self):
        return f"{self.author.fullname} for post {self.caption}"


class Comment(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField(validators=[MaxLengthValidator(255)])
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        related_name='childs',
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.author} - {self.comment}"


class PostLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'post'],
                name='PostLikeUnique'
            )
        ]


class CommentLike(BaseModel):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='likes')

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=['author', 'comment'],
                name='CommentLikeUnique'
            )
        ]


class SavePost(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved')
    post = models.ManyToManyField(to=Post, related_name='saves')
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.user} - {self.name}"
