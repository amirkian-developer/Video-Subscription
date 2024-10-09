from django.contrib import admin
from django.urls import path, include
from video_subscription.views import *
from video_subscription.viewsets import *
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, 'subscription')
router.register(r'videos', VideoViewSet, 'video')
router.register(r'watch-history', WatchHistoryViewSet)
router.register(r'manage/videos', ManageVideoViewSet, 'manage-video')
router.register(r'manage/licenses', ManageLicenseViewSet, 'manage-license')
router.register(r'users', VideoUserViewSet, )
router.register(r'licenses', LicenseViewSet, )


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include(router.urls)),

    path('api/signup/', SignUpView.as_view(), name='auth_signup'),
    path('api/profile/', ProfileListView.as_view(), name='profile'),
    path('api/profile/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
]


