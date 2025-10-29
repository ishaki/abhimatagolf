import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'
import 'sonner/dist/styles.css' // Sonner v2 styles for toast notifications

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
