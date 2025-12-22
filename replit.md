# KT App - Knowledge Transfer Application

## Overview

This is a Knowledge Transfer (KT) application that combines a Python Streamlit frontend with a Node.js/Express backend infrastructure. The application allows users to upload documents (PDF, DOCX, TXT), process them using Google's Generative AI, and interact with the content through a chat interface. The project uses a hybrid architecture with Streamlit serving as the primary user interface while maintaining a full-stack TypeScript/React setup for potential future expansion.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Primary Interface**: Streamlit (Python) - handles document upload, AI-powered document processing, and chat functionality
- **Secondary Interface**: React with TypeScript - a complete SPA setup using Vite bundler, currently showing a 404 placeholder
- **UI Components**: shadcn/ui component library with Radix UI primitives, styled with Tailwind CSS
- **State Management**: React Query for server state, Streamlit session state for Python frontend
- **Routing**: Wouter for lightweight client-side routing in React

### Backend Architecture
- **Express.js Server**: Handles API routes and serves static files in production
- **Dual Runtime**: Python (Streamlit on port 5000) and Node.js coexist
- **Storage Pattern**: Interface-based storage abstraction (`IStorage`) with in-memory implementation, designed for easy database migration
- **Build System**: Custom esbuild configuration for server bundling, Vite for client

### Data Storage
- **Current**: In-memory storage using JavaScript Map for user data
- **Database Ready**: Drizzle ORM configured with PostgreSQL dialect, schema defined in `shared/schema.ts`
- **Schema**: Users table with UUID primary key, username, and password fields
- **Document Storage**: Local filesystem (`uploaded_docs/` directory) for Streamlit uploads

### AI Integration
- **Google Generative AI**: Used for document summarization and chat-based Q&A
- **Document Processing**: PDF (pypdf), DOCX (python-docx), and TXT file support

## External Dependencies

### AI Services
- **Google Generative AI** (`@google/generative-ai`, `google-generativeai`): Powers document analysis and conversational AI features

### Database
- **PostgreSQL**: Configured via `DATABASE_URL` environment variable
- **Drizzle ORM**: Type-safe database queries with Zod schema validation
- **connect-pg-simple**: Session storage for Express (available but not active)

### Python Libraries
- **Streamlit**: Web application framework for the main UI
- **pypdf**: PDF text extraction
- **python-docx**: Word document processing

### Frontend Libraries
- **Radix UI**: Accessible component primitives (dialog, dropdown, tabs, etc.)
- **Tailwind CSS**: Utility-first styling with custom theme configuration
- **React Hook Form + Zod**: Form handling with validation
- **Embla Carousel**: Carousel/slider functionality
- **Recharts**: Charting library for data visualization

### Build & Development
- **Vite**: Frontend build tool with HMR support
- **esbuild**: Server-side bundling for production
- **TypeScript**: Full type safety across the codebase