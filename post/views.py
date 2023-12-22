from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from post.models import Post, Comment, PostLike, CommentLike
from post.serializers import PostSerializer, CommentSerializer, PostLikeSerializer, CommentLikeSerializer
from shared.custom_pagination import CustomPagination


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.all()


class PostUserListApiView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, ]
    pagination_class = CustomPagination

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)


class PostCreateApiView(generics.CreateAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class PostRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    queryset = Post.objects.all()

    # def get_object(self):
    #     posts = Post.objects.filter(post__id=self.kwargs['pk'])
    #     return posts.first()

    def put(self, request, *args, **kwargs):
        try:
            post = self.get_object()
            if post.author == self.request.user:
                serializer = PostSerializer(post, data=request.data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                data = {
                    'success': True,
                    'message': "Post o'zgartirildi!",
                    'data': serializer.data
                }
                return Response(data, status=status.HTTP_200_OK)
            else:
                return Response({
                    'success': False,
                    'message': "Ruxsat yo'q"
                }, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            data = {
                'success': False,
                'message': "Post topilmadi!",
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, *args, **kwargs):
        try:
            post = self.get_object()
            if post.author == self.request.user:

                post.delete()
                data = {
                    'success': True,
                    'message': 'Post o\'chirildi',
                }
                return Response(data, status=status.HTTP_204_NO_CONTENT)
            else:
                data = {
                    'success': False,
                    'message': "O'chirishga ruxsat yo'q"
                }
                return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except Post.DoesNotExist:
            data = {
                'success': False,
                'message': "Post topilmadi!",
            }
            return Response(data, status=status.HTTP_404_NOT_FOUND)


class PostCommentApiListView(generics.ListAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny, ]
    queryset = Comment.objects.all()

    def get_queryset(self):
        post_id = self.kwargs['pk']
        return Comment.objects.filter(post__id=post_id)


class PostCommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, ]

    def perform_create(self, serializer):
        post_id = self.kwargs['pk']
        try:
            post = Post.objects.get(pk=post_id)
            serializer.save(author=self.request.user, post=post)
        except Post.DoesNotExist:
            return Response({
                'success': False,
                'message': "Bunday post yo'q",
            }, status=status.HTTP_404_NOT_FOUND)


class PostLikesListApiViw(generics.ListAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    serializer_class = PostLikeSerializer

    def get_queryset(self):
        post_id = self.kwargs['pk']
        return PostLike.objects.filter(post__id=post_id)


class PostLikeCreateApiView(APIView):
    permission_classes = [IsAuthenticated, ]
    serializer_class = PostLikeSerializer

    def post(self, request, *args, **kwargs):
        post_id = self.kwargs['pk']
        try:
            like = PostLike.objects.get(post__id=post_id)
            like.delete()
            data = {
                'success': True,
                'message': 'Like o\'chirildi!',
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except PostLike.DoesNotExist:
            post = Post.objects.get(pk=post_id)
            like = PostLike.objects.create(author=self.request.user, post=post)
            serializer = self.serializer_class(data=like)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            data = {
                'success': True,
                'message': "Like bosildi!",
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)


class CommentLikeCreateApiView(APIView):
    permission_classes = [IsAuthenticated, ]

    def post(self, request, *args, **kwargs):
        comment_id = self.kwargs['pk']
        try:
            comment_like = CommentLike.objects.get(comment__id=comment_id)
            comment_like.delete()
            data = {
                'success': True,
                'message': 'Comment like o\'chirildi!',
            }
            return Response(data, status=status.HTTP_204_NO_CONTENT)
        except CommentLike.DoesNotExist:
            comment = Comment.objects.get(pk=comment_id)
            comment_like = CommentLike.objects.create(author=self.request.user, comment=comment)
            serializer = CommentLikeSerializer(comment_like)
            data = {
                'success': True,
                'message': "Commentga like bosildi!",
                'data': serializer.data
            }
            return Response(data, status=status.HTTP_201_CREATED)