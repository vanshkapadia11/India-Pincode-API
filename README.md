---
title: PincodeIQ
emoji: 📮
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
---

# 🇮🇳 PincodeIQ — Indian Pincode API

> Production-ready Indian Pincode REST API with AI-powered address parsing, delivery estimation, bulk lookup, nearby search and more. Built with FastAPI + PostgreSQL + Gemini AI.

![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-336791?style=flat&logo=postgresql)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-4285F4?style=flat&logo=google)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

---

## ✨ Features

- 🔍 **Pincode Lookup** — full post office details for any Indian pincode
- ✅ **Validation** — check if a pincode exists
- 🤖 **AI Address Parser** — extract & correct pincodes from messy addresses using Gemini AI
- 📦 **Delivery Estimator** — smart delivery time prediction powered by AI
- 📦 **Bulk Lookup** — up to 50 pincodes in a single request
- 📍 **Nearby Pincodes** — find all pincodes within a radius (km)
- 📏 **Distance Calculator** — straight-line distance between two pincodes
- 🚚 **Serviceability Check** — is a pincode deliverable?
- 🔤 **Auto Suggest** — prefix search for post offices and districts
- 🔐 **API Key Auth** — secure key-based authentication
- ⚡ **Caching** — in-memory cache for blazing fast repeat lookups
- 🛡️ **Rate Limiting** — per-key rate limits to prevent abuse
- 📊 **Request Logging** — every request logged with response time
- 📖 **Swagger UI** — auto-generated interactive API docs

---

## 🚀 Live Demo

```
Base URL: https://vanshkapig-pincodeiq.hf.space
Docs:     https://vanshkapig-pincodeiq.hf.space/docs
Health:   https://vanshkapig-pincodeiq.hf.space/health
```

---

## 📡 API Endpoints

### Pincode

| Method | Endpoint                         | Description                      |
| ------ | -------------------------------- | -------------------------------- |
| GET    | `/pincode/{pincode}`             | Full details for a pincode       |
| GET    | `/pincode/validate/{pincode}`    | Check if pincode is valid        |
| GET    | `/pincode/search/query?q=`       | Search by area, district, state  |
| GET    | `/pincode/state/{state}`         | All pincodes in a state          |
| GET    | `/pincode/district/{district}`   | All pincodes in a district       |
| POST   | `/pincode/bulk`                  | Lookup up to 50 pincodes at once |
| GET    | `/pincode/serviceable/{pincode}` | Check if pincode is deliverable  |
| GET    | `/pincode/suggest/query?q=`      | Auto suggest post offices        |
| GET    | `/pincode/distance/calculate`    | Distance between two pincodes    |
| GET    | `/pincode/nearby/search`         | Pincodes within X km radius      |

### AI (Gemini Powered)

| Method | Endpoint                | Description                        |
| ------ | ----------------------- | ---------------------------------- |
| POST   | `/ai/parse-address`     | Extract pincode from messy address |
| POST   | `/ai/delivery-estimate` | Smart delivery time prediction     |

### API Keys

| Method | Endpoint              | Description                    |
| ------ | --------------------- | ------------------------------ |
| POST   | `/keys/create`        | Create a new API key           |
| GET    | `/keys/list`          | List all keys with usage stats |
| DELETE | `/keys/revoke/{name}` | Revoke a key                   |
| GET    | `/keys/stats/{name}`  | View key usage stats           |

### Health

| Method | Endpoint       | Description                     |
| ------ | -------------- | ------------------------------- |
| GET    | `/health`      | Full health check (DB + Gemini) |
| GET    | `/health/ping` | Lightweight uptime check        |

---

## 📦 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/vanshkapadia11/India-Pincode-API.git
cd India-Pincode-API
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
GEMINI_API_KEY=your_gemini_api_key
MASTER_API_KEY=your_master_key
```

### 4. Import pincode data

Download the India Post dataset from [data.gov.in](https://data.gov.in) and run:

```bash
python scripts/import_data.py pincode.csv
```

### 5. Add coordinates (for distance/nearby features)

```bash
python scripts/add_coordinates.py
```

### 6. Start the server

```bash
uvicorn app.main:app --reload
```

Open [http://localhost:8000/docs](http://localhost:8000/docs) 🎉

---

## 🔐 Authentication

All endpoints require an `X-API-Key` header.

```bash
curl -H "X-API-Key: your_api_key" https://vanshkapig-pincodeiq.hf.space/pincode/400001
```

Create your first key using the master key:

```bash
curl -X POST https://vanshkapig-pincodeiq.hf.space/keys/create \
  -H "X-API-Key: your_master_key" \
  -H "Content-Type: application/json" \
  -d '{"name": "myapp"}'
