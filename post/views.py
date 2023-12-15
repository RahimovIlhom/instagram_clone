from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from post.serializers import PostSerializer


# Create your views here.


class PostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]
