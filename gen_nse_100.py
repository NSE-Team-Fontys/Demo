"""
Generate 100-row NSE survey CSV.
- Every answer to every open-text question is unique (guaranteed by PII injection into every template)
- 20 rows (~20%) have English answers
- No Label1-7 data
- Comma-separated, UTF-8 BOM
"""
import pandas as pd
import random

random.seed(99)

# ── Columns ───────────────────────────────────────────────────────────────────
COLUMNS = [
    'Jaar','Actuele BRIN-code volgens RIO','Actuele naam instelling volgens RIO',
    'Actuele CROHO-code volgens RIO','Actuele Opleidingsnaam volgens RIO',
    'Actuele BRIN-volgnummer volgens RIO','Type Student','Opleidingsvorm (vt dt du)',
    'Label1','Label2','Label3','Label4','Label5','Label6','Label7',
    'Leerroute_Track','Studiejaar volgens instelling','Kunstopleiding','Afstandsonderwijs',
    'Wil jij zelf iets kwijt over je opleiding dat nog niet aan bod is gekomen?',
    'Wil jij je opleiding nog iets meegeven over de inhoud en opzet van het onderwijs?',
    'Themascore Inhoud en opzet van het onderwijs',
    'Wil jij je opleiding nog iets meegeven over de aansluiting op de beroepspraktijk / beroepsloopbaan?',
    'Themascore Aansluiting beroepspraktijk / beroepsloopbaan (antwoord n.v.t. Toegevoegd aan het thema vanaf 2022)',
    'Wil jij je opleiding nog iets meegeven over de docenten aan je opleiding?',
    'Themascore Docenten aan de opleiding',
    'Wil jij je opleiding nog iets meegeven over de studiebegeleiding?',
    "Themascore Studiebegeleiding (antwoordoptie 'Weet ik niet/niet van toepassing' toegevoegd vanaf 2023)",
    'Wil jij je opleiding nog iets meegeven over toetsing en beoordeling?',
    'Themascore Toetsing en beoordeling',
    'Wil jij je opleiding nog iets meegeven over betrokkenheid en contact?',
    'Themascore Betrokkenheid en contact',
    'Wat voor soort belemmeringen ervaar je? Anders, namelijk:',
    'Waarom heb je jouw bijzondere omstandigheden niet gemeld bij de onderwijsinstelling? Anders, namelijk:',
    'Waarom studeer je onder bijzondere omstandigheden? Anders, namelijk:',
    'Wil jij je opleiding nog iets meegeven over studeren onder bijzondere omstandigheden?',
    'Wil jij je opleiding nog iets meegeven over de vaardigheden die je leert in je opleiding?',
    'Themascore Algemene vaardigheden',
    'Themascore Wetenschappelijke vaardigheden',
    'Themascore Praktijkgericht onderzoek',
    'Wil jij je opleiding nog iets meegeven over de studieroosters?',
    'Themascore Studieroosters',
    'Wil jij je opleiding nog iets meegeven over de studielast?',
    'Themascore Studielast',
    'Wil jij je opleiding nog iets meegeven over de groepsgrootte?',
    'Wil jij je opleiding nog iets meegeven over stages?',
    'Themascore Stages opleiding',
    'Themascore Stages ervaring',
    'Wil jij je opleiding nog iets meegeven over uitdaging en inzet?',
    'Themascore Uitdaging en inzet',
    'Wil jij je opleiding nog iets meegeven over de internationale aspecten van je opleiding?',
    'Themascore Internationale aspecten',
    'Wil jij je opleiding nog iets meegeven over je ervaringen als internationale student?',
    'Themascore Internationale studenten',
    'Wil jij je opleiding nog iets meegeven over de structuur en samenhang van je opleiding?',
    'Themascore Structuur en samenhang opleiding',
    'Wil jij je opleiding nog iets meegeven over de wijze waarop je nieuwe kennis en vaardigheden leert?',
    'Themascore Verdiepend leren',
    'Wil jij je opleiding nog iets meegeven over het verbinden van kennis en ideeen?',
    'Themascore Reflectie',
    'Wil jij je opleiding nog iets meegeven over het afstandsonderwijs?',
    'Themascore Afstandsonderwijs',
    'Wil jij je opleiding nog iets meegeven over de studiefaciliteiten?',
    'Themascore Studiefaciliteiten',
    'Wil jij je opleiding nog iets meegeven over de medezeggenschap?',
    'Themascore Medezeggenschap',
    'Wil jij je opleiding nog iets meegeven over gelijke behandeling?',
    'Themascore Gelijke behandeling',
    'Wil jij je opleiding nog iets meegeven over de flexibiliteit van het studieprogramma?',
    'Themascore Flexibiliteit studieprogramma',
    'Wil jij je opleiding nog iets meegeven over artistieke ontwikkeling en faciliteiten?',
    'Themascore Kunstonderwijs',
    'Wil jij je opleiding nog iets meegeven over online onderwijs?',
    'Themascore Online onderwijs',
    'Wil jij je opleiding nog iets meegeven over welzijn?',
    'Themascore Welzijn',
]

# ── 100 unique students with varied PII types ─────────────────────────────────
DUTCH_STUDENTS = [
    ("Emma de Vries","emma.devries@student.fontys.nl","12 maart 2004","Koningstraat 14, 5014 AB Tilburg","06-48291035"),
    ("Liam Janssen","liam.janssen@gmail.com","22 juli 2003","Dennenweg 7, 5627 HJ Eindhoven","06-39182746"),
    ("Sophie Bakker","s.bakker@student.fontys.nl","5 november 2002","Vestdijk 51, 5611 CA Eindhoven","06-72910384"),
    ("Noah Pietersen","n.pietersen@outlook.com","30 april 1998","Wilhelminaplein 9, 5611 HC Eindhoven","06-18374920"),
    ("Julia van den Berg","julia.vandenberg@hotmail.com","9 januari 2004","Stationsplein 17, 5611 AC Eindhoven","06-19283746"),
    ("Daan Smits","daan.smits@student.fontys.nl","18 mei 2003","Dommelstraat 4, 5611 CJ Eindhoven","06-28374615"),
    ("Fleur Willems","fleur.willems@gmail.com","30 september 2002","Heuvelstraat 19, 5038 AK Tilburg","06-37481920"),
    ("Lars de Boer","lars.deboer@student.fontys.nl","20 mei 2002","Spoorlaan 35, 5038 CC Tilburg","06-46291837"),
    ("Marieke Hendricks","marieke.h@fontys.nl","25 augustus 2000","Nieuwlandstraat 7, 5038 SM Tilburg","06-55182746"),
    ("Sander Meijer","sander.meijer@student.fontys.nl","14 februari 2003","Piusstraat 45, 5017 JK Tilburg","06-64273815"),
    ("Roos Vermeer","roos.vermeer@outlook.com","3 december 2001","Ringbaan Noord 60, 5025 KE Tilburg","06-73164920"),
    ("Joris van Dijk","joris.vandijk@student.fontys.nl","7 augustus 2003","Parallelweg 3, 5611 AH Eindhoven","06-82055037"),
    ("Anouk Brouwer","anouk.brouwer@hotmail.com","21 juni 2004","Grote Gracht 22, 6211 SZ Maastricht","06-91946146"),
    ("Tim Visser","tim.visser@student.fontys.nl","9 april 2002","Begijnenhof 12, 5611 EL Eindhoven","06-10837255"),
    ("Lotte Mulder","lotte.mulder@gmail.com","27 november 2003","Jan van Lieshoutstraat 8, 5611 EE Eindhoven","06-29728364"),
    ("Bram Peters","bram.peters@student.fontys.nl","15 juli 2001","Koningstraat 22, 5014 AC Tilburg","06-38619473"),
    ("Iris Hendriks","iris.hendriks@outlook.com","8 maart 2002","Dennenweg 19, 5627 HK Eindhoven","06-47510582"),
    ("Wouter Jacobs","wouter.jacobs@student.fontys.nl","19 september 2003","Vestdijk 67, 5611 CB Eindhoven","06-56401691"),
    ("Noor van Leeuwen","n.vanleeuwen@student.fontys.nl","28 februari 2004","Wilhelminaplein 3, 5611 HA Eindhoven","06-65292800"),
    ("Thijs Dekker","thijs.dekker@gmail.com","11 juni 2002","Stationsplein 5, 5611 AB Eindhoven","06-74183909"),
    ("Lisanne Bos","lisanne.bos@student.fontys.nl","4 oktober 2003","Dommelstraat 12, 5611 CK Eindhoven","06-83075018"),
    ("Koen de Graaf","koen.degraaf@hotmail.com","22 mei 2001","Heuvelstraat 33, 5038 AL Tilburg","06-92966127"),
    ("Amber Lammers","amber.lammers@student.fontys.nl","16 juli 2004","Spoorlaan 49, 5038 CD Tilburg","06-11857236"),
    ("Stijn van Beek","stijn.vanbeek@gmail.com","30 januari 2002","Nieuwlandstraat 15, 5038 SN Tilburg","06-20748345"),
    ("Femke Kuiper","femke.kuiper@student.fontys.nl","12 april 2003","Piusstraat 61, 5017 JL Tilburg","06-29639454"),
    ("Ruben Hoekstra","ruben.hoekstra@outlook.com","3 augustus 2001","Ringbaan Noord 74, 5025 KF Tilburg","06-38530563"),
    ("Bo Prins","bo.prins@student.fontys.nl","25 september 2004","Parallelweg 17, 5611 AJ Eindhoven","06-47421672"),
    ("Tijn Vlak","tijn.vlak@gmail.com","17 maart 2003","Grote Gracht 36, 6211 TA Maastricht","06-56312781"),
    ("Merel van Oss","merel.vanoss@student.fontys.nl","8 december 2002","Begijnenhof 24, 5611 EM Eindhoven","06-65203890"),
    ("Gijs Naber","gijs.naber@hotmail.com","14 november 2001","Jan van Lieshoutstraat 20, 5611 EF Eindhoven","06-74094999"),
    ("Pien Veldman","pien.veldman@student.fontys.nl","7 mei 2004","Koningstraat 30, 5014 AD Tilburg","06-82986008"),
    ("Niels Koster","niels.koster@gmail.com","23 augustus 2002","Dennenweg 31, 5627 HL Eindhoven","06-91877117"),
    ("Vera Bosman","vera.bosman@student.fontys.nl","30 juni 2003","Vestdijk 83, 5611 CC Eindhoven","06-10768226"),
    ("Rick van Rijn","rick.vanrijn@outlook.com","18 april 2001","Wilhelminaplein 15, 5611 HD Eindhoven","06-19659335"),
    ("Sofie Timmermans","sofie.timmermans@student.fontys.nl","2 oktober 2004","Stationsplein 23, 5611 AD Eindhoven","06-28550444"),
    ("Bas Hermans","bas.hermans@gmail.com","14 juli 2002","Dommelstraat 20, 5611 CL Eindhoven","06-37441553"),
    ("Lena Schouten","lena.schouten@student.fontys.nl","5 januari 2003","Heuvelstraat 47, 5038 AM Tilburg","06-46332662"),
    ("Jesse van der Meer","jesse.vandermeer@hotmail.com","27 september 2001","Spoorlaan 63, 5038 CE Tilburg","06-55223771"),
    ("Hanna Groot","hanna.groot@student.fontys.nl","20 april 2004","Nieuwlandstraat 23, 5038 SP Tilburg","06-64114880"),
    ("Tom Verhoeven","tom.verhoeven@gmail.com","16 februari 2002","Piusstraat 77, 5017 JM Tilburg","06-73005989"),
    ("Kim Evers","kim.evers@student.fontys.nl","11 december 2003","Ringbaan Noord 88, 5025 KG Tilburg","06-81897098"),
    ("Dani van Wijk","dani.vanwijk@outlook.com","8 juni 2001","Parallelweg 31, 5611 AK Eindhoven","06-90788107"),
    ("Sara Postma","sara.postma@student.fontys.nl","31 augustus 2004","Grote Gracht 50, 6211 TB Maastricht","06-09679216"),
    ("Max Fontijn","max.fontijn@gmail.com","19 oktober 2002","Begijnenhof 36, 5611 EN Eindhoven","06-18570325"),
    ("Eline Huisman","eline.huisman@student.fontys.nl","3 juli 2003","Jan van Lieshoutstraat 32, 5611 EG Eindhoven","06-27461434"),
    ("Arjan Blom","arjan.blom@hotmail.com","24 maart 2001","Koningstraat 38, 5014 AE Tilburg","06-36352543"),
    ("Chantal Vogel","chantal.vogel@student.fontys.nl","17 november 2004","Dennenweg 43, 5627 HM Eindhoven","06-45243652"),
    ("Dylan van den Hout","dylan.vandenhout@gmail.com","6 mei 2002","Vestdijk 99, 5611 CD Eindhoven","06-54134761"),
    ("Manon Kok","manon.kok@student.fontys.nl","22 februari 2003","Wilhelminaplein 21, 5611 HE Eindhoven","06-63025870"),
    ("Simon van Veen","simon.vanveen@outlook.com","10 oktober 2001","Stationsplein 31, 5611 AE Eindhoven","06-71916979"),
    ("Lisa van Dam","lisa.vandam@student.fontys.nl","14 augustus 2003","Dommelstraat 28, 5611 CM Eindhoven","06-80808088"),
    ("Pieter Hubers","pieter.hubers@gmail.com","9 februari 2002","Heuvelstraat 61, 5038 AN Tilburg","06-89699197"),
    ("Jolien Bergman","jolien.bergman@student.fontys.nl","26 november 2004","Spoorlaan 77, 5038 CF Tilburg","06-98590206"),
    ("Cas van Horssen","cas.vanhorssen@hotmail.com","13 juli 2001","Nieuwlandstraat 31, 5038 SR Tilburg","06-17481315"),
    ("Natasja Wit","natasja.wit@student.fontys.nl","5 april 2003","Piusstraat 93, 5017 JN Tilburg","06-26372424"),
    ("Robin de Haan","robin.dehaan@gmail.com","21 september 2002","Ringbaan Noord 102, 5025 KH Tilburg","06-35263533"),
    ("Eva Lubbers","eva.lubbers@student.fontys.nl","3 januari 2004","Parallelweg 45, 5611 AL Eindhoven","06-44154642"),
    ("Jeroen Westra","jeroen.westra@outlook.com","18 juni 2001","Grote Gracht 64, 6211 TC Maastricht","06-53045751"),
    ("Mirjam Ooms","mirjam.ooms@student.fontys.nl","12 oktober 2003","Begijnenhof 48, 5611 EP Eindhoven","06-61936860"),
    ("Kevin Stam","kevin.stam@gmail.com","28 maart 2002","Jan van Lieshoutstraat 44, 5611 EH Eindhoven","06-70827969"),
    ("Claire Donkers","claire.donkers@student.fontys.nl","7 december 2004","Koningstraat 46, 5014 AF Tilburg","06-79719078"),
    ("Niels van Zutphen","niels.vanzutphen@hotmail.com","23 mei 2001","Dennenweg 55, 5627 HN Eindhoven","06-88610187"),
]

