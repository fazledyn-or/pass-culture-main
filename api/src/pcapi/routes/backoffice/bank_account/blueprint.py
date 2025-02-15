from datetime import datetime

from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from markupsafe import Markup
import sqlalchemy as sa
from werkzeug.exceptions import NotFound

from pcapi.connectors.dms import api as dms_api
from pcapi.core.finance import models as finance_models
from pcapi.core.history import api as history_api
from pcapi.core.history import models as history_models
from pcapi.core.offerers import models as offerers_models
from pcapi.core.permissions import models as perm_models
from pcapi.core.users import models as users_models
from pcapi.repository import repository
from pcapi.routes.backoffice import utils
from pcapi.routes.backoffice.forms import search as search_forms
from pcapi.routes.backoffice.forms.search import TypeOptions
from pcapi.utils.human_ids import humanize

from . import forms


bank_blueprint = utils.child_backoffice_blueprint(
    "bank_account",
    __name__,
    url_prefix="/pro/bank-account",
    permission=perm_models.Permissions.READ_PRO_ENTITY,
)


def render_bank_account_details(
    bank_account: finance_models.BankAccount, edit_form: forms.EditBankAccountForm | None = None
) -> str:
    if not edit_form and utils.has_current_user_permission(perm_models.Permissions.MANAGE_PRO_ENTITY):
        edit_form = forms.EditBankAccountForm(label=bank_account.label)

    return render_template(
        "bank_account/get.html",
        search_form=search_forms.CompactProSearchForm(q=request.args.get("q"), pro_type=TypeOptions.BANK_ACCOUNT.name),
        search_dst=url_for("backoffice_web.search_pro"),
        bank_account=bank_account,
        humanized_bank_account_id=humanize(bank_account.id),
        dms_stats=dms_api.get_dms_stats(bank_account.dsApplicationId),
        active_tab=request.args.get("active_tab", "linked_venues"),
        edit_form=edit_form,
    )


@bank_blueprint.route("/<int:bank_account_id>", methods=["GET"])
def get(bank_account_id: int) -> utils.BackofficeResponse:
    bank_account = (
        finance_models.BankAccount.query.filter(finance_models.BankAccount.id == bank_account_id)
        .options(
            sa.orm.joinedload(finance_models.BankAccount.offerer),
        )
        .one_or_none()
    )
    if not bank_account:
        raise NotFound()

    return render_bank_account_details(bank_account)


@bank_blueprint.route("/<int:bank_account_id>/linked_venues", methods=["GET"])
def get_linked_venues(bank_account_id: int) -> utils.BackofficeResponse:
    linked_venues = (
        offerers_models.VenueBankAccountLink.query.filter(
            offerers_models.VenueBankAccountLink.bankAccountId == bank_account_id,
            offerers_models.VenueBankAccountLink.timespan.contains(datetime.utcnow()),
        ).options(
            sa.orm.joinedload(offerers_models.VenueBankAccountLink.venue).load_only(
                offerers_models.Venue.id,
                offerers_models.Venue.name,
                offerers_models.Venue.publicName,
                offerers_models.Venue.isVirtual,
                offerers_models.Venue.managingOffererId,
            )
        )
    ).all()

    return render_template(
        "bank_account/get/linked_venues.html", linked_venues=linked_venues, bank_account_id=bank_account_id
    )


@bank_blueprint.route("/<int:bank_account_id>/history", methods=["GET"])
def get_history(bank_account_id: int) -> utils.BackofficeResponse:
    actions_history = (
        history_models.ActionHistory.query.filter_by(bankAccountId=bank_account_id)
        .order_by(history_models.ActionHistory.actionDate.desc())
        .options(
            sa.orm.joinedload(history_models.ActionHistory.authorUser).load_only(
                users_models.User.id, users_models.User.firstName, users_models.User.lastName
            ),
        )
        .all()
    )

    return render_template(
        "bank_account/get/history.html",
        actions=actions_history,
    )


@bank_blueprint.route("/<int:bank_account_id>", methods=["POST"])
@utils.permission_required(perm_models.Permissions.MANAGE_PRO_ENTITY)
def update_bank_account(bank_account_id: int) -> utils.BackofficeResponse:
    bank_account = finance_models.BankAccount.query.get_or_404(bank_account_id)

    form = forms.EditBankAccountForm()
    if not form.validate():
        msg = Markup(
            """
            <button type="button"
                    class="btn"
                    data-bs-toggle="modal"
                    data-bs-target="#edit-bank-account-modal">
                Les données envoyées comportent des erreurs. Afficher
            </button>
            """
        ).format()
        flash(msg, "warning")
        return render_bank_account_details(bank_account, edit_form=form), 400

    if bank_account.label != form.label.data:
        action = history_api.log_action(
            history_models.ActionType.INFO_MODIFIED,
            current_user,
            bank_account=bank_account,
            modified_info={"label": {"old_info": bank_account.label, "new_info": form.label.data}},
        )
        bank_account.label = form.label.data
        repository.save(bank_account, action)
        flash("Les informations ont bien été mises à jour", "success")

    return redirect(url_for("backoffice_web.bank_account.get", bank_account_id=bank_account_id), code=303)
