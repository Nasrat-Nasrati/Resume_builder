"""Version 1 CV content contracts. User text stays plain text throughout rendering."""
from rest_framework import serializers

OPTIONAL_SECTIONS = ("projects", "awards", "publications", "references")
BASE_SECTIONS = ("personal", "experience", "education", "languages", "skills")

class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: ["Unknown field."] for key in sorted(unknown)})
        return super().to_internal_value(data)

class OptionalDate(serializers.DateField):
    def to_internal_value(self, value):
        return None if value in ("", None) else super().to_internal_value(value)

def text(length, default=""):
    return serializers.CharField(max_length=length, allow_blank=True, required=False, default=default)

class PersonalContent(StrictSerializer):
    full_name = text(160)
    email = serializers.EmailField(allow_blank=True, required=False, default="")
    phone = text(32)
    professional_title = text(160)
    summary = text(3000)
    city = text(120)
    province = text(120)
    district = text(120)
    father_name = text(160)
    tazkira_number = text(64)
    show_father_name = serializers.BooleanField(default=False)
    show_tazkira_number = serializers.BooleanField(default=False)
    show_province = serializers.BooleanField(default=True)
    show_district = serializers.BooleanField(default=True)

class DatedContent(StrictSerializer):
    start_date = OptionalDate(required=False, allow_null=True, default=None)
    end_date = OptionalDate(required=False, allow_null=True, default=None)
    is_current = serializers.BooleanField(default=False)
    def validate(self, data):
        start, end = data.get("start_date"), data.get("end_date")
        if data.get("is_current") and end:
            raise serializers.ValidationError({"end_date": ["A current entry must not have an end date."]})
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": ["End date must be on or after start date."]})
        return data

class ExperienceContent(DatedContent):
    position = text(160)
    employer = text(160)
    location = text(160)
    duties = text(6000)
    def validate(self, data):
        data = super().validate(data)
        if self.context.get("complete"):
            missing = {key: ["This field is required."] for key in ("position", "employer", "start_date") if not data.get(key)}
            if missing:
                raise serializers.ValidationError(missing)
        return data

class EducationContent(DatedContent):
    record_type = serializers.ChoiceField(choices=["education", "training"], default="education")
    qualification = text(160)
    field_of_study = text(160)
    institution = text(200)
    location = text(160)
    credential_reference = text(160)
    def validate(self, data):
        data = super().validate(data)
        if self.context.get("complete"):
            missing = {key: ["This field is required."] for key in ("qualification", "institution") if not data.get(key)}
            if missing:
                raise serializers.ValidationError(missing)
        return data

class LanguageContent(StrictSerializer):
    language = text(100)
    is_mother_tongue = serializers.BooleanField(default=False)
    proficiency = serializers.ChoiceField(choices=["", "basic", "conversational", "professional", "fluent"], default="")
    cefr_level = serializers.ChoiceField(choices=["", "A1", "A2", "B1", "B2", "C1", "C2"], default="")
    def validate(self, data):
        if self.context.get("complete"):
            if not data.get("language"):
                raise serializers.ValidationError({"language": ["Enter a language name."]})
            if not data.get("is_mother_tongue") and not data.get("proficiency"):
                raise serializers.ValidationError({"proficiency": ["Choose a proficiency or mark this as your mother tongue."]})
        return data

class SkillContent(StrictSerializer):
    name = text(100)
    skills = serializers.ListField(child=serializers.CharField(max_length=120, allow_blank=False), max_length=100, default=list)

class OptionalContent(StrictSerializer):
    title = text(200)
    organization = text(200)
    description = text(5000)
    url = serializers.URLField(max_length=500, allow_blank=True, required=False, default="")
    date = OptionalDate(required=False, allow_null=True, default=None)
    referee_name = text(160)
    referee_role = text(160)
    referee_email = serializers.EmailField(allow_blank=True, required=False, default="")
    referee_phone = text(32)
    consent_to_publish = serializers.BooleanField(default=False)
    def validate(self, data):
        if (data.get("referee_email") or data.get("referee_phone")) and not data.get("consent_to_publish"):
            raise serializers.ValidationError({"consent_to_publish": ["Confirm permission before including referee contact details."]})
        return data

class ExperienceStep(StrictSerializer):
    experience = ExperienceContent(many=True, max_length=100)

class EducationStep(StrictSerializer):
    education = EducationContent(many=True, max_length=100)

class SkillsStep(StrictSerializer):
    languages = LanguageContent(many=True, max_length=50, required=False)
    skills = SkillContent(many=True, max_length=50, required=False)
    projects = OptionalContent(many=True, max_length=100, required=False)
    awards = OptionalContent(many=True, max_length=100, required=False)
    publications = OptionalContent(many=True, max_length=100, required=False)
    references = OptionalContent(many=True, max_length=50, required=False)
    enabled_sections = serializers.ListField(child=serializers.ChoiceField(choices=OPTIONAL_SECTIONS), max_length=4, required=False)
    def validate(self, data):
        names = [row["language"].casefold() for row in data.get("languages", []) if row.get("language")]
        if len(names) != len(set(names)):
            raise serializers.ValidationError({"languages": ["Each language can appear only once."]})
        enabled = data.get("enabled_sections", [])
        if len(enabled) != len(set(enabled)):
            raise serializers.ValidationError({"enabled_sections": ["Duplicate sections are not allowed."]})
        return data

STEP_SERIALIZERS = {1: PersonalContent, 2: ExperienceStep, 3: EducationStep, 4: SkillsStep}

def validate_step(step, data, complete=False):
    serializer = STEP_SERIALIZERS[step](data=data, context={"complete": complete})
    serializer.is_valid(raise_exception=True)
    normalized = dict(serializer.data)
    if step == 1 and complete and not normalized.get("full_name"):
        raise serializers.ValidationError({"full_name": ["Enter your full name before continuing."]})
    return normalized

def readiness(document):
    errors = {}
    payloads = {
        1: document.snapshot.get("personal", {}),
        2: {"experience": document.snapshot.get("experience", [])},
        3: {"education": document.snapshot.get("education", [])},
        4: {key: document.snapshot[key] for key in ("languages", "skills", *OPTIONAL_SECTIONS) if key in document.snapshot and (key not in OPTIONAL_SECTIONS or key in document.selected_sections)},
    }
    for step, data in payloads.items():
        try:
            validate_step(step, data, complete=True)
        except serializers.ValidationError as error:
            errors[str(step)] = error.detail
    return {"ready": not errors, "revision": document.revision, "missing_fields": errors}
