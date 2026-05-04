// Mock NSE theme data

export const YEARS = ['22/23', '23/24', '24/25', '25/26']

export const FILTER_OPTIONS = {
  jaar: ['2022/2023', '2023/2024', '2024/2025', '2025/2026'],
  locatie: ['All locations', 'Eindhoven', 'Tilburg', 'Den Bosch', 'Venlo'],
  opleiding: [
    'Software Engineering',
    'Cyber Security',
    'Artificial Intelligence',
    'ICT & Business',
    'HBO-ICT',
  ],
  studievorm: ['All', 'Full-time', 'Part-time', 'Dual'],
  cohort: ['All', '2022', '2023', '2024', '2025'],
}

// Base theme definitions (shared across all profiles)
const BASE_THEMES = [
  {
    id: 'begeleiding',
    name: 'Guidance',
    icon: 'psychology',
    size: 'large',
    subtag: 'Highest sentiment climber',
    subthemes: ['Personal feedback', 'Availability', 'Coaching'],
    quotes: [
      '"The personal approach of my coach really helped me during my internship period. Always quick responses to questions."',
      '"Great support during projects, lecturers really think along with you on technical solutions."',
    ],
    aiSummary:
      'Students appreciate the accessibility of lecturers. There is a strong correlation between personal feedback and study satisfaction.',
  },
  {
    id: 'faciliteiten',
    name: 'Facilities',
    icon: 'apartment',
    size: 'medium',
    subtag: null,
    subthemes: ['Computer labs', 'Workspaces', 'Parking'],
    quotes: [
      '"The computer labs are well-equipped, but quiet study rooms are scarce during exam periods."',
      '"Nice canteen but the Wi-Fi on the third floor doesn\'t work well."',
    ],
    aiSummary:
      'Students have mixed opinions about available facilities. Computer labs are rated positively, but parking and quiet workspaces are a recurring concern.',
  },
  {
    id: 'groepsprojecten',
    name: 'Group Projects',
    icon: 'groups',
    size: 'small',
    subtag: null,
    subthemes: ['Collaboration', 'Assessment', 'Task distribution'],
    quotes: [
      '"Group projects teach you to collaborate, but it is frustrating when not everyone contributes equally."',
      '"The feedback sessions after projects are valuable, but sometimes come too late."',
    ],
    aiSummary:
      'Opinions about group projects are divided. Collaboration is appreciated, but the assessment of individual contributions is a frequently mentioned pain point.',
  },
  {
    id: 'roosters',
    name: 'Schedules',
    icon: 'calendar_month',
    size: 'small',
    subtag: 'Area of concern',
    subthemes: ['Schedule changes', 'Exam planning', 'Travel time'],
    quotes: [
      '"Schedule changes sometimes come a day in advance — that is difficult to plan around work or internship."',
      '"Sometimes there are large gaps in the schedule, meaning you have to wait a long time on campus."',
    ],
    aiSummary:
      'Schedule planning is a persistent bottleneck. Late schedule changes and unclear communication cause stress among students.',
  },
  {
    id: 'leeromgeving',
    name: 'Learning Environment',
    icon: 'menu_book',
    size: 'medium',
    subtag: null,
    subthemes: ['Canvas', 'Study materials', 'Online lessons'],
    quotes: [
      '"Study materials are well organised in Canvas, always easy to find."',
      '"Great that there are also recordings of lectures, useful when sick or for revision."',
    ],
    aiSummary:
      'The digital learning environment is well appreciated. Canvas is experienced as clear and students value the availability of study materials.',
  },
  {
    id: 'examencommissie',
    name: 'Exam Committee',
    icon: 'gavel',
    size: 'small',
    subtag: null,
    subthemes: ['Processing times', 'Communication', 'Procedures'],
    quotes: [
      '"The exam committee responds slowly to requests, making it difficult to plan my studies."',
      '"Eventually well assisted, but the process to get there was unclear."',
    ],
    aiSummary:
      'Contacts with the exam committee generally proceed formally. Students sometimes lack clarity on procedures and processing times.',
  },
  {
    id: 'stagebegeleiding',
    name: 'Internship Guidance',
    icon: 'work',
    size: 'small',
    subtag: null,
    subthemes: ['Contact moments', 'Academic support', 'Company selection'],
    quotes: [
      '"My internship supervisor was always reachable and actively thought along about my learning goals."',
      '"Great that the school also monitors the internship progress, it made me feel less alone."',
    ],
    aiSummary:
      'Internship guidance is appreciated for the frequency of contact moments. Students find supervisors easily reachable and academically strong.',
  },
]

