# Equation Prepaid Backend

Ce projet est le backend de l'application **Equation Prepaid**.

## Prérequis

Avant d'installer et d'exécuter l'application, assurez-vous que les éléments suivants sont installés :

- **Python** >= 3.13
- **Poetry** pour la gestion des dépendances et des environnements virtuels.
- **pyenv** pour gérer différentes versions de Python (optionnel mais recommandé).

### Installation de Poetry

Suivez les instructions sur la [documentation officielle de Poetry](https://python-poetry.org/docs/) pour installer Poetry sur votre machine.

### Installation de pyenv

Si vous n'avez pas `pyenv` installé, vous pouvez le faire en suivant les étapes sur la [documentation de pyenv](https://github.com/pyenv/pyenv).

Pour installer une version spécifique de Python (par exemple, 3.13.0) avec pyenv, exécutez :

```bash
pyenv install 3.13.0
pyenv global 3.13.0
```

Cela configure `pyenv` pour utiliser Python 3.13.0 dans ce projet.

## Installation des dépendances

Une fois que vous avez installé Poetry et configuré Python, vous pouvez installer les dépendances du projet avec la commande suivante :

```bash
poetry install
```

Cela installera toutes les dépendances définies dans le fichier `pyproject.toml`.

## Lancer l'application

### Mode Développement

Pour exécuter l'application en mode développement, en utilisant le rechargement automatique des modifications, lancez :

```bash
poetry run fastapi dev src/main.py
```

Cela démarrera l'application avec un serveur de développement qui se met à jour automatiquement lorsque des modifications sont apportées.

### Mode Production

Pour exécuter l'application en mode production, lancez le serveur FastAPI dans une configuration optimisée pour la production :

```bash
poetry run fastapi run src/main.py
```

Cela démarre l'application en mode production. Il est recommandé de configurer un serveur HTTP comme **Uvicorn** ou **Gunicorn** pour gérer le trafic en production.

## Documentation de l'API

La documentation interactive de l'API est disponible à l'adresse suivante une fois l'application lancée :

```
http://localhost:8000/docs
```

Cette page permet de tester facilement les endpoints de l'API via une interface utilisateur graphique.

## Tests

Si des tests sont définis pour l'application, vous pouvez les exécuter avec :

```bash
poetry run pytest
```

Assurez-vous d'abord que toutes les dépendances nécessaires pour les tests sont installées (si elles sont dans un bloc `dev` dans `pyproject.toml`).

## Pre-commit Hooks

Ce projet utilise **pre-commit** pour maintenir la qualité du code. Les hooks suivants sont configurés et s'exécutent automatiquement avant chaque commit :

### Installation de pre-commit

Pour installer pre-commit et configurer les hooks :

```bash
poetry run pre-commit install
```

### Hooks configurés

#### 1. Hooks de base (pre-commit-hooks)
- **check-added-large-files** : Vérifie qu'aucun fichier volumineux n'est ajouté au repository
- **check-toml** : Valide la syntaxe des fichiers TOML
- **check-yaml** : Valide la syntaxe des fichiers YAML
- **detect-private-key** : Détecte les clés privées dans le code
- **end-of-file-fixer** : Assure qu'il y a une ligne vide à la fin de chaque fichier
- **requirements-txt-fixer** : Trie les dépendances dans requirements.txt
- **trailing-whitespace** : Supprime les espaces en fin de ligne (exclut les fichiers de test)
- **check-json** : Valide la syntaxe des fichiers JSON
- **name-tests-test** : Vérifie que les fichiers de test suivent la convention de nommage pytest

#### 2. Ruff (Linting et Formatage)
- **ruff** : Linter Python ultra-rapide avec les règles suivantes :
  - `--select=ALL` : Active toutes les règles disponibles
  - Ignore certaines règles spécifiques (RUF100, BLE001, COM812, etc.)
  - Limite de ligne à 100 caractères
  - Correction automatique des erreurs (`--fix`)
- **ruff-format** : Formatage automatique du code Python

#### 3. Pylint
- **pylint** : Analyse statique approfondie du code Python
  - Utilise le fichier de configuration `pylintrc`
  - Exécution parallèle sur plusieurs cœurs (`--jobs=0`)
  - Score minimum requis : 9.0/10 (`--fail-under=9.0`)

#### 4. Bandit
- **bandit** : Scanner de sécurité pour détecter les vulnérabilités communes
  - Configuration via `pyproject.toml`
  - Analyse récursive de tous les fichiers (`-r .`)

### Exécution manuelle

Pour exécuter tous les hooks manuellement :

```bash
poetry run pre-commit run --all-files
```

Pour exécuter un hook spécifique :

```bash
poetry run pre-commit run ruff --all-files
```

## License

Ce projet est sous la licence **MIT License**.

## Auteur

Al Moustapha Doumbia

## Contact

Si vous avez des questions ou des retours, vous pouvez me contacter à l'adresse suivante :

```
almoustapha.doumbia@data354.com
```

## Version

La version actuelle de l'application est **1.0.0**.