INTL_STUDENTS = [
    ("Maximilian Schneider","max.schneider@student.fontys.nl","18 juni 2001","Duitsland","PP1234567"),
    ("Aisha Okonkwo","aisha.okonkwo@student.fontys.nl","14 september 2003","Nigeria",""),
    ("Kevin Tran","kevin.tran@student.fontys.nl","17 maart 2003","Vietnam","VN8876543"),
    ("Maria Gonzalez","maria.gonzalez@student.fontys.nl","22 juli 2002","Spanje","XB9087654"),
    ("Yuki Tanaka","yuki.tanaka@student.fontys.nl","30 november 2001","Japan","JP5544321"),
    ("Omar Hassan","o.hassan@student.fontys.nl","5 april 2003","Marokko",""),
    ("Ingrid Lindqvist","ingrid.lindqvist@student.fontys.nl","17 augustus 2002","Zweden","SE7788990"),
    ("Carlos Ferreira","c.ferreira@student.fontys.nl","28 februari 2001","Portugal","PT2233445"),
    ("Priya Sharma","priya.sharma@student.fontys.nl","14 juni 2003","India",""),
    ("Lucas Bernard","l.bernard@student.fontys.nl","9 september 2002","Frankrijk","FR8899001"),
    ("Fatima Al-Rashid","f.alrashid@student.fontys.nl","20 januari 2003","Jordanie",""),
    ("Tobias Weber","t.weber@student.fontys.nl","3 juli 2001","Duitsland","DE6677889"),
    ("Ana Popescu","ana.popescu@student.fontys.nl","25 december 2002","Roemenie","RO3344556"),
    ("Kwame Mensah","k.mensah@student.fontys.nl","11 mei 2003","Ghana",""),
    ("Elena Ivanova","e.ivanova@student.fontys.nl","7 maart 2002","Rusland","RU1122334"),
    ("Pierre Dubois","p.dubois@student.fontys.nl","19 oktober 2001","Belgie","BE5566778"),
    ("Layla Nasser","l.nasser@student.fontys.nl","8 februari 2004","Egypte",""),
    ("Stefan Novak","s.novak@student.fontys.nl","14 april 2002","Tsjechie","CZ9900112"),
    ("Amara Diallo","a.diallo@student.fontys.nl","29 augustus 2003","Senegal",""),
    ("Hana Kovac","h.kovac@student.fontys.nl","16 juni 2002","Kroatie","HR3456789"),
    ("Tomas Kral","t.kral@student.fontys.nl","23 januari 2001","Slowakije","SK6789012"),
    ("Nadia Petrov","n.petrov@student.fontys.nl","11 november 2003","Bulgarije","BG2345678"),
    ("Ali Celik","a.celik@student.fontys.nl","4 augustus 2002","Turkije","TR8901234"),
    ("Valentina Cruz","v.cruz@student.fontys.nl","17 februari 2004","Italie","IT4567890"),
    ("Rafael Santos","r.santos@student.fontys.nl","30 september 2001","Brazilie","BR7890123"),
    ("Ji-ho Kim","j.kim@student.fontys.nl","22 mei 2003","Zuid-Korea","KR0123456"),
    ("Miriam Flores","m.flores@student.fontys.nl","7 oktober 2002","Mexico","MX3456789"),
    ("Dmitri Volkov","d.volkov@student.fontys.nl","13 maart 2001","Oekraine","UA6789012"),
    ("Selin Aydin","s.aydin@student.fontys.nl","26 juli 2004","Turkije","TR9012345"),
    ("Nour Khalil","n.khalil@student.fontys.nl","18 april 2002","Libanon",""),
    ("Henrik Johansson","h.johansson@student.fontys.nl","5 september 2001","Zweden","SE1234567"),
    ("Isabel Ferreira","i.ferreira@student.fontys.nl","12 december 2003","Brazilie","BR4567890"),
    ("Luca Marino","l.marino@student.fontys.nl","27 februari 2002","Italie","IT7890123"),
    ("Zeynep Yilmaz","z.yilmaz@student.fontys.nl","9 juni 2004","Turkije","TR2345678"),
    ("Olena Kovalenko","o.kovalenko@student.fontys.nl","16 augustus 2001","Oekraine","UA5678901"),
    ("Marco Visconti","m.visconti@student.fontys.nl","3 november 2002","Italie","IT0123456"),
    ("Ayasha Patel","a.patel@student.fontys.nl","20 januari 2004","India",""),
    ("Pavel Novotny","p.novotny@student.fontys.nl","14 april 2001","Tsjechie","CZ3456789"),
    ("Chiara Romano","c.romano@student.fontys.nl","8 juli 2003","Italie","IT6789012"),
    ("Aarav Singh","a.singh@student.fontys.nl","25 oktober 2002","India",""),
]

# Combine to 100 students (60 Dutch, 40 international)
ALL_STUDENTS = DUTCH_STUDENTS[:60] + INTL_STUDENTS[:40]
random.shuffle(ALL_STUDENTS)

