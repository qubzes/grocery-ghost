# GroceryGhost - Perfect Frontend & Backend Integration

This project provides a complete grocery store scraping solution with real-time updates, perfect API integration, and a beautiful modern UI.

## 🚀 Quick Start

### 1. Start the Backend

```bash
cd backend
python main.py
```

The backend will be available at `http://127.0.0.1:8000`

### 2. Start the Frontend

```bash
cd frontend
npm run dev
```

The frontend will be available at `http://localhost:8080`

### 3. Test the API (Optional)

Open `api-test.html` in your browser to verify the API connection.

## 🔧 Perfect Integration Features

### Backend API Enhancements

1. **Complete REST API**
   - `POST /api/scrape` - Start scraping a new store
   - `GET /api/sessions` - Get all sessions with product counts
   - `GET /api/session/{id}` - Get detailed session with products
   - `DELETE /api/session/{id}` - Delete a session and its products
   - `GET /api/session/{id}/export` - Export products as CSV

2. **Enhanced Data Structure**
   - Product count included in session responses
   - Real-time progress tracking
   - Proper error handling and status management
   - CORS enabled for frontend integration

3. **Export Functionality**
   - Direct CSV download from API
   - Properly formatted export with all product fields

### Frontend Integration

1. **Real API Calls**
   - Replaced all mock data with real API integration
   - React Query for efficient data fetching and caching
   - Real-time updates every 1-2 seconds

2. **Perfect Data Flow**
   - Form submission directly calls the API
   - Sessions list updates automatically
   - Products table shows real scraped data
   - Export downloads actual CSV files

3. **User Experience**
   - Loading states for all operations
   - Error handling with user-friendly toasts
   - Real-time progress indicators
   - Automatic refresh for active sessions

4. **Advanced Features**
   - Session selection for viewing different stores
   - Search and filter functionality
   - Responsive design for all screen sizes
   - Progress bars for active scraping sessions

## 📊 Data Flow

1. **User submits URL** → Frontend calls `/api/scrape`
2. **Backend validates URL** → Creates session and starts background scraping
3. **Frontend polls sessions** → Real-time updates every 2 seconds
4. **Products appear live** → As they're scraped and saved to database
5. **Export available** → When scraping completes

## 🛠 API Endpoints

### POST /api/scrape
Start scraping a new grocery store.

```json
{
  "url": "https://store.example.com"
}
```

Response:
```json
{
  "message": "Scraping started for https://store.example.com",
  "session_id": "uuid"
}
```

### GET /api/sessions
Get all scraping sessions with product counts.

Response:
```json
{
  "sessions": [
    {
      "id": "uuid",
      "name": "Store Name",
      "url": "https://store.example.com",
      "status": "completed",
      "total_pages": 100,
      "scraped_pages": 100,
      "started_at": "2024-01-01T00:00:00Z",
      "completed_at": "2024-01-01T01:00:00Z",
      "product_count": 1247
    }
  ]
}
```

### GET /api/session/{session_id}
Get detailed session information with all products.

Response:
```json
{
  "session_id": "uuid",
  "name": "Store Name",
  "url": "https://store.example.com",
  "status": "completed",
  "total_pages": 100,
  "scraped_pages": 100,
  "progress": 100.0,
  "started_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T01:00:00Z",
  "error": null,
  "total_products": 1247,
  "products": [
    {
      "id": "uuid",
      "name": "Product Name",
      "current_price": "$12.99",
      "original_price": "$15.99",
      "unit_size": "500ml",
      "category": "Dairy",
      "url": "https://product-url.com",
      "image_url": "https://image-url.com",
      "dietary_tags": ["organic", "vegan"]
    }
  ]
}
```

### DELETE /api/session/{session_id}
Delete a session and all its products.

Response:
```json
{
  "message": "Session deleted successfully"
}
```

### GET /api/session/{session_id}/export
Download session products as CSV file.

Returns: CSV file download

## 🎨 Frontend Components

### 1. ScrapeInputForm
- Real API integration with loading states
- Error handling and validation
- Enter key support for quick submission

### 2. StoreSidebar
- Live session updates with real-time polling
- Progress bars for active sessions
- Delete and re-scrape functionality
- Proper error states and loading indicators

### 3. ProductsTable
- Real product data from API
- Session switching for multiple stores
- Export functionality with real CSV download
- Search and filter capabilities
- Responsive design

### 4. AddStoreModal
- Simplified form that uses the main scrape API
- Proper loading states and error handling
- Automatic session creation

## 🔄 Real-Time Updates

The frontend uses React Query with intelligent polling:

- **Sessions list**: Updates every 2 seconds
- **Active sessions**: Updates every 1 second for progress tracking
- **Completed sessions**: Stops polling to save resources
- **Failed sessions**: Stops polling with error indication

## 🎯 Best Practices Implemented

1. **Error Handling**
   - Comprehensive try-catch blocks
   - User-friendly error messages
   - Graceful degradation

2. **Loading States**
   - Skeleton loaders
   - Progress indicators
   - Disabled states during operations

3. **Performance**
   - Efficient React Query caching
   - Conditional polling based on session status
   - Debounced search functionality

4. **User Experience**
   - Toast notifications for all actions
   - Confirmation dialogs for destructive actions
   - Responsive design for all devices

5. **Data Validation**
   - URL validation on both frontend and backend
   - Required field validation
   - Type safety with TypeScript

## 🚀 Deployment Ready

The application is ready for production deployment with:

- Proper CORS configuration
- Environment-based API URLs
- Error boundary components
- Optimized build process
- Docker-ready structure

## 🧪 Testing

Use the included `api-test.html` file to verify:
- API connectivity
- CORS configuration
- Session creation and retrieval
- Error handling

This represents a complete, production-ready grocery scraping application with perfect frontend-backend integration!