// ── Per-programme AI summaries ────────────────────────────────────────────────
const AI_SUMMARIES = {
  begeleiding: {
    'Software Engineering':   'Software Engineering students value hands-on mentoring during technical projects. Lecturers are praised for their practical industry knowledge and responsiveness to questions during crunch periods.',
    'Cyber Security':         'Cyber Security students note steady improvement in lecturer availability. Peer mentoring in lab environments is positively received, though formal guidance sessions can be inconsistent in frequency.',
    'Artificial Intelligence':'AI students report highly positive mentoring experiences, particularly in research-oriented projects. Supervisors are seen as both approachable and academically rigorous, with a genuine interest in student outcomes.',
    'ICT & Business':         'ICT & Business students appreciate guidance that bridges technical and commercial perspectives. Mentors with industry backgrounds are especially valued for their ability to connect coursework to real-world contexts.',
    'HBO-ICT':                'HBO-ICT students show mixed sentiment on guidance. While lecturers are generally accessible, students on dual tracks report a stronger connection with their workplace mentors than with campus staff.',
    default:                  'Students appreciate the accessibility of lecturers. There is a strong correlation between personal feedback and study satisfaction.',
  },
  faciliteiten: {
    'Software Engineering':   'Software Engineering students frequently highlight the quality of coding labs and hardware availability. Shared workspaces during peak periods and campus parking remain recurring concerns.',
    'Cyber Security':         'Cyber Security students rate the security lab infrastructure moderately well. Specialist equipment is available, but booking systems and capacity during peak hours are cited as needing improvement.',
    'Artificial Intelligence':'AI students report limited access to GPU-equipped workstations during high-demand periods. Cloud computing alternatives are appreciated but on-campus compute resources need significant expansion.',
    'ICT & Business':         'Facilities are generally well-rated in ICT & Business. Collaborative workspaces and AV equipment meet expectations, though parking and commuter facilities consistently lag behind student needs.',
    'HBO-ICT':                'HBO-ICT students hold mixed views on facilities. General-purpose labs are adequate for most tasks but feel overcrowded during peak hours, and the campus infrastructure has not kept pace with programme growth.',
    default:                  'Students have mixed opinions about available facilities. Computer labs are rated positively, but parking and quiet workspaces are a recurring concern.',
  },
  groepsprojecten: {
    'Software Engineering':   'Group project sentiment in Software Engineering is mixed. Agile-based project structures are appreciated for their realism, but uneven contribution across team members is a persistent complaint that assessment methods do not fully address.',
    'Cyber Security':         'Cyber Security students find group projects useful for simulating real-world threat scenarios. Assessment of individual contributions within collaborative teams remains the primary area of contention.',
    'Artificial Intelligence':'Group projects in Artificial Intelligence are viewed positively, especially cross-disciplinary collaborations. Peer assessment mechanisms are seen as fairer and more transparent than in previous years.',
    'ICT & Business':         'ICT & Business students appreciate group projects that combine technical deliverables with business presentations. Coordination challenges within mixed-background teams are frequently mentioned but seen as valuable preparation.',
    'HBO-ICT':                'HBO-ICT group project feedback is broadly neutral. Students value the collaborative experience but feel assessment criteria could be more transparent and consistently applied across different project coaches.',
    default:                  'Opinions about group projects are divided. Collaboration is appreciated, but the assessment of individual contributions is a frequently mentioned pain point.',
  },
  roosters: {
    'Software Engineering':   'Schedule management is a notable pain point in Software Engineering. Last-minute changes to lab session bookings disrupt project workflows and cause significant stress, particularly during sprint deadlines.',
    'Cyber Security':         'Cyber Security students report significant frustration with timetabling. Specialised lab slots are frequently moved with little notice, making it difficult to coordinate team-based security assignments.',
    'Artificial Intelligence':'Scheduling in Artificial Intelligence is comparatively well-managed, with fewer last-minute changes than other programmes. Students appreciate structured exam planning, though travel time between buildings is occasionally raised.',
    'ICT & Business':         'Timetabling issues are persistent in ICT & Business. Part-time students juggling employment highlight the disproportionate impact of late schedule changes on their ability to manage personal commitments.',
    'HBO-ICT':                'HBO-ICT students report the most scheduling dissatisfaction of any programme. Timetable instability is the single most raised theme, with many calling for a minimum notice period before any changes are communicated.',
    default:                  'Schedule planning is a persistent bottleneck. Late schedule changes and unclear communication cause stress among students.',
  },
  leeromgeving: {
    'Software Engineering':   'Software Engineering students rate the digital learning environment highly. Canvas is well-structured with clear module pages, and lecture recordings are extensively used during revision and when resolving technical blockers.',
    'Cyber Security':         'Cyber Security students value the breadth of online resources and interactive lab simulations available through Canvas. Scenario-based learning modules tailored to security contexts receive consistent praise.',
    'Artificial Intelligence':'The learning environment for AI students is rated very highly. Access to annotated notebooks, research paper collections, and curated datasets through Canvas is particularly valued for independent study.',
    'ICT & Business':         'ICT & Business students are satisfied with Canvas organisation and the regular availability of guest lecture recordings. Real-world case study materials are especially appreciated for connecting theory to practice.',
    'HBO-ICT':                'The digital learning environment receives consistently positive feedback from HBO-ICT students. Asynchronous resources and lecture recordings are especially valued by commuter and part-time students.',
    default:                  'The digital learning environment is well appreciated. Canvas is experienced as clear and students value the availability of study materials.',
  },
  examencommissie: {
    'Software Engineering':   'Software Engineering students report moderate satisfaction with the exam committee. Processing times for routine requests are generally acceptable, though complex appeals can take longer than students consider reasonable.',
    'Cyber Security':         'Cyber Security students express frustration with exam committee response times, particularly for deferral and exemption requests. Communication during the review process is seen as insufficiently proactive.',
    'Artificial Intelligence':'AI students have relatively few interactions with the exam committee and rate it neutrally. Those who did engage describe a professional but formal experience with limited transparency during the process.',
    'ICT & Business':         'Exam committee interactions in ICT & Business are mixed. Students note that the process for grade disputes is unclear and that turnaround times vary significantly depending on the time of year.',
    'HBO-ICT':                'HBO-ICT students are the least satisfied with exam committee processes. Long wait times and inconsistent communication are the most frequently cited issues, particularly during the peak January and June periods.',
    default:                  'Contacts with the exam committee generally proceed formally. Students sometimes lack clarity on procedures and processing times.',
  },
  stagebegeleiding: {
    'Software Engineering':   'Software Engineering students are broadly positive about internship guidance. Placements in the tech sector are well-supported, and supervisors maintain regular check-ins that feel genuinely engaged rather than procedural.',
    'Cyber Security':         'Cyber Security students rate internship guidance positively, especially those placed at organisations with mature security teams. The quality of structured contact moments is consistently praised.',
    'Artificial Intelligence':'AI students value the structured approach to internship supervision. Learning goals are clearly defined and revisited at each contact moment, making the placement experience academically rewarding alongside its practical value.',
    'ICT & Business':         'Internship guidance in ICT & Business receives strong ratings. Students placed in hybrid IT-business roles benefit from supervisors who understand both dimensions of their work and can provide genuinely relevant feedback.',
    'HBO-ICT':                'HBO-ICT internship guidance is viewed moderately positively. Students on dual tracks report excellent integration between workplace and academic mentoring, while standard full-time students note fewer and shorter touchpoints.',
    default:                  'Internship guidance is appreciated for the frequency of contact moments. Students find supervisors easily reachable and academically strong.',
  },
}