# Assign supplementary PII per student
SIDS   = [f"S20{17+i//20}{100+i}" for i in range(100)]
BSNS   = [f"{287000000+i*3173}" for i in range(100)]
IBANS  = [f"NL{10+i%89:02d}ABNA{4170000000+i*1234567}" for i in range(100)]
TRACKS = ["Software Engineering","Data Science","Artificial Intelligence","Cyber Security",
          "Embedded Systems","Business IT & Management","Media Design","ICT & Business",
          "Cloud & Security","UX Design","Game Development","DevOps Engineering"]
TYPES  = {"vt":"Voltijds","dt":"Deeltijds","du":"Duaal"}
DIAGS  = ["ADHD","dyslexie","autisme spectrum stoornis","angststoornis","PTSS",
          "dyscalculie","chronische migraine","depressie","burn-out","bipolaire stoornis"]
IPS    = [f"192.168.{1+i//25}.{10+i*3%240}" for i in range(100)]
TICKS  = [f"TK-2024{1000+i}" for i in range(100)]

# ── Template pools — EVERY template has at least one {placeholder} ────────────
# This guarantees uniqueness: different PII → different rendered string

T_FREE_NL = [
    "Ik ben {name} en ik vind dat de opleiding meer aandacht moet besteden aan professionele ontwikkeling buiten het technisch vakgebied.",
    "Als student {sid} wil ik kwijt dat er onvoldoende begeleiding is bij de keuze van een minor of specialisatie.",
    "Mijn mailadres {email} staat geregistreerd maar ik ontvang geen nieuwsbrief over studiemogelijkheden.",
    "Ik woon op {address} en de reistijd is lang. Een hybride rooster zou een groot verschil maken.",
    "Student {sid} hier: er zou een vak moeten komen over ethiek in technologie. Dat ontbreekt volledig.",
    "Ik, {name}, mis concrete loopbaanoriëntatie in het eerste jaar. Dat zou eerder moeten plaatsvinden.",
    "Via mijn e-mail {email} heb ik eerder al suggesties gedaan, maar die zijn nooit opgepikt.",
    "Ik wil als {name} aandacht vragen voor betere communicatie over roosterwijzigingen.",
    "Als student {sid} mis ik vakken over agile werken en projectmanagement in de praktijk.",
    "Mijn telefoonnummer {phone} staat bij de opleiding bekend, maar er wordt nooit actief contact gezocht.",
    "Ik, {name}, zou graag zien dat er een mentorprogramma komt waarbij ouderejaars eerstejaarsstudenten begeleiden.",
    "Student {sid} vraagt aandacht voor meer keuzevrijheid in het curriculum.",
    "Ik stuur dit bericht namens mezelf, {name}: de opleiding besteedt te weinig aandacht aan duurzaamheid.",
    "Als student op {address} woonachtig, merk ik dat fysieke aanwezigheid niet altijd mogelijk is.",
    "Mijn studentnummer {sid} is geregistreerd maar mijn feedbackformulieren worden nooit behandeld.",
    "Ik heb via {email} meerdere malen een voorstel ingediend voor een vak communicatieve vaardigheden.",
    "Als {name} wil ik pleiten voor meer diversiteit in het gastsprekerscircuit van de opleiding.",
    "Ik bel via {phone} regelmatig naar de studiebalie maar word steeds doorverwezen zonder resultaat.",
    "Student {sid} mist een aanbod voor studenten die willen doorstromen naar een universitaire master.",
    "Ik, {name}, wil graag meer aandacht voor interculturele communicatie als verplicht onderdeel.",
]

T_FREE_EN = [
    "I am {name} and I feel the programme lacks focus on soft skills and professional development.",
    "As student {sid}, I believe more emphasis should be placed on ethics in technology.",
    "My email address {email} is on file but I never receive updates about programme changes.",
    "I live at {address} — the commute is very long and hybrid options would help enormously.",
    "Student {sid} here: a dedicated course on career planning in year one would be very valuable.",
    "I, {name}, would appreciate better communication about changes to the curriculum.",
    "Through {email} I have sent suggestions multiple times, but none were ever acknowledged.",
    "As {name} I want to highlight the lack of networking events organised by the programme itself.",
    "My student ID {sid} is registered but feedback I have submitted has gone unanswered.",
    "My phone number {phone} is listed but no one ever proactively reaches out.",
    "I, {name}, suggest introducing a peer mentoring programme for first-year students.",
    "Student {sid} requests more flexibility in module selection to match individual career goals.",
    "Reaching out as {name}: sustainability topics are almost completely absent from the curriculum.",
    "Living at {address}, I struggle with long commute days — a hybrid format would help.",
    "My registration number {sid} shows I have been here for three years. Still no alumni network contact.",
    "I have contacted the programme via {email} about adding an entrepreneurship module without success.",
    "As {name}, I urge the programme to diversify its guest speaker lineup significantly.",
    "I call via {phone} regularly but am redirected without ever getting a proper answer.",
    "Student {sid} is interested in studying abroad but the information on partner universities is very limited.",
    "I, {name}, want the programme to invest more in mental health resources and make them more visible.",
]

T_INHOUD_NL = [
    "Als student {sid} ervaar ik dat de vakinhoud sterk is maar de samenhang tussen blokken volledig ontbreekt.",
    "Ik, {name}, vind de diepgang goed. De lesstof sluit aan op wat ik als toekomstig professional nodig heb.",
    "Via mijn studiebegeleider heb ik, {sid}, aangegeven dat sommige vakken dringend bijgewerkt moeten worden.",
    "De inhoud van mijn opleiding als student {sid} is uitdagend maar de uitvoering is wisselend per docent.",
    "Als {name} merk ik dat de theorie sterk is maar de vertaling naar de praktijk te abstract blijft.",
    "Ik ben student {sid} en ben erg tevreden over de kwaliteit van de vakinhoud dit jaar.",
    "Mijn e-mail {email} staat in het systeem, maar reacties op mijn opmerkingen over verouderde lesstof blijven uit.",
    "De leerdoelen zijn voor mij als student {sid} duidelijk geformuleerd en worden daadwerkelijk getoetst.",
    "Ik, {name}, mis een duidelijke rode draad tussen vakken in hetzelfde blok.",
    "Student {sid} heeft de indruk dat er te veel stof oppervlakkig wordt behandeld in plaats van minder, dieper.",
    "Via {email} heb ik feedback gegeven op de studiehandleiding maar die was te vaag om nuttig te zijn.",
    "De opzet van de opleiding is voor mij, {name}, logisch opgebouwd, maar de uitvoering laat soms te wensen over.",
    "Als student {sid} zou ik graag meer interdisciplinaire projecten zien die vakken verbinden.",
    "Ik, {name}, merk dat sommige vakken qua inhoud niet zijn bijgewerkt de afgelopen jaren.",
    "Student {sid} vraagt om meer aandacht voor actuele technologische ontwikkelingen in de lesstof.",
    "De inhoud is voor mij, {name}, up-to-date maar de werkvormen mogen gevarieerder.",
    "Als student {sid} vind ik de studielast disproportioneel ten opzichte van de studiepunten van sommige vakken.",
    "Ik heb via {email} positieve feedback gegeven over de kwaliteit van de vakinhoud dit semester.",
    "Mijn naam is {name} en ik vind dat de opleiding meer ruimte moet geven aan creatief denken.",
    "Student {sid} vraagt aandacht voor betere afstemming tussen vakken die tegelijk worden aangeboden.",
]

T_INHOUD_EN = [
    "As student {sid} I find the content strong but the cohesion between blocks is often missing.",
    "I, {name}, think the depth of the curriculum is one of the programme's greatest strengths.",
    "I sent feedback via {email} about outdated modules but never received a response.",
    "The content for me as student {sid} is challenging and professionally relevant.",
    "As {name} I notice that theory is well covered but the link to practice remains too abstract.",
    "Student {sid} is very satisfied with the content quality this academic year.",
    "My email {email} is registered but comments about the curriculum go unanswered.",
    "Learning goals are clear to me as student {sid} and assessments are aligned to them.",
    "I, {name}, miss a clear common thread connecting modules in the same block.",
    "Student {sid} finds that too many topics are covered superficially rather than fewer in depth.",
    "Via {email} I provided feedback on the study guide but it was too vague to be actionable.",
    "The structure of the programme is logical to me, {name}, though execution varies between lecturers.",
    "As student {sid} I would love to see more interdisciplinary projects connecting modules.",
    "I, {name}, notice that some modules have not been updated in several years.",
    "Student {sid} requests more attention to emerging technology trends in the curriculum.",
    "The content is up-to-date for me, {name}, but teaching methods could be more varied.",
    "As student {sid} the workload feels disproportionate to the credits some modules carry.",
    "I sent positive feedback via {email} about the content quality this semester.",
    "My name is {name} and I believe the programme should give more room for creative thinking.",
    "Student {sid} calls for better alignment between modules that run simultaneously.",
]

T_BEROEP_NL = [
    "Als student {sid} merk ik dat de aansluiting op de beroepspraktijk sterk is dankzij de gastlessen.",
    "Ik, {name}, vind dat er te weinig actuele praktijkcases worden aangeboden in het curriculum.",
    "Mijn stageplek via de opleiding was voor mij als {name} uitstekend en goed begeleid.",
    "Student {sid} vraagt om meer gastlessen vanuit het mkb in plaats van alleen grote corporates.",
    "Via {email} heb ik contact gehad met de stagecoordinator over de aansluiting op het werkveld.",
    "Als {name} ben ik tevreden over de manier waarop de opleiding mij voorbereidt op de arbeidsmarkt.",
    "Student {sid} vraagt om meer bedrijfsbezoeken als verplicht onderdeel van het curriculum.",
    "Ik, {name}, vind de projecten met echte opdrachtgevers het meest waardevolle deel van de opleiding.",
    "Als werkende student is de aansluiting voor mij, {name}, direct merkbaar in mijn dagelijks werk.",
    "Student {sid} mist een jaarlijkse carrièrebeurs georganiseerd door de opleiding zelf.",
    "Via mijn e-mail {email} heb ik feedback gegeven over het gebrek aan stage-kansen in de regio.",
    "Ik, {name}, vind de praktijkgerichte opdrachten uitstekend en goed afgestemd op de markt.",
    "Als student {sid} zou ik graag meer aandacht zien voor ondernemerschap naast het vakinhoudelijke.",
    "Mijn contactpersoon bij de opleiding heeft mij, {name}, goed begeleid bij het vinden van mijn stageplek.",
    "Student {sid} vraagt om een betere koppeling tussen keuzevakken en actuele beroepspraktijk.",
    "Ik, {name}, wil aandacht vragen voor stage-kansen buiten de Randstad en regio Eindhoven.",
    "Via {email} heb ik positieve feedback gegeven over de gastlessen die dit semester zijn aangeboden.",
    "Als student {sid} merk ik dat de opleiding te weinig contact heeft met bedrijven in mijn specialisatie.",
    "Ik, {name}, vind het waardevol dat de opleiding samenwerkt met echte opdrachtgevers voor projecten.",
    "Student {sid} vraagt meer aandacht voor internationale stage-mogelijkheden voor studenten.",
]

