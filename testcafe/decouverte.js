import { Selector } from 'testcafe'

import BROWSER_ROOT_URL from './helpers/config'
import regularUser from './helpers/roles'

  const nextButton  = Selector('button.button.after')
  const showVerso  = Selector('button.button.to-recto')
  const versoDiv  = Selector('div.verso')
  const clueDiv  = Selector('div.clue')
  const closeButton  = Selector('.close-button')
  const spanPrice  = Selector('.price')
  const draggableImage = Selector('.react-draggable')

fixture `Découverte | Je ne suis pas connecté·e`
.page `${BROWSER_ROOT_URL+'decouverte'}`

  test("Je suis redirigé vers la page /connexion", async t =>
  {
    await t
    const location = await t.eval(() => window.location)
    await t.expect(location.pathname).eql('/connexion')
  })

fixture `Découverte | Après connexion | Les offres sont en cours de chargement`

     .beforeEach( async t => {
       await t
       .useRole(regularUser)
    })

    test("Je suis informé·e du fait que les offres sont en cours de chargement", async t => {
      await t
      .expect(Selector('.loading').innerText).eql('\nchargement des offres\n')
    })

    test("Je suis redirigé·e vers la première page de tutoriel /decouverte/tuto/AE", async t =>
    {
      await t
      // test instable, reste par moment sur decouverte... Voir si location ne garderait pas la valeur du précédant test...
      const location = await t.eval(() => window.location)
      await t.expect(location.pathname).eql('/decouverte/tuto/AE')
    })

    test('Lorsque je clique sur la flêche suivante, je vois la page suivante du tutoriel', async t => {
      await t
      .click(nextButton)
      .wait(1000)
      const location = await t.eval(() => window.location)
      await t.expect(location.pathname).eql('/decouverte/tuto/A9')
    })

    test('Lorsque je clique sur la flêche vers le haut, je vois le verso de la recommendation et je peux la fermer', async t => {
      await t
      .navigateTo(BROWSER_ROOT_URL+'decouverte/tuto/A9')
      .wait(1000)
      await t.expect(clueDiv.visible).ok()
      .click(showVerso)
      .wait(1000)
      .expect(versoDiv.hasClass('flipped')).ok()
      .click(closeButton)
      .expect(versoDiv.hasClass('flipped')).notOk()
    })

fixture `Découverte | Après connexion | Recommandations`
    .beforeEach( async t => {
    await t
    .useRole(regularUser)
    .navigateTo(BROWSER_ROOT_URL+'decouverte/AH7Q/AU#AM')
  })

  test.skip("Je vois les informations de l'accroche du recto", async t => {
    await t
    // TODO
  })

  test("Je vois le verso des cartes lorsque je fais glisser la carte vers le haut", async t => {
    await t
    .navigateTo(BROWSER_ROOT_URL+'decouverte/AH7Q/AU')
    .wait(500)
    .click(showVerso)
    .wait(500)
    await t.expect(versoDiv.find('h1').innerText).eql('Vhils')
    await t.expect(versoDiv.find('h2').innerText).eql('LE CENTQUATRE-PARIS')
    // TODO
  })

// TODO tester le drag des images https://devexpress.github.io/testcafe/documentation/test-api/actions/drag-element.html
