from .models import VideoUser,License
from rest_framework import generics
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import *



class ProfileListView(generics.ListAPIView):
    queryset = VideoUser.objects.all()
    serializer_class = VideoUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VideoUser.objects.all()
    serializer_class = VideoUserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)


class SignUpView(generics.CreateAPIView):
    queryset = VideoUser.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = SignUpSerializer


class ProfileAddBalanceView(generics.CreateAPIView):
    queryset = VideoUser.objects.all()
    serializer_class = AddBalanceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)
