import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './styles/globals.css'

// StrictMode disabled — it runs effects twice in dev which spawns/kills
// real PTY processes and causes double terminals + false exit messages.
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