// ── Per-programme student quotes ──────────────────────────────────────────────
const QUOTES = {
  begeleiding: {
    'Software Engineering': [
      '"My mentor scheduled regular one-on-ones and tracked my progress across each sprint. It made a real difference during crunch time."',
      '"The SE lecturers are always willing to jump on a call when you are stuck — faster response than I expected from a university."',
    ],
    'Cyber Security': [
      '"Lab supervisors in Cyber Security know their field. When I had a question about penetration testing methodology, I got a thorough and timely answer."',
      '"Guidance is improving year on year. My second-year mentor was far more proactive than in year one."',
    ],
    'Artificial Intelligence': [
      '"My research supervisor went above and beyond to help me find relevant papers and guided my methodology from the very start."',
      '"The AI department has a genuine open-door culture. I never felt like my questions were an imposition on anyone\'s time."',
    ],
    'ICT & Business': [
      '"My mentor helped me see how the technical work connects to business outcomes — that dual perspective was invaluable for my internship."',
      '"Guidance sessions covered both my coding progress and my presentation skills. A well-rounded approach that prepared me well."',
    ],
    'HBO-ICT': [
      '"Guidance is decent but can feel inconsistent — some lecturers are very hands-on while others are difficult to reach outside class hours."',
      '"The buddy system in year one was a great initiative. I felt supported from day one on campus."',
    ],
    default: [
      '"The personal approach of my coach really helped me during my internship period. Always quick responses to questions."',
      '"Great support during projects, lecturers really think along with you on technical solutions."',
    ],
  },
  faciliteiten: {
    'Software Engineering': [
      '"The coding labs have the latest hardware and dual monitors — hard to complain when you have a proper setup for your project work."',
      '"Parking is a nightmare during morning lectures. I end up cycling from across town to avoid the queue entirely."',
    ],
    'Cyber Security': [
      '"The security labs are impressive — dedicated virtual environments for each student make the practicals far more realistic."',
      '"Booking a specialist workstation for an evening session is hit or miss. A proper reservation system would make a big difference."',
    ],
    'Artificial Intelligence': [
      '"GPU cluster access is limited to a few students at a time. For deep learning experiments the wait can completely break your workflow."',
      '"The cloud credits provided through the programme are genuinely useful when on-campus compute is unavailable or oversubscribed."',
    ],
    'ICT & Business': [
      '"Meeting rooms for group work are plentiful and well-equipped with screens and whiteboards. They really support project collaboration."',
      '"The printing quota feels outdated — for a business programme we end up producing a lot of formal reports and pitch decks."',
    ],
    'HBO-ICT': [
      '"General labs are fine for most tasks but feel very crowded during the first weeks of semester one."',
      '"The Wi-Fi in the older lecture halls cuts out regularly during hybrid sessions. It disrupts the flow when you are presenting online."',
    ],
    default: [
      '"The computer labs are well-equipped, but quiet study rooms are scarce during exam periods."',
      '"Nice canteen but the Wi-Fi on the third floor doesn\'t work well."',
    ],
  },
  groepsprojecten: {
    'Software Engineering': [
      '"Our agile sprints were well-structured by the project coach, but peer grading felt inconsistent across different teams in the same module."',
      '"Group work taught me more about git branching and conflict resolution than any individual lecture. Valuable despite the friction."',
    ],
    'Cyber Security': [
      '"The red team and blue team exercises were the highlight of my year — real collaboration under realistic pressure."',
      '"Assigning equal grades when effort is clearly unequal is frustrating. We need a better mechanism to capture individual contribution."',
    ],
    'Artificial Intelligence': [
      '"Our cross-faculty group project combined AI with design students — challenging but one of the most valuable learning experiences I have had."',
      '"The feedback session at project end was thorough and constructive. I left with clear, actionable points to improve on."',
    ],
    'ICT & Business': [
      '"Mixing students with technical and business backgrounds in one team creates a realistic work environment. Hard at times but genuinely rewarding."',
      '"Some group members focus only on the slides while others do all the coding. Fairer task distribution tools would improve the experience."',
    ],
    'HBO-ICT': [
      '"Group projects are a core part of the HBO-ICT experience. When the team gels, the output can be genuinely impressive."',
      '"Assessment rubrics for group work could be clearer — what counts as a strong individual contribution is never fully defined upfront."',
    ],
    default: [
      '"Group projects teach you to collaborate, but it is frustrating when not everyone contributes equally."',
      '"The feedback sessions after projects are valuable, but sometimes come too late."',
    ],
  },
  roosters: {
    'Software Engineering': [
      '"A lab booking was moved two hours earlier with one day\'s notice. My whole team had to scramble to rearrange their schedules."',
      '"The schedule app is useful, but push notifications for changes arrive too late to act on in any meaningful way."',
    ],
    'Cyber Security': [
      '"Specialised security labs are overbooked and the timetable reflects that chaos. A proper advance booking system is badly needed."',
      '"I had three consecutive rescheduled sessions in one week during the exam period. Completely unworkable."',
    ],
    'Artificial Intelligence': [
      '"Schedule changes are rare in the AI programme — timetable management seems far more deliberate than what peers in other programmes describe."',
      '"Travel time between the AI lab and the main lecture hall is around fifteen minutes. Back-to-back bookings simply don\'t account for that."',
    ],
    'ICT & Business': [
      '"As a part-time student with a full-time job, a Wednesday evening schedule change ruins my entire week\'s planning."',
      '"The timetable for combined ICT and Business modules is especially messy — the two departments rarely coordinate their scheduling."',
    ],
    'HBO-ICT': [
      '"I have had five schedule changes in six weeks. I now check the app every single morning before leaving home."',
      '"Gaps of two to three hours in the timetable are very common. Finding a seat on campus during those periods is almost impossible."',
    ],
    default: [
      '"Schedule changes sometimes come a day in advance — that is difficult to plan around work or internship."',
      '"Sometimes there are large gaps in the schedule, meaning you have to wait a long time on campus."',
    ],
  },
  leeromgeving: {
    'Software Engineering': [
      '"Canvas is well-structured with clear module pages. I can always find last week\'s slides within thirty seconds."',
      '"Recorded lectures are a lifesaver when you are sick or need to revisit a complex concept before an exam."',
    ],
    'Cyber Security': [
      '"The interactive lab simulations in Canvas are excellent. Being able to practice in a sandboxed environment builds real confidence."',
      '"Reading lists are curated and actually relevant — the lecturers clearly update them each year rather than recycling old material."',
    ],
    'Artificial Intelligence': [
      '"The annotated Jupyter notebooks shared through Canvas are invaluable — they serve as both a tutorial and a lasting reference."',
      '"Access to curated paper summaries and ArXiv reading packs through Canvas makes independent research far more manageable."',
    ],
    'ICT & Business': [
      '"The case study library on Canvas is extensive and well-organised. It saves hours compared to searching for industry examples yourself."',
      '"Guest lecture recordings are always uploaded promptly. Being able to rewatch them before client presentations is incredibly useful."',
    ],
    'HBO-ICT': [
      '"Canvas organisation is consistent across all modules — once you learn the layout you know exactly where to look for anything."',
      '"For commuter students like me, the asynchronous content means I can study effectively on the train. That flexibility matters enormously."',
    ],
    default: [
      '"Study materials are well organised in Canvas, always easy to find."',
      '"Great that there are also recordings of lectures, useful when sick or for revision."',
    ],
  },
  examencommissie: {
    'Software Engineering': [
      '"My exemption request was processed in three weeks, which felt reasonable. The outcome letter was clearly written."',
      '"The committee was ultimately fair but I had to follow up twice before receiving a status update. A tracking portal would help."',
    ],
    'Cyber Security': [
      '"I waited six weeks for a response on a deferral request. By the time it arrived the exam period had already passed."',
      '"The outcome was eventually fine, but the lack of any communication during the wait caused real and unnecessary anxiety."',
    ],
    'Artificial Intelligence': [
      '"I submitted one request in two years and it was handled professionally and clearly. No complaints at all."',
      '"The process is formal and takes time, but the decision was well-reasoned and the reasoning was communicated clearly."',
    ],
    'ICT & Business': [
      '"The committee website is unclear about which form to submit for which request type. I had to ask three different people."',
      '"Once I navigated the process, the response was fair. But it should not require that much effort just to get started."',
    ],
    'HBO-ICT': [
      '"Response times are inconsistent — classmates heard back in two weeks while mine took two months for the same type of request."',
      '"The procedures themselves are fine but communication during the waiting period is almost non-existent. A simple status email would go a long way."',
    ],
    default: [
      '"The exam committee responds slowly to requests, making it difficult to plan my studies."',
      '"Eventually well assisted, but the process to get there was unclear."',
    ],
  },
  stagebegeleiding: {
    'Software Engineering': [
      '"My workplace supervisor and academic coach held a joint midpoint meeting. That coordination made the feedback far more actionable."',
      '"The internship portal on Canvas kept everything in one place — learning goals, reflections, and supervisor reports all together."',
    ],
    'Cyber Security': [
      '"Being placed at a company with a mature SOC team meant my academic supervisor could set genuinely challenging learning goals."',
      '"Contact moments were scheduled every three weeks — enough to stay connected and supported without feeling micromanaged."',
    ],
    'Artificial Intelligence': [
      '"My supervisor had a research background and understood my ML project deeply. The quality of guidance was on a different level."',
      '"The structured learning goal framework gave the internship real academic rigour while still allowing practical flexibility."',
    ],
    'ICT & Business': [
      '"My mentor understood both the technical and business dimensions of my role. That dual perspective made the guidance uniquely valuable."',
      '"A three-way meeting with my workplace manager and academic supervisor aligned everyone\'s expectations from the start."',
    ],
    'HBO-ICT': [
      '"On the dual track, my workplace and academic mentors communicated regularly. I never felt like I was navigating two separate worlds."',
      '"The internship guidance structure has clearly improved — far more structured than what students who graduated two years ago describe."',
    ],
    default: [
      '"My internship supervisor was always reachable and actively thought along about my learning goals."',
      '"Great that the school also monitors the internship progress, it made me feel less alone."',
    ],
  },
}