T_DOC_NL = [
    "Ik heb als student {sid} herhaaldelijk gemaild naar {email} maar docent van het statistiekvak reageert niet.",
    "Mijn naam is {name} en ik wil positief benoemen dat de docenten dit jaar zeer betrokken zijn.",
    "Via mijn nummer {phone} heb ik geprobeerd mijn begeleidend docent te bereiken, maar zonder resultaat.",
    "Als student {sid} merk ik een groot kwaliteitsverschil tussen docenten die hetzelfde vak geven.",
    "Ik, {name}, waardeer de open houding van de meeste docenten — je kunt altijd aankloppen met vragen.",
    "Docent Van der Berg reageert niet op mails van student {sid} en gaat in de les te snel door de stof.",
    "Mijn e-mail {email} staat bij de opleiding bekend maar mijn klacht over didactiek is nooit behandeld.",
    "Als {name} wil ik aandacht vragen voor het gebrek aan feedback van docenten buiten lesmomenten.",
    "Student {sid} ervaart dat docenten inhoudelijk sterk zijn maar weinig variëren in werkvorm.",
    "Ik heb via {phone} contact gezocht met de studiecoordinator over de bereikbaarheid van docenten.",
    "Als student {sid} ben ik blij dat docenten openstaan voor feedback op hun lesaanpak.",
    "Mijn naam is {name} en ik wil het docentenkorps bedanken voor hun inzet dit jaar.",
    "Via {email} heb ik een klacht ingediend over de uitleg in het wiskundevak — nooit reactie ontvangen.",
    "Ik, {name}, vind dat docenten te weinig gebruik maken van praktijkvoorbeelden uit de sector.",
    "Student {sid} vraagt om verplichte didactische training voor alle nieuwe docenten.",
    "Als {name} merk ik dat sommige docenten moeite hebben met inclusief lesgeven.",
    "Via mijn telefoonnummer {phone} heb ik geprobeerd een gesprek te plannen over mijn leerachterstanden.",
    "Ik, {name}, vind de aanpak van de praktijkdocenten veel beter dan die van de theoriedocenten.",
    "Student {sid} wijst erop dat reactietijden op Teams van docenten soms meer dan vijf werkdagen zijn.",
    "Mijn e-mail {email} is bekend bij de examencommissie maar mijn vraag over beoordeling bleef onbeantwoord.",
]

T_DOC_EN = [
    "I have emailed from {email} multiple times but my lecturer has not responded once.",
    "My name is {name} and I want to highlight that the teaching quality this year has been exceptional.",
    "Via my number {phone} I tried to reach my supervising lecturer — without any response.",
    "As student {sid} I notice a significant quality gap between lecturers teaching the same module.",
    "I, {name}, value the open-door policy maintained by most lecturers in this programme.",
    "The statistics lecturer does not reply to emails sent by student {sid} and rushes through material.",
    "My email {email} is on file but my complaint about teaching quality was never addressed.",
    "As {name} I want to highlight the lack of accessible feedback from lecturers between classes.",
    "Student {sid} notices lecturers are strong on content but very limited in teaching variety.",
    "I contacted via {phone} the study coordinator regarding the poor availability of lecturers.",
    "As student {sid} I appreciate that lecturers are open to feedback about their teaching.",
    "My name is {name} and I want to thank the teaching staff for their dedication this year.",
    "Via {email} I submitted a complaint about the mathematics module explanation — never received a reply.",
    "I, {name}, feel that lecturers rely too little on real-world examples from the industry.",
    "Student {sid} requests mandatory pedagogical training for all newly hired lecturers.",
    "As {name} I notice that some lecturers struggle to create an inclusive classroom environment.",
    "Via my phone {phone} I tried to schedule a discussion about my learning difficulties.",
    "I, {name}, find the approach of the practical lecturers far superior to the theory lecturers.",
    "Student {sid} notes that Teams response times from some lecturers exceed five working days.",
    "My email {email} is with the exam committee but my grading query has gone unanswered.",
]

T_BEG_NL = [
    "Mijn SLB-er kent mijn dossier als student {sid} goed en biedt gepersonaliseerde begeleiding.",
    "Ik, {name}, heb vier keer geprobeerd een afspraak te maken bij mijn studiebegeleider zonder succes.",
    "Geboren op {dob} heb ik als oudere student andere behoeften — maar de begeleiding is generiek.",
    "Student {sid} wijst erop dat SLB-gesprekken te kort zijn en alleen over studiepunten gaan.",
    "Via mijn e-mail {email} heb ik meerdere verzoeken ingediend voor begeleidingsgesprekken buiten kantooruren.",
    "Ik, {name}, ben tevreden over de manier waarop mijn begeleider mij ondersteunt bij planningsvragen.",
    "Als student {sid} met een bijbaantje kan ik alleen na 17:00 terecht — maar dan is er nooit iemand.",
    "Mijn studiecoach heeft mij, {name}, goed geholpen bij het aanvragen van bijzondere omstandigheden.",
    "Als student geboren op {dob} heb ik specifieke vragen over studieplanning die niet worden beantwoord.",
    "Student {sid} ervaart te weinig continuïteit — elk blok een andere begeleider maakt opbouw onmogelijk.",
    "Ik woon op {address} en de reistijd maakt het moeilijk om op de campus te komen voor begeleiding.",
    "Als {name} mis ik een digitaal systeem waar de begeleider aantekeningen bijhoudt over onze gesprekken.",
    "Student {sid} vraagt om begeleiding die verder gaat dan het invullen van een studieplan.",
    "Mijn naam is {name} en ik wil positief melden dat mijn SLB-er boven verwachting betrokken is.",
    "Via mijn nummer {phone} heb ik meerdere keren geprobeerd contact op te nemen met de decaan.",
    "Ik, {name}, heb een doorverwijzing gekregen naar de studentenpsycholoog maar de wachttijd was zes weken.",
    "Als student {sid} met dyslexie mis ik specifieke ondersteuning die verder gaat dan extra tentamentijd.",
    "Mijn begeleider weet wie ik ben, {name}, en vraagt actief naar mijn welbevinden. Dat geeft vertrouwen.",
    "Student {sid} vraagt om een vast aanspreekpunt voor de hele studieloopbaan.",
    "Via {email} heb ik verzocht om een begeleidingsgesprek over mijn studieachterstand — nooit reactie.",
]

T_BEG_EN = [
    "My SLB knows my file as student {sid} well and provides personalised guidance.",
    "I, {name}, made four attempts to schedule a meeting with my study advisor — all unsuccessful.",
    "Born on {dob} I have different needs as a mature student — but guidance is one-size-fits-all.",
    "Student {sid} notes that advisor sessions are too short and focus only on credit counts.",
    "Via my email {email} I requested support meetings outside office hours — no response.",
    "I, {name}, am satisfied with how my advisor supports my planning and progression.",
    "As student {sid} working part-time I can only meet after 17:00 — but no one is ever available then.",
    "My study coach has helped me, {name}, navigate the exceptional circumstances process.",
    "As a student born on {dob} I have specific planning questions that are never answered.",
    "Student {sid} experiences poor continuity — a new advisor every block makes meaningful support impossible.",
    "I live at {address} and the travel time makes attending campus support sessions very difficult.",
    "As {name} I miss a digital system where advisors record notes from previous sessions.",
    "Student {sid} asks for guidance that goes beyond filling in a study plan template.",
    "My name is {name} and I want to note that my SLB-er is exceptionally engaged.",
    "Via my phone {phone} I repeatedly tried to reach the student dean without success.",
    "I, {name}, was referred to the student psychologist but the waiting time was six weeks.",
    "As student {sid} with dyslexia I miss targeted support beyond just extra exam time.",
    "My advisor knows who I am, {name}, and actively asks about my wellbeing. That builds trust.",
    "Student {sid} requests a permanent single point of contact throughout their full degree.",
    "Via {email} I requested a meeting about my study delay — still waiting for a reply.",
]

T_TOETS_NL = [
    "Als student {sid} heb ik drie weken moeten wachten op mijn tentamencijfer — dat is niet acceptabel.",
    "Mijn naam is {name} en ik vind de beoordelingscriteria vaag. Elke docent interpreteert de rubric anders.",
    "Via {email} heb ik meerdere keren om toelichting gevraagd op mijn beoordeling, nooit antwoord gekregen.",
    "Student {sid} heeft een klacht ingediend over een nakijktermijn van zes weken zonder resultaat.",
    "Ik, {name}, ben tevreden over de transparantie van de beoordelingsrubrics bij dit vak.",
    "Als student {sid} mis ik duidelijkheid over hoe de individuele bijdrage in groepswerk wordt beoordeeld.",
    "Mijn telefoonnummer {phone} heb ik achtergelaten bij de examencommissie maar nooit teruggebeld gekregen.",
    "Ik, {name}, vind de terugkoppeling na toetsen constructief en goed bruikbaar voor volgende opdrachten.",
    "Student {sid} ervaart grote inconsistentie in beoordelingsstrengheid tussen docenten van hetzelfde vak.",
    "Via {email} heb ik gevraagd om inzage in mijn portfolio-beoordeling maar dat verzoek is genegeerd.",
    "Als {name} vind ik de cesuur bij tentamens onduidelijk uitgelegd — hoe het eindcijfer tot stand komt is vaag.",
    "Student {sid} vraagt om een maximale nakijktermijn van twee weken vastgelegd in het OER.",
    "Ik heb als {name} positieve ervaringen met de beoordelingsprocedure voor mijn stage-opdracht.",
    "Via mijn nummer {phone} heb ik contact gezocht met de examencommissie over mijn herkansingsrecht.",
    "Student {sid} merkt dat formatieve feedback te laat komt om nog bij te kunnen sturen.",
    "Ik, {name}, zou graag peer-assessments zien als aanvulling op de beoordeling door docenten.",
    "Als student {sid} vind ik de beoordeling van presentaties te subjectief zonder duidelijke criteria.",
    "Mijn e-mail {email} is bij de coordinator bekend maar mijn vraag over de beoordelingsuitslag bleef onbeantwoord.",
    "Ik, {name}, waardeer dat de docent de beoordeling mondeling toelicht na elk tentamen.",
    "Student {sid} vraagt om standaardisatie van rubrics over alle docenten die hetzelfde vak geven.",
]

