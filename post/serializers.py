from rest_framework import serializers

from post.models import Post, PostLike, Comment, CommentLike
from users.models import User


class UserSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'photo', 'user_role']


class PostSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    post_likes_count = serializers.SerializerMethodField('get_post_likes_count')
    post_comment_count = serializers.SerializerMethodField('get_post_comment_count')
    me_like = serializers.SerializerMethodField('get_me_like')
    post_saved_count = serializers.SerializerMethodField('get_post_saved_count')

    class Meta:
        model = Post
        fields = [
            'id',
            'author',
            'image',
            'caption',
            'create_time',
            'post_likes_count',
            'post_comment_count',
            'me_like',
            'post_saved_count',
        ]

    def get_post_likes_count(self, obj):
        return obj.likes.count()

    def get_post_comment_count(self, obj):
        return obj.comments.count()

    def get_me_like(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            try:
                like = PostLike.objects.get(author=request.user, post=obj)
                return True
            except:
                return False
        return False

    def get_post_saved_count(self, obj):
        return obj.saves.count()


class CommentSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)
    comment_like_count = serializers.SerializerMethodField('get_comment_like_count')
    me_like = serializers.SerializerMethodField('get_me_like')
    replises = serializers.SerializerMethodField('get_replises')

    class Meta:
        model = Comment
        fields = ['id', 'author', 'comment', 'create_time', 'comment_like_count', 'me_like', 'replises']

    def get_comment_like_count(self, obj):
        return obj.likes.count()

    def get_me_like(self, obj):
        request = self.context.get('request', None)
        if request and request.user.is_authenticated:
            try:
                like = CommentLike.objects.get(author=request.user, comment=obj)
                return True
            except:
                return False
        return False

    def get_replises(self, obj):
        replises = self.__class__(obj)
        return replises

# if obj.child.exists():
#     serializers = self.__class__(obj.child.all(), many=True, context=self.context)
#     return serializers.data
# else:
#     return None


class PostLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = PostLike
        fields = ['id', 'author']


class CommentLikeSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    author = UserSerializer(read_only=True)

    class Meta:
        model = CommentLike
        fields = ['id', 'author']
