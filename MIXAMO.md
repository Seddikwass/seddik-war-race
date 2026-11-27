# Ajouter des personnages Mixamo à SEDDIK WAR RACE

Le jeu a déjà des personnages 3D faits par le code (Maya, Coach, le commissaire au drapeau).
S'il trouve des modèles Mixamo, il les utilise automatiquement à leur place, avec leur animation.

Mixamo est gratuit avec un compte Adobe. Ses personnages et animations peuvent être utilisés dans un jeu, même commercial, tant qu'ils restent intégrés au jeu (on ne les revend pas et on ne les partage pas en fichiers séparés).

## 1. Télécharger les 3 personnages

Sur **mixamo.com** : onglet **Characters**, choisis un personnage, puis onglet **Animations**, choisis l'animation, puis **Download**.

| Rôle dans le jeu | Idée de personnage Mixamo | Animation à chercher | Nom du fichier |
|---|---|---|---|
| Maya, la mécanicienne (garage) | une femme en tenue de travail | « Idle » ou « Kneeling » | `maya.fbx` |
| Coach Trabelsi (garage) | un homme d'âge mûr | « Standing Arms Crossed » ou « Idle » | `coach.fbx` |
| Commissaire de course (ligne de départ) | n'importe quel personnage | « Waving » | `marshal.fbx` |

Réglages de téléchargement :
- **Format** : FBX Binary (.fbx)
- **Skin** : **With Skin**
- **Frames per second** : 30
- **Keyframe Reduction** : uniform (fichier plus léger)

Conseil : évite les personnages à l'allure de héros connus. Tu peux aussi envoyer ton propre personnage dans Mixamo (bouton « Upload Character ») pour qu'il soit animé automatiquement.

## 2. Les mettre dans le projet

1. Copie les fichiers dans le dossier `assets/models/` du dépôt.
2. Dans ce même dossier, renomme `manifest.example.json` en `manifest.json`. Il contient déjà les trois rôles :
   ```json
   {
     "characters": {
       "maya":    { "file": "maya.fbx" },
       "coach":   { "file": "coach.fbx" },
       "marshal": { "file": "marshal.fbx" }
     }
   }
   ```
   Tu peux retirer une ligne si tu n'as pas ce personnage. Ajoute `"scale": 0.012` si un personnage paraît trop petit ou trop grand (la valeur par défaut est 0.01 pour les FBX).
3. Envoie sur GitHub (ou dépose les fichiers dans la conversation et Claude s'en charge).
   L'APK et la version web les incluront automatiquement.

## 3. Poids et performance

- Un personnage Mixamo pèse en général de 2 à 10 Mo en FBX. Reste sous 3 personnages pour garder un chargement rapide sur téléphone.
- Pour alléger : ouvre le FBX dans Blender (gratuit), puis **File › Export › glTF 2.0 (.glb)** avec compression. Le jeu lit aussi les `.glb` (mets `"file": "maya.glb"`).

Pense à noter chaque personnage dans `CREDITS.md`.
