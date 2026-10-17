from typing import Optional

from indian_legal_mcp_server.prompts.system_instructions import DISCLAIMER
from indian_legal_mcp_server.services.statute_index import StatuteIndex
from indian_legal_mcp_server.utils.formatters import format_confidence

CONCEPTS = {
    # ── Original v0.5 Concepts ──────────────────────────────────────
    "res_ipsa_loquitur": {
        "name": "Res Ipsa Loquitur",
        "aliases": ["res ipsa", "things speak for themselves"],
        "domain": "tort",
        "explanation": "A doctrine in tort law where the mere occurrence of an accident implies negligence. If the thing causing injury was under the defendant's control and the accident wouldn't normally happen without negligence, the burden shifts to the defendant to prove they were not negligent.",
        "elements": [
            "Thing causing injury was under defendant's control",
            "Accident would not normally occur without negligence",
            "No direct evidence of negligence available to plaintiff",
        ],
        "statutes": ["Indian Evidence Act 1872 (now BNSA 2023)"],
        "landmark_cases": [
            "M.P. State Road Transport Corp. vs. Sudhakar (2008)",
            "Pushpabai vs. Ranjit G&P Co. (1977)",
        ],
    },
    "res_judicata": {
        "name": "Res Judicata",
        "aliases": ["claim preclusion", "matter already judged"],
        "domain": "civil_procedure",
        "explanation": "A final judgment by a competent court on the merits bars the same parties from re-litigating the same cause of action. Codified in CPC s. 11. The principle is that there must be an end to litigation.",
        "elements": [
            "Matter directly and substantially in issue in former suit",
            "Former suit between same parties or their representatives",
            "Former court was competent to try the suit",
            "Matter finally decided in former suit",
        ],
        "statutes": ["CPC s. 11"],
        "landmark_cases": [
            "Satyadhan Ghosal vs. Deorajin Debi (1960)",
            "Hope Plantations vs. Taluk Land Board (1999)",
        ],
    },
    "stare_decisis": {
        "name": "Stare Decisis",
        "aliases": ["precedent", "binding precedent"],
        "domain": "constitutional",
        "explanation": "The principle that courts should follow previous judicial decisions when deciding similar cases. In India, Supreme Court decisions bind all courts under Art. 141 of the Constitution. High Court decisions bind subordinate courts within that state.",
        "elements": [
            "Ratio decidendi — binding part of judgment",
            "Obiter dicta — persuasive but not binding",
            "Hierarchy of courts determines binding force",
        ],
        "statutes": ["Constitution of India, Art. 141"],
        "landmark_cases": [
            "Kesavananda Bharati vs. State of Kerala (1973)",
            "Bengal Immunity vs. State of Bihar (1955)",
        ],
    },
    "natural_justice": {
        "name": "Principles of Natural Justice",
        "aliases": [
            "natural justice",
            "audi alteram partem",
            "nemo judex in causa sua",
        ],
        "domain": "administrative_law",
        "explanation": "Fundamental principles of fair procedure: (1) No one can be a judge in their own cause (nemo judex in causa sua), and (2) both sides must be heard (audi alteram partem). These principles are the bedrock of Indian administrative and judicial procedure.",
        "elements": [
            "Rule against bias (nemo judex in causa sua)",
            "Right to be heard (audi alteram partem)",
            "Reasoned decision (speaking order)",
        ],
        "statutes": [
            "Constitution of India, Art. 14, 21",
            "BNSS 2023 (criminal procedure)",
        ],
        "landmark_cases": [
            "Maneka Gandhi vs. Union of India (1978)",
            "A.K. Kraipak vs. Union of India (1969)",
        ],
    },
    "due_process": {
        "name": "Due Process of Law",
        "aliases": [
            "procedural due process",
            "substantive due process",
            "Article 21",
            "art. 21",
            "right to life",
        ],
        "domain": "constitutional",
        "explanation": "Art. 21 of the Constitution guarantees that no person shall be deprived of life or personal liberty except according to procedure established by law. Since Maneka Gandhi (1978), the procedure must be 'fair, just, and reasonable' — effectively reading due process into Art. 21.",
        "elements": [
            "Procedure must be fair, just, and reasonable",
            "Substantive rights cannot be taken away arbitrarily",
            "Right to life includes right to livelihood, dignity, health, education",
        ],
        "statutes": ["Constitution of India, Art. 21"],
        "landmark_cases": [
            "Maneka Gandhi vs. Union of India (1978)",
            "K.S. Puttaswamy vs. Union of India (2017) — privacy",
        ],
    },
    "bail_not_jail": {
        "name": "Bail is the Rule, Jail is the Exception",
        "aliases": ["bail rule jail exception", "presumption of innocence"],
        "domain": "criminal",
        "explanation": "A fundamental principle in Indian criminal jurisprudence that bail should ordinarily be granted and pre-trial detention is the exception. Rooted in Art. 21 (right to life and liberty) of the Constitution. The accused is presumed innocent until proven guilty.",
        "elements": [
            "Presumption of innocence until proven guilty",
            "Liberty is the norm, detention is the exception",
            "Refusal of bail requires strong grounds",
        ],
        "statutes": ["Constitution of India, Art. 21", "BNSS ss. 478-493"],
        "landmark_cases": [
            "State of Rajasthan vs. Balchand (1977)",
            "Nikesh Tarachand Shah vs. Union of India (2018)",
        ],
    },
    "vicarious_liability": {
        "name": "Vicarious Liability",
        "aliases": [
            "master-servant liability",
            "employer liability",
            "respondent superior",
        ],
        "domain": "tort",
        "explanation": "A principle where one person is held liable for the torts of another. Most commonly, employers are vicariously liable for acts of employees committed in the course of employment. Under BNS s. 127 (s. 34 IPC), vicarious liability also applies in criminal law for acts done in furtherance of common intention.",
        "elements": [
            "Relationship (employer-employee, principal-agent)",
            "Act committed in course of employment/agency",
            "Connection between relationship and wrongful act",
        ],
        "statutes": ["BNS s. 127 (common intention)", "Tort law (common law)"],
        "landmark_cases": [
            "State of Gujarat vs. Memon (2020)",
            "S.K. Alagh vs. State of U.P. (2008)",
        ],
    },
    "double_jeopardy": {
        "name": "Protection Against Double Jeopardy",
        "aliases": ["autrefois acquit", "autrefois convict", "Art. 20(2)"],
        "domain": "criminal",
        "explanation": "No person shall be prosecuted and punished for the same offence more than once. Guaranteed by Art. 20(2) of the Constitution and codified in BNSS s. 313 (CrPC s. 300). The protection applies when: (1) there was a previous prosecution, (2) for the same offence, (3) before a competent court, (4) resulting in conviction or acquittal.",
        "elements": [
            "Previous prosecution before a competent court",
            "Same offence in both proceedings",
            "Previous proceeding ended in conviction or acquittal",
        ],
        "statutes": ["Constitution of India, Art. 20(2)", "BNSS s. 313"],
        "landmark_cases": [
            "Maqbool Hussain vs. State of Bombay (1953)",
            "Kalawati vs. State of HP (1953)",
        ],
    },
    "ex_post_facto": {
        "name": "Ex Post Facto Law",
        "aliases": ["retrospective law", "Art. 20(1)"],
        "domain": "constitutional",
        "explanation": "Art. 20(1) of the Constitution prohibits conviction under an ex post facto law — a law that criminalizes acts committed before its enactment. However, it does NOT prevent procedural changes or changes in punishment (mitigating) from applying retrospectively.",
        "elements": [
            "Law must be penal/criminal in nature",
            "Act must have been committed before law came into force",
            "Protection only against conviction and punishment, not against trial under new procedure",
        ],
        "statutes": [
            "Constitution of India, Art. 20(1)",
            "BNS s. 3 (temporal operation)",
        ],
        "landmark_cases": [
            "Rao Shiv Bahadur Singh vs. State of V.P. (1953)",
            "T. Barai vs. Henry Ah Hoe (1983)",
        ],
    },
    "self_incrimination": {
        "name": "Protection Against Self-Incrimination",
        "aliases": ["right to silence", "Art. 20(3)", "nemo tenetur"],
        "domain": "criminal",
        "explanation": "No person accused of an offence shall be compelled to be a witness against themselves. Guaranteed by Art. 20(3) of the Constitution. The right extends to: (1) testimonial evidence, (2) documentary evidence, (3) oral evidence. It does NOT cover: fingerprints, blood samples, handwriting samples, or DNA samples.",
        "elements": [
            "Person must be formally accused of an offence",
            "Must be compulsion (threat, coercion, inducement)",
            "Must be testimony (oral/documentary, not physical evidence)",
        ],
        "statutes": [
            "Constitution of India, Art. 20(3)",
            "BNSA (Evidence Act) ss. 24-30",
            "BNSS s. 312",
        ],
        "landmark_cases": [
            "Nandini Satpathy vs. P.L. Dani (1978)",
            "Selvi vs. State of Karnataka (2010) — narcoanalysis",
        ],
    },
    # ── Criminal Law ──────────────────────────────────────────────
    "abetment": {
        "name": "Abetment",
        "aliases": ["abet", "aiding", "instigating", "criminal abetment"],
        "domain": "criminal",
        "explanation": "A person abets the doing of a thing when they: (1) instigate any person to do that thing, (2) engage in a conspiracy to do that thing, or (3) intentionally aid the doing of that thing. Abetment is punishable even if the abetted act is not committed. Codified under BNS ss. 45-57.",
        "elements": [
            "Instigation (active suggestion or incitement)",
            "Conspiracy with an act in furtherance",
            "Intentional aid or facilitation",
        ],
        "statutes": ["BNS ss. 45-57", "IPC ss. 107-120 (repealed)"],
        "landmark_cases": [
            "Faguna Kanta Nath vs. State of Assam (1959)",
            "Shiv Ram vs. State of U.P. (1998)",
        ],
    },
    "criminal_conspiracy": {
        "name": "Criminal Conspiracy",
        "aliases": ["conspiracy", "criminal agreement"],
        "domain": "criminal",
        "explanation": "When two or more persons agree to do an illegal act or a legal act by illegal means. An overt act in furtherance of the conspiracy is required except for certain serious conspiracies. The agreement itself is the essence of the offence.",
        "elements": [
            "Agreement between two or more persons",
            "Agreement to commit an illegal act or achieve a lawful end by unlawful means",
            "Overt act (for most conspiracies)",
        ],
        "statutes": ["BNS s. 46 (criminal conspiracy)", "BNS s. 111 (organised crime)"],
        "landmark_cases": [
            "R.S. Nayak vs. A.R. Antulay (1984)",
            "Kehar Singh vs. State (1988) — Indira Gandhi assassination",
        ],
    },
    "attempt": {
        "name": "Attempt to Commit an Offence",
        "aliases": ["criminal attempt", "attempted crime"],
        "domain": "criminal",
        "explanation": "When a person intentionally does an act towards the commission of an offence but fails or is prevented. The act must be more than mere preparation — it must be a direct step toward completion. Attempt is punishable with up to half the punishment for the completed offence under BNS s. 62.",
        "elements": [
            "Intention to commit the offence",
            "Act done towards commission (beyond preparation)",
            "Act did not result in the full offence",
        ],
        "statutes": ["BNS s. 62", "IPC s. 511 (repealed)"],
        "landmark_cases": [
            "Abhayanand Mishra vs. State of Bihar (1961)",
            "Malkiat Singh vs. State of Punjab (1969)",
        ],
    },
    "common_intention": {
        "name": "Common Intention",
        "aliases": [
            "section 34 IPC",
            "joint liability",
            "common intent",
            "BNS s. 127",
        ],
        "domain": "criminal",
        "explanation": "When a criminal act is done by several persons in furtherance of the common intention of all, each is liable as if they did it alone. Codified under BNS s. 127 (IPC s. 34). Requires a pre-arranged plan and active participation, though the acts of each participant need not be identical.",
        "elements": [
            "Criminal act done by multiple persons",
            "Pre-conceived plan or common intention",
            "Act in furtherance of that common intention",
            "Active participation by each accused",
        ],
        "statutes": ["BNS s. 127", "IPC s. 34 (repealed)"],
        "landmark_cases": [
            "Pandurang vs. State of Hyderabad (1955)",
            "Krishna Govind Patil vs. State of Maharashtra (1963)",
        ],
    },
    "right_of_private_defence": {
        "name": "Right of Private Defence",
        "aliases": [
            "self-defence",
            "self defence",
            "self defense",
            "private defence",
            "defence of property",
        ],
        "domain": "criminal",
        "explanation": "Every person has the right to defend their own body and the body of another person against any offence affecting the human body. The right also extends to defending property (movable and immovable). The right is subject to the limitation that no more harm than is necessary should be inflicted. BNS ss. 34-44 codify this right.",
        "elements": [
            "Imminent and reasonable apprehension of harm",
            "No time to avail public authorities",
            "Force used must be proportionate to the threat",
            "Right ceases when the threat ends",
        ],
        "statutes": ["BNS ss. 34-44", "IPC ss. 96-106 (repealed)"],
        "landmark_cases": [
            "Jai Dev vs. State of Punjab (1963)",
            "State of U.P. vs. Ram Swarup (1974)",
            "Darshan Singh vs. State of Punjab (2010)",
        ],
    },
    "theft": {
        "name": "Theft",
        "aliases": ["stealing", "chori"],
        "domain": "criminal",
        "explanation": "Whoever, intending to take dishonestly any movable property out of the possession of any person without that person's consent, moves that property to take it, commits theft. The taking must be dishonest (intending wrongful gain or loss). Codified under BNS s. 301 (IPC s. 378).",
        "elements": [
            "Dishonest intention to take property",
            "Movable property in someone's possession",
            "Moving the property to take it",
            "Without the person's consent",
        ],
        "statutes": ["BNS s. 301-304 (theft)", "BNS s. 303 (theft in dwelling house)"],
        "landmark_cases": [
            "K.N. Mehra vs. State of Rajasthan (1957)",
            "Pyare Lal vs. State of Rajasthan (1963)",
        ],
    },
    "extortion": {
        "name": "Extortion",
        "aliases": ["blackmail", "coercion for property"],
        "domain": "criminal",
        "explanation": "Whoever intentionally puts any person in fear of injury to that person or another, and thereby dishonestly induces the person so put in fear to deliver any property or valuable security, commits extortion. The injury threatened may be to body, mind, reputation, or property. Codified under BNS s. 305 (IPC s. 383).",
        "elements": [
            "Putting a person in fear of injury",
            "Fear must be intentional",
            "Dishonest inducement to deliver property",
            "Delivery of property by the person in fear",
        ],
        "statutes": [
            "BNS s. 305-308 (extortion)",
            "BNS s. 306 (robbery includes extortion)",
        ],
        "landmark_cases": [
            "R.S. Nayak vs. A.R. Antulay (1984)",
            "Sushil Kumar vs. State of Punjab (2009)",
        ],
    },
    "cheating": {
        "name": "Cheating",
        "aliases": ["fraud", "deception", "dishonest inducement"],
        "domain": "criminal",
        "explanation": "Whoever, by deceiving any person, fraudulently or dishonestly induces the person so deceived to deliver any property to any person, or to consent that any person shall retain any property, or intentionally induces the person to do or omit to do anything which they would not do or omit if not deceived, commits cheating. Codified under BNS s. 318 (IPC s. 415).",
        "elements": [
            "Deception of any person",
            "Dishonest or fraudulent intention",
            "Inducement to deliver property or do/omit an act",
            "Act or omission causes or may cause damage/harm",
        ],
        "statutes": [
            "BNS ss. 318-322 (cheating)",
            "BNS s. 319 (cheating with knowledge of wrongful loss)",
        ],
        "landmark_cases": [
            "Ramaswamy Nadar vs. State of Madras (1958)",
            "Ishwarlal vs. State of Maharashtra (1968)",
        ],
    },
    "wrongful_restraint": {
        "name": "Wrongful Restraint",
        "aliases": ["unlawful detention", "wrongful confinement"],
        "domain": "criminal",
        "explanation": "Wrongful restraint occurs when a person is voluntarily obstructed from proceeding in any direction they have a right to proceed. Wrongful confinement is a more serious form — the person is wrongfully restrained so as to prevent them from proceeding beyond certain circumscribed limits. Codified under BNS ss. 272-275 (IPC ss. 339-348).",
        "elements": [
            "Voluntary obstruction of movement",
            "Obstruction prevents proceeding in a lawful direction",
            "Knowledge of the obstruction",
        ],
        "statutes": ["BNS ss. 272-275", "IPC ss. 339-348 (repealed)"],
        "landmark_cases": [
            "State of Kerala vs. K. N. Bhaskaran (1986)",
            "Rameshwar vs. State of Rajasthan (2014)",
        ],
    },
    "defamation": {
        "name": "Defamation (Criminal)",
        "aliases": ["maanahani", "reputation injury"],
        "domain": "criminal",
        "explanation": "Whoever makes or publishes any imputation concerning any person intending to harm, or knowing or having reason to believe that such imputation will harm, the reputation of that person, is said to defame that person. Truth is a defence if made for the public good. Codified under BNS s. 353 (IPC s. 499).",
        "elements": [
            "Imputation concerning a person (spoken, written, or visual)",
            "Intention or knowledge that imputation will harm reputation",
            "Publication or communication to at least one person",
        ],
        "statutes": [
            "BNS s. 353 (defamation)",
            "Constitution Art. 19(1)(a) (free speech limitation)",
        ],
        "landmark_cases": [
            "Subramanian Swamy vs. Union of India (2016) — constitutional validity upheld",
            "S. Khushboo vs. Kanniammal (2010)",
        ],
    },
    # ── Constitutional Law ─────────────────────────────────────────
    "equality_before_law": {
        "name": "Equality Before Law",
        "aliases": ["equal protection", "Article 14", "right to equality"],
        "domain": "constitutional",
        "explanation": "Art. 14 of the Constitution guarantees equality before the law and equal protection of the laws within India. This prohibits class legislation but permits reasonable classification based on intelligible differentia with a rational nexus to the objective. It is a fundamental right and the cornerstone of Indian constitutionalism.",
        "elements": [
            "Equality before the law (no special privileges)",
            "Equal protection of the laws",
            "Reasonable classification permitted — must be based on intelligible differentia with rational nexus",
        ],
        "statutes": ["Constitution of India, Art. 14"],
        "landmark_cases": [
            "Chiranjit Lal Chowdhury vs. Union of India (1950)",
            "State of W.B. vs. Anwar Ali Sarkar (1952)",
            "E.P. Royappa vs. State of T.N. (1974)",
        ],
    },
    "freedom_of_speech": {
        "name": "Freedom of Speech and Expression",
        "aliases": ["free speech", "Article 19(1)(a)", "right to express"],
        "domain": "constitutional",
        "explanation": "Art. 19(1)(a) guarantees all citizens the right to freedom of speech and expression. This includes the right to express opinions, publish ideas, communicate through any medium, and the right to receive information. It is subject to reasonable restrictions under Art. 19(2) in the interests of sovereignty, security, public order, decency, morality, contempt of court, defamation, and incitement.",
        "elements": [
            "Right to express opinions and ideas",
            "Right to publish and circulate",
            "Right to receive information",
            "Limited by reasonable restrictions under Art. 19(2)",
        ],
        "statutes": ["Constitution of India, Art. 19(1)(a), 19(2)"],
        "landmark_cases": [
            "Romesh Thapar vs. State of Madras (1950)",
            "Bennett Coleman vs. Union of India (1973) — newsprint case",
            "Shreya Singhal vs. Union of India (2015) — s. 66A struck down",
        ],
    },
    "right_to_privacy": {
        "name": "Right to Privacy",
        "aliases": ["privacy right", "Article 21 privacy", "personal autonomy"],
        "domain": "constitutional",
        "explanation": "The right to privacy is a constitutionally protected fundamental right under Art. 21 of the Constitution, as declared by the Supreme Court in K.S. Puttaswamy (2017). Privacy includes: (1) decisional autonomy (personal choices), (2) spatial control (home, body), and (3) informational privacy (control over personal data). It is not absolute and may be restricted by law on legitimate state aims.",
        "elements": [
            "Decisional autonomy — right to make personal choices",
            "Spatial control — freedom from intrusion into private spaces",
            "Informational privacy — control over personal data",
            "Proportionality test for any state restriction",
        ],
        "statutes": ["Constitution of India, Art. 21"],
        "landmark_cases": [
            "K.S. Puttaswamy vs. Union of India (2017) — 9-judge bench",
            "M.P. Sharma vs. Satish Chandra (1954) — overruled in part",
            "PUCL vs. Union of India (1997) — telephone tapping",
        ],
    },
    "right_to_education": {
        "name": "Right to Education",
        "aliases": ["Article 21A", "RTE Act", "education right"],
        "domain": "constitutional",
        "explanation": "The Constitution (86th Amendment) Act, 2002 inserted Art. 21A guaranteeing the right to free and compulsory education of all children aged 6-14 years. The RTE Act, 2009 implements this right. The right has also been read into Art. 21 (right to life) for higher education, requiring the state to ensure accessible and affordable education.",
        "elements": [
            "Free and compulsory education for children 6-14",
            "Quality standards under RTE Act",
            "No child can be denied admission for lack of documents",
        ],
        "statutes": ["Constitution of India, Art. 21A", "RTE Act, 2009"],
        "landmark_cases": [
            "Unni Krishnan vs. State of A.P. (1993) — education as a fundamental right",
            "Society for Unaided Private Schools vs. Union of India (2012) — RTE upheld",
        ],
    },
    "directive_principles": {
        "name": "Directive Principles of State Policy",
        "aliases": ["DPSP", "Part IV", "Article 36-51"],
        "domain": "constitutional",
        "explanation": "Part IV of the Constitution (Arts. 36-51) contains directive principles that are fundamental in the governance of the country. Though not enforceable by any court, they are nevertheless fundamental in the governance of the country. Key principles include: adequate livelihood, equal pay, right to work, living wage, uniform civil code, free legal aid, and environmental protection.",
        "elements": [
            "Non-justiciable but fundamental in governance",
            "State shall apply them in making laws",
            "Harmonious interpretation with Fundamental Rights",
        ],
        "statutes": ["Constitution of India, Arts. 36-51"],
        "landmark_cases": [
            "Kesavananda Bharati vs. State of Kerala (1973) — basic structure",
            "Minerva Mills vs. Union of India (1980) — DPSP-FR balance",
        ],
    },
    "fundamental_duties": {
        "name": "Fundamental Duties",
        "aliases": ["Part IVA", "Article 51A", "citizen duties"],
        "domain": "constitutional",
        "explanation": "Part IVA (Art. 51A) of the Constitution, inserted by the 42nd Amendment (1976), lists 11 fundamental duties of every citizen. These include: respecting the Constitution, cherishing national freedom, promoting harmony, protecting the environment, safeguarding public property, and striving towards excellence. While not directly enforceable, they guide judicial interpretation of fundamental rights.",
        "elements": [
            "Respect Constitution, national flag, and anthem",
            "Cherish and follow noble ideals of the freedom struggle",
            "Defend the country and render national service when called",
            "Promote harmony and brotherhood",
            "Protect the environment and public property",
        ],
        "statutes": ["Constitution of India, Art. 51A"],
        "landmark_cases": [
            "Rangarajan vs. P. Jagjivan Ram (1989) — duties and rights balance",
            "AIIMS Students Union vs. AIIMS (2001) — duties as interpretive aid",
        ],
    },
    "writ_jurisdiction": {
        "name": "Writ Jurisdiction",
        "aliases": [
            "constitutional remedies",
            "Article 32",
            "Article 226",
            "habeas corpus",
            "mandamus",
            "prohibition",
            "certiorari",
            "quo warranto",
        ],
        "domain": "constitutional",
        "explanation": "Writs are constitutional remedies for enforcement of fundamental rights. The Supreme Court can issue writs under Art. 32, and High Courts under Art. 226. Five types: (1) Habeas Corpus — produce a detained person, (2) Mandamus — command performance of duty, (3) Prohibition — prevent a lower court from exceeding jurisdiction, (4) Certiorari — quash an order, (5) Quo Warranto — challenge a person's right to hold public office.",
        "elements": [
            "Habeas Corpus — unlawful detention",
            "Mandamus — public duty not performed",
            "Prohibition — lower tribunal exceeding jurisdiction",
            "Certiorari — judicial or quasi-judicial order to be quashed",
            "Quo Warranto — usurpation of public office",
        ],
        "statutes": [
            "Constitution of India, Art. 32 (SC)",
            "Constitution of India, Art. 226 (HC)",
        ],
        "landmark_cases": [
            "A.D.M. Jabalpur vs. Shivkant Shukla (1976) — habeas corpus during Emergency",
            "Bandhua Mukti Morcha vs. Union of India (1984) — mandamus for bonded labour",
        ],
    },
    "public_interest_litigation": {
        "name": "Public Interest Litigation (PIL)",
        "aliases": ["PIL", "social action litigation", "public law litigation"],
        "domain": "constitutional",
        "explanation": "PIL is a mechanism whereby any public-spirited citizen can approach the court for enforcement of rights of disadvantaged groups who cannot approach the court themselves. Originating from the post-Emergency era, PIL has been used for environmental protection, prison reform, police reform, and accountability. Strict locus standi rules are relaxed.",
        "elements": [
            "Bona fide public interest (not personal gain)",
            "Disadvantaged or vulnerable group affected",
            "Substantial public importance",
            "No alternative efficacious remedy",
        ],
        "statutes": ["Constitution of India, Art. 32, 226"],
        "landmark_cases": [
            "S.P. Gupta vs. Union of India (1981) — PIL originated",
            "M.C. Mehta vs. Union of India (1987) — Ganga pollution",
            "Vishaka vs. State of Rajasthan (1997) — sexual harassment guidelines",
        ],
    },
    # ── Tort Law ───────────────────────────────────────────────────
    "negligence": {
        "name": "Negligence",
        "aliases": ["carelessness", "duty of care", "tort of negligence"],
        "domain": "tort",
        "explanation": "Negligence is the breach of a legal duty to take care resulting in damage to the plaintiff. The tort has four elements: duty of care, breach of that duty, causation (factual and legal), and damage. In India, negligence is also a criminal offence in certain cases (BNS s. 278 — causing death by negligence).",
        "elements": [
            "Duty of care owed by defendant to plaintiff",
            "Breach of that duty (below the standard of care)",
            "Causation — breach caused the damage",
            "Damage — actual loss or injury",
        ],
        "statutes": [
            "BNS s. 278 (causing death by negligence)",
            "Motor Vehicles Act, 1988",
        ],
        "landmark_cases": [
            "Donoghue vs. Stevenson (1932) — neighbour principle",
            "M.C. Mehta vs. Union of India (1987) — absolute liability",
            "State of Rajasthan vs. Khandaka Jain (2007)",
        ],
    },
    "nuisance": {
        "name": "Nuisance",
        "aliases": ["public nuisance", "private nuisance", "tort of nuisance"],
        "domain": "tort",
        "explanation": "Nuisance is an unlawful interference with a person's use or enjoyment of land, or with the public's rights. Private nuisance affects an individual; public nuisance affects the community. Under BNS s. 310, a public nuisance is punishable. Remedies include damages, injunction, and abatement.",
        "elements": [
            "Unreasonable interference",
            "With use/enjoyment of land (private) or public rights (public)",
            "Damage or substantial annoyance",
        ],
        "statutes": [
            "BNS s. 310 (public nuisance)",
            "Environmental Protection Act, 1986",
        ],
        "landmark_cases": [
            "Municipal Council, Ratlam vs. Vardhichand (1980)",
            "Rural Litigation and Entitlement Kendra (1985) — Doon Valley",
        ],
    },
    "strict_liability": {
        "name": "Strict Liability",
        "aliases": ["no-fault liability", "Rylands v. Fletcher"],
        "domain": "tort",
        "explanation": "The rule in Rylands v. Fletcher (1868) holds that a person who brings and keeps a dangerous thing on their land is strictly liable if it escapes and causes damage, regardless of negligence. The rule applies to non-natural use of land. Defences include: consent, act of God, act of third party, and statutory authority.",
        "elements": [
            "Dangerous thing brought onto land",
            "Non-natural use of land",
            "Escape of the thing",
            "Damage caused by the escape",
        ],
        "statutes": ["Common law (adopted in India)"],
        "landmark_cases": [
            "M.C. Mehta vs. Union of India (1987) — Shriram gas leak",
            "Rylands vs. Fletcher (1868) — origin of principle",
        ],
    },
    "absolute_liability": {
        "name": "Absolute Liability",
        "aliases": ["no-defence liability", "M.C. Mehta principle"],
        "domain": "tort",
        "explanation": "The Supreme Court in M.C. Mehta vs. Union of India (1987) evolved the principle of absolute liability for enterprises engaged in hazardous activities. Unlike strict liability, absolute liability does NOT permit defences like act of God or third-party intervention. The quantum of damages must be proportional to the enterprise's capacity.",
        "elements": [
            "Enterprise engaged in inherently dangerous activity",
            "Escape of hazardous substance",
            "Damage caused by the escape",
            "No defences available",
        ],
        "statutes": ["Public Liability Insurance Act, 1991"],
        "landmark_cases": [
            "M.C. Mehta vs. Union of India (1987) — oleum gas leak",
            "Union Carbide vs. Union of India (1989) — Bhopal gas tragedy",
        ],
    },
    # ── Law of Evidence ────────────────────────────────────────────
    "burden_of_proof": {
        "name": "Burden of Proof",
        "aliases": ["onus probandi", "onus of proof"],
        "domain": "evidence",
        "explanation": "The burden of proof lies on the person who would fail if no evidence were given on either side. In criminal cases, the prosecution must prove guilt beyond reasonable doubt. In civil cases, the plaintiff must prove their case on the balance of probabilities. Certain presumptions may shift the burden (e.g., presumption of innocence, presumption of legitimacy).",
        "elements": [
            "He who asserts must prove",
            "Criminal: prosecution must prove beyond reasonable doubt",
            "Civil: plaintiff must prove on balance of probabilities",
            "Burden may shift by statute or presumption",
        ],
        "statutes": [
            "BNSA ss. 101-114A (Evidence Act)",
            "Indian Evidence Act 1872, ss. 101-114A",
        ],
        "landmark_cases": [
            "Woolmington vs. DPP (1935) — golden thread of criminal law",
            "Rahul vs. State of Delhi (2023) — BSA application",
        ],
    },
    "dying_declaration": {
        "name": "Dying Declaration",
        "aliases": ["deathbed statement", "letus mortem declaratio"],
        "domain": "evidence",
        "explanation": "A statement made by a person as to the cause of their death or as to circumstances resulting in death is relevant and admissible even though the maker is dead. Under BNSA s. 25(1) (Indian Evidence Act s. 32(1)), a dying declaration does not need to be on oath or subject to cross-examination. It is a powerful piece of evidence but must be carefully scrutinised.",
        "elements": [
            "Statement relates to cause of death or circumstances",
            "Maker is dead or cannot be found",
            "Statement must be voluntary and reliable",
            "No requirement of oath or cross-examination",
        ],
        "statutes": ["BNSA s. 25(1)", "Indian Evidence Act 1872, s. 32(1)"],
        "landmark_cases": [
            "Kushal Rao vs. State of Bombay (1958)",
            "Paniben vs. State of Gujarat (1992)",
            "Laxman vs. State of Maharashtra (2002)",
        ],
    },
    "confession": {
        "name": "Confession",
        "aliases": ["judicial confession", "extra-judicial confession", "guilty plea"],
        "domain": "evidence",
        "explanation": "A confession is an admission of guilt by an accused person. It may be judicial (made before a magistrate) or extra-judicial (made to anyone else). Confessions must be voluntary and free from inducement, threat, or promise. Confessions made to a police officer are generally inadmissible under BNSA ss. 24-30 (Evidence Act ss. 24-30).",
        "elements": [
            "Clear admission of guilt",
            "Voluntary — no inducement, threat, or promise",
            "Judicial: made before magistrate with warnings",
            "Extra-judicial: corroboration generally required",
        ],
        "statutes": ["BNSA ss. 24-30", "Indian Evidence Act 1872, ss. 24-30"],
        "landmark_cases": [
            "R. vs. Baldry (1852) — voluntariness test",
            "Sahai vs. State of U.P. (1996)",
            "State of Rajasthan vs. Balchand (1977)",
        ],
    },
    "expert_evidence": {
        "name": "Expert Evidence",
        "aliases": ["expert opinion", "expert testimony", "skilled witness"],
        "domain": "evidence",
        "explanation": "When the court has to form an opinion on a point of foreign law, science, art, identity, handwriting, or finger impression, the opinions of experts in that field are relevant. Under BNSA ss. 39-52 (Evidence Act ss. 45-51), experts may give opinions. The court is not bound by expert opinion and may form its own conclusion.",
        "elements": [
            "Specialised knowledge in the relevant field",
            "Court requires assistance to form opinion",
            "Expert must be qualified and competent",
            "Opinion must be reasoned and supported",
        ],
        "statutes": ["BNSA ss. 39-52", "Indian Evidence Act 1872, ss. 45-51"],
        "landmark_cases": [
            "R. vs. Turner (1975) — scope of expert evidence",
            "Murarilal vs. State of M.P. (1980) — expert in criminal cases",
        ],
    },
    "oral_evidence": {
        "name": "Oral Evidence",
        "aliases": ["viva voce", "testimony", "witness testimony"],
        "domain": "evidence",
        "explanation": "Oral evidence refers to statements made by witnesses before the court. All facts except the contents of documents may be proved by oral evidence under BNSA s. 56 (Evidence Act s. 59). Witnesses must speak from personal knowledge unless the court permits otherwise. The court may test the credibility through cross-examination.",
        "elements": [
            "Witness must have personal knowledge",
            "Evidence given in court on oath",
            "Subject to cross-examination by the opposite party",
            "Contents of documents must be proved by primary evidence",
        ],
        "statutes": ["BNSA ss. 56-60", "Indian Evidence Act 1872, ss. 59-63"],
        "landmark_cases": [
            "State of U.P. vs. Jaggo (1971)",
            "Shivaji Sahebrao Bobade vs. State of Maharashtra (1973)",
        ],
    },
    "documentary_evidence": {
        "name": "Documentary Evidence",
        "aliases": ["documentary proof", "primary evidence", "secondary evidence"],
        "domain": "evidence",
        "explanation": "Documentary evidence comprises documents produced for the inspection of the court. Primary evidence is the document itself; secondary evidence includes certified copies, counterparts, and oral accounts of the document's contents. Under BNSA ss. 61-75 (Evidence Act ss. 61-90), documents must generally be proved by primary evidence.",
        "elements": [
            "Primary evidence: the document itself",
            "Secondary evidence: copies, counterparts, oral accounts",
            "Primary evidence is the general rule",
            "Exception for lost, destroyed, or detained documents",
        ],
        "statutes": ["BNSA ss. 61-75", "Indian Evidence Act 1872, ss. 61-90"],
        "landmark_cases": [
            "R. vs. Chhagan (1976)",
            "Hiralal vs. Badkulal (1953) — proving handwritten documents",
        ],
    },
    # ── Civil Procedure ────────────────────────────────────────────
    "cause_of_action": {
        "name": "Cause of Action",
        "aliases": ["COA", "right to sue", "basis of claim"],
        "domain": "civil_procedure",
        "explanation": "A cause of action is a set of facts sufficient to justify a right to sue and obtain money, property, or enforcement of a right against another party. It comprises every fact which, if traversed, the plaintiff must prove to succeed. A suit must be filed only after the cause of action has arisen. CPC s. 20 addresses the place of suing based on cause of action.",
        "elements": [
            "Existence of a legal right in the plaintiff",
            "Violation of that right by the defendant",
            "Every fact essential to the claim",
        ],
        "statutes": ["CPC s. 20", "CPC s. 26 (institution of suits)"],
        "landmark_cases": [
            "Mohd. Khalil Khan vs. Mahbub Ali (1948)",
            "Bloom Dekor vs. Subhash Himmatlal (1994)",
        ],
    },
    "locus_standi": {
        "name": "Locus Standi",
        "aliases": ["right to sue", "standing", "standing to sue"],
        "domain": "civil_procedure",
        "explanation": "Locus standi means the right of a party to appear and be heard before a court. Only a person whose legal rights have been directly affected has the standing to sue. In PIL, this rule is relaxed. The principle prevents busybodies and meddlesome interlopers from filing frivolous cases.",
        "elements": [
            "Direct injury or infringement of legal right",
            "Sufficient interest in the subject matter",
            "Not a mere busybody or meddlesome interloper",
        ],
        "statutes": ["CPC s. 9", "Constitution of India, Art. 32, 226"],
        "landmark_cases": [
            "S.P. Gupta vs. Union of India (1981) — PIL standing relaxed",
            "Bombay Corporation vs. Advance Builders (1971)",
        ],
    },
    "injunction": {
        "name": "Injunction",
        "aliases": [
            "temporary injunction",
            "perpetual injunction",
            "interlocutory injunction",
            "stay order",
        ],
        "domain": "civil_procedure",
        "explanation": "An injunction is a judicial order restraining a person from doing or continuing a particular act, or compelling them to do a particular act. Temporary injunctions (CPC O.39) remain in force until a specified date or further order. Perpetual injunctions (Specific Relief Act s. 38-42) are granted by final decree. The remedy is equitable and discretionary.",
        "elements": [
            "Prima facie case in favour of the applicant",
            "Balance of convenience favours injunction",
            "Irreparable injury if injunction is not granted",
            "No alternative efficacious remedy",
        ],
        "statutes": ["CPC O. 39 (temporary)", "Specific Relief Act, 1963 ss. 36-42"],
        "landmark_cases": [
            "Dalpat Kumar vs. Prahlad Singh (1992)",
            "Wander Ltd. vs. Antox India (1990)",
        ],
    },
    "specific_performance": {
        "name": "Specific Performance of Contract",
        "aliases": ["specific relief", "enforcement of contract"],
        "domain": "civil_procedure",
        "explanation": "Specific performance is an equitable remedy where the court orders a party to perform their obligations under a contract as agreed, rather than merely paying damages. Available when damages are inadequate compensation (e.g., sale of land, rare goods). Governed by the Specific Relief Act, 1963 (ss. 9-25).",
        "elements": [
            "Valid and enforceable contract exists",
            "Plaintiff has performed or is ready to perform their part",
            "Damages are not an adequate remedy",
            "Contract is not personal in nature",
        ],
        "statutes": ["Specific Relief Act, 1963 ss. 9-25", "Indian Contract Act, 1872"],
        "landmark_cases": [
            "Kallathil Sreedharan vs. Komath (2002)",
            "N.P. Thirugnanam vs. R. Jagan Mohan Rao (1995)",
        ],
    },
    "attachment": {
        "name": "Attachment of Property",
        "aliases": ["assets attachment", "property attachment", "garnishee order"],
        "domain": "civil_procedure",
        "explanation": "Attachment is the seizure of a defendant's property by court order before or after judgment to ensure satisfaction of a decree. Under CPC O.38, attachment before judgment prevents the defendant from disposing of assets pending suit. CPC O.21 deals with attachment in execution of a decree. Certain properties (e.g., tools of trade, essential clothing) are exempt.",
        "elements": [
            "Court order for seizure of property",
            "Before judgment: likelihood of asset dissipation",
            "After judgment: execution of decree",
            "Attached property is held pending court's further orders",
        ],
        "statutes": ["CPC O. 38 (before judgment)", "CPC O. 21 (execution)"],
        "landmark_cases": [
            "Premier Tyres vs. Kerala State Road Transport (1993)",
            "Rajendran vs. K. Krishnan (2015)",
        ],
    },
    "discovery_and_inspection": {
        "name": "Discovery and Inspection",
        "aliases": [
            "discovery of documents",
            "interrogatories",
            "disclosure",
        ],
        "domain": "civil_procedure",
        "explanation": "Discovery is the pre-trial stage where parties disclose documents and information relevant to the case. Under CPC O.11, parties may serve interrogatories (written questions), request discovery (list of relevant documents), and seek inspection (physical examination of documents). The purpose is to narrow issues, prevent surprise, and secure evidence.",
        "elements": [
            "Interrogatories: written questions to be answered on oath",
            "Discovery: list of relevant documents filed",
            "Inspection: right to examine opposing party's documents",
            "Privileged documents immune from discovery",
        ],
        "statutes": ["CPC O. 11"],
        "landmark_cases": [
            "M.L. Sethi vs. R.P. Kapur (1972)",
            "K. Satwant Singh vs. State of Punjab (1960)",
        ],
    },
    "limitation": {
        "name": "Law of Limitation",
        "aliases": ["period of limitation", "time bar", "limitation period"],
        "domain": "civil_procedure",
        "explanation": "The Limitation Act, 1963 prescribes the maximum time period within which a suit, appeal, or application must be filed. After the prescribed period expires, the right to sue is barred (though the right itself may survive). Key periods: 3 years for contracts, 12 years for immovable property, 1 year for torts. The court cannot sue moto raise limitation — it must be pleaded.",
        "elements": [
            "Prescribed period varies by cause of action",
            "Period starts from accrual of cause of action",
            "Expired period bars the remedy, not the right",
            "Limitation must be specifically pleaded as a defence",
        ],
        "statutes": ["Limitation Act, 1963", "CPC s. 3 (bar of limitation)"],
        "landmark_cases": [
            "Bangalore Water Supply vs. Rajappa (1978)",
            "P.K. Ramachandran vs. State of Kerala (1997)",
        ],
    },
    # ── Family Law ──────────────────────────────────────────────────
    "cruelty_divorce": {
        "name": "Cruelty as a Ground for Divorce",
        "aliases": [
            "cruelty",
            "matrimonial cruelty",
            "mental cruelty",
            "physical cruelty",
        ],
        "domain": "family",
        "explanation": "Cruelty is a ground for divorce under the Hindu Marriage Act, 1955 (s. 13(1)(ia)), Special Marriage Act, 1954 (s. 27(1)(d)), and other personal laws. Cruelty includes both physical and mental cruelty. Mental cruelty includes behaviour that causes reasonable apprehension of harm or injury, or makes cohabitation intolerable. The test is objective — what a reasonable person would consider cruelty.",
        "elements": [
            "Physical cruelty: bodily harm or violence",
            "Mental cruelty: behaviour causing anguish, fear, or distress",
            "Conduct must be grave and weighty",
            "Reasonable apprehension of harm or injury",
        ],
        "statutes": [
            "HMA 1955 s. 13(1)(ia)",
            "Special Marriage Act 1954 s. 27(1)(d)",
            "DV Act 2005",
        ],
        "landmark_cases": [
            "N.G. Dastane vs. S. Dastane (1975)",
            "V. Bhagat vs. D. Bhagat (1994)",
            "S. Hanumantha Rao vs. S. Ramani (1999)",
        ],
    },
    "restitution_conjugal_rights": {
        "name": "Restitution of Conjugal Rights",
        "aliases": ["RCR", "withdrawal from society", "conjugal society"],
        "domain": "family",
        "explanation": "If a spouse withdraws from the society of the other without reasonable excuse, the aggrieved spouse may petition the court for restitution of conjugal rights. Available under HMA s. 9, Special Marriage Act s. 36, and other personal laws. The court may order the deserting spouse to resume cohabitation. Non-compliance may lead to an inference of desertion for divorce.",
        "elements": [
            "Marriage between the parties",
            "One spouse has withdrawn from the other's society",
            "Withdrawal is without reasonable excuse",
            "Aggrieved spouse desires resumption of cohabitation",
        ],
        "statutes": [
            "HMA 1955 s. 9",
            "Special Marriage Act 1954 s. 36",
        ],
        "landmark_cases": [
            "Saroj Rani vs. Sudarshan Kumar (1984)",
            "S. Hanumantha Rao vs. S. Ramani (1999)",
        ],
    },
    "judicial_separation": {
        "name": "Judicial Separation",
        "aliases": ["separation decree", "legal separation"],
        "domain": "family",
        "explanation": "Judicial separation is a decree whereby spouses are allowed to live apart without dissolving the marriage. Available under HMA s. 10 and other personal laws. Grounds are similar to divorce. The decree does not sever the marriage bond — the parties remain married and cannot remarry. Judicial separation may be followed by divorce if reconciliation fails.",
        "elements": [
            "Grounds identical to divorce (adultery, cruelty, desertion, etc.)",
            "Decree permits living apart without divorce",
            "Duty to cohabit ceases",
            "Court may attempt reconciliation before granting",
        ],
        "statutes": [
            "HMA 1955 s. 10",
            "Special Marriage Act 1954 s. 35",
        ],
        "landmark_cases": [
            "Sureshta Devi vs. Om Prakash (1991)",
            "S. Hanumantha Rao vs. S. Ramani (1999)",
        ],
    },
    "maintenance": {
        "name": "Maintenance and Alimony",
        "aliases": [
            "spousal support",
            "wife maintenance",
            "interim maintenance",
            "permanent alimony",
        ],
        "domain": "family",
        "explanation": "Maintenance is financial support paid by one spouse to another during or after marriage. Under various Indian laws: CrPC/BNSS s. 144 (support for wife/children/parents), HMA s. 24-25 (spousal maintenance), DV Act s. 20 (monetary relief), and the Maintenance and Welfare of Parents and Senior Citizens Act, 2007. Key factors: financial need, capacity to pay, and standard of living.",
        "elements": [
            "Spouse/parent unable to maintain themselves",
            "Other party has sufficient means",
            "Quantum depends on lifestyle, income, and needs",
            "May be interim (during proceedings) or permanent",
        ],
        "statutes": [
            "BNSS s. 144 (CrPC s. 125)",
            "HMA 1955 ss. 24-25",
            "DV Act 2005 s. 20",
        ],
        "landmark_cases": [
            "Mohd. Ahmed Khan vs. Shah Bano Begum (1985)",
            "Danial Latifi vs. Union of India (2001)",
            "Rajnesh vs. Neha (2021)",
        ],
    },
    "child_custody": {
        "name": "Child Custody",
        "aliases": ["custody of child", "parental custody", "guardianship"],
        "domain": "family",
        "explanation": "Child custody refers to the legal and practical care of a minor child following separation or divorce. The paramount consideration is the welfare of the child. Custody may be: (1) physical custody — where the child lives, (2) legal custody — decision-making authority. Courts consider age, gender, education, financial stability, and the child's preference (if old enough).",
        "elements": [
            "Welfare of the child is the paramount consideration",
            "Child's age, health, education, and emotional needs",
            "Parent's financial capacity and moral fitness",
            "Child's preference (if sufficiently mature)",
        ],
        "statutes": [
            "HMA 1955 s. 26",
            "Guardians and Wards Act, 1890",
            "Hindu Minority and Guardianship Act, 1956",
        ],
        "landmark_cases": [
            "Rosy Jacob vs. Jacob Chakramakkal (1973)",
            "Mausami Moitra Ganguli vs. Jayanta Ganguli (2008)",
            "Vivek Singh vs. Romani Singh (2017)",
        ],
    },
    "guardianship": {
        "name": "Guardianship",
        "aliases": ["guardian of minor", "legal guardian", "natural guardian"],
        "domain": "family",
        "explanation": "A guardian is a person who has the care of the person or property of a minor. Natural guardians under Hindu law: father (then mother). Testamentary guardians may be appointed by will. The court may appoint guardians under the Guardians and Wards Act, 1890. The guardian's powers over the minor's property are limited — they cannot alienate without court permission.",
        "elements": [
            "Minor (below 18) or person of unsound mind",
            "Guardian may be natural, testamentary, or court-appointed",
            "Duty to protect the ward's person and property",
            "Court approval required for sale of minor's property",
        ],
        "statutes": [
            "Hindu Minority and Guardianship Act, 1956",
            "Guardians and Wards Act, 1890",
        ],
        "landmark_cases": [
            "Gita Hariharan vs. RBI (1999) — mother as natural guardian",
            "Lakshmi Kant Pandey vs. Union of India (1984) — inter-country adoption",
        ],
    },
    "adoption": {
        "name": "Adoption",
        "aliases": ["child adoption", "datta homam"],
        "domain": "family",
        "explanation": "Adoption is the legal process whereby a person takes another person's child into their family as their own. Hindus may adopt under the Hindu Adoption and Maintenance Act, 1956. Non-Hindus may adopt under JJ Act, 2015 and CARA regulations. Adoption severs ties with biological parents and transfers all rights to the adoptive parents. Inter-country adoption is regulated by CARA.",
        "elements": [
            "Adoptive parent must have capacity and intent",
            "Child must be capable of being adopted",
            "Legal formalities (registered deed, court order)",
            "CARA compliance for inter-country adoption",
        ],
        "statutes": [
            "Hindu Adoption and Maintenance Act, 1956",
            "Juvenile Justice (Care and Protection) Act, 2015",
            "CARA Guidelines",
        ],
        "landmark_cases": [
            "Lakshmi Kant Pandey vs. Union of India (1984)",
            "Shabnam Hashmi vs. Union of India (2014)",
        ],
    },
    # ── Property Law ────────────────────────────────────────────────
    "adverse_possession": {
        "name": "Adverse Possession",
        "aliases": ["squatter's rights", "hostile possession", "prescription"],
        "domain": "property",
        "explanation": "A person who is not the owner of land may acquire title by possessing it adversely to the true owner for the statutory period (12 years under the Limitation Act, 1963). The possession must be: (1) actual, (2) open and notorious, (3) exclusive, (4) hostile to the true owner's title, and (5) continuous for the full period. The true owner's right to recover is extinguished.",
        "elements": [
            "Actual physical possession of the property",
            "Open and notorious (not secret)",
            "Exclusive possession",
            "Hostile (adverse) to the true owner's interest",
            "Continuous for 12 years",
        ],
        "statutes": ["Limitation Act, 1963 Arts. 64-65 (12 years)"],
        "landmark_cases": [
            "Ravinder Kaur Grewal vs. Manjit Kaur (2019)",
            "Karnataka Board of Wakf vs. Indian Society (2004)",
            "M. Venkatesh vs. B.S. Gopal (2025)",
        ],
    },
    "easement": {
        "name": "Easement",
        "aliases": ["right of way", "servitude", "right of easement"],
        "domain": "property",
        "explanation": "An easement is a right enjoyed by the owner of land over the land of another for the beneficial enjoyment of their own land. Examples: right of way, right to light, right to air, right to drainage. Easements may be created by: express grant, prescription (continuous use for 20 years), necessity, or custom. Governed by the Indian Easements Act, 1882.",
        "elements": [
            "Dominant tenement (benefited land) and servient tenement (burdened land)",
            "Right must be for the beneficial enjoyment of the dominant tenement",
            "Two distinct owners (one cannot have an easement over their own land)",
            "Right must be certain and capable of forming the subject matter",
        ],
        "statutes": ["Indian Easements Act, 1882"],
        "landmark_cases": [
            "Chapsibhai Dhanjibhai vs. Purushottam (1971)",
            "Sunderbai vs. Bhanudas (1994)",
        ],
    },
    "mortgage": {
        "name": "Mortgage",
        "aliases": ["home loan", "hypothecation", "pledge of property"],
        "domain": "property",
        "explanation": "A mortgage is the transfer of an interest in specific immovable property for securing a loan or debt. The transferor is the mortgagor; the transferee is the mortgagee. Types include: simple mortgage, mortgage by conditional sale, usufructuary mortgage, English mortgage, and equitable mortgage (by deposit of title deeds). Governed by the Transfer of Property Act, 1882 (ss. 58-104).",
        "elements": [
            "Transfer of interest in immovable property",
            "Security for payment of money (loan/debt)",
            "Mortgagor retains right to redeem the property",
            "Mortgagee has right to sell or foreclose on default",
        ],
        "statutes": ["Transfer of Property Act, 1882 ss. 58-104"],
        "landmark_cases": [
            "K.K. Verma vs. Union of India (1954)",
            "Narandas Karsondas vs. S.A. Kamtam (1977)",
        ],
    },
    "lease": {
        "name": "Lease of Immovable Property",
        "aliases": ["rental agreement", "tenancy", "rent agreement"],
        "domain": "property",
        "explanation": "A lease is the transfer of a right to enjoy immovable property for a certain time in consideration of rent or premium. The transferor is the lessor; the transferee is the lessee. Leases are governed by the Transfer of Property Act, 1882 (ss. 105-117). Leases for more than 12 months must be registered. The lessee has a right to quiet enjoyment and can assign the lease unless prohibited.",
        "elements": [
            "Transfer of right to enjoy property",
            "Fixed term or periodic term",
            "Consideration: rent or premium",
            "Lessor's covenants: quiet enjoyment, non-derogation from grant",
            "Lessee's covenants: pay rent, maintain property",
        ],
        "statutes": ["Transfer of Property Act, 1882 ss. 105-117"],
        "landmark_cases": [
            "S.B. (House Building) Society vs. O.P. Gupta (1997)",
            "Rajendra Kumar vs. Poosammal (2014)",
        ],
    },
    "gift": {
        "name": "Gift (Transfer of Property)",
        "aliases": ["donation", "gratuitous transfer", "hiba"],
        "domain": "property",
        "explanation": "A gift is the voluntary transfer of existing movable or immovable property by one person to another without consideration (gratuitously). Under the Transfer of Property Act, 1882 (ss. 122-129), a gift of immovable property must be by registered deed and accepted during the donor's lifetime. Gifts may be revoked for certain reasons (e.g., non-payment of maintenance or coercion).",
        "elements": [
            "Voluntary and without consideration",
            "Existing property (not future property)",
            "Immovable: registered deed + acceptance",
            "Movable: delivery + acceptance (or registered deed)",
            "Donor must be competent and of sound mind",
        ],
        "statutes": ["Transfer of Property Act, 1882 ss. 122-129"],
        "landmark_cases": [
            "H.S. Rikhy vs. New Delhi Municipal Committee (1962)",
            "K. Balakrishnan vs. K. Kamalam (2004)",
        ],
    },
    # ── Contract / Commercial ───────────────────────────────────────
    "consideration": {
        "name": "Consideration in Contract",
        "aliases": ["quid pro quo", "something in return", "privity of consideration"],
        "domain": "commercial",
        "explanation": "Consideration is the price paid for the promise of the other. It is an essential element of a valid contract under the Indian Contract Act, 1872 (s. 10). Consideration may be past, present, or future. It must be real, though it need not be adequate. The doctrine of privity means only parties to the contract can sue — third parties cannot enforce a contract even if made for their benefit.",
        "elements": [
            "At the desire of the promisor",
            "Movable by the promise or any other person",
            "May be an act, abstinence, or return promise",
            "Must be real (not illusory) but need not be adequate",
        ],
        "statutes": ["Indian Contract Act, 1872 ss. 2(d), 10, 25"],
        "landmark_cases": [
            "Currie vs. Misa (1875) — definition of consideration",
            "Chinnaya vs. Ramayya (1882) — stranger to consideration",
            "Mohori Bibi vs. Dharmodas Ghose (1903) — minor's contract void",
        ],
    },
    "breach_of_contract": {
        "name": "Breach of Contract",
        "aliases": ["contract breach", "default", "non-performance"],
        "domain": "commercial",
        "explanation": "Breach of contract occurs when a party fails to perform their obligations under a contract without lawful excuse. Breach may be: (1) actual — failure to perform on due date, or (2) anticipatory — repudiation before performance is due. Remedies include: damages (compensatory, nominal, or liquidated), specific performance, injunction, and quantum meruit.",
        "elements": [
            "Valid and enforceable contract",
            "Obligation due from the defendant",
            "Failure to perform without lawful excuse",
            "Damage suffered by the plaintiff",
        ],
        "statutes": [
            "Indian Contract Act, 1872 ss. 51-75",
            "Specific Relief Act, 1963",
        ],
        "landmark_cases": [
            "Hadley vs. Baxendale (1854) — remoteness of damage",
            "Murlidhar Chiranjilal vs. Harishchandra (1962)",
            "Karsandas vs. Gopaldas (2018)",
        ],
    },
    "bailment": {
        "name": "Bailment",
        "aliases": ["pledge", "custody", "deposit"],
        "domain": "commercial",
        "explanation": "Bailment is the delivery of goods by one person (bailor) to another (bailee) for a specific purpose, upon a contract that the goods will be returned when the purpose is accomplished. Under the Indian Contract Act, 1872 (ss. 148-181). Pledge (ss. 172-181) is a special form — goods are delivered as security for a debt. Bailee must take reasonable care of the goods.",
        "elements": [
            "Delivery of movable goods",
            "Specific purpose for delivery",
            "Return of goods on completion of purpose",
            "Bailee's duty: reasonable care",
        ],
        "statutes": ["Indian Contract Act, 1872 ss. 148-181"],
        "landmark_cases": [
            "Union of India vs. Amar Singh (1960)",
            "State Bank of India vs. Quality Bread Factory (1983)",
        ],
    },
    "indemnity": {
        "name": "Contract of Indemnity",
        "aliases": ["indemnification", "hold harmless"],
        "domain": "commercial",
        "explanation": "A contract of indemnity is a contract by which one party promises to save the other from loss caused by the conduct of the promisor or any other person. Under the Indian Contract Act, 1872 (ss. 124-125). The indemnified party can recover: (1) damages caused by an act of the indemnifier, (2) costs of defending the claim, and (3) sums paid under legal compulsion.",
        "elements": [
            "Promise to compensate for loss",
            "Loss caused by the promisor or another person",
            "Indemnified party may recover all necessary costs",
        ],
        "statutes": ["Indian Contract Act, 1872 ss. 124-125"],
        "landmark_cases": [
            "Gajanan Moreshwar vs. Moreshwar Madan (1942)",
            "Askey vs. Golden Wine (1948)",
        ],
    },
    "partnership": {
        "name": "Partnership",
        "aliases": ["firm", "partnership firm", "partners"],
        "domain": "commercial",
        "explanation": "Partnership is the relation between persons who have agreed to share the profits of a business carried on by all or any of them acting for all. Governed by the Indian Partnership Act, 1932. Key features: mutual agency (each partner binds the firm), unlimited liability, and no separate legal entity. Registration is not mandatory but offers significant legal advantages.",
        "elements": [
            "Agreement between two or more persons",
            "Business carried on for profit",
            "Shared profits (and losses)",
            "Mutual agency — each partner is agent for the firm",
            "Unlimited liability of partners",
        ],
        "statutes": ["Indian Partnership Act, 1932"],
        "landmark_cases": [
            "Cox vs. Hickman (1860) — mutual agency test",
            "Dulichand vs. CIT (1956)",
        ],
    },
}

