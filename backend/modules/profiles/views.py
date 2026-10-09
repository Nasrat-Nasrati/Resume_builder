from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import CareerProfile
from .serializers import CareerProfileSerializer

class CareerProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = CareerProfileSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_object(self):
        profile, _created = CareerProfile.objects.get_or_create(user=self.request.user)
        return profile

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Experience
from .serializers import ExperienceSerializer, ExperienceReorderSerializer

class ExperienceViewSet(viewsets.ModelViewSet):
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Experience.objects.filter(profile__user=self.request.user).select_related("profile")

    def perform_create(self, serializer):
        profile, _created = CareerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        serializer = ExperienceReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        items = list(self.get_queryset().filter(id__in=ids))
        if len(items) != len(ids):
            return Response({"detail": "One or more experience records were not found.", "code": "not_found", "fields": {}}, status=status.HTTP_404_NOT_FOUND)
        by_id = {item.id: item for item in items}
        with transaction.atomic():
            for index, item_id in enumerate(ids):
                Experience.objects.filter(pk=item_id, profile__user=request.user).update(sort_order=index)
        return Response(self.get_serializer([by_id[item_id] for item_id in ids], many=True).data)

from rest_framework.decorators import action
from .models import EducationRecord
from .serializers import EducationRecordSerializer

class EducationRecordViewSet(viewsets.ModelViewSet):
    serializer_class = EducationRecordSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return EducationRecord.objects.filter(profile__user=self.request.user).select_related("profile")
    def perform_create(self, serializer):
        profile, _created = CareerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)

    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        serializer = ExperienceReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        items = list(self.get_queryset().filter(id__in=ids))
        if len(items) != len(ids):
            return Response({"detail": "One or more education records were not found.", "code": "not_found", "fields": {}}, status=status.HTTP_404_NOT_FOUND)
        by_id = {item.id: item for item in items}
        with transaction.atomic():
            for index, item_id in enumerate(ids):
                EducationRecord.objects.filter(pk=item_id, profile__user=request.user).update(sort_order=index)
        return Response(self.get_serializer([by_id[item_id] for item_id in ids], many=True).data)
    @action(detail=False, methods=["get"], url_path="institutions")
    def institutions(self, request):
        query = str(request.query_params.get("q", "")).strip()
        if len(query) < 2:
            return Response([])
        results = self.get_queryset().filter(institution__icontains=query).values_list("institution", flat=True).distinct()[:10]
        return Response(list(results))

from .models import LanguageEntry, SkillGroup
from .serializers import LanguageEntrySerializer, SkillGroupSerializer, SkillSerializer
from .models import Skill

class LanguageEntryViewSet(viewsets.ModelViewSet):
    serializer_class = LanguageEntrySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return LanguageEntry.objects.filter(profile__user=self.request.user).select_related("profile")
    def perform_create(self, serializer):
        profile, _created = CareerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)

class SkillGroupViewSet(viewsets.ModelViewSet):
    serializer_class = SkillGroupSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return SkillGroup.objects.filter(profile__user=self.request.user).prefetch_related("skills")
    def perform_create(self, serializer):
        profile, _created = CareerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)
    @action(detail=False, methods=["post"], url_path="reorder")
    def reorder(self, request):
        serializer = ExperienceReorderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["ids"]
        items = list(self.get_queryset().filter(id__in=ids))
        if len(items) != len(ids):
            return Response({"detail": "One or more skill groups were not found.", "code": "not_found", "fields": {}}, status=status.HTTP_404_NOT_FOUND)
        by_id = {item.id: item for item in items}
        with transaction.atomic():
            for index, item_id in enumerate(ids):
                SkillGroup.objects.filter(pk=item_id, profile__user=request.user).update(sort_order=index)
        return Response(self.get_serializer([by_id[item_id] for item_id in ids], many=True).data)

class SkillViewSet(viewsets.ModelViewSet):
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Skill.objects.filter(group__profile__user=self.request.user).select_related("group", "group__profile")


from .models import OptionalProfileEntry
from .serializers import OptionalProfileEntrySerializer

class OptionalProfileEntryViewSet(viewsets.ModelViewSet):
    serializer_class = OptionalProfileEntrySerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        queryset = OptionalProfileEntry.objects.filter(profile__user=self.request.user).select_related("profile")
        entry_type = self.request.query_params.get("type")
        return queryset.filter(entry_type=entry_type) if entry_type in dict(OptionalProfileEntry.ENTRY_TYPES) else queryset
    def perform_create(self, serializer):
        profile, _created = CareerProfile.objects.get_or_create(user=self.request.user)
        serializer.save(profile=profile)
