from jinja2 import BaseLoader, Environment


class NoticeTemplate:
    def __init__(self, template_str: str):
        # Renders plain-text Markdown notices, not HTML. autoescape=True would
        # corrupt legitimate values ("Adv. & Co.", "<name>"), so it stays off;
        # nosec records that this is deliberate rather than overlooked.
        self.env = Environment(loader=BaseLoader(), autoescape=False)  # nosec B701
        self.template = self.env.from_string(template_str)

    def render(self, **kwargs) -> str:
        return self.template.render(**kwargs)


BASE_NOTICE_SKELETON = """\
**{{ notice_type.upper() }} NOTICE**
**DRAFT — FOR ADVOCATE REVIEW ONLY**

---

**To,**
{{ recipient_name }}
{{ recipient_address }}

**From,**
{{ client_name }}
{{ client_address }}

**Through,**
Adv. {{ advocate_name }}
{{ advocate_details }}

---

**Subject: {{ subject }}**

---

Sir/Madam,

{{ body }}

---

Please take notice that unless the demands herein are complied with within {{ deadline_days }} days from the receipt of this notice, we shall be constrained to initiate appropriate legal proceedings against you without any further notice to you.

---

**Dated:** {{ date }}

**Yours faithfully,**
(Adv. {{ advocate_name }})
{{ advocate_details }}

---

*This is a computer-generated draft notice. The advocate must verify all facts, citations, and legal provisions before service.*
"""


class DocumentGenerator:
    def __init__(self):
        self.base_template = NoticeTemplate(BASE_NOTICE_SKELETON)

    def generate_notice(
        self,
        notice_type: str,
        advocate_name: str,
        advocate_details: str,
        client_name: str,
        client_address: str,
        recipient_name: str,
        recipient_address: str,
        subject: str,
        body: str,
        deadline_days: int = 15,
        date: str = "",
    ) -> str:
        from datetime import date as date_mod

        return self.base_template.render(
            notice_type=notice_type,
            advocate_name=advocate_name,
            advocate_details=advocate_details,
            client_name=client_name,
            client_address=client_address,
            recipient_name=recipient_name,
            recipient_address=recipient_address,
            subject=subject,
            body=body,
            deadline_days=deadline_days,
            date=date or date_mod.today().isoformat(),
        )
