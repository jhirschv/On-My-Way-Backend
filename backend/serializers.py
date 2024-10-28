from rest_framework import serializers
from .models import User, Message, ChatSession, Task
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.utils.timesince import timesince
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.core.files.images import get_image_dimensions
import uuid

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        return token

class UserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='Username must be alphanumeric and can include underscores',
                code='invalid_username'
            ),
            MinLengthValidator(4, message="Username must be at least 4 characters long."),
            MaxLengthValidator(20, message="Username must be no longer than 20 characters.")
        ]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        style={'input_type': 'password'},
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9!@#$%^&*()_+=\[\]{};:\'"\\|,.<>\/?~-]+$',
                message="Password must consist of alphanumeric and special characters only."
            ),
            MinLengthValidator(8, message="Password must be at least 8 characters long."),
            MaxLengthValidator(20, message="Password must be no longer than 20 characters.")
        ]
    )
    email = serializers.EmailField()

    class Meta:
        model = User
        fields = ('username', 'password', 'email')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
    
class GuestRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        required=False,  # No longer required in the incoming request
        default='',
        validators=[
            RegexValidator(
                regex='^[a-zA-Z0-9_]+$',
                message='Username must be alphanumeric and can include underscores',
                code='invalid_username'
            ),
            MinLengthValidator(4, message="Username must be at least 4 characters long."),
            MaxLengthValidator(20, message="Username must be no longer than 20 characters.")
        ]
    )
    password = serializers.CharField(
        required=False,  # No longer required in the incoming request
        default='',
        write_only=True,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9!@#$%^&*()_+=\[\]{};:\'"\\|,.<>\/?~-]+$',
                message="Password must consist of alphanumeric and special characters only."
            ),
            MinLengthValidator(8, message="Password must be at least 8 characters long."),
            MaxLengthValidator(20, message="Password must be no longer than 20 characters.")
        ]
    )
    email = serializers.EmailField(read_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'email', 'guest')

    def validate(self, data):
        # Generate values
        data['username'] = f"guest_{uuid.uuid4().hex[:8]}"
        data['email'] = f"{data['username']}@example.com"
        data['password'] = uuid.uuid4().hex[:20]

        # Apply validators manually since these fields are read-only and would skip normal validation
        for validator in self.fields['username'].validators:
            validator(data['username'])
        for validator in self.fields['password'].validators:
            validator(data['password'])

        return data

    def create(self, validated_data):
        # Extract the plaintext password from validated data before creating the user
        plaintext_password = validated_data['password']

        # Create the user object
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=plaintext_password,  # Django hashes the password here
            guest=True
        )

         # Create or retrieve a ChatSession for the guest and John or user with ID 1
        john_user = User.objects.get(id=27)  # Assuming user with ID 1 exists and is John
        chat_session = ChatSession.objects.create()
        chat_session.participants.add(user, john_user)

        # Create an initial message in this chat session
        Message.objects.create(
            chat_session=chat_session,
            sender=john_user,
            content="Welcome to Discourse!"
        )

        # Return both the user object and the plaintext password
        return user, plaintext_password

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'id','profile_picture']
        extra_kwargs = {
            'profile_picture': {'required': False}
        }

    def validate_profile_picture(self, value):
        """
        Validates the uploaded image.
        - Checks that it is a JPEG, PNG, or MPO file by MIME type.
        - Ensures the file size does not exceed 2MB.
        """
        # Validate file type by MIME type
        valid_mime_types = ['image/jpeg', 'image/png', 'image/mpo']
        mime_type = value.content_type  # Directly access content_type
        print(f"File MIME type: {mime_type}")  # Log the MIME type
        if mime_type not in valid_mime_types:
            raise serializers.ValidationError("File must be a JPEG or PNG image.")

        # Validate file size
        if value.size > 10 * 1024 * 1024:  # 2MB limit
            raise serializers.ValidationError("Image file too large ( > 2MB ).")

        # Optionally, validate image dimensions
        width, height = get_image_dimensions(value)
        if width > 8000 or height > 8000:
            raise serializers.ValidationError("Image dimensions should not be greater than 4000x4000 pixels.")

        return value
    
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'user', 'task_name', 'description', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class ChatSessionSerializer(serializers.ModelSerializer):
    participants = UserSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    class Meta:
        model = ChatSession
        fields = ['id', 'created_at', 'participants', 'last_message']

    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-timestamp').first()  # Get the most recent message
        if last_message:
            time_since = timesince(last_message.timestamp).split(',')[0]  # Simplify to the most significant unit
            if last_message.sender == self.context['request'].user:
                return {"message": f"You: {last_message.content}", "timestamp": time_since, "exact_time": last_message.timestamp.isoformat(), "read": last_message.read, "id": last_message.id, "sender": "user"}
            else:
                return {"message": last_message.content, "timestamp": time_since, "exact_time": last_message.timestamp.isoformat(), "read": last_message.read, "id": last_message.id, "sender": "other_user"}
        return None