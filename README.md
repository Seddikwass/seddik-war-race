# SEDDIK WAR RACE — Projet de livraison (web + Android)

Jeu 3D de course-combat, 20 missions en 5 actes, 4 circuits, 6 véhicules, 2 fins.
Moteur : Three.js r128 (WebGL). Emballage Android : Capacitor 7.

## Contenu du dossier

| Élément | Rôle |
|---|---|
| `src/index.html` | Le jeu complet (source unique) |
| `scripts/build.js` | Construit `www/` : Three.js et polices en local, pour jouer hors ligne |
| `scripts/android-patch.js` | Force le mode paysage, le plein écran et l'écran allumé dans l'APK |
| `assets/` | Icône et écran de démarrage (générés automatiquement en toutes tailles) |
| `capacitor.config.json` | Identifiant de l'app : `com.seddik.warrace` |
| `.github/workflows/android.yml` | Compile l'APK automatiquement sur GitHub |
| `render.yaml` | Mise en ligne de la version web sur Render |

---

## Option A — Obtenir l'APK sans Android Studio (recommandé)

GitHub compile l'APK pour toi, gratuitement.

1. Crée un dépôt **privé** sur GitHub, par exemple `seddik-war-race`.
2. Envoie tout le contenu de ce dossier dans le dépôt, **y compris le dossier caché `.github`**.
   Le plus simple, si Git est installé sur ton PC :
   ```bash
   cd seddik-war-race
   git init
   git add .
   git commit -m "SEDDIK WAR RACE v1.0"
   git branch -M main
   git remote add origin https://github.com/TON-COMPTE/seddik-war-race.git
   git push -u origin main
   ```
3. Sur GitHub, ouvre l'onglet **Actions**. La tâche « APK Android » démarre seule (environ 5 à 8 minutes).
4. Quand elle est verte, clique dessus, puis télécharge **seddik-war-race-apk** en bas de la page.
5. Dézippe : tu obtiens `app-debug.apk`. Envoie-le sur ton téléphone, ouvre-le et autorise l'installation depuis cette source.

Si la tâche est rouge, ouvre l'étape en erreur et envoie-moi le message : je corrige.

## Option B — Compiler sur ton PC avec Android Studio

Prérequis : [Node.js 22](https://nodejs.org) et [Android Studio](https://developer.android.com/studio) (avec un SDK Android installé).

```bash
cd seddik-war-race
npm install
npm run android:init     # crée le projet Android, l'icône et le mode paysage
npm run android:open     # ouvre Android Studio
```
Dans Android Studio : **Build › Build Bundle(s) / APK(s) › Build APK(s)**.
Ou branche ton téléphone en USB (débogage USB activé) et clique sur ▶ Run.

Après une modification du jeu (`src/index.html`) : `npm run android:sync`, puis relance.

## Option C — Version web sur Render

1. Le dépôt GitHub de l'option A suffit.
2. Sur [dashboard.render.com](https://dashboard.render.com) : **New › Blueprint**, choisis le dépôt. Render lit `render.yaml`.
   (Ou **New › Static Site** avec : Build Command `npm install && npm run build`, Publish Directory `www`.)
3. Le jeu est en ligne à une adresse du type `https://seddik-war-race.onrender.com`. Il se met à jour à chaque `git push`.

Pour tester en local : `npm install && npm run build && npm run serve`, puis ouvre http://localhost:8080.

---

## Checklist de test sur téléphone réel

Active **Paramètres › Afficher les FPS** pendant les tests.

- [ ] La voiture tourne immédiatement quand on appuie sur ◀ ou ▶, et tourne tant qu'on garde le doigt dessus.
- [ ] GAZ, FREIN, DRIFT, NITRO, EMP et CAM répondent, y compris à plusieurs doigts en même temps.
- [ ] Le mode gaucher inverse bien les deux groupes de boutons.
- [ ] Aucune voiture ne traverse les murs, et l'IA ne reste jamais bloquée.
- [ ] Chaque mission se termine, donne ses crédits et débloque la suivante.
- [ ] La progression est conservée après fermeture complète de l'app.
- [ ] Le bouton retour Android met la course en pause.
- [ ] Les circuits de nuit, la pluie et le tunnel (mission 11) restent lisibles.
- [ ] Au moins 30 FPS en course. Sinon, le jeu baisse sa qualité tout seul (à désactiver dans les paramètres si besoin).
- [ ] Il n'y a pas de menu bloqué, et le son se coupe quand l'app passe en arrière-plan.

Note tes FPS, ton modèle de téléphone et tout bug visuel (avec une capture) : c'est la base de la phase d'optimisation.

## Publication sur Google Play (plus tard)

1. Compte développeur Google Play (frais d'inscription unique).
2. Dans Android Studio : **Build › Generate Signed Bundle / APK › Android App Bundle**. Crée une clé de signature et **garde-la précieusement** : sans elle, impossible de publier des mises à jour.
3. Fiche du jeu : description, captures, icône 512 px (à partir de `assets/icon-only.png`), politique de confidentialité (le jeu ne collecte aucune donnée ; la progression reste sur l'appareil).
4. Questionnaire de classification : violence stylisée entre véhicules, aucun sang, aucun achat.
5. Vérifie le niveau d'API cible exigé par Google Play au moment de la publication. Capacitor 7 cible une version récente, mais les exigences changent chaque année.

## Ce qui reste à faire

- Tests et réglages sur des téléphones réels (performances, taille des boutons, difficulté).
- Musique originale (aujourd'hui : sons de moteur, impacts et alertes générés par le code).
- Éventuellement : publicité récompensée facultative, sans paiement pour gagner (voir le cahier des charges §17).