T_TOETS_EN = [
    "As student {sid} I waited three weeks for my exam result — that is simply not acceptable.",
    "My name is {name} and I find the assessment criteria vague — each lecturer interprets the rubric differently.",
    "Via {email} I requested feedback on my grading multiple times and never received a reply.",
    "Student {sid} filed a complaint about a six-week marking period — no outcome was communicated.",
    "I, {name}, am satisfied with the transparency of assessment rubrics in this module.",
    "As student {sid} I find it unclear how individual contributions are assessed in group assignments.",
    "My phone number {phone} was left with the exam board but I was never called back.",
    "I, {name}, find the post-assessment feedback constructive and useful for future work.",
    "Student {sid} experiences major inconsistency in marking strictness between lecturers teaching the same module.",
    "Via {email} I requested access to my portfolio assessment — this request was ignored.",
    "As {name} the pass mark calculation is unclear — how the final grade is determined is not explained.",
    "Student {sid} requests a maximum two-week marking period to be written into the exam regulations.",
    "As {name} I have had positive experiences with the assessment procedure for my internship assignment.",
    "Via my phone {phone} I contacted the exam board about my resit rights without a clear outcome.",
    "Student {sid} notices formative feedback arrives too late to make meaningful adjustments.",
    "I, {name}, would welcome peer assessment as a complement to lecturer-only grading.",
    "As student {sid} I find presentation assessments too subjective without clear evaluation criteria.",
    "My email {email} is with the coordinator but my grading query remained unanswered.",
    "I, {name}, appreciate that the lecturer verbally explains the grading after each examination.",
    "Student {sid} calls for standardisation of rubrics across all lecturers teaching the same module.",
]

T_CONTACT_NL = [
    "Ik, {name}, ervaar structureel te weinig contactmomenten in het vak voor mijn track {track}.",
    "Student {sid} wijst erop dat spreekuren niet werken — docenten zijn daar nauwelijks aanwezig.",
    "Via {email} heb ik gevraagd om meer contactmomenten buiten reguliere lessen — geen reactie.",
    "Mijn naam is {name} en ik voel me een nummer op de opleiding, niet een student.",
    "Als student {sid} waardeer ik de open sfeer waarbij docenten ook buiten de les bereikbaar zijn.",
    "Via {phone} heb ik contact gezocht met de coordinator over het ontbreken van feedbackmomenten.",
    "Ik, {name}, ben positief over de community-gevoel binnen de opleiding — studenten kennen elkaar.",
    "Student {sid} ervaart dat Teams-kanalen slecht worden bijgehouden door docenten.",
    "Als {name} wil ik meer informele contactmomenten buiten de formele lessen om.",
    "Mijn contactmomenten als student {sid} zijn voldoende maar de kwaliteit varieert sterk per docent.",
    "Via {email} heb ik gemeld dat contacturen structureel uitvallen zonder compensatie of vervanging.",
    "Ik, {name}, heb bij het secretariaat aangegeven dat de communicatie vanuit de opleiding onduidelijk is.",
    "Student {sid} vraagt om meer studiedagen en events die de binding met de opleiding versterken.",
    "Als {name} merk ik dat er nauwelijks communitygevoel is — studenten kennen elkaar amper.",
    "Mijn aanwezigheidsregistratie als student {sid} klopt niet — ik was aanwezig maar ben als afwezig geregistreerd.",
    "Via {phone} heb ik de opleiding gewaarschuwd dat aanwezigheidsverplichting te onduidelijk is gecommuniceerd.",
    "Ik, {name}, ben blij dat er een vast aanspreekpunt is op de opleiding voor organisatorische vragen.",
    "Student {sid} ervaart dat contactmomenten vaak te laat in de ochtend worden ingepland.",
    "Als {name} waardeer ik de gastlessen als extra contactmoment buiten de vaste roosteruren.",
    "Student {sid} vraagt om een vaste wekelijkse vragenuur bij elke docent als minimumvereiste.",
]

T_VAARD_NL = [
    "Als student {sid} leer ik sterke technische vaardigheden maar communicatie blijft onderbelicht.",
    "Ik, {name}, vind dat presentatievaardigheden onvoldoende aan bod komen in het curriculum.",
    "Student {sid} waardeert de focus op kritisch denken en probleemoplossend vermogen.",
    "Via {email} heb ik gevraagd om meer aandacht voor academisch schrijven in de opleiding.",
    "Als {name} merk ik dat teamwork goed wordt geoefend maar individuele begeleiding hierbij ontbreekt.",
    "Student {sid} vraagt om meer aandacht voor onderzoeksvaardigheden naast de technische vakken.",
    "Ik, {name}, vind de vaardigheidstraining te generiek — meer specialisatie is gewenst.",
    "Als student {sid} leer ik zowel technische als soft skills — dat is een goede balans.",
    "Via {phone} heb ik gesproken met mijn SLB over het gebrek aan reflectievaardigheidstraining.",
    "Ik, {name}, ben positief over de manier waarop analytisch denken wordt aangeleerd in de vakken.",
]

T_ROOST_NL = [
    "Als student {sid} wordt het rooster te laat gepubliceerd — soms pas twee dagen van tevoren.",
    "Ik, {name}, ervaar grote gaten in het rooster die leiden tot onproductieve wachttijden op campus.",
    "Via {email} heb ik meerdere keren een klacht ingediend over structurele te vroege lessen in de ochtend.",
    "Student {sid} vraagt aandacht voor roosterconflicten die deeltijdstudenten benadelen.",
    "Als {name} vind ik het rooster goed gespreid en logisch opgebouwd over de week.",
    "Student {sid} ervaart roosterwijzigingen te laat gecommuniceerd — geeft veel onrust.",
    "Via {phone} heb ik contact gezocht over de onduidelijke aanwezigheidsplicht in het rooster.",
    "Ik, {name}, ben tevreden dat lessen goed zijn ingedeeld zodat er voldoende tijd is voor zelfstudie.",
    "Student {sid} wijst op roosters die niet kloppen met wat in de studiehandleiding staat.",
    "Als {name} ervaar ik te veel vrijdagmiddaglessen waardoor studenten de dag eerder afronden.",
    "Via {email} heb ik gevraagd om een flexibel rooster voor werkende studenten — geen reactie.",
    "Student {sid} meldt dat lokaalindeling soms niet klopt — lessen worden op het laatste moment verplaatst.",
    "Ik, {name}, vind de roostertool handig maar de updates zijn niet altijd tijdig.",
    "Als student {sid} ervaar ik dat maandagochtend 08:00 starten onhaalbaar is met openbaar vervoer.",
    "Via {phone} heb ik contact gehad met de roosterafdeling over structurele roosterfouten.",
]

T_LAST_NL = [
    "Als student {sid} heb ik in blok 2 meer dan vijftig uur per week aan studietaken gewerkt.",
    "Mijn naam is {name} en ik vind de studielast dit semester hoog maar haalbaar als je goed plant.",
    "Student {sid} wijst op drie grote deadlines in dezelfde week — dat is onverantwoorde planning.",
    "Ik woon op {address} en de reistijd telt mee bij de studielast — dit is zwaar te combineren.",
    "Als {name} vind ik de verdeling van de studielast over het jaar goed en evenwichtig.",
    "Student {sid} ervaart dat de verwachte zelfstudie-uren per vak niet overeenkomen met de werkelijkheid.",
    "Ik, {name}, combineer studie met een parttime baan en de studielast is aan de hoge kant.",
    "Via {email} heb ik het opleidingshoofd geïnformeerd over de onhaalbare werkdruk in periode 3.",
    "Student {sid} ervaart pieken in de studielast rondom tentamenweken die nauwelijks te dragen zijn.",
    "Als {name} ben ik tevreden dat deadlines goed gespreid zijn en planning haalbaar is.",
    "Mijn telefoonnummer {phone} is bij de decaan bekend — ik heb meerdere keren gebeld over studiedruk.",
    "Student {sid} vraagt om een betere verdeling van opdrachten over het blok.",
    "Ik, {name}, sliep soms maar vier uur per nacht in de drukste periode van het jaar.",
    "Als student {sid} bij een bijbaan werkend, is de werkdruk structureel te hoog.",
    "Via {email} heb ik gevraagd om meer flexibiliteit in deadlines voor bijzondere omstandigheden.",
]

T_LAST_EN = [
    "As student {sid} I worked more than fifty hours per week on study tasks during block two.",
    "My name is {name} and I find the workload this semester high but manageable with good planning.",
    "Student {sid} points to three major deadlines in the same week — that is irresponsible planning.",
    "I live at {address} and the commute adds significantly to an already heavy workload.",
    "As {name} I think the workload distribution across the year is well-balanced.",
    "Student {sid} notices that expected self-study hours per module do not match reality.",
    "I, {name}, combine studying with a part-time job and find the workload quite high.",
    "Via {email} I informed the programme director about the unmanageable workload in period three.",
    "Student {sid} experiences workload peaks around exam weeks that are barely manageable.",
    "As {name} I am happy that deadlines are spread well and planning feels achievable.",
    "My phone {phone} is with the student dean — I called multiple times about study pressure.",
    "Student {sid} requests better distribution of assignments across the block.",
    "I, {name}, slept only four hours some nights during the busiest period of the year.",
    "As student {sid} working a side job, the structural workload is consistently too high.",
    "Via {email} I requested more flexibility in deadlines for students with special circumstances.",
]