// ── Per-opleiding data profiles ───────────────────────────────────────────────
export const OPLEIDING_PROFILES = {
  'Software Engineering': {
    begeleiding:     { percentage: 18, sentiment: 'positive', sentimentScore: 72, sentimentBreakdown: { positive: 72, neutral: 18, negative: 10 }, trend: [12, 14, 17, 18], comparison: { voltijd: 78, deeltijd: 62, duaal: 45 } },
    faciliteiten:    { percentage: 14, sentiment: 'neutral',  sentimentScore: 54, sentimentBreakdown: { positive: 54, neutral: 28, negative: 18 }, trend: [16, 15, 13, 14], comparison: { voltijd: 68, deeltijd: 71, duaal: 60 } },
    groepsprojecten: { percentage:  9, sentiment: 'neutral',  sentimentScore: 48, sentimentBreakdown: { positive: 48, neutral: 32, negative: 20 }, trend: [10,  9,  8,  9], comparison: { voltijd: 55, deeltijd: 48, duaal: 52 } },
    roosters:        { percentage:  8, sentiment: 'critical', sentimentScore: 28, sentimentBreakdown: { positive: 28, neutral: 22, negative: 50 }, trend: [11, 10,  9,  8], comparison: { voltijd: 38, deeltijd: 29, duaal: 35 } },
    leeromgeving:    { percentage: 11, sentiment: 'positive', sentimentScore: 65, sentimentBreakdown: { positive: 65, neutral: 25, negative: 10 }, trend: [ 9, 10, 11, 11], comparison: { voltijd: 72, deeltijd: 68, duaal: 61 } },
    examencommissie: { percentage:  4, sentiment: 'neutral',  sentimentScore: 44, sentimentBreakdown: { positive: 44, neutral: 36, negative: 20 }, trend: [ 3,  4,  4,  4], comparison: { voltijd: 50, deeltijd: 45, duaal: 40 } },
    stagebegeleiding:{ percentage:  7, sentiment: 'positive', sentimentScore: 61, sentimentBreakdown: { positive: 61, neutral: 27, negative: 12 }, trend: [ 5,  6,  7,  7], comparison: { voltijd: 70, deeltijd: 55, duaal: 65 } },
  },
  'Cyber Security': {
    begeleiding:     { percentage: 15, sentiment: 'neutral',  sentimentScore: 55, sentimentBreakdown: { positive: 55, neutral: 28, negative: 17 }, trend: [10, 12, 14, 15], comparison: { voltijd: 65, deeltijd: 52, duaal: 40 } },
    faciliteiten:    { percentage: 12, sentiment: 'neutral',  sentimentScore: 50, sentimentBreakdown: { positive: 50, neutral: 30, negative: 20 }, trend: [13, 13, 12, 12], comparison: { voltijd: 62, deeltijd: 67, duaal: 55 } },
    groepsprojecten: { percentage:  7, sentiment: 'neutral',  sentimentScore: 45, sentimentBreakdown: { positive: 45, neutral: 35, negative: 20 }, trend: [ 8,  7,  7,  7], comparison: { voltijd: 50, deeltijd: 44, duaal: 48 } },
    roosters:        { percentage: 11, sentiment: 'critical', sentimentScore: 24, sentimentBreakdown: { positive: 24, neutral: 20, negative: 56 }, trend: [14, 13, 12, 11], comparison: { voltijd: 32, deeltijd: 25, duaal: 30 } },
    leeromgeving:    { percentage: 16, sentiment: 'positive', sentimentScore: 70, sentimentBreakdown: { positive: 70, neutral: 22, negative:  8 }, trend: [12, 13, 15, 16], comparison: { voltijd: 75, deeltijd: 70, duaal: 63 } },
    examencommissie: { percentage:  6, sentiment: 'critical', sentimentScore: 35, sentimentBreakdown: { positive: 35, neutral: 30, negative: 35 }, trend: [ 5,  5,  6,  6], comparison: { voltijd: 42, deeltijd: 38, duaal: 35 } },
    stagebegeleiding:{ percentage: 12, sentiment: 'positive', sentimentScore: 67, sentimentBreakdown: { positive: 67, neutral: 24, negative:  9 }, trend: [ 8,  9, 11, 12], comparison: { voltijd: 73, deeltijd: 58, duaal: 70 } },
  },
  'Artificial Intelligence': {
    begeleiding:     { percentage: 20, sentiment: 'positive', sentimentScore: 78, sentimentBreakdown: { positive: 78, neutral: 15, negative:  7 }, trend: [14, 16, 19, 20], comparison: { voltijd: 82, deeltijd: 66, duaal: 50 } },
    faciliteiten:    { percentage: 10, sentiment: 'critical', sentimentScore: 38, sentimentBreakdown: { positive: 38, neutral: 22, negative: 40 }, trend: [14, 13, 11, 10], comparison: { voltijd: 45, deeltijd: 50, duaal: 42 } },
    groepsprojecten: { percentage: 11, sentiment: 'positive', sentimentScore: 60, sentimentBreakdown: { positive: 60, neutral: 28, negative: 12 }, trend: [ 8,  9, 10, 11], comparison: { voltijd: 65, deeltijd: 55, duaal: 58 } },
    roosters:        { percentage:  6, sentiment: 'neutral',  sentimentScore: 45, sentimentBreakdown: { positive: 45, neutral: 30, negative: 25 }, trend: [ 9,  8,  7,  6], comparison: { voltijd: 48, deeltijd: 38, duaal: 42 } },
    leeromgeving:    { percentage: 18, sentiment: 'positive', sentimentScore: 74, sentimentBreakdown: { positive: 74, neutral: 20, negative:  6 }, trend: [13, 15, 17, 18], comparison: { voltijd: 78, deeltijd: 72, duaal: 65 } },
    examencommissie: { percentage:  3, sentiment: 'neutral',  sentimentScore: 50, sentimentBreakdown: { positive: 50, neutral: 35, negative: 15 }, trend: [ 3,  3,  3,  3], comparison: { voltijd: 55, deeltijd: 48, duaal: 44 } },
    stagebegeleiding:{ percentage:  9, sentiment: 'positive', sentimentScore: 64, sentimentBreakdown: { positive: 64, neutral: 26, negative: 10 }, trend: [ 6,  7,  8,  9], comparison: { voltijd: 70, deeltijd: 56, duaal: 66 } },
  },
  'ICT & Business': {
    begeleiding:     { percentage: 16, sentiment: 'neutral',  sentimentScore: 58, sentimentBreakdown: { positive: 58, neutral: 25, negative: 17 }, trend: [11, 13, 15, 16], comparison: { voltijd: 68, deeltijd: 70, duaal: 55 } },
    faciliteiten:    { percentage: 15, sentiment: 'positive', sentimentScore: 62, sentimentBreakdown: { positive: 62, neutral: 26, negative: 12 }, trend: [14, 14, 15, 15], comparison: { voltijd: 66, deeltijd: 74, duaal: 62 } },
    groepsprojecten: { percentage: 13, sentiment: 'neutral',  sentimentScore: 52, sentimentBreakdown: { positive: 52, neutral: 30, negative: 18 }, trend: [11, 12, 12, 13], comparison: { voltijd: 58, deeltijd: 62, duaal: 55 } },
    roosters:        { percentage:  9, sentiment: 'critical', sentimentScore: 32, sentimentBreakdown: { positive: 32, neutral: 25, negative: 43 }, trend: [12, 11, 10,  9], comparison: { voltijd: 40, deeltijd: 32, duaal: 37 } },
    leeromgeving:    { percentage: 10, sentiment: 'positive', sentimentScore: 60, sentimentBreakdown: { positive: 60, neutral: 28, negative: 12 }, trend: [ 8,  9, 10, 10], comparison: { voltijd: 65, deeltijd: 66, duaal: 58 } },
    examencommissie: { percentage:  5, sentiment: 'neutral',  sentimentScore: 46, sentimentBreakdown: { positive: 46, neutral: 36, negative: 18 }, trend: [ 4,  4,  5,  5], comparison: { voltijd: 50, deeltijd: 52, duaal: 44 } },
    stagebegeleiding:{ percentage:  8, sentiment: 'positive', sentimentScore: 65, sentimentBreakdown: { positive: 65, neutral: 25, negative: 10 }, trend: [ 6,  7,  7,  8], comparison: { voltijd: 68, deeltijd: 72, duaal: 64 } },
  },
  'HBO-ICT': {
    begeleiding:     { percentage: 17, sentiment: 'neutral',  sentimentScore: 60, sentimentBreakdown: { positive: 60, neutral: 24, negative: 16 }, trend: [11, 13, 16, 17], comparison: { voltijd: 70, deeltijd: 60, duaal: 48 } },
    faciliteiten:    { percentage: 13, sentiment: 'neutral',  sentimentScore: 52, sentimentBreakdown: { positive: 52, neutral: 30, negative: 18 }, trend: [15, 14, 13, 13], comparison: { voltijd: 60, deeltijd: 65, duaal: 57 } },
    groepsprojecten: { percentage: 10, sentiment: 'neutral',  sentimentScore: 50, sentimentBreakdown: { positive: 50, neutral: 32, negative: 18 }, trend: [ 9,  9, 10, 10], comparison: { voltijd: 52, deeltijd: 46, duaal: 50 } },
    roosters:        { percentage: 14, sentiment: 'critical', sentimentScore: 26, sentimentBreakdown: { positive: 26, neutral: 22, negative: 52 }, trend: [17, 16, 15, 14], comparison: { voltijd: 35, deeltijd: 27, duaal: 32 } },
    leeromgeving:    { percentage: 12, sentiment: 'positive', sentimentScore: 66, sentimentBreakdown: { positive: 66, neutral: 24, negative: 10 }, trend: [10, 11, 12, 12], comparison: { voltijd: 70, deeltijd: 66, duaal: 60 } },
    examencommissie: { percentage:  5, sentiment: 'neutral',  sentimentScore: 42, sentimentBreakdown: { positive: 42, neutral: 38, negative: 20 }, trend: [ 4,  4,  5,  5], comparison: { voltijd: 46, deeltijd: 42, duaal: 38 } },
    stagebegeleiding:{ percentage:  8, sentiment: 'neutral',  sentimentScore: 56, sentimentBreakdown: { positive: 56, neutral: 30, negative: 14 }, trend: [ 6,  7,  7,  8], comparison: { voltijd: 62, deeltijd: 50, duaal: 60 } },
  },
}

