# Architecture Design

## System Components

### Frontend (React SPA)
- Responsive UI with Tailwind CSS
- State management with Redux Toolkit
- API client with Axios
- Authentication with JWT tokens

### Backend Services

#### API Gateway
- Routes requests to microservices
- Rate limiting and throttling
- Request validation
- CORS handling

#### Auth Service
- User registration and login
- JWT token generation
- Password hashing with bcrypt
- OAuth2 integration

#### Product Service
- Product CRUD operations
- Search with Elasticsearch
- Image storage in S3
- Inventory management

#### Order Service
- Order creation and tracking
- Order history
- Status updates
- Email notifications

#### Payment Service
- Stripe integration
- Payment processing
- Refund handling
- Transaction logging

## Data Flow
1. User authenticates via Auth Service
2. Frontend receives JWT token
3. Subsequent requests include JWT in headers
4. API Gateway validates token and routes to services
5. Services communicate via REST APIs
6. Events published to message queue for async processing
