THEMES_LIST = [
    "Content and Organisation",
    "Professional Practice",
    "Teachers",
    "Support / Mentoring",
    "Examination & Assessment",
    "Engagement & Contact",
    "Special Circumstances",
]

THEME_LLM_DEFINITIONS = {

    "Content and Organisation": (
        "Comments about how the programme, curriculum, courses, and learning activities are "
        "structured and organized. Focus on course content, module sequence, curriculum coherence, "
        "schedules, timetables, planning, workload, study materials, learning objectives, and "
        "whether information is clear and available on time. "
        "Include: unclear planning, heavy or uneven workload, missing materials, confusing course "
        "structure, overlap between modules, timetable issues, and programme-level organization. "
        "Exclude: individual teacher behaviour or teaching quality, mentoring or personal guidance, "
        "assessment quality, grading fairness, exams, and special accommodations."
    ),

    "Professional Practice": (
        "Comments about how well the programme prepares students for professional work and real "
        "practice. Focus on internships, projects, practical assignments, industry relevance, "
        "workplace preparation, career orientation, professional skills, teamwork, employability, "
        "and applying theory in realistic situations. "
        "Include: lack of practical experience, weak connection to the profession, useful projects, "
        "internship preparation, professional skills, and real-world application. "
        "Exclude: general course organization, normal study workload, teacher performance, exam "
        "procedures, grading, and general mentoring unless it is directly about career or workplace preparation."
    ),

    "Teachers": (
        "Comments about teachers, lecturers, tutors, and instructors in their teaching role. Focus "
        "on lesson quality, clarity of explanations, subject expertise, didactics, enthusiasm, "
        "communication during class, responsiveness to course-related questions, classroom guidance, "
        "and feedback on learning activities or assignments. "
        "Include: unclear explanations, inspiring teaching, poor lesson preparation, teacher expertise, "
        "availability for subject questions, and feedback from teachers on coursework. "
        "Boundary rule: if the comment is about a teacher acting as a course instructor, classify it "
        "as Teachers; if it is about a mentor, study coach, or advisor helping with study progress, "
        "personal circumstances, or wellbeing outside class, classify it as Support / Mentoring. "
        "Exclude: personal coaching, study planning support, wellbeing support, disability support, "
        "special accommodations, grading fairness, and exam procedures."
    ),

    "Support / Mentoring": (
        "Comments about structured support outside normal classroom teaching. Focus on mentors, "
        "study coaches, academic advisors, student counsellors, study progress guidance, personal "
        "guidance, planning help, motivation support, accessibility of help, and wellbeing-oriented "
        "conversations provided by the programme or institution. "
        "Include: mentor availability, useful or missing study guidance, help with planning, advice "
        "about study choices, follow-up on student progress, and access to personal or academic support. "
        "Boundary rule: if the comment is mainly about lessons, explanations, teacher expertise, or "
        "feedback in a course, classify it as Teachers. If the comment is mainly about a diagnosed "
        "condition, disability, mental health issue, financial pressure, caring responsibility, work-study "
        "conflict, or formal accommodation, classify it as Special Circumstances unless the student is "
        "specifically evaluating the support they received for that situation. "
        "Exclude: teacher performance in class, exam and grading issues, general curriculum organization, "
        "and special circumstances themselves without a clear support or mentoring angle."
    ),

    "Examination & Assessment": (
        "Comments about how students are tested, assessed, graded, and given assessment feedback. "
        "Focus on exams, tests, assignments as assessments, rubrics, assessment criteria, grading "
        "fairness, resits, deadlines tied to assessments, assessment workload, feedback on graded work, "
        "and examination procedures. "
        "Include: unclear criteria, unfair grades, too many assessments, late grades, resit issues, "
        "rubric problems, and feedback on assessed assignments. "
        "Exclude: general teaching quality, general course content, planning that is not assessment-related, "
        "mentoring, personal support, and professional practice unless the comment is specifically about assessment."
    ),

    "Engagement & Contact": (
        "Comments about connection, communication, interaction, and involvement within the programme. "
        "Focus on student participation, student voice, opportunities to give input, responsiveness "
        "to feedback, contact with fellow students, collaboration, community feeling, belonging, and "
        "general communication between students and the programme. "
        "Include: feeling unheard, weak communication, strong community, poor contact with classmates, "
        "collaboration opportunities, participation, and whether student feedback is acted on. "
        "Exclude: one-to-one mentoring, individual wellbeing support, teacher expertise, exam quality, "
        "grading fairness, and curriculum structure unless the comment is mainly about communication or involvement."
    ),

    "Special Circumstances": (
        "Comments about studying while dealing with circumstances that create extra barriers or require "
        "formal flexibility. Focus on disabilities, chronic conditions, ADHD, autism, dyslexia, concentration "
        "difficulties, mental health challenges, severe stress, financial pressure, accessibility issues, "
        "caring responsibilities, family circumstances, elite sports, employment, entrepreneurship, work-study "
        "balance, and accommodations such as extra time, adjusted deadlines, accessible materials, or other provisions. "
        "Include: difficulty combining study with work or care duties, mental health pressure, disability-related "
        "barriers, requests for accommodations, accessibility problems, and experiences with special arrangements. "
        "Boundary rule: classify the underlying circumstance here even if the student also mentions needing help. "
        "Use Support / Mentoring only when the main point is the quality, availability, or absence of guidance "
        "provided by mentors, coaches, advisors, or student support staff. "
        "Exclude: ordinary study stress or normal workload without a special circumstance, general mentoring, "
        "teaching quality, curriculum organization, and exam quality unless an accommodation or special barrier is central."
    )

}

