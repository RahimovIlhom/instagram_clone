from django.urls import path

from post.views import PostListView, PostUserListApiView, PostCreateApiView, PostRetrieveUpdateDeleteView, \
    PostCommentApiListView, PostCommentCreateView, PostLikesListApiViw, PostLikeCreateApiView, CommentLikeCreateApiView

urlpatterns = [
    path('list/', PostListView.as_view()),
    path('list/me/', PostUserListApiView.as_view()),
    path('create/', PostCreateApiView.as_view()),
    path('<uuid:pk>/', PostRetrieveUpdateDeleteView.as_view()),
    path('<uuid:pk>/comments/', PostCommentApiListView.as_view()),
    path('<uuid:pk>/comments/create/', PostCommentCreateView.as_view()),

    path('<uuid:pk>/likes/', PostLikesListApiViw.as_view()),
    path('<uuid:pk>/likes/like/', PostLikeCreateApiView.as_view()),

    path('comments/<uuid:pk>/like/', CommentLikeCreateApiView.as_view()),
]