// ── Study mode modifiers ──────────────────────────────────────────────────────
const STUDIEVORM_MODIFIERS = {
  'All': {},
  'Full-time': {
    begeleiding:     { scoreDelta: +4,  positiveDelta: +4,  negativeDelta: -3,  percentageDelta: +2 },
    roosters:        { scoreDelta: +2,  positiveDelta: +2,  negativeDelta: -4,  percentageDelta: -1 },
    groepsprojecten: { scoreDelta: +5,  positiveDelta: +5,  negativeDelta: -4,  percentageDelta: +1 },
    leeromgeving:    { scoreDelta: +3,  positiveDelta: +3,  negativeDelta: -2,  percentageDelta: +1 },
  },
  'Part-time': {
    begeleiding:     { scoreDelta: -8,  positiveDelta: -8,  negativeDelta: +6,  percentageDelta: -2 },
    roosters:        { scoreDelta: -10, positiveDelta: -8,  negativeDelta: +10, percentageDelta: +2 },
    faciliteiten:    { scoreDelta: +5,  positiveDelta: +5,  negativeDelta: -4,  percentageDelta: +2 },
    stagebegeleiding:{ scoreDelta: -4,  positiveDelta: -4,  negativeDelta: +3,  percentageDelta: -2 },
  },
  'Dual': {
    stagebegeleiding:{ scoreDelta: +12, positiveDelta: +12, negativeDelta: -8,  percentageDelta: +4 },
    begeleiding:     { scoreDelta: +6,  positiveDelta: +6,  negativeDelta: -4,  percentageDelta: +2 },
    roosters:        { scoreDelta: -6,  positiveDelta: -6,  negativeDelta: +8,  percentageDelta: +2 },
    groepsprojecten: { scoreDelta: +4,  positiveDelta: +4,  negativeDelta: -3,  percentageDelta: +1 },
  },
}

