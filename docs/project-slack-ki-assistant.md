# Projekt: Slack KI-Wissensassistent mit Confluence-Integration und Anthropic LLM

## Ziel
Ein semantischer Chatbot, der in Slack integriert ist und Antworten auf Teamfragen basierend auf dem Wissen aus Confluence-Dokumenten liefert. Die Antworten werden von einem Large Language Model (LLM) von Anthropic (Claude) generiert.

---

## Komponenten

| Komponente            | Aufgabe                                                                 |
|-----------------------|------------------------------------------------------------------------|
| **Slack App**         | Empfängt Nutzeranfragen                                                |
| **Confluence Crawler**| Holt Seiteninhalte über die API                                       |
| **Embedding Service** | Wandelt Inhalte in numerische Vektoren um (mittels sentence-transformers) |
| **Vektor-Datenbank**  | Speichert und indexiert Embeddings (z. B. FAISS oder Qdrant)           |
| **LLM (Anthropic)**   | Generiert auf Basis der Treffer eine natürliche Antwort                |
| **Backend (FastAPI)** | Bindeglied zwischen Slack, Vektorsuche und LLM                         |

---

## Architekturüberblick

```text
Slack ↔ FastAPI ↔ Vektor-Datenbank (FAISS/Qdrant)
                    ↕️                     
          Confluence API  →  Embedding Service
                    ↕️                     
                  Claude (Anthropic LLM)
```

---

## Projekt-Meilensteine

### 1. Confluence API Zugriff
- [ ] API-Zugang (Token) einrichten
- [ ] Spaces oder Labels zum Crawlen definieren
- [ ] Seiteninhalte + Metadaten abrufen und speichern

### 2. Embedding & Vektorspeicherung
- [ ] Texte in Chunks (z. B. 512 Tokens) teilen
- [ ] Mit `sentence-transformers` Embeddings erzeugen
- [ ] In FAISS oder Qdrant speichern (inkl. Metadaten wie Titel, URL)

### 3. Slack Integration
- [ ] Slack App registrieren
- [ ] Slash-Command `/askai` oder Message-Shortcut definieren
- [ ] Verbindung zum Backend herstellen

### 4. LLM-Antwort-Logik
- [ ] Semantisch passende Chunks via Vektorsuche finden
- [ ] Kontext + Frage als Prompt an Claude senden
- [ ] Formulierte Antwort an Slack zurücksenden

---

## Tool-Stack

| Bereich             | Tool                                                                      |
|---------------------|---------------------------------------------------------------------------|
| Embeddings          | `sentence-transformers` oder Claude Embeddings                            |
| Vektor-Datenbank    | FAISS (lokal) oder Qdrant (Cloud/Metadata-Support)                        |
| Backend/API         | FastAPI                                                                   |
| Slack SDK           | `slack_bolt` (Python)                                                     |
| LLM API             | Anthropic Claude (z. B. `claude-3-opus` oder `claude-3-sonnet`)           |

---

## Erweiterungen (optional)
- [ ] Periodisches Re-Indexing bei neuen Confluence-Seiten
- [ ] Zugriffsrechte (nur Inhalte, die der Slack-Nutzer auch in Confluence sehen darf)
- [ ] Feedback-Funktion zur Qualität der Antwort
- [ ] Logging und Analyse der meistgestellten Fragen

---

## Nächster Schritt
Beginn mit dem Modul **Confluence Crawling + Embedding & Speicherung**. Ein entsprechendes Python-Skript wird vorbereitet.