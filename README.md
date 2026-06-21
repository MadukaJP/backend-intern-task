# Text Classifier API

A high-performance text classification API built with FastAPI. It leverages Groq's Llama 3 model to classify incoming text into specific categories: question, complaint, feedback, request, spam, or other.

**Live Deployment URL:** [https://text-classify-api.vercel.app](https://text-classify-api.vercel.app)
**API Documentation:** [https://text-classify-api.vercel.app/docs](https://text-classify-api.vercel.app/docs)

---

## Table of Contents
1. [How It Works](#how-it-works)
2. [API Specification](#api-specification)
3. [Local Development Setup](#local-development-setup)
4. [Scaling Strategy (If Traffic Doubled)](#scaling-strategy-if-traffic-doubled)

---

## How It Works

The system is designed with responsiveness, rate limiting, and caching built in:

* **FastAPI Framework:** Handles asynchronous requests efficiently, enabling the API to sustain high concurrency.
* **LLM Integration via httpx:** Classifies incoming text using an asynchronous HTTP client to communicate with the Groq API. It enforces structured JSON responses via a system prompt.
* **In-Memory Caching:** Uses a TTL (Time-To-Live) cache powered by `cachetools`. Identical queries return cached results instantly, which bypasses downstream LLM calls and reduces latency.
* **Rate Limiting:** Enforces client-based rate limits using `slowapi` based on the real client IP.
* **Robust Error Handling:** Features custom exception handlers for validation errors, HTTP exceptions, and generic server errors to return clean JSON error payloads.

---

## API Specification

### 1. Classify Text
Classifies a piece of text into one of the designated categories.

* **Endpoint:** `POST /classify`
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "text": "Your text to classify goes here."
  }
  ```

* **Successful Response (200 OK):**
  ```json
  {
    "type": "question",
    "confidence": 0.95
  }
  ```

* **Error Response (422 Unprocessable Entity):**
  ```json
  {
    "status": "error",
    "message": "text is required"
  }
  ```

### 2. Health Check
* **Endpoint:** `GET /health`
* **Response (200 OK):**
  ```json
  {
    "status": "success",
    "message": "The service is running"
  }
  ```

### 3. Interactive API Documentation (Swagger UI)
* **Endpoint:** `GET /docs`
* **Description:** Provides the interactive Swagger UI documentation for testing and discovering endpoints.
* **Live Link:** [https://text-classify-api.vercel.app/docs](https://text-classify-api.vercel.app/docs)

---

## Local Development Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/MadukaJP/backend-intern-task.git
   cd backend-intern-task
   ```

2. **Set Up the Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory:
   ```env
   ENV=development
   GROQ_API_KEY=your_groq_api_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   RATE_LIMIT=120/minute
   ```

5. **Run the Server:**
   ```bash
   fastapi dev app.py
   ```

---

## Scaling Strategy (If Traffic Doubled)

If the sustained traffic doubles to 200 requests per minute or more, the system can scale through the following enhancements:

### 1. Distributed Cache (Redis)
* **Current State:** The current caching mechanism uses `cachetools.TTLCache` in memory. This is limited to individual application instances.
* **Scale Action:** We would replace the in-memory cache with a shared Redis instance. This ensures that cached classification results are shared across all scaled instances of the API, increasing the cache hit rate and removing redundant calls to Groq.

### 2. Centralized Rate Limiting
* **Current State:** `slowapi` manages rate limits in-memory on each local instance.
* **Scale Action:** We would configure `slowapi` or the underlying `limits` library to use Redis as a shared backend. This prevents users from bypassing the rate limit by hitting different load-balanced instances of the server.

### 3. Load Balancing and Horizontal Scaling
* **Current State:** Single application instance running behind Uvicorn.
* **Scale Action:** Deploy the application in containers using Docker. We can run multiple containers behind a load balancer (such as Nginx or AWS ALB) to distribute incoming traffic. The application can automatically scale out horizontally as CPU or network traffic increases.

### 4. Groq API Rate Limit Management
* **Current State:** Direct synchronous call to Groq's chat completion API.
* **Scale Action:** To handle higher volumes without hitting Groq API rate limits, we would implement key-rotation or establish a fallback to alternative providers (such as OpenAI or Anthropic). We can also utilize an asynchronous task queue like Celery or RabbitMQ to manage background processing if clients do not require real-time synchronous classification.
