# 🤖 Slack KI-Wissensassistent mit Confluence-Integration und Anthropic LLM

Ein semantischer Chatbot, der in Slack integriert ist und Teamfragen mit Hilfe von Confluence-Dokumenten und einem leistungsstarken LLM (Claude von Anthropic) beantwortet.

## 🔍 Ziel

Hilf Slack-Nutzern, auf einfache Weise auf internes Wissen zuzugreifen – direkt im Chat, intelligent und kontextbasiert.

---

## 🧱 Architektur

```text
Slack ↔ FastAPI ↔ Vektor-Datenbank (FAISS/Qdrant)
                    ↕️                     
          Confluence API  →  Embedding Service
                    ↕️                     
                  Claude (Anthropic LLM)
```

---

## 🚀 Features

- 🔗 Integration mit Slack (Slash-Command `/askai`)
- 📘 Crawling von Confluence-Seiten über die API
- 🧠 Semantische Suche durch Vektor-Datenbank
- 💬 Formulierung präziser Antworten mit Claude
- 🛠 Erweiterbar, z. B. durch Feedback oder Rechteprüfung

---

## ⚙️ Technologie-Stack

| Bereich             | Tool/Technologie                   |
|---------------------|------------------------------------|
| Embeddings          | `sentence-transformers`            |
| Vektor-Datenbank    | FAISS oder Qdrant                  |
| Backend/API         | FastAPI                            |
| Slack SDK           | `slack_bolt` (Python)              |
| LLM API             | Claude (Anthropic)                 |

---

## 📦 Installation (lokal)

```bash
git clone <repo-url>
cd <projektordner>
pip install -r requirements.txt
# .env Datei mit API-Zugängen anlegen
uvicorn main:app --reload
```

---

## 📄 Projektstruktur

```text
.
├── main.py                # FastAPI Backend
├── confluence_crawler.py # API-Zugriff auf Confluence
├── vector_store.py       # Embedding + FAISS Logik
├── slack_handler.py      # Slack-Eingabe & Routing
├── llm_service.py        # Claude-Kommunikation
├── requirements.txt
├── README.md
└── .env                  # Enthält API Keys und Tokens
```

---

## 🧪 Beispiel

```bash
/askai Wie aktualisiere ich mein Passwort?
→ Antwort mit Kontext aus Confluence + natürlicher Formulierung
```

---

## 📌 Nächste Schritte

- [ ] Confluence API Integration
- [ ] Vektorspeicherung & Embedding
- [ ] Slack Routing & Claude-Antwort
- [ ] Deployment (Docker, ggf. AWS/GCP)

---

## 📬 Kontakt

Projektleitung: [Vladislav Sabolotny](mailto:vlad@example.com)

---

## 📝 Lizenz

MIT License – feel free to use, contribute, and improve!

---

## Image bauen
docker build -t faiss-example .

## Container ausführen
docker run --rm faiss-example

---

## Ressoursen

Admin panel atlassian https://admin.atlassian.com/

## Datenbank Qdrant

Dashboard: http://localhost:6333/dashboard#/collections 