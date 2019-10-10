export class OffererClass {
  constructor(offerer = {}, adminUserOfferer) {
    this.id = offerer.id || ''
    this.siren = offerer.siren || ''
    this.name = offerer.name || ''
    this.address = offerer.address || ''
    this.bic = offerer.bic || ''
    this.iban = offerer.iban || ''
    this.adminUserOfferer = adminUserOfferer
  }

  isIdOrNameDefined = () => !!(this.id || this.name)

  areBankInformationProvided = () => !!(this.bic && this.iban)
}
