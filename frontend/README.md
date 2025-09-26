# Customer Support Chatbot Frontend

A modern React/TypeScript frontend for the customer support chatbot application.

## Features

- 🔐 **Secure Authentication** - Email and passcode login
- 💬 **Real-time Chat Interface** - Seamless conversation experience
- 📝 **Session Management** - Create, view, and switch between chat sessions
- 🎨 **Modern UI** - Clean, responsive design with Tailwind CSS
- 🔄 **Loading States** - Smooth user experience with loading indicators
- ⚠️ **Error Handling** - Graceful error messages and recovery

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Axios** for API communication
- **React Hook Form** for form handling
- **Zod** for validation
- **Lucide React** for icons

## Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

3. Open http://localhost:5173 in your browser

## Production

Build the application for production:
```bash
npm run build
```

The built files will be in the `dist` directory.

## Docker

Build and run with Docker:
```bash
docker build -t customer-support-frontend .
docker run -p 3000:80 customer-support-frontend
```

## Demo Credentials

You can use any email from the customer database with passcode: `12345`

Example:
- Email: `dmadocjones0@oracle.com`
- Passcode: `12345`