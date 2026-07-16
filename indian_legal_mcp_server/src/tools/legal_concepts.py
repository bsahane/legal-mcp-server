from typing import Optional

from indian_legal_mcp_server.services.statute_index import StatuteIndex
from indian_legal_mcp_server.utils.formatters import (
    format_confidence,
    format_data_freshness,
)
from indian_legal_mcp_server.prompts.system_instructions import DISCLAIMER

CONCEPTS = {
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
        "aliases": ["procedural due process", "substantive due process"],
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
                    a.lower() for a in val.get("aliases", [])
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