STATUTE_INDEX: Optional[StatuteIndex] = None


def get_index() -> StatuteIndex:
    global STATUTE_INDEX
    if STATUTE_INDEX is None:
        STATUTE_INDEX = StatuteIndex.from_default_path()
    return STATUTE_INDEX


async def legal_concepts(
    concept: str,
    include_case_law: bool = True,
    max_related_sections: int = 5,
) -> dict:
    try:
        concept_key = concept.lower().strip().replace(" ", "_")

        direct_match = CONCEPTS.get(concept_key)
        if not direct_match:
            for key, val in CONCEPTS.items():
                if concept_key in key or concept_key in [
                    a.lower().replace(" ", "_") for a in val.get("aliases", [])
                ]:
                    direct_match = val
                    concept_key = key
                    break

        if not direct_match:
            return {
                "status": "error",
                "error": f"Concept '{concept}' not found. Available concepts: {', '.join(sorted(CONCEPTS.keys()))}",
            }

        index = get_index()
        related_sections = index.search(
            direct_match["name"], max_results=max_related_sections
        )

        result = {
            "status": "success",
            "concept": direct_match["name"],
            "domain": direct_match["domain"],
            "explanation": direct_match["explanation"],
            "elements": direct_match["elements"],
            "governing_statutes": direct_match["statutes"],
            "related_sections": [
                {
                    "act": s.get("full_title", ""),
                    "section": s["section_number"],
                    "title": s["section_title"],
                    "text": s["text"],
                }
                for s in related_sections
            ]
            if include_case_law
            else [],
            "confidence": format_confidence(0.95 if concept_key in CONCEPTS else 0.8),
            "disclaimer": DISCLAIMER,
        }

        if include_case_law:
            result["landmark_cases"] = direct_match.get("landmark_cases", [])

        return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "concept": concept,
        }
