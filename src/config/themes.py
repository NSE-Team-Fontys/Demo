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
        "Comments about curriculum content, courses, modules, schedules, timetables, workload, "
        "planning, study materials, learning objectives, course structure, information provided "
        "to students, and programme organization. "
        "Include: curriculum, planning, workload, schedules, course content, module structure. "
        "Exclude: teacher behaviour, mentoring, grading, exams, personal support."
    ),

    "Professional Practice": (
        "Comments about preparation for professional work, practical assignments, projects, "
        "internships, industry relevance, professional skills, real-world application, teamwork, "
        "and career preparation. "
        "Include: internships, projects, workplace relevance, practical experience, employability. "
        "Exclude: general curriculum organization, teacher quality, exams, mentoring."
    ),

    "Teachers": (
        "Comments about teachers, lecturers, tutors, and instructors. Focus on teaching quality, "
        "clarity of explanations, expertise, communication during lessons, availability for course-related "
        "questions, enthusiasm, feedback quality, and classroom guidance. "
        "Include: explanations, teaching style, expertise, responsiveness, teacher feedback. "
        "Exclude: study coaching, personal wellbeing support, disabilities, special accommodations."
    ),

    "Support / Mentoring": (
        "Comments about coaching, mentoring, study guidance, personal support, academic advising, "
        "student wellbeing support, accessibility of help, and individual guidance outside normal teaching. "
        "Include: mentors, coaches, study advisors, personal guidance, wellbeing support. "
        "Exclude: teacher performance in class, exams, grades, disabilities unless specifically about support received."
    ),

    "Examination & Assessment": (
        "Comments about exams, tests, assignments, grading, assessment criteria, rubrics, feedback "
        "on assessment, fairness of grading, resits, deadlines related to assessment, and examination procedures. "
        "Include: grades, exams, rubrics, assessment criteria, fairness, feedback on assignments. "
        "Exclude: general teaching quality, curriculum organization, mentoring."
    ),

    "Engagement & Contact": (
        "Comments about communication, interaction, participation, student involvement, sense of community, "
        "contact with fellow students, collaboration, responsiveness, and opportunities to provide input. "
        "Include: communication, interaction, participation, student voice, community feeling. "
        "Exclude: personal mentoring, teacher expertise, assessment quality."
    ),

    "Special Circumstances": (
        "Comments about studying under special circumstances. Includes disabilities, ADHD, autism, "
        "dyslexia, concentration difficulties, mental health challenges, stress, financial concerns, "
        "accessibility issues, caring responsibilities, elite sports, employment, entrepreneurship, "
        "family circumstances, and accommodations related to these situations. "
        "Include: ADHD, dyslexia, accessibility, financial stress, disability support, work-study balance. "
        "Exclude: general mentoring, normal academic support, teaching quality, curriculum organization."
    )

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
}

METADATA_ALIASES = {
    "institution": ["institution", "actuele naam instelling volgens rio"],
    "academic_year": ["academic_year", "jaar"],
    "location": ["location"],
    "programme": ["programme", "leerroute_track", "actuele opleidingsnaam volgens rio"],
    "study_mode": ["study_mode", "type student", "opleidingsvorm (vt dt du)"],
    "cohort": ["cohort", "studiejaar volgens instelling"],
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
        "study_mode",
        "Type Student",
        "Opleidingsvorm (vt dt du)",
    ],
    "cohort": [
        "cohort",
        "Studiejaar volgens instelling",
    ],
}