T_GROEP_NL = [
    "Als student {sid} vind ik groepen van acht te groot — vier tot vijf personen is het maximum.",
    "Ik, {name}, ben tevreden over de kleine klassen die zorgen voor persoonlijker onderwijs.",
    "Student {sid} ervaart dat vrije rijders in groepen niet effectief worden aangepakt.",
    "Via {email} heb ik gesuggereerd om vaste groepen te handhaven over het hele jaar.",
    "Als {name} vind ik dat groepssamenstellingen meer rekening moeten houden met de competentiemix.",
    "Student {sid} vraagt om een mechanisme om individuele bijdragen zichtbaar te maken in groepswerk.",
    "Ik, {name}, werk het liefst in groepen van vier — dat is de ideale omvang voor ons type projecten.",
    "Als student {sid} merk ik dat vaste jaargroepen de samenwerking aanzienlijk verbeteren.",
    "Via {phone} heb ik met de coordinator gesproken over de samenstelling van projectgroepen.",
    "Ik, {name}, vind dat de groepsgroottes per vak beter afgestemd moeten worden op de opdrachtvorm.",
]

T_STAGE_NL = [
    "Als student {sid} was de stageplek via de opleiding uitstekend en goed begeleid.",
    "Ik, {name}, heb weinig begeleiding gekregen van de stagedocent — maximaal twee contactmomenten.",
    "Student {sid} vraagt om meer transparantie in het aanbod van stage-bedrijven.",
    "Via {email} heb ik de stagecoordinator benaderd over een mogelijke internationale stage.",
    "Als {name} vind ik de stage-eisen duidelijk maar de zoekprocedure voor plekken onduidelijk.",
    "Student {sid} ervaart dat stage te vroeg in het curriculum plaatsvindt zonder voldoende basiskennis.",
    "Ik, {name}, heb een stageplek gevonden die naadloos aansluit op mijn track en toekomstplannen.",
    "Via {phone} heb ik de stagecoordinator gebeld over de begeleiding tijdens mijn stage-periode.",
    "Student {sid} vraagt om betere begeleiding voor studenten die internationaal stage lopen.",
    "Als {name} was stage de meest leerzame periode van mijn opleiding tot nu toe.",
]

T_UIT_NL = [
    "Als student {sid} word ik goed uitgedaagd door de opleiding en voel ik progressie.",
    "Ik, {name}, vind dat de lat soms te laag ligt — meer complexe opdrachten zijn nodig.",
    "Student {sid} vraagt om meer ruimte voor studenten die het curriculum sneller willen doorlopen.",
    "Via {email} heb ik aangegeven dat sommige vakken te weinig differentieren naar niveau.",
    "Als {name} merk ik dat de opleiding inzet beloont — dat motiveert me enorm.",
    "Student {sid} ervaart te weinig uitdaging in het keuzegedeelte van de opleiding.",
    "Ik, {name}, vind de uitdaging goed in balans — niet te zwaar, niet te gemakkelijk.",
    "Via {phone} heb ik met een docent gesproken over extra uitdagend materiaal buiten het standaard curriculum.",
    "Student {sid} vraagt om meer differentiatie voor studenten op verschillende niveaus.",
    "Als {name} ben ik blij dat er altijd docenten zijn die extra materiaal willen aanreiken.",
]

T_INTL_NL = [
    "Als student {sid} vind ik de internationale aspecten goed geïntegreerd in de vakinhoud.",
    "Ik, {name}, mis engelstalige vakken voor internationale studenten in mijn track.",
    "Student {sid} waardeert de uitwisselingsprogramma's die de opleiding aanbiedt.",
    "Via {email} heb ik gevraagd naar meer internationale stage-kansen — geen reactie gekregen.",
    "Als {name} ben ik tevreden over de internationale sfeer op de opleiding.",
    "Student {sid} vraagt om meer internationale gastdocenten als vast onderdeel van het curriculum.",
    "Ik, {name}, vind dat de opleiding te weinig zichtbaar maakt wat de internationale mogelijkheden zijn.",
    "Via {phone} heb ik het International Office gebeld voor informatie over studiepunten in het buitenland.",
    "Student {sid} vraagt aandacht voor betere voorbereiding van studenten die internationaal willen studeren.",
    "Als {name} heb ik via de opleiding een semester in het buitenland gedaan — dat was uitstekend.",
]

T_STRUCT_NL = [
    "Als student {sid} merk ik dat er een duidelijke rode draad is door de vier jaar heen.",
    "Ik, {name}, mis samenhang tussen vakken in hetzelfde blok — ze lijken los van elkaar te staan.",
    "Student {sid} ervaart te veel herhaling van stof die al eerder behandeld is.",
    "Via {email} heb ik feedback gegeven over de opbouw van het tweede studiejaar.",
    "Als {name} vind ik de leerlijn van jaar 1 naar jaar 4 logisch opgebouwd.",
    "Student {sid} ervaart dat de blokindeling te strak is voor de hoeveelheid stof per vak.",
    "Ik, {name}, ben tevreden over de samenhang tussen vakken die op elkaar voortbouwen.",
    "Via {phone} heb ik gesproken met de opleidingscoordinator over de structuur van het derde jaar.",
    "Student {sid} vraagt om meer expliciete verbinding tussen vakken in hetzelfde blok.",
    "Als {name} merkt de student dat de structuur ieder jaar wordt aangepast, wat verwarrend werkt.",
]

T_LEREN_NL = [
    "Als student {sid} waardeer ik de gevarieerde werkvormen die actief leren stimuleren.",
    "Ik, {name}, vind dat er te veel frontaal college wordt gegeven zonder interactie.",
    "Student {sid} leert het meest van de projecten en het minst van de standaard hoorcolleges.",
    "Via {email} heb ik gesuggereerd om meer flipped classroom toe te passen.",
    "Als {name} merk ik dat de docenten de leeraanpak goed aanpassen op het niveau van de groep.",
    "Student {sid} vraagt om meer ruimte voor experimenteren en fouten maken als leermethode.",
    "Ik, {name}, vind peer learning effectief en waardeer dat het wordt gestimuleerd.",
    "Via {phone} heb ik met een docent besproken dat de leermethoden beter kunnen aansluiten op mijn leerstijl.",
    "Student {sid} ervaart dat online leermateriaal goed is maar te weinig actief wordt gebruikt tijdens lessen.",
    "Als {name} vind ik de mix van individueel en groepsleren goed in balans.",
]

T_REFLEC_NL = [
    "Als student {sid} vind ik reflectie verplicht maar de begeleiding hierbij te summier.",
    "Ik, {name}, leer door de interdisciplinaire opdrachten bewust kennis te verbinden.",
    "Student {sid} ervaart het reflectieportfolio als nuttig maar tijdsintensief.",
    "Via {email} heb ik gevraagd om meer begeleiding bij reflectieopdrachten.",
    "Als {name} merk ik dat ik steeds beter verbanden zie tussen vakken uit verschillende blokken.",
    "Student {sid} vindt reflectietaken zinvol maar te weinig besproken met de begeleider.",
    "Ik, {name}, ervaar dat kennis verbinden goed wordt gestimuleerd via de projectopdrachten.",
    "Via {phone} heb ik feedback gegeven op de manier waarop reflectie wordt beoordeeld.",
    "Student {sid} vraagt om meer persoonlijke begeleiding bij het schrijven van reflecties.",
    "Als {name} vind de student dat reflectie-opdrachten te weinig worden gekoppeld aan praktijkervaringen.",
]

T_AFSTOND_NL = [
    "Als student {sid} ervaar ik dat online lessen slecht georganiseerd zijn — docenten starten te laat.",
    "Ik, {name}, vind Canvas stabiel maar de structuur per vak is inconsistent ingedeeld.",
    "Student {sid} mist video-opnames van lessen die soms pas na drie dagen beschikbaar zijn.",
    "Via {email} heb ik gemeld dat het afstandsonderwijs voor deeltijdstudenten onvoldoende functioneert.",
    "Als {name} functioneert het afstandsonderwijs goed voor mij — ik leer thuis efficiënter.",
    "Student {sid} vraagt om een standaard protocol voor online lessen per vak.",
    "Ik, {name}, ervaar problemen met de microfoon en webcam van docenten bij online lessen.",
    "Via {phone} heb ik geklaagd over de kwaliteit van online tentamens — geen antispiekprotocol.",
    "Student {sid} vraagt om betere tooling voor online groepswerk.",
    "Als {name} vind ik de kwaliteit van online lessen lager dan face-to-face — interactie mist.",
]

T_FAC_NL = [
    "Als student {sid} heb ik een IT-ticket {ticket} ingediend maar dat staat al twee weken open.",
    "Ik, {name}, ervaar dat computerzalen verouderd zijn en de hardware regelmatig faalt.",
    "Student {sid} meldt dat softwarelicenties halverwege het blok verlopen zonder aankondiging.",
    "Via {email} heb ik de IT-helpdesk benaderd over mijn IBAN {iban} voor de digitale middelenvergoeding.",
    "Als {name} ben ik tevreden over de studiefaciliteiten — voldoende werkplekken en stabiele wifi.",
    "Student {sid} ervaart op IP-adres {ip} regelmatig fout 403 op het campusnetwerk.",
    "Ik, {name}, vind dat er meer stille studieplekken nodig zijn op de campus.",
    "Via {phone} heb ik de campusbeveiliging gebeld over toegang tot gebouwen na 20:00.",
    "Student {sid} wijst erop dat Azure en AWS credits voor studenten moeilijk te activeren zijn.",
    "Als {name} mis ik voldoende stopcontacten in de studiezalen voor laptops en opladers.",
    "Mijn IBAN {iban} is ingediend voor een vergoeding maar ik heb nooit iets ontvangen.",
    "Student {sid} heeft ticket {ticket} ingediend over wifi-storingen — nog geen oplossing.",
    "Ik, {name}, ervaar dat de bibliotheek weinig actuele vakliteratuur beschikbaar heeft.",
    "Via {email} heb ik geklaagd over trage IT-ondersteuning — mijn probleem met IP {ip} duurt al weken.",
    "Student {sid} vraagt om meer flexibele werkruimtes voor projectgroepen op de campus.",
]

