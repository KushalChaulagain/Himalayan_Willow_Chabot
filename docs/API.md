# API Documentation

Base URL: `https://your-app.railway.app` (or `http://localhost:8000` for development)

## Authentication

Currently, the API does not require authentication for chat and product endpoints. Future versions will implement JWT-based authentication for admin endpoints.

## Rate Limiting

- **Chat endpoints**: 60 requests per minute per IP
- **Other endpoints**: No limit (will be added in future)

## Endpoints

### Health Check

#### GET `/health`

Check if API is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-25T10:30:00Z",
  "environment": "production"
}
```

---

### Chat

#### POST `/api/chat/session`

Create a new chat session.

**Request Body:**
```json
{
  "user_id": 123  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "started_at": "2026-02-25T10:30:00Z"
}
```

#### POST `/api/chat/message`

Send a chat message and get AI response.

**Request Body:**
```json
{
  "message": "I want to buy a cricket bat",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"  // Optional
}
```

**Response:**
```json
{
  "message": "Great! I can help you find the perfect bat. What's your playing level?",
  "product_cards": [
    {
      "id": 1,
      "name": "Kashmir Willow Cricket Bat - Beginner",
      "price": 2500.00,
      "image_url": "https://...",
      "reason": "Perfect for beginners with good balance",
      "in_stock": true
    }
  ],
  "quick_replies": ["Beginner", "Intermediate", "Professional"],
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### GET `/api/chat/history/{session_id}`

Get chat history for a session.

**Response:**
```json
{
  "success": true,
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "sender": "user",
      "message": "I want a bat",
      "timestamp": "2026-02-25T10:30:00Z"
    },
    {
      "sender": "bot",
      "message": "Great! What's your budget?",
      "timestamp": "2026-02-25T10:30:05Z"
    }
  ]
}
```

---

### Orders

#### POST `/api/orders/create`

Create a new order.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "items": [
    {
      "product_id": 1,
      "product_name": "Kashmir Willow Bat",
      "product_sku": "BAT-KW-001",
      "unit_price": 250000,  // In paisa (NPR 2500)
      "quantity": 1,
      "subtotal": 250000
    }
  ],
  "payment_method": "esewa",  // "esewa" | "khalti" | "cod"
  "delivery_address": {
    "street": "Thamel, Kathmandu",
    "city": "Kathmandu",
    "postal_code": "44600"
  },
  "customer_phone": "9841234567",
  "customer_email": "customer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": "HW-12345",
  "total_amount": 2500.00,
  "payment_method": "esewa",
  "status": "PENDING",
  "message": "Order created successfully"
}
```

#### GET `/api/orders/{order_id}`

Get order details.

**Response:**
```json
{
  "success": true,
  "order": {
    "order_id": "HW-12345",
    "status": "CONFIRMED",
    "payment_status": "PAID",
    "payment_method": "esewa",
    "total_amount": 2500.00,
    "delivery_address": {
      "street": "Thamel, Kathmandu",
      "city": "Kathmandu",
      "postal_code": "44600"
    },
    "customer_phone": "9841234567",
    "courier_name": "Pathao",
    "tracking_number": "PATH123456",
    "created_at": "2026-02-25T10:30:00Z"
  }
}
```

#### POST `/api/orders/track`

Track order by order ID or phone number.

**Request Body:**
```json
{
  "order_id": "HW-12345"  // OR "phone_number": "9841234567"
}
```

**Response:**
```json
{
  "success": true,
  "orders": [
    {
      "order_id": "HW-12345",
      "status": "DISPATCHED",
      "payment_status": "PAID",
      "total_amount": 2500.00,
      "courier_name": "Pathao",
      "tracking_number": "PATH123456",
      "created_at": "2026-02-25T10:30:00Z"
    }
  ]
}
```

---

### Payments

#### POST `/api/payments/initiate`

Initiate payment for an order.

**Request Body:**
```json
{
  "order_id": "HW-12345",
  "payment_method": "esewa",
  "amount": 250000,  // In paisa
  "customer_info": {
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "9841234567",
    "address": {
      "street": "Thamel",
      "city": "Kathmandu",
      "postal_code": "44600"
    }
  }
}
```

**Response (eSewa):**
```json
{
  "success": true,
  "payment_url": "https://uat.esewa.com.np/epay/main",
  "payment_data": {
    "amount": 2500.00,
    "transaction_uuid": "HW-12345",
    "product_code": "EPAYTEST",
    "signature": "abc123...",
    "success_url": "https://api.example.com/api/payments/esewa/success",
    "failure_url": "https://api.example.com/api/payments/esewa/failure"
  }
}
```

**Response (Khalti):**
```json
{
  "success": true,
  "payment_url": "https://khalti.com/payment/...",
  "pidx": "khalti_payment_id",
  "expires_at": "2026-02-25T11:30:00Z"
}
```

**Response (COD):**
```json
{
  "success": true,
  "order_id": "HW-12345",
  "payment_method": "COD",
  "message": "Order confirmed! Our team will call you before dispatch."
}
```

#### POST `/api/payments/verify`

Verify payment completion.

**Request Body:**
```json
{
  "order_id": "HW-12345",
  "payment_method": "esewa",
  "payment_reference": "0007KMA"  // eSewa refId or Khalti pidx
}
```

**Response:**
```json
{
  "success": true,
  "message": "Payment verified"
}
```

#### GET `/api/payments/status/{order_id}`

Get payment status for an order.

**Response:**
```json
{
  "success": true,
  "order_id": "HW-12345",
  "payment_status": "PAID",
  "payment_method": "esewa",
  "payment_reference": "0007KMA"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "success": false,
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "timestamp": "2026-02-25T10:30:00Z"
}
```

### Common Error Codes

- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid auth)
- `404` - Not Found (resource doesn't exist)
- `429` - Too Many Requests (rate limit exceeded)
- `500` - Internal Server Error

---

## Webhooks

### eSewa Webhook

**POST `/api/webhooks/esewa`**

Receives payment confirmation from eSewa.

**Headers:**
- `X-eSewa-Signature`: HMAC signature for verification

**Request Body:**
```json
{
  "transaction_uuid": "HW-12345",
  "refId": "0007KMA",
  "status": "COMPLETE",
  "total_amount": 2500.00
}
```

---

## Interactive API Documentation

Visit `/docs` for interactive Swagger UI documentation where you can test all endpoints.

Example: `https://your-app.railway.app/docs`
