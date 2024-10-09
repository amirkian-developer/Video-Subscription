from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import VideoUser, Subscription, Video, License, WatchHistory
from .serializers import *
from django.db.models import Q



def get_licensed_users(user:VideoUser):
    subscription_list = Subscription.objects.filter(user=user)
    users = []
    for sub in subscription_list:
        if sub.is_active():
            users.append(sub.license.user)
    return users


class WatchHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WatchHistory.objects.all()
    serializer_class = WatchHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.videouser
        return self.queryset.filter(user=user)


class VideoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user.videouser
        licensed_users = get_licensed_users(user)
        return self.queryset.filter(Q(user__in=licensed_users)&Q(is_hide=False))


    def retrieve(self, request, pk=None):
        video = self.get_object()
        user = request.user.videouser
        WatchHistory.objects.create(user=user, video=video)
        serializer = self.get_serializer(video)
        return Response(serializer.data)


    @action(detail=True, methods=['GET'])
    def get_views(self, request, pk):
        video = get_object_or_404(Video, pk=pk)
        views = WatchHistory.objects.filter(video=video).count()
        return Response({'views': views})


    @action(detail=True, methods=['GET'])
    def get_comments(self, request, pk):
        video = get_object_or_404(Video, pk=pk)
        comments = Comment.objects.filter(video=video)
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['GET'])
    def get_rates(self, request, pk):
        video = get_object_or_404(Video, pk=pk)
        rates = Rate.objects.filter(video=video)
        serializer = RateSerializer(rates, many=True)
        return Response(serializer.data)


    @action(detail=True, methods=['POST'])
    def new_comment(self, request, pk):
        text = request.data.get('text')
        if text == "" or text is None:
            return Response({'text': 'please fill text field.'})

        user = request.user.videouser
        video = get_object_or_404(Video, pk=pk)
        Comment.objects.create(user=user, video=video, text=text)

        return Response({'comment': 'The comment was registered.'})


    @action(detail=True, methods=['POST'])
    def new_rate(self, request, pk):
        rate = request.data.get('rate')
        if rate is None:
            return Response({'rate': 'please fill rate field.'})

        try:
            rate = int(rate)
            if rate < 0 or rate > 5:
                return Response({'rate': 'The rate must be between 0 and 5.'})
        except:
            return Response({'rate': 'Enter Integer.'})

        user = request.user.videouser
        video = get_object_or_404(Video, pk=pk)

        try:
            Rate.objects.create(user=user, video=video, rate=rate)
        except:
            return Response({'rate': 'You have already rated this video.'})

        return Response({'rate': 'The rate was registered.'})



class LicenseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = License.objects.all()
    serializer_class = LicenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.exclude(user__user__username=user.username)

    @action(detail=True, methods=['POST'])
    def buy_license(self, request, pk):
        user = request.user.videouser
        license = get_object_or_404(License, pk=pk)
        if user == license.user:
            return Response({'license': 'You cannot purchase your license.'})
        subscriptions = Subscription.objects.filter(
            Q(user=user) &
            Q(license__user=license.user)
        )
        if subscriptions.exists():
            if subscriptions.first().is_active():
                return Response({'license': 'You already have an active license for this user.'})
            else:
                for sub in subscriptions:
                    sub.delete()

        if user.balance < license.price:
            raise serializers.ValidationError({'license': 'Insufficient balance.'})
        user.balance -= license.price
        user.save()

        sub = Subscription.objects.create(user=user, license=license, duration=license.duration)

        return Response({'license': 'The license was successfully purchased.'})



class VideoUserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoUser.objects.all()
    serializer_class = VideoUserReadOnlySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return self.queryset.exclude(user__username=user.username)


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