```

---

## 💡 Usage Examples

### Lookup a pincode

```bash
curl -H "X-API-Key: pk_xxx" \
  https://vanshkapig-pincodeiq.hf.space/pincode/400001
```

```json
{
  "pincode": "400001",
  "total_post_offices": 2,
  "post_offices": [
    {
      "post_office": "Fort S.O",
      "office_type": "S.O",
      "delivery": "Delivery",
      "district": "Mumbai",
      "state": "MAHARASHTRA"
    }
  ]
}
```

### AI Address Parser

```bash
curl -X POST https://vanshkapig-pincodeiq.hf.space/ai/parse-address \
  -H "X-API-Key: pk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"address": "near bandra station mumbai 400050"}'
```

```json
{
  "extracted_pincode": "400050",
  "corrected_pincode": "400050",
  "ai_message": "Pincode extracted successfully.",
  "details": { "...": "..." }
}
```

### Bulk Lookup

```bash
curl -X POST https://vanshkapig-pincodeiq.hf.space/pincode/bulk \
  -H "X-API-Key: pk_xxx" \
  -H "Content-Type: application/json" \
  -d '{"pincodes": ["400001", "110001", "560001"]}'
```

### Nearby Pincodes

```bash
curl -H "X-API-Key: pk_xxx" \
  "https://vanshkapig-pincodeiq.hf.space/pincode/nearby/search?pincode=400001&km=10"
```

### Distance Between Pincodes

```bash
curl -H "X-API-Key: pk_xxx" \
  "https://vanshkapig-pincodeiq.hf.space/pincode/distance/calculate?from_pincode=400001&to_pincode=110001"
```

```json
{
  "from_": { "pincode": "400001", "district": "Mumbai", "state": "MAHARASHTRA" },
  "to": { "pincode": "110001", "district": "Delhi", "state": "DELHI" },
  "distance_km": 1385.4,
  "distance_label": "1385.4 km"
}
```

---

## 🛠️ Tech Stack

| Layer         | Technology                   |
| ------------- | ---------------------------- |
| Framework     | FastAPI                      |
| Database      | PostgreSQL (Neon)            |
| ORM           | SQLAlchemy                   |
| AI            | Google Gemini 2.5 Flash      |
| Caching       | In-memory (Python)           |
| Rate Limiting | SlowAPI                      |
| Deployment    | Hugging Face Spaces + Docker |
| Data Source   | India Post (154,797 records) |

---

## 📁 Project Structure

```
pincodeiq/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # PostgreSQL connection
│   ├── models.py            # DB table models
│   ├── schemas.py           # Request/Response schemas
│   ├── logger.py            # Logging config
│   ├── middleware/
│   │   ├── auth.py          # API key authentication
│   │   ├── rate_limit.py    # Rate limiting
│   │   └── logging.py       # Request logging middleware
│   ├── routes/
│   │   ├── pincode.py       # Core pincode endpoints
│   │   ├── ai.py            # Gemini AI endpoints
│   │   ├── keys.py          # API key management
│   │   └── health.py        # Health check endpoints
│   └── services/
│       ├── pincode_service.py  # DB query logic
│       ├── geo_service.py      # Distance & nearby logic
│       ├── gemini_service.py   # Gemini API integration
│       └── cache_service.py    # In-memory cache
├── scripts/
│   ├── import_data.py       # Import India Post CSV
│   └── add_coordinates.py   # Add lat/lng via OpenStreetMap
├── Dockerfile
├── requirements.txt
└── .env
```

---

## ⚡ Rate Limits

| Endpoint                  | Limit         |
| ------------------------- | ------------- |
| Pincode lookup / validate | 60 req/min    |
| Search / state / district | 30 req/min    |
| Bulk lookup               | 20 req/min    |
| AI endpoints              | 20 req/min    |
| Nearby / distance         | 20-30 req/min |

---

## 🗺️ Roadmap

- [ ] Redis caching for production scale
- [ ] Webhook support for address validation
- [ ] Courier serviceability (Bluedart, Delhivery, DTDC)
- [ ] RapidAPI marketplace listing
- [ ] SDKs for Python, JavaScript, PHP

---

## 📄 License

MIT License — free to use for personal and commercial projects.

---

## 🙌 Contributing

Pull requests are welcome! For major changes, please open an issue first.

---

Built with ❤️ in India 🇮🇳