T_MED_NL = [
    "Als student {sid} wist ik pas in jaar drie dat er een studentenraad bestond.",
    "Ik, {name}, vind de medezeggenschap goed functioneren — de OC is actief en communicatief.",
    "Student {sid} ervaart dat beslissingen worden genomen zonder studenten vooraf te raadplegen.",
    "Via {email} heb ik gesuggereerd om vergaderingen van de opleidingscommissie openbaar te maken.",
    "Als {name} ben ik actief lid van de studentenraad en ben tevreden over de inspraakmogelijkheden.",
    "Student {sid} vraagt om meer zichtbaarheid van de medezeggenschap onder studenten.",
    "Ik, {name}, vind dat feedback van studenten te vaak verdwijnt zonder terugkoppeling.",
    "Via {phone} heb ik contact gehad met een lid van de opleidingscommissie over een curriculumwijziging.",
    "Student {sid} vraagt om studenten actief te betrekken bij curriculumvernieuwingen.",
    "Als {name} merk ik dat de OC haar best doet maar weinig draagvlak heeft bij studenten.",
]

T_GELIJK_NL = [
    "Ik, {name}, heb als student met achtergrond {country} meermaals microagressies ervaren van medestudenten.",
    "Student {sid} heeft diagnose {diagnosis} maar docenten zijn hier nauwelijks van op de hoogte.",
    "Via {email} heb ik een melding gedaan over ongelijke behandeling — nooit een reactie gekregen.",
    "Als {name} voel ik me volledig geaccepteerd door zowel docenten als medestudenten.",
    "Mijn BSN {bsn} staat geregistreerd voor extra ondersteuning maar dat is niet doorgekomen bij de opleiding.",
    "Student {sid} vraagt om een duidelijk en toegankelijk meldpunt voor discriminatie-ervaringen.",
    "Ik, {name}, merk dat studenten met niet-westerse achtergrond weinig zijn vertegenwoordigd in gastlessen.",
    "Als student {sid} met {diagnosis} mis ik specifiek beleid voor studenten met psychische aandoeningen.",
    "Via {phone} heb ik de vertrouwenspersoon gecontacteerd — de drempel is hoog maar het gesprek hielp.",
    "Student {sid} vraagt om verplichte bewustzijnstraining over diversiteit voor alle docenten.",
    "Ik, {name}, vind de diversiteitsaanpak goed zichtbaar. De opleiding neemt inclusiviteit serieus.",
    "Als student met {diagnosis} meld ik, {sid}, dat aanpassingen niet vanzelfsprekend worden geregeld.",
    "Via {email} heb ik een verzoek ingediend voor aanpassingen maar mijn BSN {bsn} stond niet in het systeem.",
    "Ik, {name}, vind inclusiviteit meer dan een poster in de gang — de opleiding moet structureel handelen.",
    "Student {sid} ervaart dat docenten weinig kennis hebben over de impact van {diagnosis} op studeren.",
]

T_GELIJK_EN = [
    "I, {name}, have experienced microaggressions from peers related to my background in {country}.",
    "Student {sid} has a diagnosis of {diagnosis} but lecturers are unaware of its implications.",
    "Via {email} I reported unequal treatment — I never received any response.",
    "As {name} I feel fully accepted by both staff and fellow students.",
    "My BSN {bsn} is registered for additional support but this was not communicated to the programme.",
    "Student {sid} requests a clear and accessible reporting channel for discrimination experiences.",
    "I, {name}, notice that students from non-Western backgrounds are underrepresented in guest lectures.",
    "As student {sid} with {diagnosis} I miss a specific policy for students with mental health conditions.",
    "Via {phone} I contacted the confidential advisor — the barrier was high but the conversation helped.",
    "Student {sid} requests mandatory diversity awareness training for all staff.",
    "I, {name}, find the diversity approach genuinely visible. The programme takes inclusivity seriously.",
    "As a student with {diagnosis} I, {sid}, find that reasonable adjustments are not automatically arranged.",
    "Via {email} I submitted a request for adjustments but my BSN {bsn} was not in the system.",
    "I, {name}, believe inclusivity is more than a poster on the wall — structural action is needed.",
    "Student {sid} finds that lecturers have limited knowledge of how {diagnosis} affects studying.",
]

T_FLEX_NL = [
    "Als student {sid} vind ik weinig flexibiliteit bij vertraging door bijzondere omstandigheden.",
    "Ik, {name}, ben tevreden over de mogelijkheden om vakken naar eigen tempo in te plannen.",
    "Student {sid} ervaart problemen bij het aanvragen van vrijstellingen op basis van eerder leren.",
    "Via {email} heb ik gevraagd om meer keuzeruimte in het curriculum voor mijn specialisatie.",
    "Als {name} vind ik de minors en keuzevakken voldoende ruimte geven voor eigen invulling.",
    "Student {sid} vraagt om flexibele instroomopties voor studenten die van baan wisselen.",
    "Ik, {name}, vind het moeilijk om een vak te volgen buiten het eigen cohort.",
    "Via {phone} heb ik contact gezocht over de mogelijkheden van eerder verworven competenties.",
    "Student {sid} is tevreden over de flexibiliteit die de deeltijdroute biedt.",
    "Als {name} vraag ik om betere erkenning van werkervaring bij het vrijstellingsbeleid.",
]

T_ONLINE_NL = [
    "Als student {sid} zijn online lessen goed georganiseerd en opnames snel beschikbaar.",
    "Ik, {name}, ervaar dat Teams-meetings soms 15 minuten te laat starten zonder bericht.",
    "Student {sid} vraagt om een consistent protocol voor online lessen per vak.",
    "Via {email} heb ik gemeld dat Canvas-structuur per vak te veel verschilt.",
    "Als {name} leer ik online even goed als op de campus — de tools werken prima.",
    "Student {sid} ervaart dat interactie tijdens online lessen minimaal is — cameras blijven uit.",
    "Ik, {name}, vind de online toetsen onvoldoende beveiligd — dat is oneerlijk voor eerlijke studenten.",
    "Via {phone} heb ik geklaagd over hybride lessen met slechte apparatuur in de collegezalen.",
    "Student {sid} vraagt om opnames van lessen altijd binnen 24 uur na de les beschikbaar te stellen.",
    "Als {name} vind ik de kwaliteit van online leermateriaal goed maar het gebruik in lessen te beperkt.",
]

T_WELZ_NL = [
    "Als student {sid} is er te weinig aandacht voor mentaal welzijn en de druk is merkbaar.",
    "Ik, {name}, heb een burn-out gehad en werd weken niet actief gevolgd door de opleiding.",
    "Via {email} heb ik contact opgenomen over studiedruk en de opleiding heeft proactief gereageerd.",
    "Student {sid} ervaart dat het welzijnsaanbod er is maar studenten het niet kunnen vinden.",
    "Als {name} voel ik me gezien als persoon, niet alleen als student — dat maakt het verschil.",
    "Student {sid} meldde stress via officieel kanaal maar hoorde weken niets terug.",
    "Ik, {name}, wist pas in het derde blok dat er een studentpsycholoog beschikbaar was.",
    "Via {phone} heb ik contact gehad met de decaan over de werkdruk en psychische klachten.",
    "Student {sid} vraagt om welzijnscheck-ins structureel op te nemen in de SLB-gesprekken.",
    "Als {name} zijn er goede welzijnsresources aanwezig maar de communicatie hierover is te zwak.",
    "Ik heb als student {sid} een burn-outpreventietraining gevolgd — die was nuttig maar vrijwillig.",
    "Via {email} heb ik positieve feedback gegeven over de ondersteuning die ik heb ontvangen.",
    "Student {sid} vraagt om een peer-support netwerk aanvullend op de professionele begeleiding.",
    "Als {name} vind ik dat de opleiding burn-outpreventie structureel moet opnemen in het curriculum.",
    "Student {sid} ervaart dat de sfeer op de opleiding positief is — studenten ondersteunen elkaar.",
]

T_WELZ_EN = [
    "As student {sid} there is too little attention to mental wellbeing and the pressure is visible.",
    "I, {name}, experienced burnout and was not actively followed up for weeks by the programme.",
    "Via {email} I contacted the programme about study pressure and they responded proactively.",
    "Student {sid} finds that wellbeing support exists but students simply cannot find it.",
    "As {name} I feel seen as a person, not just as a student — that makes a real difference.",
    "Student {sid} filed a stress report through the official channel but heard nothing for weeks.",
    "I, {name}, only found out about the student psychologist in my third block — far too late.",
    "Via {phone} I spoke with the student dean about workload and mental health concerns.",
    "Student {sid} requests wellbeing check-ins to be built into every standard mentor session.",
    "As {name} the wellbeing resources are present but far too poorly communicated to students.",
    "As student {sid} I attended a burnout prevention workshop — it was useful but only optional.",
    "Via {email} I gave positive feedback about the support I received during a difficult period.",
    "Student {sid} requests a peer support network in addition to professional counselling.",
    "As {name} I believe burnout prevention should be a structural part of the curriculum.",
    "Student {sid} appreciates that the atmosphere on the programme is positive and supportive.",
]

# ── Queue-based unique answer assigner ────────────────────────────────────────
class UniqueQueue:
    def __init__(self, templates):
        self.templates = templates
        self.shuffled = list(templates)
        random.shuffle(self.shuffled)
        self.idx = 0
        self.used = set()

    def next(self, **pii):
        for _ in range(len(self.templates) * 3):
            tmpl = self.shuffled[self.idx % len(self.shuffled)]
            self.idx += 1
            rendered = tmpl.format(**pii)
            if rendered not in self.used:
                self.used.add(rendered)
                return rendered
        # Fallback: always unique because sid is unique
        tmpl = random.choice(self.templates)
        rendered = tmpl.format(**pii) + f" [ref. {pii.get('sid','')}]"
        self.used.add(rendered)
        return rendered

