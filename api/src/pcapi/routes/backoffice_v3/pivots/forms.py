from flask import flash
from flask_wtf import FlaskForm
import wtforms

import pcapi.core.providers.repository as providers_repository

from ..forms import fields


class SearchPivotForm(FlaskForm):
    class Meta:
        csrf = False

    q = fields.PCOptSearchField("ID ou nom de lieu, identifiant cinéma")


class EditPivotForm(FlaskForm):
    venue_id = fields.PCTomSelectField(
        "Lieu", choices=[], validate_choice=False, endpoint="backoffice_v3_web.autocomplete_venues", coerce=int
    )


class EditAllocineForm(EditPivotForm):
    theater_id = fields.PCStringField(
        "Identifiant cinéma (Allociné)",
        validators=(
            wtforms.validators.InputRequired("Information obligatoire"),
            wtforms.validators.Length(min=1, max=20, message="Doit contenir au maximum %(max)d caractères"),
        ),
    )
    internal_id = fields.PCStringField("Identifiant interne Allociné")


class EditBoostForm(EditPivotForm):
    cinema_id = fields.PCStringField("Identifiant Cinéma (Boost)")
    username = fields.PCStringField("Nom de l'utilisateur (Boost)")
    password = fields.PCPasswordField("Mot de passe (Boost)")
    cinema_url = fields.PCStringField(
        "URL du cinéma (Boost)",
        validators=(
            wtforms.validators.InputRequired("Information obligatoire"),
            wtforms.validators.URL("Doit avoir la forme d'une URL"),
        ),
    )

    def validate(self, extra_validators=None) -> bool:  # type: ignore [no-untyped-def]
        # do not use this custom validation on DeleteForm
        if not isinstance(self, EditBoostForm):
            return super().validate(extra_validators)

        boost_provider = providers_repository.get_provider_by_local_class("BoostStocks")
        pivot = providers_repository.get_pivot_for_id_at_provider(
            id_at_provider=self.cinema_id.data, provider_id=boost_provider.id
        )
        if pivot and pivot.venueId != self.venue_id.data[0]:
            flash("Cet identifiant cinéma existe déjà pour un autre lieu", "danger")
            return False

        return super().validate(extra_validators)


class EditCGRForm(EditPivotForm):
    cinema_id = fields.PCStringField("Identifiant Cinéma (CGR)")
    cinema_url = fields.PCStringField(
        "URL du cinéma (CGR)",
        validators=(
            wtforms.validators.InputRequired("Information obligatoire"),
            wtforms.validators.URL("Doit avoir la forme d'une URL"),
        ),
    )
    password = fields.PCPasswordField("Mot de passe (CGR)")

    def validate(self, extra_validators=None) -> bool:  # type: ignore [no-untyped-def]
        # do not use this custom validation on DeleteForm
        if not isinstance(self, EditCGRForm):
            return super().validate(extra_validators)

        cgr_provider = providers_repository.get_provider_by_local_class("CGRStocks")
        pivot = providers_repository.get_pivot_for_id_at_provider(
            id_at_provider=self.cinema_id.data, provider_id=cgr_provider.id
        )
        if pivot and pivot.venueId != self.venue_id.data[0]:
            flash("Cet identifiant cinéma existe déjà pour un autre lieu", "danger")
            return False

        return super().validate(extra_validators)


class EditCineOfficeForm(EditPivotForm):
    cinema_id = fields.PCStringField("Identifiant cinéma (CDS)")
    account_id = fields.PCStringField("Nom de compte (CDS)")
    api_token = fields.PCStringField("Clé API (CDS)")

    def validate(self, extra_validators=None) -> bool:  # type: ignore [no-untyped-def]
        # do not use this custom validation on DeleteForm
        if not isinstance(self, EditCineOfficeForm):
            return super().validate(extra_validators)

        cds_provider = providers_repository.get_provider_by_local_class("CDSStocks")
        pivot = providers_repository.get_pivot_for_id_at_provider(
            id_at_provider=self.cinema_id.data, provider_id=cds_provider.id
        )
        if pivot and pivot.venueId != self.venue_id.data[0]:
            flash("Cet identifiant cinéma existe déjà pour un autre lieu", "danger")
            return False

        return super().validate(extra_validators)
