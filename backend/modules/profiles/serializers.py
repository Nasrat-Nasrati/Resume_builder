from rest_framework import serializers
from .models import CareerProfile

class CareerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CareerProfile
        fields = ["id", "professional_title", "summary", "city", "province", "district", "father_name", "tazkira_number", "show_father_name", "show_tazkira_number", "show_province", "show_district", "include_projects", "include_awards", "include_publications", "include_references", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


from .models import Experience

class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ["id", "position", "employer", "location", "start_date", "end_date", "is_current", "duties", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        current = attrs.get("is_current", getattr(self.instance, "is_current", False))
        if end and start and end < start:
            raise serializers.ValidationError({"end_date": ["End date must be on or after the start date."]})
        if current and end:
            raise serializers.ValidationError({"end_date": ["A current position must not have an end date."]})
        return attrs

class ExperienceReorderSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=True, max_length=200)
    def validate_ids(self, value):
        if len(value) != len(set(value)):
            raise serializers.ValidationError("Duplicate experience IDs are not allowed.")
        return value

from .models import EducationRecord

class EducationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = EducationRecord
        fields = ["id", "record_type", "qualification", "field_of_study", "institution", "location", "start_date", "end_date", "is_current", "credential_reference", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        current = attrs.get("is_current", getattr(self.instance, "is_current", False))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": ["End date must be on or after the start date."]})
        if current and end:
            raise serializers.ValidationError({"end_date": ["Current study must not have an end date."]})
        return attrs

from .models import LanguageEntry, SkillGroup, Skill

class LanguageEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LanguageEntry
        fields = ["id", "language", "is_mother_tongue", "proficiency", "cefr_level", "sort_order"]
        read_only_fields = ["id"]
    def validate(self, attrs):
        mother = attrs.get("is_mother_tongue", getattr(self.instance, "is_mother_tongue", False))
        proficiency = attrs.get("proficiency", getattr(self.instance, "proficiency", ""))
        cefr = attrs.get("cefr_level", getattr(self.instance, "cefr_level", ""))
        if not mother and not proficiency:
            raise serializers.ValidationError({"proficiency": ["Choose a self-described proficiency or mark this as your mother tongue."]})
        if mother and not proficiency and cefr:
            raise serializers.ValidationError({"cefr_level": ["CEFR level is optional and should only be set with a proficiency estimate."]})
        language = attrs.get("language", getattr(self.instance, "language", "")).strip()
        profile = self.context["request"].user.career_profile if hasattr(self.context["request"].user, "career_profile") else None
        if language and profile and LanguageEntry.objects.filter(profile=profile, language__iexact=language).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError({"language": ["This language has already been added."]})
        return attrs

class SkillGroupSerializer(serializers.ModelSerializer):
    skills = serializers.SerializerMethodField()
    class Meta:
        model = SkillGroup
        fields = ["id", "name", "sort_order", "skills"]
        read_only_fields = ["id", "skills"]
    def get_skills(self, obj):
        return SkillSerializer(obj.skills.all(), many=True).data

class SkillSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=SkillGroup.objects.all())
    class Meta:
        model = Skill
        fields = ["id", "group", "name", "sort_order"]
        read_only_fields = ["id"]

    def validate_group(self, value):
        if value.profile.user_id != self.context["request"].user.pk:
            raise serializers.ValidationError("Skill groups must belong to your profile.")
        return value
    def validate(self, attrs):
        group = attrs.get("group", getattr(self.instance, "group", None))
        name = attrs.get("name", getattr(self.instance, "name", "")).strip()
        if group and Skill.objects.filter(group=group, name__iexact=name).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError({"name": ["This skill is already in the selected group."]})
        return attrs


from .models import OptionalProfileEntry

class OptionalProfileEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionalProfileEntry
        fields = ["id", "entry_type", "title", "organization", "description", "url", "date", "referee_name", "referee_role", "referee_email", "referee_phone", "consent_to_publish", "sort_order", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        entry_type = attrs.get("entry_type", getattr(self.instance, "entry_type", ""))
        if entry_type == OptionalProfileEntry.REFERENCE:
            name = attrs.get("referee_name", getattr(self.instance, "referee_name", "")).strip()
            email = attrs.get("referee_email", getattr(self.instance, "referee_email", "")).strip()
            phone = attrs.get("referee_phone", getattr(self.instance, "referee_phone", "")).strip()
            consent = attrs.get("consent_to_publish", getattr(self.instance, "consent_to_publish", False))
            if not name:
                raise serializers.ValidationError({"referee_name": ["A referee name is required."]})
            if (email or phone) and not consent:
                raise serializers.ValidationError({"consent_to_publish": ["Explicit consent is required before referee contact details can be included in a CV."]})
        elif attrs.get("consent_to_publish"):
            raise serializers.ValidationError({"consent_to_publish": ["Consent applies only to reference entries."]})
        return attrs