// ── Location modifiers ────────────────────────────────────────────────────────
const LOCATIE_MODIFIERS = {
  'All locations': {},
  'Eindhoven': {},
  'Tilburg': {
    faciliteiten:    { scoreDelta: +6,  positiveDelta: +6,  negativeDelta: -5,  percentageDelta: +2 },
    roosters:        { scoreDelta: -4,  positiveDelta: -4,  negativeDelta: +5,  percentageDelta: +1 },
  },
  'Den Bosch': {
    begeleiding:     { scoreDelta: -5,  positiveDelta: -5,  negativeDelta: +4,  percentageDelta: -2 },
    leeromgeving:    { scoreDelta: +7,  positiveDelta: +7,  negativeDelta: -5,  percentageDelta: +2 },
  },
  'Venlo': {
    stagebegeleiding:{ scoreDelta: +8,  positiveDelta: +8,  negativeDelta: -6,  percentageDelta: +3 },
    examencommissie: { scoreDelta: -6,  positiveDelta: -6,  negativeDelta: +5,  percentageDelta: -1 },
  },
}

// ── Academic year modifiers ───────────────────────────────────────────────────
const JAAR_MODIFIERS = {
  '2022/2023': {
    leeromgeving:    { scoreDelta: -6, percentageDelta: -3 },
    roosters:        { scoreDelta: -4, percentageDelta: +3 },
    begeleiding:     { scoreDelta: -4, percentageDelta: -2 },
    faciliteiten:    { scoreDelta: -2, percentageDelta: -1 },
  },
  '2023/2024': {
    leeromgeving:    { scoreDelta: -3, percentageDelta: -1 },
    roosters:        { scoreDelta: -2, percentageDelta: +1 },
    faciliteiten:    { scoreDelta: +2, percentageDelta: +1 },
    begeleiding:     { scoreDelta: -2, percentageDelta: -1 },
  },
  '2024/2025': {},
  '2025/2026': {
    begeleiding:     { scoreDelta: +3, percentageDelta: +1 },
    leeromgeving:    { scoreDelta: +2, percentageDelta: +1 },
    roosters:        { scoreDelta: -2, percentageDelta: -1 },
    stagebegeleiding:{ scoreDelta: +3, percentageDelta: +1 },
  },
}