# Per-column queues
Q = {
    'free_nl':    UniqueQueue(T_FREE_NL),
    'free_en':    UniqueQueue(T_FREE_EN),
    'inhoud_nl':  UniqueQueue(T_INHOUD_NL),
    'inhoud_en':  UniqueQueue(T_INHOUD_EN),
    'beroep_nl':  UniqueQueue(T_BEROEP_NL),
    'doc_nl':     UniqueQueue(T_DOC_NL),
    'doc_en':     UniqueQueue(T_DOC_EN),
    'beg_nl':     UniqueQueue(T_BEG_NL),
    'beg_en':     UniqueQueue(T_BEG_EN),
    'toets_nl':   UniqueQueue(T_TOETS_NL),
    'toets_en':   UniqueQueue(T_TOETS_EN),
    'contact_nl': UniqueQueue(T_CONTACT_NL),
    'vaard_nl':   UniqueQueue(T_VAARD_NL),
    'roost_nl':   UniqueQueue(T_ROOST_NL),
    'last_nl':    UniqueQueue(T_LAST_NL),
    'last_en':    UniqueQueue(T_LAST_EN),
    'groep_nl':   UniqueQueue(T_GROEP_NL),
    'stage_nl':   UniqueQueue(T_STAGE_NL),
    'uit_nl':     UniqueQueue(T_UIT_NL),
    'intl_nl':    UniqueQueue(T_INTL_NL),
    'struct_nl':  UniqueQueue(T_STRUCT_NL),
    'leren_nl':   UniqueQueue(T_LEREN_NL),
    'reflec_nl':  UniqueQueue(T_REFLEC_NL),
    'afstond_nl': UniqueQueue(T_AFSTOND_NL),
    'fac_nl':     UniqueQueue(T_FAC_NL),
    'med_nl':     UniqueQueue(T_MED_NL),
    'gelijk_nl':  UniqueQueue(T_GELIJK_NL),
    'gelijk_en':  UniqueQueue(T_GELIJK_EN),
    'flex_nl':    UniqueQueue(T_FLEX_NL),
    'online_nl':  UniqueQueue(T_ONLINE_NL),
    'welz_nl':    UniqueQueue(T_WELZ_NL),
    'welz_en':    UniqueQueue(T_WELZ_EN),
}

# ── Row builder ────────────────────────────────────────────────────────────────
ENGLISH_ROWS = set(random.sample(range(100), 20))
BLANK_PROB   = 0.20   # 20% chance a non-key field is blank (realistic)

def sc(): return random.randint(1, 5)

def make_row(i):
    s = ALL_STUDENTS[i]
    is_intl = len(s) > 3
    if is_intl:
        name, email, dob, country = s[0], s[1], s[2], s[3]
        passport = s[4] if len(s) > 4 else ''
    else:
        name, email, dob, address, phone = s[0], s[1], s[2], s[3], s[4]
        country, passport = 'Nederland', ''

    sid    = SIDS[i]
    bsn    = BSNS[i]
    iban   = IBANS[i]
    diag   = DIAGS[i % len(DIAGS)]
    ip     = IPS[i]
    ticket = TICKS[i]
    phone  = s[4] if not is_intl else f"06-{40000000+i*1234567%59999999}"
    address= s[3] if not is_intl else f"Campuslaan {i+1}, 5612 AP Eindhoven"
    track  = TRACKS[i % len(TRACKS)]
    vorm   = ["vt","vt","vt","vt","vt","dt","du"][i % 7]
    sj     = (i % 4) + 1

    pii = dict(name=name, email=email, dob=dob, sid=sid, bsn=bsn,
               iban=iban, phone=phone, address=address, diagnosis=diag,
               ip=ip, ticket=ticket, country=country, passport=passport,
               track=track)

    en = i in ENGLISH_ROWS

    def get(key_nl, key_en=None, blank=False):
        if blank and random.random() < BLANK_PROB:
            return ''
        if en and key_en:
            return Q[key_en].next(**pii)
        return Q[key_nl].next(**pii)

    r = {c: '' for c in COLUMNS}
    r.update({
        'Jaar': 2023 if i % 5 == 0 else 2024,
        'Actuele BRIN-code volgens RIO': '27UM',
        'Actuele naam instelling volgens RIO': 'Fontys Hogescholen',
        'Actuele CROHO-code volgens RIO': '34479',
        'Actuele Opleidingsnaam volgens RIO': 'HBO-ICT',
        'Actuele BRIN-volgnummer volgens RIO': '00',
        'Type Student': TYPES[vorm],
        'Opleidingsvorm (vt dt du)': vorm,
        'Leerroute_Track': track,
        'Studiejaar volgens instelling': sj,
        'Kunstopleiding': 'Nee',
        'Afstandsonderwijs': 'Ja' if vorm == 'dt' else 'Nee',
        # open-text answers
        'Wil jij zelf iets kwijt over je opleiding dat nog niet aan bod is gekomen?':
            get('free_nl','free_en', blank=True),
        'Wil jij je opleiding nog iets meegeven over de inhoud en opzet van het onderwijs?':
            get('inhoud_nl','inhoud_en'),
        'Wil jij je opleiding nog iets meegeven over de aansluiting op de beroepspraktijk / beroepsloopbaan?':
            get('beroep_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de docenten aan je opleiding?':
            get('doc_nl','doc_en'),
        'Wil jij je opleiding nog iets meegeven over de studiebegeleiding?':
            get('beg_nl','beg_en'),
        'Wil jij je opleiding nog iets meegeven over toetsing en beoordeling?':
            get('toets_nl','toets_en'),
        'Wil jij je opleiding nog iets meegeven over betrokkenheid en contact?':
            get('contact_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de vaardigheden die je leert in je opleiding?':
            get('vaard_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de studieroosters?':
            get('roost_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de studielast?':
            get('last_nl','last_en'),
        'Wil jij je opleiding nog iets meegeven over de groepsgrootte?':
            get('groep_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over stages?':
            get('stage_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over uitdaging en inzet?':
            get('uit_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de internationale aspecten van je opleiding?':
            get('intl_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de structuur en samenhang van je opleiding?':
            get('struct_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de wijze waarop je nieuwe kennis en vaardigheden leert?':
            get('leren_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over het verbinden van kennis en ideeen?':
            get('reflec_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over het afstandsonderwijs?':
            get('afstond_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over de studiefaciliteiten?':
            get('fac_nl'),
        'Wil jij je opleiding nog iets meegeven over de medezeggenschap?':
            get('med_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over gelijke behandeling?':
            get('gelijk_nl','gelijk_en'),
        'Wil jij je opleiding nog iets meegeven over de flexibiliteit van het studieprogramma?':
            get('flex_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over online onderwijs?':
            get('online_nl', blank=True),
        'Wil jij je opleiding nog iets meegeven over welzijn?':
            get('welz_nl','welz_en'),
        # barrier fields
        'Wat voor soort belemmeringen ervaar je? Anders, namelijk:':
            f"{diag}, gediagnosticeerd" if random.random() < 0.3 else '',
        'Waarom studeer je onder bijzondere omstandigheden? Anders, namelijk:':
            f"Mijn BSN {bsn} staat bij DUO geregistreerd maar de opleiding heeft dit niet verwerkt." if random.random() < 0.2 else '',
        'Wil jij je opleiding nog iets meegeven over studeren onder bijzondere omstandigheden?':
            f"Student {sid}: de aanvraagprocedure voor tentamenaanpassingen is onduidelijk." if random.random() < 0.15 else '',
        # Scores
        'Themascore Inhoud en opzet van het onderwijs': sc(),
        'Themascore Aansluiting beroepspraktijk / beroepsloopbaan (antwoord n.v.t. Toegevoegd aan het thema vanaf 2022)': sc(),
        'Themascore Docenten aan de opleiding': sc(),
        "Themascore Studiebegeleiding (antwoordoptie 'Weet ik niet/niet van toepassing' toegevoegd vanaf 2023)": sc(),
        'Themascore Toetsing en beoordeling': sc(),
        'Themascore Betrokkenheid en contact': sc(),
        'Themascore Algemene vaardigheden': sc(),
        'Themascore Wetenschappelijke vaardigheden': sc() if random.random() > 0.2 else '',
        'Themascore Praktijkgericht onderzoek': sc() if random.random() > 0.2 else '',
        'Themascore Studieroosters': sc(),
        'Themascore Studielast': sc(),
        'Themascore Stages opleiding': sc() if random.random() > 0.4 else '',
        'Themascore Stages ervaring': sc() if random.random() > 0.4 else '',
        'Themascore Uitdaging en inzet': sc(),
        'Themascore Internationale aspecten': sc() if random.random() > 0.5 else '',
        'Themascore Internationale studenten': sc() if is_intl else '',
        'Themascore Structuur en samenhang opleiding': sc(),
        'Themascore Verdiepend leren': sc(),
        'Themascore Reflectie': sc(),
        'Themascore Afstandsonderwijs': sc() if vorm == 'dt' else '',
        'Themascore Studiefaciliteiten': sc(),
        'Themascore Medezeggenschap': sc() if random.random() > 0.4 else '',
        'Themascore Gelijke behandeling': sc(),
        'Themascore Flexibiliteit studieprogramma': sc(),
        'Themascore Kunstonderwijs': '',
        'Themascore Online onderwijs': sc() if random.random() > 0.3 else '',
        'Themascore Welzijn': sc(),
    })
    return r

rows = [make_row(i) for i in range(100)]
df = pd.DataFrame(rows, columns=COLUMNS)

out = 'C:/Users/nickv/Downloads/NSE_100.csv'
df.to_csv(out, index=False, encoding='utf-8-sig')

# Verify
q_cols = [c for c in COLUMNS if c.endswith('?')]
dupes = sum(df[c].replace('', None).dropna().duplicated().sum() for c in q_cols)
filled = df[q_cols].replace('', None).notna().sum().sum()
total = len(df) * len(q_cols)
print(f"Rows: {len(df)}  |  Cols: {len(COLUMNS)}")
print(f"Duplicate answers: {dupes}")
print(f"Fill rate: {filled}/{total} ({100*filled//total}%)")
print(f"English rows: {len(ENGLISH_ROWS)}")
print(f"Labels empty: {df[['Label1','Label2','Label3','Label4','Label5','Label6','Label7']].replace('',None).isna().all().all()}")
print(f"Output: {out}")
