from io import BytesIO
from PIL import Image, UnidentifiedImageError
from rest_framework import serializers
from django.core.files.base import ContentFile

MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_DIMENSION = 6000
MAX_PHOTO_PIXELS = 25_000_000

class SafePhotoSerializer(serializers.Serializer):
    photo = serializers.FileField()
    def validate_photo(self, uploaded):
        if uploaded.size > MAX_PHOTO_BYTES:
            raise serializers.ValidationError("Photo must be 5 MB or smaller.")
        try:
            image = Image.open(uploaded)
            if image.format not in {"JPEG", "PNG", "WEBP"}:
                raise serializers.ValidationError("Upload a JPEG, PNG, or WebP image.")
            width, height = image.size
            if width < 100 or height < 100 or width > MAX_PHOTO_DIMENSION or height > MAX_PHOTO_DIMENSION or width * height > MAX_PHOTO_PIXELS:
                raise serializers.ValidationError("Image dimensions are outside the allowed range.")
            image.verify()
            uploaded.seek(0)
            image = Image.open(uploaded)
            image.load()
            if image.mode in ("RGBA", "LA") or "transparency" in image.info:
                rgba = image.convert("RGBA")
                background = Image.new("RGB", rgba.size, "white")
                background.paste(rgba, mask=rgba.getchannel("A"))
                sanitized = background
            else:
                sanitized = image.convert("RGB")
            sanitized.thumbnail((600, 750), Image.Resampling.LANCZOS)
            output = BytesIO()
            sanitized.save(output, format="JPEG", quality=85, optimize=True)
            if output.tell() > 512 * 1024:
                output = BytesIO()
                sanitized.save(output, format="JPEG", quality=72, optimize=True)
            if output.tell() > 512 * 1024:
                raise serializers.ValidationError("The optimized photo must be 512 KB or smaller.")
            uploaded.seek(0)
            return ContentFile(output.getvalue(), name="profile-photo.jpg")
        except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
            raise serializers.ValidationError("The uploaded file is not a valid supported image.")
