from typing import Iterable

from pcapi.tasks.serialization import sendinblue_tasks

from .. import models


class BaseBackend:
    def send_mail(
        self,
        recipients: Iterable,
        data: models.TransactionalEmailData | models.TransactionalWithoutTemplateEmailData,
        bcc_recipients: Iterable[str] = (),
    ) -> models.MailResult:
        raise NotImplementedError()

    def create_contact(self, payload: sendinblue_tasks.UpdateSendinblueContactRequest) -> None:
        raise NotImplementedError()

    def delete_contact(self, contact_email: str) -> None:
        raise NotImplementedError()
