from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import VideoUser, Subscription, Video, License, WatchHistory
from .serializers import VideoSerializer, SubscriptionSerializer
from .serializers import ManageVideoSerializer, ManageLicenseSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied



def get_licensed_users(user:VideoUser):
    subscription_list = Subscription.objects.filter(user=user)
    users = []
    for sub in subscription_list:
        if sub.is_active():
            users.append(sub.license.user)
    return users


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.videouser
        licensed_users = get_licensed_users(user)
        return self.queryset.filter(user__in=licensed_users)


    def retrieve(self, request, pk=None):
        video = self.get_object()
        user = request.user.videouser
        WatchHistory.objects.create(user=user, video=video)
        serializer = self.get_serializer(video)
        return Response(serializer.data)


class SubscriptionViewSet(viewsets.ModelViewSet):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]


    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def get_queryset(self):
        return self.queryset.filter(user__user=self.request.user)

    def perform_create(self, serializer):
        license = serializer.validated_data['license']
        serializer.save(user=self.request.user.videouser, duration=license.duration)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, pk=None):
        try:
            subscription = Subscription.objects.get(pk=pk)

            user = self.request.user.videouser
            if user.balance < subscription.license.price:
                return Response({'detail': 'Insufficient balance.'}, status=status.HTTP_400_BAD_REQUEST)
            user.balance -= subscription.license.price
            user.save()

            subscription.duration += subscription.license.duration
            subscription.save()
            return Response({"status": "Subscription renewed"}, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({"error": "Subscription not found"}, status=status.HTTP_404_NOT_FOUND)

    def partial_update(self, request, *args, **kwargs):
        raise PermissionDenied("You are not allowed to edit this subscription.")


class ManageVideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = ManageVideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user.videouser)


class ManageLicenseViewSet(viewsets.ModelViewSet):
    queryset = License.objects.all()
    serializer_class = ManageLicenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user.videouser)


