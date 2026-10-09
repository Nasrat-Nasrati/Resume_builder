import uuid
from django.conf import settings
from django.db import models

class CareerProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="career_profile")
    professional_title = models.CharField(max_length=160, blank=True)
    summary = models.TextField(blank=True, max_length=3000)
    city = models.CharField(max_length=120, blank=True)
    province = models.CharField(max_length=120, blank=True)
    district = models.CharField(max_length=120, blank=True)
    father_name = models.CharField(max_length=160, blank=True)
    tazkira_number = models.CharField(max_length=64, blank=True)
    show_father_name = models.BooleanField(default=False)
    show_tazkira_number = models.BooleanField(default=False)
    show_province = models.BooleanField(default=True)
    show_district = models.BooleanField(default=True)
    include_projects = models.BooleanField(default=False)
    include_awards = models.BooleanField(default=False)
    include_publications = models.BooleanField(default=False)
    include_references = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Career profile for {self.user_id}"

class Experience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(CareerProfile, on_delete=models.CASCADE, related_name="experiences")
    position = models.CharField(max_length=160)
    employer = models.CharField(max_length=160)
    location = models.CharField(max_length=160, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    duties = models.TextField(blank=True, max_length=6000)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "-start_date"]
        constraints = [models.CheckConstraint(condition=models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")), name="experience_end_after_start")]

    def __str__(self):
        return f"{self.position} at {self.employer}"

class EducationRecord(models.Model):
    EDUCATION = "education"
    TRAINING = "training"
    RECORD_TYPES = [(EDUCATION, "Education"), (TRAINING, "Training")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(CareerProfile, on_delete=models.CASCADE, related_name="education_records")
    record_type = models.CharField(max_length=16, choices=RECORD_TYPES, default=EDUCATION)
    qualification = models.CharField(max_length=160)
    field_of_study = models.CharField(max_length=160, blank=True)
    institution = models.CharField(max_length=200)
    location = models.CharField(max_length=160, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    credential_reference = models.CharField(max_length=160, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["sort_order", "-end_date", "-start_date"]
        constraints = [models.CheckConstraint(condition=models.Q(start_date__isnull=True) | models.Q(end_date__isnull=True) | models.Q(end_date__gte=models.F("start_date")), name="education_end_after_start")]

class LanguageEntry(models.Model):
    PROFICIENCY_CHOICES = [("basic", "Basic"), ("conversational", "Conversational"), ("professional", "Professional"), ("fluent", "Fluent")]
    CEFR_CHOICES = [(value, value) for value in ("A1", "A2", "B1", "B2", "C1", "C2")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(CareerProfile, on_delete=models.CASCADE, related_name="languages")
    language = models.CharField(max_length=100)
    is_mother_tongue = models.BooleanField(default=False)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_CHOICES, blank=True)
    cefr_level = models.CharField(max_length=2, choices=CEFR_CHOICES, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["sort_order", "language"]
        constraints = [models.UniqueConstraint(fields=["profile", "language"], name="unique_profile_language")]

class SkillGroup(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(CareerProfile, on_delete=models.CASCADE, related_name="skill_groups")
    name = models.CharField(max_length=100)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["sort_order", "name"]

class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(SkillGroup, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=120)
    sort_order = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [models.UniqueConstraint(fields=["group", "name"], name="unique_skill_in_group")]


class OptionalProfileEntry(models.Model):
    """Typed optional career content, kept private to its owning profile."""
    PROJECT = "project"
    AWARD = "award"
    PUBLICATION = "publication"
    REFERENCE = "reference"
    ENTRY_TYPES = [(key, key.title()) for key in (PROJECT, AWARD, PUBLICATION, REFERENCE)]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(CareerProfile, on_delete=models.CASCADE, related_name="optional_entries")
    entry_type = models.CharField(max_length=16, choices=ENTRY_TYPES)
    title = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True, max_length=5000)
    url = models.URLField(blank=True, max_length=500)
    date = models.DateField(null=True, blank=True)
    referee_name = models.CharField(max_length=160, blank=True)
    referee_role = models.CharField(max_length=160, blank=True)
    referee_email = models.EmailField(blank=True)
    referee_phone = models.CharField(max_length=32, blank=True)
    consent_to_publish = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ["sort_order", "-date", "title"]