THEME_EMBEDDING_DEFINITIONS = {

    "Content and Organisation": (
        "Inhoud en organisatie van de opleiding, curriculum, vakinhoud, modules, leerlijnen, "
        "rooster, planning, studielast, werkdruk, lesmateriaal, informatievoorziening, "
        "opbouw van het programma, course structure, workload, timetable, study materials."
    ),

    "Professional Practice": (
        "Beroepspraktijk, praktijkopdrachten, projecten, stages, werkveld, praktijkervaring, "
        "professionele vaardigheden, beroepsvaardigheden, samenwerken, toepassen in de praktijk, "
        "arbeidsmarkt, employability, internships, professional skills, real-world application."
    ),

    "Teachers": (
        "Docenten, leraren, lecturers, tutors, lesgeven, lessen, uitleg, vakinhoudelijke "
        "deskundigheid, didactiek, bereikbaarheid van docenten, communicatie tijdens de les, "
        "enthousiasme, begeleiding in de les, feedback van docenten op vakken en opdrachten."
    ),

    "Support / Mentoring": (
        "Studiebegeleiding, mentoring, coaching, SLB, mentor, studiecoach, studentbegeleider, "
        "studieadviseur, persoonlijke begeleiding bij studievoortgang, voortgangsgesprekken, "
        "hulp bij plannen, keuzes maken, motivatie, welzijnsgesprekken, academic advising."
    ),

    "Examination & Assessment": (
        "Toetsing en beoordeling, tentamens, examens, toetsen, opdrachten beoordelen, cijfers, "
        "beoordelingscriteria, rubrics, nakijken, feedback op beoordeling, herkansingen, "
        "deadlines voor toetsen, toetsprocedure, grading, assessment criteria."
    ),

    "Engagement & Contact": (
        "Betrokkenheid, contact, communicatie, interactie, participatie, inspraak, studentvoice, "
        "meedenken, responsiviteit, binding met de opleiding, gemeenschapsgevoel, contact met "
        "medestudenten, samenwerking, student involvement, sense of community."
    ),

    "Special Circumstances": (
        "Bijzondere omstandigheden, functiebeperking, beperking, handicap, ADHD, autisme, "
        "dyslexie, concentratieproblemen, mentale gezondheid, psychische klachten, stress, "
        "financiele zorgen, mantelzorg, topsport, werk naast studie, familieomstandigheden, "
        "toegankelijkheid, voorzieningen, HEALTH, aanpassingen, extra tijd, accommodations."
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