// ── Cohort modifiers ──────────────────────────────────────────────────────────
const COHORT_MODIFIERS = {
  'All': {},
  '2022': {
    begeleiding:     { scoreDelta: +5, percentageDelta: -1 },
    examencommissie: { scoreDelta: +4, percentageDelta: +1 },
    faciliteiten:    { scoreDelta: +3, percentageDelta: +2 },
  },
  '2023': {
    groepsprojecten: { scoreDelta: -3, percentageDelta: +2 },
    examencommissie: { scoreDelta: -3, percentageDelta: +1 },
    leeromgeving:    { scoreDelta: -2, percentageDelta: -1 },
  },
  '2024': {
    roosters:        { scoreDelta: -3, percentageDelta: +1 },
    groepsprojecten: { scoreDelta: -4, percentageDelta: +2 },
    leeromgeving:    { scoreDelta: +2, percentageDelta: +1 },
    faciliteiten:    { scoreDelta: -2, percentageDelta: -1 },
  },
  '2025': {
    leeromgeving:    { scoreDelta: +3, percentageDelta: +2 },
    stagebegeleiding:{ scoreDelta: -2, percentageDelta: -1 },
    faciliteiten:    { scoreDelta: -3, percentageDelta: -1 },
    begeleiding:     { scoreDelta: +2, percentageDelta: +1 },
  },
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function clamp(v, min = 0, max = 100) { return Math.max(min, Math.min(max, v)) }

function applyModifiers(stats, ...modSets) {
  let s  = { ...stats }
  let bd = { ...stats.sentimentBreakdown }
  for (const mods of modSets) {
    if (!mods) continue
    if (mods.scoreDelta)      s.sentimentScore = clamp(s.sentimentScore + mods.scoreDelta)
    if (mods.positiveDelta)   bd.positive      = clamp(bd.positive + mods.positiveDelta)
    if (mods.negativeDelta)   bd.negative      = clamp(bd.negative + mods.negativeDelta)
    if (mods.percentageDelta) s.percentage     = clamp(s.percentage + mods.percentageDelta, 1, 35)
  }
  bd.neutral = clamp(100 - bd.positive - bd.negative)
  if (s.sentimentScore >= 65)      s.sentiment = 'positive'
  else if (s.sentimentScore <= 38) s.sentiment = 'critical'
  else                             s.sentiment = 'neutral'
  s.sentimentLabel =
    s.sentimentScore >= 75 ? 'Very Positive' :
    s.sentimentScore >= 60 ? 'Positive' :
    s.sentimentScore >= 45 ? 'Mixed' :
    s.sentimentScore >= 30 ? 'Neutral' : 'Critical'
  s.sentimentBreakdown = bd
  return s
}

// ── Main data builder ─────────────────────────────────────────────────────────
export function getFilteredThemes(filters) {
  const { opleiding, studievorm, locatie, jaar, cohort } = filters
  const profile    = OPLEIDING_PROFILES[opleiding] || OPLEIDING_PROFILES['Software Engineering']
  const svMods     = STUDIEVORM_MODIFIERS[studievorm] || {}
  const locMods    = LOCATIE_MODIFIERS[locatie]       || {}
  const jaarMods   = JAAR_MODIFIERS[jaar]             || {}
  const cohortMods = COHORT_MODIFIERS[cohort]         || {}

  return BASE_THEMES.map((base) => {
    const profileData = profile[base.id]
    const merged = applyModifiers(
      profileData,
      svMods[base.id],
      locMods[base.id],
      jaarMods[base.id],
      cohortMods[base.id],
    )
    const aiSummary = AI_SUMMARIES[base.id]?.[opleiding] ?? AI_SUMMARIES[base.id]?.default ?? base.aiSummary
    const quotes    = QUOTES[base.id]?.[opleiding]       ?? QUOTES[base.id]?.default       ?? base.quotes
    return { ...base, ...merged, aiSummary, quotes }
  })
}

// Default themes (Software Engineering, All, All locations, 2025/2026, All)
export const THEMES = getFilteredThemes({
  opleiding:  'Software Engineering',
  studievorm: 'All',
  locatie:    'All locations',
  jaar:       '2025/2026',
  cohort:     'All',
})

export const PROGRAMMES = [
  { id: 'se',  name: 'Software Engineering',   year: '2024/2025', respondents: 432 },
  { id: 'cs',  name: 'Cyber Security',          year: '2024/2025', respondents: 287 },
  { id: 'ai',  name: 'Artificial Intelligence', year: '2024/2025', respondents: 198 },
  { id: 'ict', name: 'ICT & Business',           year: '2024/2025', respondents: 311 },
]

export const COMPARISON_DATA = {
  se:  { inhoud: 4.4, docenten: 3.8, sfeer: 4.6, begeleiding: 3.2, toetsing: 4.0, faciliteiten: 3.7, beroep: 4.5, planning: 3.6, betrokken: 4.2, studielast: 3.9 },
  cs:  { inhoud: 4.1, docenten: 4.3, sfeer: 4.2, begeleiding: 3.5, toetsing: 3.9, faciliteiten: 4.1, beroep: 4.4, planning: 3.3, betrokken: 3.9, studielast: 3.7 },
  ai:  { inhoud: 4.6, docenten: 4.1, sfeer: 4.0, begeleiding: 3.8, toetsing: 3.7, faciliteiten: 3.5, beroep: 4.7, planning: 3.4, betrokken: 4.4, studielast: 4.1 },
  ict: { inhoud: 4.2, docenten: 3.9, sfeer: 4.3, begeleiding: 3.6, toetsing: 3.8, faciliteiten: 4.0, beroep: 4.1, planning: 3.7, betrokken: 4.0, studielast: 3.8 },
}

export const COMPARISON_LABELS = {
  inhoud: 'Content', docenten: 'Lecturers', sfeer: 'Atmosphere', begeleiding: 'Guidance',
  toetsing: 'Assessment', faciliteiten: 'Facilities', beroep: 'Career',
  planning: 'Planning', betrokken: 'Engagement', studielast: 'Workload',
}
