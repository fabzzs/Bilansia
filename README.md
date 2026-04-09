# Bilansia
Outil Analyse Financière assisté par IA 
---
### 👨‍💻 Auteur
**Fabrice Donisa**

**⬡ Bilansia**
Plateforme d'Audit Forensic & d'Analyse Financière assistée par IA

Bilansia est une application décisionnelle conçue pour les professionnels du chiffre, les Administrateurs et les Mandataires Judiciaires. Elle automatise le diagnostic financier et la détection d'anomalies comptables grâce à l'intelligence artificielle.

**🚀 Fonctionnalités Clés**
Analyse de Données Multi-sources : Import automatique de Fichiers des Écritures Comptables (FEC) et de liasses fiscales au format PDF.

Moteur Forensic Déterministe : Détection d'anomalies critiques (mouvements de caisse atypiques, stocks morts, décalages de TVA, passif fiscal alarmant).

IA ARIS (Audit Risk Intelligence System) : Assistant intelligent basé sur Google Gemini pour interroger les données en langage naturel et évaluer le risque de cessation des paiements.

Reporting Automatisé : Génération de rapports d'audit détaillés au format PDF prêts pour l'exploitation judiciaire.

**🛠️ Stack Technique**
Langage : Python

Interface : Streamlit

Analyse de données : Pandas, Numpy, Scipy

Visualisation : Plotly (Graphiques interactifs)

Intelligence Artificielle : Google Gemini API (LLM)

**📦 Installation & Utilisation**
Cloner le projet

Installer les dépendances : pip install -r requirements.txt

Lancer l'application : streamlit run scanner_gestion.py

**🧪 Test de l'application**

Vous pouvez tester la puissance d'analyse de Bilansia de trois manières différentes :

**Avec vos propres données :** Importez n'importe quel FEC (Fichier des Écritures Comptables) au format .csv / .txt ou une liasse fiscale (Bilan/Compte de Résultat) au format .pdf.

**Via le fichier de démonstration :** Pour une prise en main rapide, un fichier de test nommé **Fec_test_demo.txt** est disponible à la racine de ce repository. Téléchargez-le et glissez-le dans l'interface pour voir les alertes s'activer.

**Interrogation IA (ARIS) :** Une fois les données chargées, rendez-vous dans l'onglet Assistant IA pour poser des questions complexes (ex: "Analyse la solvabilité à court terme" ou "Y a-t-il des anomalies dans les écritures de caisse ?").

**Ce qu'il faut observer lors du test :**

🚩 Les Alertes Actives : Le compteur rouge en haut à droite s'incrémente automatiquement selon la gravité des anomalies détectées.

📊 La Cohérence des Scores : Les KPI s'ajustent en temps réel pour refléter la santé financière (Marge, BFR, Seuil de rentabilité).

🤖 La pertinence d'ARIS : L'IA ne se contente pas de lire les chiffres, elle interprète les cycles d'exploitation pour vous aider dans votre diagnostic.


N'hésitez pas à me contacter pour discuter de ce projet ou d'opportunités de collaboration :
- [LinkedIn] https://www.linkedin.com/in/fabrice-donisa-443555112
- [Email]fdbrice@yahoo.fr
