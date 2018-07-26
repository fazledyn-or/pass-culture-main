import { Selector } from 'testcafe'
import { ROOT_PATH } from '../src/utils/config'

import { regularOfferer } from './helpers/roles'

const navbarLink = Selector('a.navbar-link')
const offerersNavbarLink = Selector("a.navbar-item[href='/structures']")
const offererButton  = Selector("a[href^='/structures/']").withText('THEATRE NATIONAL DE CHAILLOT')
const newVenueButton  = Selector("a.button.is-secondary").withText("+ Ajouter un lieu")

const siretInput = Selector('#venue-siret')
const nameInput = Selector("#venue-name")
const adressInput = Selector("#venue-address")
const postalCodeInput = Selector("#venue-postalCode")
const cityInput = Selector("#venue-city")
const latitudeInput = Selector("#venue-latitude")
const longitudeInput = Selector("#venue-longitude")
const submitButton  = Selector('button.button.is-primary') //créer un lieu
const updateButton  = Selector('a.button.is-secondary') //modifier un lieu
const notificationError  = Selector('.notification.is-danger')
const notificationSuccess  = Selector('.notification.is-success')
const siretInputError  = Selector('#venue-siret-error')
const closeButton  = Selector('button.close').withText('OK')
const backButton  = Selector('a.back-button')
const venueName  = Selector('.list-content p.name')

fixture `05_01 VenuePage | Créer un nouveau lieu avec succès`
test("Je rentre une nouveau lieu via son siret avec succès", async t => {
  await t
  .useRole(regularOfferer)
  // le userRole a l'option preserveUrl: true donc le test commence sur la page /offres

  // navigation
  await t
    .click(navbarLink)
    .click(offerersNavbarLink)
    .click(offererButton)
    .wait(500)
    .click(newVenueButton)
  // input
  await t
    .typeText(siretInput, '69203951400017')
    .wait(1000)

  // check other completed fields
  await t.expect(nameInput.value).eql("THEATRE NATIONAL DE CHAILLOT")
  await t.expect(adressInput.value).eql("1 PL TROCADERO ET DU 11 NOVEMBRE")
  await t.expect(postalCodeInput.value).eql("75116")
  await t.expect(cityInput.value).eql("PARIS 16")
  await t.expect(latitudeInput.value).eql("48.862923")
  await t.expect(longitudeInput.value).eql("2.287896")

  // create venue
  await t
    .click(submitButton)
    const location = await t.eval(() => window.location)
    await t.expect(location.pathname).eql('/structures/AE/lieux/AE')
    .expect(notificationSuccess.innerText).eql('Lieu ajouté avec succès !OK')

    // close notification div
    await t
    .click(closeButton)
    .expect(notificationError.exists).notOk()

})

fixture `05_02 VenuePage | Je ne peux pas créer de lieu, j'ai des erreurs`

.beforeEach( async t => {
  await t
  .useRole(regularOfferer)

  // navigation
  await t
    .click(navbarLink)
    .click(offerersNavbarLink)
    .click(offererButton)
    .wait(500)
    .click(newVenueButton)
})

test("Le code SIRET doit correspondre à un établissement de votre structure", async t => {

  // input
  await t
    .typeText(siretInput, '69203951400017')
    .wait(1000)

  // create venue
  await t
    .click(submitButton)
    // .wait(1000)

  // error response
  await t
    .expect(siretInputError.innerText).eql('\nUne entrée avec cet identifiant existe déjà dans notre base de données\n')
    .expect(notificationError.innerText).eql('Formulaire non validéOK')

  // close notification div
  await t
    .click(closeButton)
    .expect(notificationError.exists).notOk()
})

test("Le code SIRET doit correspondre à un établissement de votre structure", async t => {

  // input
  await t
    .typeText(siretInput, '492475033 00022')
    .wait(1000)

  // create venue
  await t
    .click(submitButton)
    .wait(1000)

  // error response
  await t
    .expect(siretInputError.innerText).eql('\nLe code SIRET doit correspondre à un établissement de votre structure\n')
    .expect(notificationError.innerText).eql('Formulaire non validéOK')

})

test("Le siret n'est pas valide", async t => {
  // TODO
})


fixture `05_03 VenuePage |  Component | Je suis sur la page de détail du lieu`
  .beforeEach( async t => {
    await t
      .useRole(regularOfferer)
      .navigateTo(ROOT_PATH+'structures/AE/lieux/AE')
    })

test("Je vois les détails du lieu", async t => {

  // Navigate to offerer Detail page and found venue added
  await t
  .click(backButton)
  const location = await t.eval(() => window.location)
  await t.expect(location.pathname).eql('/structures/AE')
  .expect(venueName.innerText).eql('THEATRE NATIONAL DE CHAILLOT')

})

test("Je peux modifier le lieu", async t => {
  // Submit button should disapear
  // update
  await t
    .click(updateButton)
})
