THEMES_LIST = [
    "Content and Organisation",
    "Professional Practice",
    "Teachers",
    "Support / Mentoring",
    "Examination & Assessment",
    "Engagement & Contact",
    "Special Circumstances",
]

THEME_DEFINITIONS = {
    "Content and Organisation": (
        "Curriculum content, course organization, planning, schedules, workload, "
        "study materials, module structure, learning objectives, and information "
        "about how the programme is arranged."
    ),
    "Professional Practice": (
        "Connection to professional practice, internships, industry projects, "
        "guest lectures, career readiness, workplace skills, practical assignments, "
        "and links with companies or the professional field."
    ),
    "Teachers": (
        "Lecturers and instructors, teaching quality, explanations, subject expertise, "
        "didactic skill, classroom teaching, teacher feedback, and teacher availability "
        "for learning-related questions."
    ),
    "Support / Mentoring": (
        "Mentors, study coaches, student advisors, counseling, personal guidance, "
        "wellbeing support, non-academic support, supervision, and mentoring."
    ),
    "Examination & Assessment": (
        "Exams, tests, assignments, grading, assessment criteria, rubrics, resits, "
        "assessment alignment, and feedback on assessed work."
    ),
    "Engagement & Contact": (
        "Student involvement, belonging, contact with classmates or staff, communication, "
        "student voice, feeling heard, class atmosphere, community, and participation."
    ),
    "Special Circumstances": (
        "Accommodations for disability, illness, caregiving, financial stress, accessibility, "
        "special personal circumstances, flexible arrangements, and study adjustments."
    ),
}

METADATA_COLS = {
    "ID",
    "Institution",
    "academic_year",
    "location",
    "programme",
    "study_mode",
    "cohort",
    "Jaar",
    "Actuele BRIN-code volgens RIO",
    "Actuele naam instelling volgens RIO",
    "Actuele CROHO-code volgens RIO",
    "Actuele Opleidingsnaam volgens RIO",
    "Actuele BRIN-volgnummer volgens RIO",
    "Type Student",
    "Opleidingsvorm (vt dt du)",
    "Leerroute_Track",
    "Studiejaar volgens instelling",
    "Kunstopleiding",
    "Afstandsonderwijs",
    "Label1",
    "Label2",
    "Label3",
    "Label4",
    "Label5",
    "Label6",
    "Label7",
}

METADATA_ALIASES = {
    "institution": ["institution", "actuele naam instelling volgens rio"],
    "academic_year": ["academic_year", "jaar"],
    "location": ["location"],
    "programme": ["programme", "leerroute_track", "actuele opleidingsnaam volgens rio"],
    "study_mode": ["study_mode", "Type Student", "Opleidingsvorm (vt dt du)"],
    "cohort": ["cohort", "studiejaar volgens instelling"],
    "sector": ["sector", "Label3"],
    "language": ["language", "Label5"],
}

SOURCE_METADATA_ALIASES = {
    "institution": [
        "Institution",
        "Actuele naam instelling volgens RIO",
    ],
    "academic_year": [
        "academic_year",
        "Jaar",
    ],
    "location": [
        "location",
    ],
    "programme": [
        "programme",
        "Leerroute_Track",
        "Actuele Opleidingsnaam volgens RIO",
    ],
    "study_mode": [
        "Opleidingsvorm (vt dt du)",
        "study_mode",
    ],
    "cohort": [
        "cohort",
        "Studiejaar volgens instelling",
    ],
    "sector": [
        "Label3",
    ],
    "language": [
        "Label5",
    ],
}
