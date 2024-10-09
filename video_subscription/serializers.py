from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User
from django.db.models import Q



class SignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoUser
        fields = ('username','password','email','first_name','last_name','phone')

    username   = serializers.CharField(write_only=True, required=True)
    password   = serializers.CharField(write_only=True, required=True)
    email      = serializers.EmailField(write_only=True, required=True)
    first_name = serializers.CharField(write_only=True, required=True)
    last_name  = serializers.CharField(write_only=True, required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError({'username': 'Username already taken.'})
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError({'email': 'Email already taken.'})
        return value

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
        )
        user.set_password(validated_data['password'])
        user.save()
        video_user = VideoUser.objects.create(user=user,phone=validated_data['phone'])
        return video_user


class VideoUserSerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(source='user.username')
    email = serializers.EmailField(source='user.email',)
    first_name = serializers.CharField(source='user.first_name',)
    last_name = serializers.CharField(source='user.last_name',)

    class Meta:
        model = VideoUser
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'phone', 'balance', 'url')
        read_only_fields = ['user', 'balance']
        extra_kwargs = {
            'url': {'view_name':'profile-detail', 'lookup_field':'pk'}
        }

    def validate_username(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(username=value).exists():
            raise serializers.ValidationError({'username': 'Username already taken.'})
        return value

    def validate_email(self, value):
        user = self.context['request'].user
        if User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError({'email': 'Email already taken.'})
        return value


    def update(self, value, validated_data):
        user = value
        user.user.username = validated_data['user']['username']
        user.user.email = validated_data['user']['email']
        user.user.first_name = validated_data['user']['first_name']
        user.user.last_name = validated_data['user']['last_name']
        user.phone = validated_data['phone']
        user.user.save()
        user.save()

        return user



class LicenseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = License
        fields = ['id', 'title', 'duration', 'price', 'url']


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'video', 'created_at', 'text']


class RateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rate
        fields = ['id', 'user', 'video', 'created_at', 'rate']


class WatchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WatchHistory
        fields = ['id', 'user', 'video', 'watched_at']


class VideoUserReadOnlySerializer(serializers.HyperlinkedModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    licenses = LicenseSerializer(many=True)

    class Meta:
        model = VideoUser
        fields = ('id', 'username', 'first_name', 'last_name', 'licenses', 'url')
        read_only_fields = ['user',]



class VideoSerializer(serializers.HyperlinkedModelSerializer):
    publisher = serializers.CharField(source='user.user.username', read_only=True)

    class Meta:
        model = Video
        fields = [
            'id', 'publisher', 'title', 'description', 'file_url', 'category',
            'created_at', 'updated_at', 'is_hide', 'url'
        ]
        extra_kwargs = {
            'url': {'view_name':'video-detail'}
        }


class SubscriptionSerializer(serializers.HyperlinkedModelSerializer):
    license = serializers.PrimaryKeyRelatedField(queryset=License.objects.all())
    license_title = serializers.CharField(source='license.title', read_only=True)
    license_user  = serializers.CharField(source='license.user', read_only=True)
    username = serializers.CharField(source='user.user.username', read_only=True)

    class Meta:
        model = Subscription
        fields = [
            'id', 'username', 'license', 'license_user', 'license_title', 'duration', 
            'start_date', 'end_date', 'is_active', 'url'
        ]
        read_only_fields = ['duration', 'start_date', 'end_date', 'is_active']
        extra_kwargs = {
            'url': {'view_name':'subscription-detail'}
        }


    def validate_license(self, value):
        request = self.context.get('request')
        user = request.user.videouser
        if user == value.user:
            raise serializers.ValidationError(
                {'license': 'You cannot purchase your license.'}
            )
        subscriptions = Subscription.objects.filter(
            Q(user=user) &
            Q(license__user=value.user)
        )
        if subscriptions.exists():
            if subscriptions.first().is_active():
                raise serializers.ValidationError(
                    {'license': 'You already have an active license for this user.'}
                )
            else:
                for sub in subscriptions:
                    sub.delete()

        if user.balance < value.price:
            raise serializers.ValidationError({'license': 'Insufficient balance.'})
        user.balance -= value.price
        user.save()

        return value


class ManageVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'description', 'file_url', 'category',
            'created_at', 'updated_at', 'is_hide', 'url'
        ]
        extra_kwargs = {
            'url': {'view_name':'manage-video-detail'}
        }


class ManageLicenseSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = License
        fields = ['id', 'title', 'duration', 'price', 'url']
        extra_kwargs = {
            'url': {'view_name':'manage-license-detail'}
        }
