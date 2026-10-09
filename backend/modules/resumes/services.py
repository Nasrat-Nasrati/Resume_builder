from django.db import transaction
from rest_framework.exceptions import ValidationError
from modules.profiles.models import CareerProfile, Experience, EducationRecord, LanguageEntry, SkillGroup, OptionalProfileEntry
from .models import CVDocument as ResumeDocument

ALLOWED_SECTIONS = {"profile", "experience", "education", "languages", "skills", "projects", "awards", "publications", "references"}
OPTIONAL_SECTION_FLAGS = {"projects": "include_projects", "awards": "include_awards", "publications": "include_publications", "references": "include_references"}

def _entry_data(entry, section):
    data = {"title": entry.title, "organization": entry.organization, "description": entry.description, "url": entry.url, "date": entry.date.isoformat() if entry.date else None}
    if section == "references":
        data.update({"referee_name": entry.referee_name, "referee_role": entry.referee_role})
        if entry.consent_to_publish:
            data.update({"referee_email": entry.referee_email, "referee_phone": entry.referee_phone, "consent_to_publish": True})
    return data

@transaction.atomic
def create_profile_snapshot(*, user, title="Untitled CV", output_language="en", cv_type="general", selected_sections):
    if not isinstance(selected_sections, list) or not selected_sections:
        raise ValidationError({"selected_sections": ["Select at least one section."]})
    if len(selected_sections) != len(set(selected_sections)) or set(selected_sections) - ALLOWED_SECTIONS:
        raise ValidationError({"selected_sections": ["Section selection contains duplicates or unknown sections."]})
    profile, _ = CareerProfile.objects.get_or_create(user=user)
    chosen = set(selected_sections)
    data = {}
    if "profile" in chosen:
        data["personal"] = {"full_name": user.get_full_name(), "email": user.email, "phone": user.phone, "show_father_name": profile.show_father_name, "show_tazkira_number": profile.show_tazkira_number, "show_province": profile.show_province, "show_district": profile.show_district, "professional_title": profile.professional_title, "summary": profile.summary, "city": profile.city,
            "province": profile.province if profile.show_province else "", "district": profile.district if profile.show_district else "",
            "father_name": profile.father_name if profile.show_father_name else "", "tazkira_number": profile.tazkira_number if profile.show_tazkira_number else ""}
    if "experience" in chosen:
        data["experience"] = list(Experience.objects.filter(profile=profile).values("position", "employer", "location", "start_date", "end_date", "is_current", "duties"))
        data["experience"] = [{**x, "start_date": x["start_date"].isoformat(), "end_date": x["end_date"].isoformat() if x["end_date"] else None} for x in data["experience"]]
    if "education" in chosen:
        data["education"] = list(EducationRecord.objects.filter(profile=profile).values("record_type", "qualification", "field_of_study", "institution", "location", "start_date", "end_date", "is_current", "credential_reference"))
        data["education"] = [{**x, "start_date": x["start_date"].isoformat() if x["start_date"] else None, "end_date": x["end_date"].isoformat() if x["end_date"] else None} for x in data["education"]]
    if "languages" in chosen:
        data["languages"] = list(LanguageEntry.objects.filter(profile=profile).values("language", "is_mother_tongue", "proficiency", "cefr_level"))
    if "skills" in chosen:
        data["skills"] = [{"name": group.name, "skills": list(group.skills.values_list("name", flat=True))} for group in SkillGroup.objects.filter(profile=profile).prefetch_related("skills")]
    for section, enabled_field in OPTIONAL_SECTION_FLAGS.items():
        if section in chosen:
            if not getattr(profile, enabled_field):
                raise ValidationError({"selected_sections": [f"The {section} section is not enabled in your profile."]})
            entries = OptionalProfileEntry.objects.filter(profile=profile, entry_type=OptionalProfileEntry.REFERENCE if section == "references" else section[:-1] if section.endswith("s") else section)
            data[section] = [_entry_data(entry, section) for entry in entries]
    if output_language not in {"en", "fa", "ps"}:
        raise ValidationError({"output_language": ["Choose English, Dari, or Pashto."]})
    return ResumeDocument.objects.create(owner=user, title=title.strip() or "Untitled CV", output_language=output_language, cv_type=cv_type, schema_version=1, template_version=1, revision=1, selected_sections=["personal" if value == "profile" else value for value in selected_sections], snapshot=data)
